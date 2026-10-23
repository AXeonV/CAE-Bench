"""Replay actual fixed/upstream Cantera and independently cross-check complete physical outputs."""
import argparse,importlib.util,json,subprocess,time,shutil,hashlib
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
Q=Path(__file__).resolve().parents[1]
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--docker',default='docker');p.add_argument('--image',required=True);p.add_argument('--mode',required=True);a=p.parse_args()
 adapter=mod('adapter',Q/'public/run_case.py');checker=mod('checker',Q/'extension/caeoj_task_ext/flow_constraint.py');ind=mod('independent',Q/'author/independent.py')
 image=json.loads(subprocess.check_output([a.docker,'image','inspect',a.image]))[0]['Id'];report={'mode':a.mode,'image':image,'producer':'actual Cantera FlowReactor/ReactorNet (and real SurfPhase/kinetics direct outputs where requested)','cases':[]}
 policy=json.loads((Q/'author/grading-template.json').read_text())['quantities']
 for path in sorted((Q/'cases').glob('*/problem.json')):
  problem=load_problem(path);errors=[];checker.check(problem,errors)
  if errors:raise ValueError((path,errors))
  cmd=[a.docker,'run','--rm','--network','none','--cpus','4','--memory','8g','--user','1000:1000','-i',image,'/opt/cantera1655-build/bin/flow-driver']
  start=time.monotonic();r=subprocess.run(cmd,input=adapter.serialize(problem),text=True,capture_output=True,timeout=70)
  log=Path('work/repair-22/cantera-1655/replay')/a.mode/path.parent.name;log.mkdir(parents=True,exist_ok=True);(log/'stdout.json').write_text(r.stdout);(log/'stderr.log').write_text(r.stderr)
  if r.returncode:
   if a.mode=='reference':raise RuntimeError(str(path)+': '+r.stderr)
   report['cases'].append({'case':path.parent.name,'score':0,'status':'driver_failure','exit_code':r.returncode,'stderr':r.stderr});(Q/'author/data-evidence'/(a.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n');print(path.parent.name,a.mode,'driver_failure',flush=True);continue
  y=np.asarray(json.loads(r.stdout));values={k:y[None,:,left:right] for k,(left,right) in adapter.SLICES.items()};expected=ind.evaluate(problem.arrays);checks={}
  for k,v in values.items():
   rule=policy[problem.manifest['outputs'][k]['quantity']]['rule'];diff=abs(v-expected[k]);fraction=diff/(rule['atol']+rule['rtol']*abs(expected[k]));checks[k]={'max_absolute_error':float(diff.max()),'max_tolerance_fraction':float(fraction.max()),'passed':bool((fraction<=1).all())}
  if a.mode=='reference' and not all(v['passed'] for v in checks.values()):raise ValueError((path,checks))
  target=Q/'reference'/path.parent.name if a.mode=='reference' else log;target.mkdir(parents=True,exist_ok=True);out=target/('reference.h5' if a.mode=='reference' else 'result.h5');write_result(out,problem,values)
  if a.mode=='reference':write_direct_grading(target,author_policy(Q))
  grade=grade_case(path,out,Q/'reference'/path.parent.name/'grading.json');report['cases'].append({'case':path.parent.name,'score':grade['score'],'checks':checks,'elapsed_seconds':time.monotonic()-start,'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()});(Q/'author/data-evidence'/(a.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n');print(path.parent.name,a.mode,grade['score'],flush=True)
 if a.mode=='reference':
  for n,name in [('01','01-reacting-last-public'),('02','02-inert-last-public')]:
   root=Q/'samples'/n;shutil.copytree(Q/'cases'/name,root/'input',dirs_exist_ok=True);shutil.copytree(Q/'reference'/name,root/'reference',dirs_exist_ok=True);(root/'output').mkdir(exist_ok=True);shutil.copyfile(root/'reference/reference.h5',root/'output/result.h5')
