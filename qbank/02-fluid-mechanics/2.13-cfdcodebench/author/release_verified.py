"""Publish only fully certified CFDCodeBench24 data to an isolated HF branch.

Uses existing pack/upload/select/assemble/verify APIs. Never writes HF main.
The operation is resumable, with a durable fixed-commit consumer audit.
"""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
from catalog import ROOT,SECTION,WORK,catalog
from caeoj.sdk import load_problem,write_result
from caeoj_tools import data_pool as pool

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):pool.write_json(p,v)
def readiness():
 cert=read(WORK/'certification.json');installed=read(WORK/'installed-real-cases/summary.json')['rows']
 by={r['index']:r for r in cert};cli={r['index']:r for r in installed};missing=[]
 for c in catalog():
  i=c['index'];ref=WORK/'local-pool'/c['task']/f'C{i:02}-base/reference/reference.h5'
  if by.get(i,{}).get('status')!='verified_with_stated_limits' or cli.get(i,{}).get('status')!='passed':missing.append(i);continue
  if not ref.is_file() or sha(ref)!=by[i]['reference_sha256'] or sha(ref)!=cli[i]['reference_sha256']:missing.append(i)
 return by,missing

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);ap.add_argument('--branch',default='cases/cfdcodebench-24-20261020');ap.add_argument('--check',action='store_true');ap.add_argument('--publish',action='store_true');a=ap.parse_args()
 cert,missing=readiness()
 if a.check:print(json.dumps({'ready':not missing,'missing':missing,'expected':24}));return
 if missing:raise ValueError('Numerical/installed-reference gates not ready: '+str(missing))
 if not a.output:raise ValueError('Explicit output required')
 if a.branch in ('main','master') or not a.branch.startswith('cases/'):raise ValueError('Use an isolated cases/ branch')
 out=a.output.resolve();out.relative_to((ROOT/'runs').resolve());out.mkdir(parents=True,exist_ok=True)
 fd=os.open(out/'release.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 with os.fdopen(fd,'w') as f:json.dump({'pid':os.getpid(),'started_unix':time.time()},f)
 try:release(a,out,cert)
 finally:(out/'release.lock').unlink()

def release(a,out,cert):
 state_path=out/'release.json';state=read(state_path) if state_path.exists() else {'phase':'preparing','branch':a.branch,'repo_id':'jimzhouzzy2006/CAE-Bench-OJ','rows':[]}
 if state['branch']!=a.branch:raise ValueError('Branch differs from durable release intent')
 save(state_path,state)
 rows=[]
 for c in catalog():
  i=c['index'];task=SECTION/c['task'];source=WORK/'local-pool'/c['task']/f'C{i:02}-base'
  prepared=out/'prepared'/c['task'];bundle=out/'bundles'/c['task']
  if not bundle.exists():
   if prepared.exists():raise ValueError('Review partial prepared source before retry: '+str(prepared))
   shutil.copytree(source/'input',prepared/'cases/001');shutil.copytree(source/'reference',prepared/'reference/001')
   sample=prepared/'samples/01';shutil.copytree(source/'input',sample/'input')
   p=load_problem(sample/'input/problem.json');rng=np.random.default_rng(2026102000+i);fields={}
   for spec in p.manifest['outputs'].values():
    shape=(len(p.arrays[p.manifest['time_axes'][spec['time_axis']]]),len(p.arrays[p.manifest['locations'][spec['location']]['ids']]),*spec['component_shape'])
    fields[spec['array']]=rng.uniform(-1,1,shape).astype(spec['dtype'])
   write_result(sample/'output/result.h5',p,fields);save(sample/'example.json',{'kind':'format'})
   if (task/'data-manifest.json').exists():value=pool.manifest(task/'data-manifest.json')
   else:
    tid=f'caeoj-{i+5:06d}'
    if any(read(p).get('task_id')==tid for p in (ROOT/'qbank').rglob('data-manifest.json')):raise ValueError('Stable task ID conflict')
    value={'schema_version':4,'task_id':tid,'repository':{'repo_id':state['repo_id'],'repo_type':'dataset','path':task.relative_to(ROOT).as_posix()}}
   pool.pack(prepared,bundle,value)
  value,store,_=pool.validate_bundle(bundle);cid=value['cases']['001']['case_id']
  # A resumed bundle must still bind the currently certified input/reference.
  for path in (source/'input').rglob('*'):
   if path.is_file() and sha(path)!=sha(prepared/'cases/001'/path.relative_to(source/'input')):raise ValueError('Source input changed')
  if sha(prepared/'reference/001/reference.h5')!=cert[i]['reference_sha256'] or sha(source/'reference/grading.json')!=sha(prepared/'reference/001/grading.json'):raise ValueError('Certified reference or grading changed')
  selected=pool.select(value,store,['001='+cid],[],format_samples=['01='+cid]);save(bundle/'selection.json',selected)
  rows.append({'index':i,'task':c['task'],'task_id':value['task_id'],'pool_case_id':cid,'bundle':str(bundle),'reference_sha256':cert[i]['reference_sha256']})
 state.update(phase='prepared',rows=rows);save(state_path,state)
 if not a.publish:print(json.dumps({'phase':'prepared','tasks':24,'uploaded':False}));return
 from huggingface_hub import HfApi
 api=HfApi();repo=state['repo_id']
 if 'hf' not in state:
  base=api.repo_info(repo,repo_type='dataset',revision='main').sha
  branches={b.name:b.target_commit for b in api.list_repo_refs(repo,repo_type='dataset').branches}
  if a.branch in branches:raise ValueError('Unowned preexisting HF branch; choose a new name')
  state['hf']={'main_start_commit':base,'branch':a.branch,'uploads':[]};save(state_path,state)
  api.create_branch(repo,repo_type='dataset',branch=a.branch,revision=base)
  state['hf']['branch_created']=True;save(state_path,state)
 elif not state['hf'].get('branch_created'):
  # Recover only the exact branch creation, never adopt arbitrary data.
  branches={b.name:b.target_commit for b in api.list_repo_refs(repo,repo_type='dataset').branches}
  if a.branch not in branches:api.create_branch(repo,repo_type='dataset',branch=a.branch,revision=state['hf']['main_start_commit'])
  elif branches[a.branch]!=state['hf']['main_start_commit']:raise ValueError('Uncertain branch creation needs review')
  state['hf']['branch_created']=True;save(state_path,state)
 state['phase']='uploading';save(state_path,state)
 for row in rows:
  if any(r['task']==row['task'] for r in state['hf']['uploads']):continue
  receipt=pool.upload(Path(row['bundle']),revision=a.branch)
  state['hf']['uploads'].append({'task':row['task'],**receipt});save(state_path,state)
 fixed=state['hf'].get('fixed_commit') or api.repo_info(repo,repo_type='dataset',revision=a.branch).sha
 state['hf']['fixed_commit']=fixed;state['phase']='fixed_commit_verification';save(state_path,state)
 remote=pool.HubStore(repo,fixed,out/'hf-cache');installed=ROOT/'runs/install-check/cfdcodebench-20261019/venv/Scripts/python.exe'
 for row in rows:
  task=SECTION/row['task'];value=pool.manifest(Path(row['bundle'])/'selection.json')
  selected=pool.select(value,remote,['001='+row['pool_case_id']],[],format_samples=['01='+row['pool_case_id']])
  save(task/'data-manifest.json',selected);fetched=pool.fetch(selected,remote)
  assembly=pool.assemble(task,selected,remote,update=True);verified=pool.verify(task,strict=True)
  if fetched['revision']!=fixed or assembly.get('revision')!=fixed:raise ValueError('Consumer revision mismatch')
  if sha(task/'reference/001/reference.h5')!=row['reference_sha256']:raise ValueError('Downloaded reference SHA mismatch')
  if (task/'samples/01/reference').exists():raise ValueError('Format example leaks reference')
  commands=[['grade','--input',str(task/'cases/001/problem.json'),'--output',str(task/'reference/001/reference.h5'),'--grading',str(task/'reference/001/grading.json')],['validate-output','--input',str(task/'samples/01/input/problem.json'),'--output',str(task/'samples/01/output/result.h5')]]
  for j,args in enumerate(commands):
   p=subprocess.run([str(installed),'-I','-m','caeoj',*args],cwd=out,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/f"C{row['index']:02}-installed-{j}.json").write_text(p.stdout,encoding='utf-8')
   if p.returncode:raise RuntimeError('Installed consumer failed: '+p.stdout+p.stderr)
  detail={**row,'hf_branch':a.branch,'hf_commit':fixed,'manifest_sha256':sha(task/'data-manifest.json'),'descriptor_sha256':selected['cases']['001']['case']['sha256'],'samples':1,'sample_kind':'format','sample_seed':2026102000+row['index'],'sample_output_sha256':sha(task/'samples/01/output/result.h5'),'strict_integrity':verified,'assembly_report':assembly,'numerical_validation':cert[row['index']],'resource_status':'awaiting_calibration','installed_consumption':'passed'}
  save(task/'author/data-evidence/hf-release.json',detail)
  save(task/'author/data-evidence/format-example.json',{k:v for k,v in detail.items() if k!='numerical_validation'})
  state.setdefault('verified',{})[row['task']]=detail;save(state_path,state)
 state['hf']['main_end_commit']=api.repo_info(repo,repo_type='dataset',revision='main').sha
 state.update(phase='verified',verified_count=24,ended_unix=time.time());save(state_path,state)
 light={'task_count':24,'cases':24,'samples':24,'sample_kind':'format','hf':state['hf'],'full_report':state_path.relative_to(ROOT).as_posix(),'rows':[{k:v[k] for k in ('index','task','task_id','pool_case_id','reference_sha256','manifest_sha256','descriptor_sha256','sample_kind','sample_output_sha256')} for v in state['verified'].values()]}
 save(SECTION/'author/hf-release-index.json',light)
 save(SECTION/'author/local-assembly-index.json',{'schema_version':1,'task_count':24,'cases':24,'samples':24,'sample_kind':'format','hf_uploaded':True,'hf_branch':a.branch,'hf_commit':fixed,'strict_integrity':'24/24 passed','installed_consumption':'24/24 passed','resource_status':'awaiting_calibration','release_index':'hf-release-index.json','historical_23_task_batch':'history/local-assembly-23-20261020.json','rows':light['rows']})
 print(json.dumps({'phase':'verified','tasks':24,'branch':a.branch,'fixed_commit':fixed,'main_written':False}))
if __name__=='__main__':main()
