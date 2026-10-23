"""Run actual Cantera driver and compare independent two-temperature mixture identities."""
import argparse,json,subprocess,time,importlib.util,hashlib,shutil
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
Q=Path(__file__).resolve().parents[1]
W=Path('work/repair-22/cantera-1872')
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--docker',default='docker');p.add_argument('--image');p.add_argument('--container');p.add_argument('--mode',choices=['reference','defect','validation'],required=True);a=p.parse_args()
 adapter=mod('adapter',Q/'public/run_case.py');validator=mod('validator',Q/'extension/caeoj_task_ext/plasma_state.py')
 report={'producer':'actual Cantera v3.1.0 PlasmaPhase API','mode':a.mode,'cases':[]}
 for path in sorted((Q/'cases').glob('*/problem.json')):
  problem=load_problem(path);errors=[];validator.check(problem,errors)
  if errors:raise ValueError(errors)
  cmd=[a.docker,'exec','-i',a.container,'/opt/cantera-source/build/bin/plasma-driver'] if a.container else [a.docker,'run','--rm','--network','none','--cpus','4','--memory','8g','--user','1000:1000','-i',a.image,'/opt/cantera-source/build/bin/plasma-driver']
  start=time.monotonic();r=subprocess.run(cmd,input=adapter.serialize(problem),text=True,capture_output=True,timeout=40)
  log=W/'replay'/a.mode/path.parent.name;log.mkdir(parents=True,exist_ok=True)
  (log/'stdout.json').write_text(r.stdout,encoding='utf-8');(log/'stderr.log').write_text(r.stderr,encoding='utf-8')
  if r.returncode:raise RuntimeError(r.stderr)
  y=np.asarray(json.loads(r.stdout));values={'pressure':y[None,:,0:1],'electron_pressure':y[None,:,1:2],'density':y[None,:,2:3],'concentrations':y[None,:,3:6]}
  expected=json.loads((W/'generated'/(path.parent.name+'.json')).read_text());checks={}
  for k,v in values.items():
   exact=np.asarray(expected[k]);atol={'pressure':1e-7,'electron_pressure':1e-7,'density':1e-12,'concentrations':1e-14}[k]
   z=abs(v-exact)/(atol+1e-10*abs(exact));checks[k]={'max_absolute_error':float(abs(v-exact).max()),'max_tolerance_fraction':float(z.max()),'passed':bool((z<=1).all())}
  target=Q/'reference'/path.parent.name if a.mode=='reference' else log;target.mkdir(parents=True,exist_ok=True)
  output=target/('reference.h5' if a.mode=='reference' else 'result.h5');write_result(output,problem,values)
  if a.mode=='reference':
   if not all(c['passed'] for c in checks.values()):raise ValueError((path,checks))
   write_direct_grading(target,author_policy(Q))
  grade=grade_case(path,output,Q/'reference'/path.parent.name/'grading.json')
  report['cases'].append({'case':path.parent.name,'score':grade['score'],'checks':checks,'elapsed_seconds':time.monotonic()-start,'command':cmd,'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
  (Q/'author/data-evidence'/(a.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
  print(path.parent.name,a.mode,grade['score'],flush=True)
 if a.mode=='reference':
  for n,name in [('01','01-issue-public'),('02','02-equilibrium-public')]:
   root=Q/'samples'/n;shutil.copytree(Q/'cases'/name,root/'input',dirs_exist_ok=True);shutil.copytree(Q/'reference'/name,root/'reference',dirs_exist_ok=True);(root/'output').mkdir(exist_ok=True);shutil.copyfile(root/'reference/reference.h5',root/'output/result.h5')
