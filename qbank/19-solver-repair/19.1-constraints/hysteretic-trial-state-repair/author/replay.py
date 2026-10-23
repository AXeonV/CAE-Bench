"""Replay both genuine OpenSees materials and check every observation independently."""
import argparse,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
from independent import reference
TASK=Path(__file__).resolve().parents[1]
ROOT=TASK.parents[3]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--image',required=True);parser.add_argument('--mode',choices=['reference','defect'],required=True);args=parser.parse_args()
 adapter=module('adapter',TASK/'public/run_case.py');checker=module('checker',TASK/'extension/caeoj_task_ext/material_state.py')
 image=json.loads(subprocess.check_output([DOCKER,'image','inspect',args.image]))[0]['Id']
 report={'mode':args.mode,'image_id':image,'producer':'Actual upstream materials; independent piecewise backbone and committed trapezoid/state identities validate every output.','cases':[]}
 report['hash_semantics']={'driver_input_sha256': 'SHA256 of the exact UTF-8 serialized input.txt payload passed to the real C++ driver (public adapter serialize(programs(problem))); not raw input.h5 or problem.json bytes.', 'result_sha256': 'SHA256 of the HDF5 written by write_result from actual raw driver observations. reference mode: reference/<case>/reference.h5; defect mode: runs/authoring/repair-22/opensees-replay/defect/<case>/result.h5. It is not the raw driver output.txt hash.'}
 tolerances={'strain':(1e-19,0.),'stress':(1e-6,1e-10),'tangent':(1e-4,1e-10),'work_density':(1e-8,1e-10)}
 for path in sorted((TASK/'cases').glob('*/problem.json')):
  problem=load_problem(path);errors=[];checker.check(problem,errors)
  if errors:raise ValueError((path,errors))
  programs=adapter.programs(problem);directory=ROOT/'runs/authoring/repair-22/opensees-replay'/args.mode/path.parent.name;directory.mkdir(parents=True,exist_ok=True)
  (directory/'input.txt').write_text(adapter.serialize(programs),encoding='utf-8',newline='\n')
  command=[DOCKER,'run','--rm','--network','none','--cpus','2','--memory','2g','--user','1000:1000','--mount',f'type=bind,source={directory.resolve()},target=/job',image,'/opt/material-build/material_driver','/job/input.txt','/job/output.txt']
  started=time.monotonic();process=subprocess.run(command,capture_output=True,text=True,timeout=30);elapsed=time.monotonic()-started
  (directory/'stdout.log').write_text(process.stdout);(directory/'stderr.log').write_text(process.stderr)
  if process.returncode:raise RuntimeError((path,process.returncode,process.stderr))
  raw=np.loadtxt(directory/'output.txt').reshape(len(programs),6,4)
  exact=np.stack([reference(p) for p in programs]);values={name:raw[:,:,i][None] for i,name in enumerate(tolerances)};checks={}
  for i,(name,(atol,rtol)) in enumerate(tolerances.items()):
   error=abs(raw[:,:,i]-exact[:,:,i]);ratio=error/(atol+rtol*abs(exact[:,:,i]));checks[name]={'max_absolute_error':float(error.max()),'max_tolerance_fraction':float(ratio.max()),'passed':bool(np.all(ratio<=1))}
  target=TASK/'reference'/path.parent.name if args.mode=='reference' else directory;target.mkdir(parents=True,exist_ok=True)
  output=target/('reference.h5' if args.mode=='reference' else 'result.h5');write_result(output,problem,values)
  if args.mode=='reference':
   if not all(x['passed'] for x in checks.values()):raise ValueError((path,checks))
   write_direct_grading(target,author_policy(TASK))
  grading=TASK/'reference'/path.parent.name/'grading.json';score=grade_case(path,output,grading)['score'] if grading.exists() else None
  report['cases'].append({'case':path.parent.name,'programs':len(programs),'seconds':elapsed,'score':score,'checks':checks,'driver_input_sha256':hashlib.sha256((directory/'input.txt').read_bytes()).hexdigest(),'result_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
  (TASK/'author/data-evidence'/(args.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
  print(path.parent.name,args.mode,score,flush=True)
