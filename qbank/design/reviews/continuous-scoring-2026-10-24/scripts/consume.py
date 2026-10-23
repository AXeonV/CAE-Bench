"""Install and grade from the final RC, without importing the checkout."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('D:/Code/CAE-Bench-OJ')
WORK=ROOT/'runs/continuous-scoring'
RELEASE=ROOT/'runs/releases/caeoj-qbank-20261024-rc5'
CHECKS=ROOT/'runs/releases/verification-rc5-20261024'
CHECKS.mkdir(exist_ok=True)
catalog=json.loads((RELEASE/'catalog.json').read_text(encoding='utf-8'))
state={'started_unix':time.time(),'tasks':[],
       'scope':'Final RC extraction, normal pip install without dependencies, existing third-party environment, actual grader controls; no solver/model.'}
def save(): (WORK/'independent-consumption.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
def run(args,label,timeout=900):
    started=time.monotonic()
    p=subprocess.run(args,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=timeout)
    (WORK/(label+'.stdout.txt')).write_text(p.stdout,encoding='utf-8')
    (WORK/(label+'.stderr.txt')).write_text(p.stderr,encoding='utf-8')
    if p.returncode:raise RuntimeError(label+': '+p.stderr[-2000:]+' '+p.stdout[-1000:])
    return {'returncode':p.returncode,'seconds':time.monotonic()-started,'stdout':p.stdout}
save()
state['verify']=run([sys.executable,'-I',str(RELEASE/'release.py'),'verify'],'final-verify');save()
selected=['smoke-test','case-grading-test','heat-conduction-steady-2d','advection-1d',
          'newtonian-incompressible-transient-2d','immiscible-interface-2d',
          'cc-2d-steady-heat-equation','cc-2d-navier-stokes-cavity','cc-pipe-flow-disk-evp',
          'compressible-navier-stokes-3d']
for slug in selected:
    task=next(t for t in catalog['tasks'] if t['task']==slug)
    workspace=CHECKS/slug;installed=CHECKS/(slug+'-installed')
    record={'task':slug,'stage':'extracting'};state['tasks'].append(record);save()
    record['extract']=run([sys.executable,'-I',str(RELEASE/'release.py'),'extract',slug,str(workspace)],slug+'-extract')
    record['stage']='installing';save()
    record['install']=run([sys.executable,'-m','pip','install','--no-deps','--no-build-isolation','--no-compile','--target',str(installed),str(workspace)],slug+'-install',180)
    code=r'''
import json,sys,shutil,math,time
from pathlib import Path
installed=Path(INSTALLED);sys.path.insert(0,str(installed))
import h5py,numpy as np
import caeoj,caeoj_bundle
from caeoj.sdk import load_problem
from caeoj.validation import validate_output
from caeoj.case_grading import grade_case
from caeoj.grading_policy import resolve_policy
assert Path(caeoj.__file__).resolve().is_relative_to(installed.resolve())
root=Path(WORKSPACE);task=root/TASKPATH;slot=SLOT
problem=task/'cases'/slot/'problem.json';reference=task/'reference'/slot/'reference.h5';grading=task/'reference'/slot/'grading.json'
started=time.monotonic();positive=grade_case(problem,reference,grading);positive_seconds=time.monotonic()-started
assert positive['score']==1,positive
config=json.loads(grading.read_text(encoding='utf-8'));controls=[]
if 'scoring' in config and SLUG!='compressible-navier-stokes-3d':
 p=load_problem(problem);check=config['checks'][0];rules=resolve_policy(check['policy'],p)['fields']
 candidates=[(name,spec) for name,spec in p.manifest['outputs'].items() if spec['dtype']=='float64' and not check.get('transforms',{}).get(name,{}).get('remove_mean',False)]
 name,spec=candidates[0];rule=rules[name];key=spec['array']
 with h5py.File(reference) as f: values=f[key][...]
 field=values.reshape(values.shape[0],values.shape[1],-1)
 transform_offset=check.get('transforms',{}).get(name,{}).get('offset',0)
 centered=field[0,:,0]-transform_offset-rule.get('reference_offset',0)
 weights=p.arrays[p.manifest['fields'][rule['weight_field']]['array']][0,:,0] if 'weight_field' in rule else np.ones(len(centered))
 denominator=max(float(np.sqrt(np.average(centered**2,weights=weights))),rule['scale_floor'])
 for error,expected in [(0.025,1.0),(0.075,0.5),(0.125,0.0)]:
  output=root/('control-'+str(error)+'.h5');shutil.copyfile(reference,output)
  with h5py.File(output,'r+') as f:
   changed=values.copy();flat=changed.reshape(field.shape);flat[0,:,0]+=error*denominator;f[key][...]=changed
  result=grade_case(problem,output,grading)
  assert result['score'] is not None and abs(result['score']-expected)<1e-7,(name,error,expected,result)
  assert abs(result['total_nrmse']-error)<1e-8,result
  controls.append({'nrmse':result['total_nrmse'],'score':result['score'],'status':result['status'],'output':name})
 invalid=root/'invalid-output.h5';shutil.copyfile(reference,invalid)
 with h5py.File(invalid,'r+') as f: f[key][...]=np.nan
 invalid_result=grade_case(problem,invalid,grading)
 assert invalid_result['score']==0 and invalid_result['status']=='invalid_output',invalid_result
elif 'scoring' not in config:
 assert SLUG in ('smoke-test','case-grading-test')
samples=[]
for sample in sorted((task/'samples').iterdir()):
 if not sample.is_dir():continue
 assert not (sample/'reference').exists()
 assert validate_output(sample/'input/problem.json',sample/'output/result.h5')['valid']
 samples.append(sample.name)
loaded={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.startswith(('caeoj','caeoj_ext','caeoj_bundle')) and getattr(m,'__file__',None)}
assert all(Path(path).is_relative_to(installed.resolve()) for path in loaded.values()),loaded
budget=json.loads((task/'judge-config.json').read_text(encoding='utf-8')).get('evaluation_timeout_seconds',60)
assert positive_seconds<budget,('Actual evaluation exceeds declared evaluation budget',positive_seconds,budget)
print(json.dumps({'task':SLUG,'positive_score':positive['score'],'positive_evaluation_seconds':positive_seconds,'evaluation_budget_seconds':budget,'continuous_controls':controls,'format_samples_checked':samples,'loaded_project_modules':loaded}))
'''
    for token,value in [('INSTALLED',str(installed)),('WORKSPACE',str(workspace)),('TASKPATH',task['path']),('SLOT',next(iter(task['cases']))),('SLUG',slug)]:code=code.replace(token,repr(value))
    record['consumption']=json.loads(run([sys.executable,'-I','-X','utf8','-c',code],slug+'-grade',240)['stdout'])
    record['stage']='passed';save();print(slug+': final archive installed and actual scores checked',flush=True)
state.update(status='passed',completed_unix=time.time());save()
