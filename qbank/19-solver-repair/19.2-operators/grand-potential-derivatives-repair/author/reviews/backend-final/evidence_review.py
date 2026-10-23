from pathlib import Path
import json,hashlib,zipfile,tarfile,io,csv,re,sys,tempfile
import numpy as np,h5py
ROOT=Path(__file__).resolve().parents[3];TASK=ROOT/'qbank/19-solver-repair/19.2-operators/grand-potential-derivatives-repair';OUT=Path(__file__).parent;E=TASK/'author/data-evidence';sys.path.insert(0,str(ROOT/'src'))
from caeoj.sdk import load_problem
from caeoj.case_grading import prepare_case
sys.path.insert(0,str(TASK/'public'));import run_case
sha=lambda data:hashlib.sha256(data).hexdigest()
J=lambda p:json.loads(p.read_text())
report={'sha256':{},'frozen':{},'raw':[],'backend':[]}
def read(p):
 b=p.read_bytes();report['sha256'][str(p)]=sha(b);return b
def arrays(p):
 read(p)
 with h5py.File(p) as f:return {k:f[k][()] for k in f}
frozen=J(E/'harbor-oracle-v1/frozen-run.json');prepared=ROOT/'runs/harbor/tasks/grand-potential-derivatives-repair'
for name,s in frozen['task_sha256'].items():
 actual=sha(read(prepared/name));assert actual==s,(name,actual,s);report['frozen'][name]=actual
assert report['frozen']['tests/judge.py']=='5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f'
for rec in J(E/'harbor-oracle-v1/manifest.json'):
 p=TASK/rec['path'];assert len(read(p))==rec['bytes'] and sha(p.read_bytes())==rec['sha256']
zpath=ROOT/'dist/grand-potential-derivatives-repair-agent.zip';assert sha(read(zpath))=='04563d1ff3576d2ee759f620f3f8ae3d73dfb40a7aacab75912ccefde57e26cc'
with zipfile.ZipFile(zpath) as z:
 tarname=next(n for n in z.namelist() if n.endswith('public/moose-source.tar.gz'));blob=z.read(tarname);closure=J(E/'source-closure.json');assert sha(blob)==closure['closure_sha256']
 with tarfile.open(fileobj=io.BytesIO(blob)) as t:public={m.name:t.extractfile(m).read() for m in t if m.isfile()}
 assert set(public)=={r['path'] for r in closure['files']}
 for rec in closure['files']:assert sha(public[rec['path']])==rec['sha256']
 archive=Path('C:/Users/Jim Zhou/.cache/caeoj-repair22/archived-source-downloads/moose-30236-baseline.tar.gz');assert sha(read(archive))==closure['upstream_archive_sha256']
 wanted={rec['source_path']:rec['sha256'] for rec in closure['files']};found=set()
 with tarfile.open(archive,mode='r|gz') as t:
  prefix=None
  for member in t:
   if prefix is None:prefix=member.name+'/'
   name=member.name[len(prefix):]
   if name in wanted and member.isfile():assert sha(t.extractfile(member).read())==wanted[name],name;found.add(name)
 assert found==set(wanted)
 report['source_closure']={'count':len(public),'bytes':len(blob),'sha256':sha(blob),'all_fixed_archive_bytes_equal':True}
 versions=J(E/'target-source-versions.json')
 for name,expected in versions['files'].items():
  target='modules/phase_field/'+('src/materials/' if name.endswith('.C') else 'include/materials/')+name
  assert sha(public[target])==expected['baseline']
  for role,path in [('upstream',TASK/'author/upstream'/name),('author-complete',TASK/'author/generated'/name)]:assert sha(read(path))==expected[role]
 # Public archive must not contain author reference or hidden inputs.
 assert not any('/author/' in n or '/reference/' in n and '/samples/' not in n or '/cases/' in n and '/qbank/' in '/'+n for n in z.namelist())
report['source_versions']=versions
logical=['phi','eta0','eta1','eta2','eta3']
for problem in sorted((TASK/'cases').glob('*/problem.json')):
 name=problem.parent.name;m=J(problem);params={k:v['value'] for k,v in m['physics']['parameters'].items()};prob=load_problem(problem);plan=prepare_case(prob,TASK/'reference'/name/'grading.json');reference=arrays(TASK/'reference'/name/'reference.h5')
 with tempfile.TemporaryDirectory(dir=OUT) as tmp:
  run_case.prepare(prob,Path(tmp));native_input=(Path(tmp)/'case.i').read_bytes()
 for version in ['reference','upstream','defect']:
  d=ROOT/'runs/authoring/repair-22/moose-30236-replay'/version/name
  text=read(d/'stdout.log').decode();assert read(d/'case.i')==native_input;read(d/'stderr.log');rows=list(csv.DictReader(io.StringIO(read(d/'result.csv').decode())));assert len(rows)==1
  observed={k:np.zeros_like(reference[k]) for k in m['outputs']}
  for k in observed:
   if k.startswith('constraint_'):continue
   for i in range(observed[k].shape[1]):
    for c in range(observed[k].shape[2]):observed[k][0,i,c]=float(rows[0][f'p{i}_{k}_{c}'])
  vec=re.search(r'Vec_\w+\s*=\s*\[(.*?)\];',text,re.S);assert vec
  residual=np.array([float(x) for x in vec.group(1).split()]);analytic=text.split('Hand-coded Jacobian ----------',1)[1].split('Finite difference Jacobian ----------',1)[0]
  size=tuple(map(int,re.search(r'% Size = (\d+) (\d+)',analytic).groups()));matrix=np.zeros(size)
  for line in re.search(r'zzz = \[(.*?)\];',analytic,re.S).group(1).splitlines():
   if not line.strip():continue
   row,col,value=line.split();matrix[int(row)-1,int(col)-1]=float(value)
  dofs=sorted(csv.DictReader(io.StringIO(read(d/'result_dofs_0000.csv').decode())),key=lambda r:float(r['x']));assert len(dofs)==2*len(reference['program_ids'])
  names=logical+['w','c'] if params['variable_name_set']==0 else ['pore_state','grain_a','grain_b','grain_c','grain_d','mu_state','fraction_state']
  allids=[]
  for i in range(len(reference['program_ids'])):
   pair=dofs[2*i:2*i+2];L=params['probe_length'];assert np.allclose([float(x['x']) for x in pair],[3*i*L,(3*i+1)*L],atol=1e-12,rtol=1e-12)
   ids=[[int(float(x['dof_'+v])) for x in pair] for v in names];allids+=sum(ids,[]);row=ids[6]
   observed['constraint_residual'][0,i]=residual[row]
   observed['constraint_state_jacobian'][0,i]=np.concatenate([matrix[np.ix_(row,col)].ravel() for col in ids[:5]])
   observed['constraint_potential_jacobian'][0,i]=matrix[np.ix_(row,ids[5])].ravel();observed['constraint_concentration_jacobian'][0,i]=matrix[np.ix_(row,ids[6])].ravel()
  assert len(set(allids))==len(residual)==size[0]==size[1]
  for k in ['program_ids','times']:observed[k]=reference[k]
  actual=plan.evaluate(observed);score=actual['score']
  if version=='reference':assert all(np.array_equal(observed[k],reference[k]) for k in reference),(name,version)
  else:
   saved=arrays(d/'result.h5');assert all(np.array_equal(observed[k],saved[k]) for k in saved)
  report['raw'].append({'case':name,'version':version,'score':score,'all20_native_observations_reextracted':True,'mixed_hessian_accepted':actual['checks']['outputs']['fields']['solid_minimum_hessian']['passed']})
for d in sorted((E/'backend-raw').iterdir()):
 record=json.loads(read(d/'stdout.log'));assert record['passed'];read(d/'stderr.log')
 for p in (d/'verifier').rglob('*'):
  if p.is_file():read(p)
 report['backend'].append(record)
for path in [E/'public-cli.json',E/'hf-assembly.json',E/'runtime.json',TASK/'harbor/source-repair.json',TASK/'harbor/task.toml',TASK/'judge-config.json',ROOT/'src/utils/harbor/tests/source_repair.py',ROOT/'src/utils/harbor/tests/judge.py',Path(__file__)]:read(path)
publiccli=J(E/'public-cli.json');assert 'site-packages' in publiccli['installed_core'] and 'site-packages' in publiccli['installed_bundle']
assert [r['returncode'] for s in publiccli['samples'] for r in s['commands']]==[0,0,0,1]*2
report['public_cli']={'installed_core':publiccli['installed_core'],'installed_bundle':publiccli['installed_bundle'],'commands':8,'expected_baseline_scores':[json.loads(s['commands'][-1]['stdout'])['score'] for s in publiccli['samples']]}
report['formal_summary']={k:J(E/'harbor-oracle-v1/verifier-report.json')[k] for k in ['score','total_cases','completed_cases','complete','reward']}
original=J(E/'original-replay.json');report['original_execution']=[]
for row in original['versions']:
 d=ROOT/'runs/authoring/repair-22/moose-30236-original'/row['version'];assert sha(read(d/'SinteringParabolic.i'))==original['input_sha256'];assert sha(read(d/'stdout.log'))==row['stdout_sha256'];text=(d/'stdout.log').read_text();assert 'Time Step 2' in text
 for output in row['exodus_outputs']:assert sha(read(d/output['name']))==output['sha256']
 read(d/'stderr.log');report['original_execution'].append({'version':row['version'],'original_two_step_raw_and_exodus_hashes_valid':True})
(OUT/'evidence-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS source closure',report['source_closure'],'native raws',len(report['raw']),'probes',len(report['backend']))
