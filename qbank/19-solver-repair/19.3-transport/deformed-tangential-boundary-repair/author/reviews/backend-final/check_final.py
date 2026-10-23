"""Read-only final prepared identity and actual trial payload check."""
import hashlib,json,sys
from pathlib import Path
import h5py,numpy as np
ROOT=Path(__file__).resolve().parents[3];TASK=ROOT/'qbank/19-solver-repair/19.3-transport/deformed-tangential-boundary-repair';PREP=ROOT/'runs/harbor/tasks/deformed-tangential-boundary-repair';OUT=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
job=sys.argv[1] if len(sys.argv)>1 else 'repair22-aspect6818-oracle-v2'
state=json.loads((ROOT/'runs/authoring/repair-22'/(job+'.json')).read_text());report={'job':job,'phase':state['phase'],'frozen_files':{},'prepared_data':{},'trial':{}}
for name,digest in state['task_sha256'].items():
 actual=sha(PREP/name);assert actual==digest,(name,digest,actual);report['frozen_files'][name]=actual
assert report['frozen_files']['environment/agent.zip']==report['frozen_files']['tests/agent.zip']=='9acb735ced6dcc52c86ffb187a5c7b3ae34e784713ba5b963f6d412e3e6b63ee'
for c in (TASK/'cases').iterdir():
 for local,prepared in [(c,PREP/'tests/cases'/c.name),(TASK/'reference'/c.name,PREP/'tests/reference'/c.name)]:
  for p in local.iterdir():assert sha(p)==sha(prepared/p.name),(p,prepared)
 report['prepared_data'][c.name]='all input/reference/grading bytes exact'
judge=PREP/'tests/judge.py';source=ROOT/'src/utils/harbor/tests/judge.py';assert judge.read_bytes()==source.read_bytes().replace(b'\r\n',b'\n')
assert sha(judge)=='5595500ff6c8612f4682f4eda0cdc6521c5af94343dcba6c825bb3555141180f'
trials=list((ROOT/'runs/harbor/jobs'/job).glob('*/result.json'))
if len(trials)==1:
 trial=trials[0].parent;r=json.loads(trials[0].read_text());report['trial']['exception_info']=r.get('exception_info')
 for name in ['report.json','build/baseline-report.json','build/baseline-probe-report.json','build/report.json']:
  p=trial/'verifier'/name
  if p.exists():report['trial'][name]=json.loads(p.read_text())
 results=list((trial/'verifier').rglob('result.h5'));report['trial']['result_payloads']={}
 for path in results:
  name=path.parent.name
  if not (TASK/'reference'/name/'reference.h5').exists():continue
  with h5py.File(path) as a,h5py.File(TASK/'reference'/name/'reference.h5') as b:
   assert set(a)==set(b);eq={k:np.array_equal(a[k][:],b[k][:]) for k in b};assert all(eq.values()),(name,eq)
  report['trial']['result_payloads'][name]={'sha256':sha(path),'all_arrays_exactly_equal':True}
report['complete']=state['phase']=='completed' and report['trial'].get('exception_info') is None and len(report['trial'].get('result_payloads',{}))==12
(OUT/'final-check.json').write_text(json.dumps(report,indent=2));print({'phase':report['phase'],'complete':report['complete'],'frozen_files':len(report['frozen_files']),'result_payloads':len(report['trial'].get('result_payloads',{}))})
