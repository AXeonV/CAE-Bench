"""Final read-only evidence closure; no prepare or native benchmark launch."""
from pathlib import Path
import json,hashlib,sys,subprocess
import numpy as np
import h5py
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
TASK=ROOT/'qbank/19-solver-repair/19.6-waves/complex-helmholtz-fmm-repair'
sys.path.insert(0,str(ROOT/'src'))
from caeoj.case_grading import grade_case
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def info(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
runpath=ROOT/'runs/authoring/repair-22/repair22-bempp20-oracle-v4.json';run=read(runpath)
assert run['phase']=='completed' and run['returncode']==0 and run['trials']==1 and run['exception_info'] is None
prepared=ROOT/'runs/harbor/tasks'/TASK.name
freeze=[]
for n,h in run['task_sha256'].items():
 p=prepared/n;actual=sha(p);assert actual==h,(n,h,actual);freeze.append(info(p))
assert len(freeze)==72
final_zip=sha(ROOT/'dist'/f'{TASK.name}-agent.zip')
assert final_zip=='3b2f5344125bf5679bd026bef828bbe97a44c9a132cca97a5975a25ed8d319bf'
assert all(run['task_sha256'][n]==final_zip for n in ['environment/agent.zip','tests/agent.zip'])
job=ROOT/'runs/harbor/jobs/repair22-bempp20-oracle-v4'
trials=[p for p in job.iterdir() if p.is_dir()];assert len(trials)==1
trial=trials[0];tr=read(trial/'result.json');assert tr['exception_info'] is None
v=trial/'verifier';report=read(v/'report.json')
assert report['complete'] is True and report['score']==report['completed_cases']==report['total_cases']==12 and report['reward']==1
assert float((v/'reward.txt').read_text())==1
cases=[];all_h5_elements=0
for row in report['cases']:
 c=row['case'];assert row['score']==1 and row['status']=='accepted'
 assert read(v/c/'execution.json') is None
 manifest=read(prepared/'tests/cases'/c/'problem.json')
 assert sha(prepared/'tests/cases'/c/'problem.json')==sha(TASK/'cases'/c/'problem.json')
 for asset in ['input.h5']+(['surface.msh'] if manifest['meshes'] else []):assert sha(prepared/'tests/cases'/c/asset)==sha(TASK/'cases'/c/asset)
 assert sha(prepared/'tests/reference'/c/'reference.h5')==sha(TASK/'reference'/c/'reference.h5')
 assert sha(prepared/'tests/reference'/c/'grading.json')==sha(TASK/'reference'/c/'grading.json')
 grade=grade_case(prepared/'tests/cases'/c/'problem.json',v/c/'result.h5',prepared/'tests/reference'/c/'grading.json');assert grade['score']==1
 arrays={};names={x['array'] for x in manifest['outputs'].values()}
 with h5py.File(v/c/'result.h5') as a,h5py.File(prepared/'tests/reference'/c/'reference.h5') as b:
  assert set(a)==set(b)
  for n in a:
   aa=a[n][...];bb=b[n][...];assert aa.shape==bb.shape and aa.dtype==bb.dtype
   all_h5_elements+=aa.size
   if n in names:
    fraction=np.abs(aa-bb)/(1e-6+1e-5*np.abs(bb));assert np.isfinite(aa).all() and (fraction<=1).all()
    arrays[n]={'shape':list(aa.shape),'max_absolute_error':float(np.max(np.abs(aa-bb))),'max_tolerance_fraction':float(np.max(fraction)),'scalar_count':int(aa.size)}
   else:assert np.array_equal(aa,bb),n
 cases.append({'case':c,'elapsed_seconds':row['elapsed_seconds'],'public_sample':row.get('public_sample'),'actual_output':info(v/c/'result.h5'),'reference':info(prepared/'tests/reference'/c/'reference.h5'),'arrays':arrays,'regrade_score':grade['score']})
assert {x['case']:x['public_sample'] for x in cases if x['public_sample']}=={'002':'01','007':'02'}
build=read(v/'build/report.json');baseline=read(v/'build/baseline-report.json');health=read(v/'build/baseline-probe-report.json')
cfg=read(prepared/'tests/source-repair.json')
assert build['status']==baseline['status']=='built' and health['status']=='ready'
assert all(x['elapsed_seconds']<60 for x in [build,baseline,health])
assert build['removed_build_artifacts']==baseline['removed_build_artifacts']==cfg['rebuild_files']
assert set(build['built_artifacts_sha256'])==set(cfg['rebuild_files'])
assert health['command'][5:]==cfg['baseline_probe']
for n,h in build['sources_sha256'].items():
 assert h==sha(TASK/'author/generated'/n)==sha(trial/'artifacts/app/submission'/n)==run['task_sha256']['solution/'+n]
assert (ROOT/'src/utils/harbor/tests/judge.py').read_bytes().replace(b'\r\n',b'\n')==(prepared/'tests/judge.py').read_bytes()
save('final-oracle-v4-independent.json',{'runner':info(runpath),'trial_result':info(trial/'result.json'),'trial_exception':tr['exception_info'],'frozen_files':freeze,'frozen_count':len(freeze),'frozen_mismatches':[],'zip_sha256':final_zip,'verifier_report':info(v/'report.json'),'physical_output_scalars':sum(v['scalar_count'] for c in cases for v in c['arrays'].values()),'all_hdf5_elements_including_axes':int(all_h5_elements),'cases':cases,'build':build,'baseline':baseline,'health':health,'health_stdout':(v/'build/baseline-probe-stdout.log').read_text(),'judge':info(prepared/'tests/judge.py'),'source_repair':info(prepared/'tests/source_repair.py'),'configuration':info(prepared/'tests/source-repair.json')})
context=ROOT/'work/repair-22/bempp-20/probe-context-v4';probes=ROOT/'runs/authoring/repair-22/bempp-backend-probes-v4'
assert sha(context/'tests/agent.zip')==final_zip
assert sha(context/'tests/judge.py')==sha(prepared/'tests/judge.py')
assert sha(context/'tests/source_repair.py')==sha(prepared/'tests/source_repair.py')
assert sha(context/'tests/source-repair.json')==sha(prepared/'tests/source-repair.json')
results=[]
for row in read(probes/'report.json'):
 if row['mode']=='image-build':assert row['returncode']==0;continue
 mode=row['mode'];p=probes/(mode+'.stdout.log');r=json.loads(p.read_text().strip().splitlines()[-1]);assert r['passed'] and row['returncode']==0
 if mode in ['valid','valid-surface']:
  assert r['binding']['uid']==1000 and r['binding']['network']=='denied'
  assert r['cpu_max'].strip()=='400000 100000' and r['memory_max'].strip()=='4294967296'
  assert not any(x['write'] for x in r['binding']['permissions'].values())
  assert r['build']['sources_sha256']==build['sources_sha256']
  assert r['build']['built_artifacts_sha256']==build['built_artifacts_sha256']
  for binding in r['binding']['binding'].values():
   assert binding['source_sha256']==build['sources_sha256'][Path(binding['source']).name]
   assert binding['pyc_sha256']==build['built_artifacts_sha256'][binding['cache']]
 elif mode=='compiler':assert r['error']=='Trusted baseline build failed: build_error'
 elif mode=='baseline-runtime':assert r['error']=='Trusted baseline runtime probe failed: probe_error'
 elif mode=='syntax':assert r['classification']=='build_error'
 elif mode in ['extra','symlink']:assert r['classification']=='invalid_submission'
 elif mode=='runtime-timeout':assert r['process_stopped']
 results.append({'run':row,'result':r,'stdout':info(p),'stderr':info(probes/(mode+'.stderr.log'))})
assert len(results)==8
save('final-probes-v4-independent.json',{'state':read(probes/'state.json'),'final_zip':info(context/'tests/agent.zip'),'fixture':info(context/'backend_probe.py'),'pipeline':info(ROOT/'runs/authoring/repair-22/bempp-probes-v4-pipeline.py'),'judge_sha256':sha(context/'tests/judge.py'),'source_repair_sha256':sha(context/'tests/source_repair.py'),'config_sha256':sha(context/'tests/source-repair.json'),'results':results})
offline=TASK/'author/data-evidence/offline-install-v2';state=read(offline/'state.json');installed=read(offline/'result.json')
assert state['zip_sha256']==final_zip and state['returncode']==0 and len(installed['cases'])==12
assert installed['installed_checker_sha256']==sha(TASK/'extension/caeoj_task_ext/helmholtz.py')
assert [(x['returncode'],x['score']) for x in installed['samples']]==[(1,0),(0,0)]
docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
image=subprocess.check_output([docker,'image','inspect','caeoj-bempp20-runtime:base','--format','{{.Id}}'],text=True).strip()
assert image==read(OUT/'runtime-readonly-inspection.json')['image_id']
save('final-offline-and-runtime-identity.json',{'offline_files':[info(p) for p in sorted(offline.iterdir()) if p.is_file()],'state':state,'result':installed,'check_script':info(ROOT/'work/repair-22/bempp-20/check-offline.py'),'current_base_image_id':image,'matches_preliminary_readonly_image':True})
print(json.dumps({'frozen_count':len(freeze),'cases':len(cases),'scalar_count':sum(v['scalar_count'] for c in cases for v in c['arrays'].values()),'max_tolerance_fraction':max(v['max_tolerance_fraction'] for c in cases for v in c['arrays'].values()),'probes':len(results),'baseline_seconds':baseline['elapsed_seconds'],'health_seconds':health['elapsed_seconds'],'candidate_seconds':build['elapsed_seconds'],'max_case_seconds':max(c['elapsed_seconds'] for c in cases)}))
