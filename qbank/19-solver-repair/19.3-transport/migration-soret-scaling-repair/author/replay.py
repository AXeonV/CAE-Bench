"""Produce real Elmer fields, independently audit continuum and discrete solutions."""
import argparse,hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.validation import read_mesh
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
from independent import reference
TASK=Path(__file__).resolve().parents[1];ROOT=TASK.parents[3]
DOCKER='C:/Program Files/Docker/Docker/resources/bin/docker.exe'
sys.path.insert(0,str(TASK/'public'))
import run_case
from native_result import read_result
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--image',required=True);p.add_argument('--mode',choices=['reference','defect'],required=True);a=p.parse_args()
 checker=module('transport_checker',TASK/'extension/caeoj_task_ext/transport.py')
 image=json.loads(subprocess.check_output([DOCKER,'image','inspect',a.image]))[0]['Id']
 report={'image_id':image,'mode':a.mode,'producer':'Actual complete Elmer HeatSolve, StatCurrentSolve and AdvectionDiffusion modules on prescribed 2D QUAD4 mesh.', 'hash_semantics':{'native_input_sha256':'SHA256 concatenation of sorted relative native input filenames, NUL, and raw bytes for case.sif plus four mesh files before solver execution; not problem.json or HDF5 bytes.','result_sha256':'Raw HDF5 bytes written from actual native case.result fields. reference mode: task/reference/<case>/reference.h5; defect mode: authoring replay case directory/result.h5.'},'cases':[]}
 for path in sorted((TASK/'cases').glob('*/problem.json')):
  problem=load_problem(path);problem.meshes['main'].update(read_mesh(path.parent/'mesh.msh',geometry=True));errors=[];checker.check(problem,errors)
  if errors:raise ValueError((str(path),errors))
  directory=ROOT/'runs/authoring/repair-22/elmer-870-replay'/a.mode/path.parent.name;directory.mkdir(parents=True,exist_ok=True);run_case.prepare(problem,directory)
  h=hashlib.sha256()
  for f in sorted([directory/'case.sif',*[x for x in (directory/'mesh').glob('mesh.*') if x.suffix in ('.header','.nodes','.elements','.boundary')]]):h.update(f.relative_to(directory).as_posix().encode()+b'\0'+f.read_bytes())
  cmd=[DOCKER,'run','--rm','--network','none','--cpus','2','--memory','2g','--user','1000:1000','--mount',f'type=bind,source={directory.resolve()},target=/job','--workdir','/job',image,run_case.ELMER,'case.sif']
  started=time.monotonic();process=subprocess.run(cmd,capture_output=True,text=True,timeout=30);elapsed=time.monotonic()-started
  (directory/'stdout.log').write_text(process.stdout);(directory/'stderr.log').write_text(process.stderr)
  if process.returncode or 'ALL DONE' not in process.stdout:raise RuntimeError((str(path),process.returncode,process.stdout[-1500:],process.stderr))
  fields,frames=read_result(directory/'mesh/case.result');values={name:fields[key][None,:,None] for name,key in [('concentration','conc'),('temperature','thermalfield'),('potential','electricfield')]}
  discrete=reference(problem,discrete=True);continuum=reference(problem);rho=problem.manifest['physics']['parameters']['density']['value'];scale=rho if problem.manifest['physics']['parameters']['concentration_units']['value']==1 else 1
  checks={}
  for name,v in values.items():
   norm=scale if name=='concentration' else 1;err=float(np.max(abs(v-discrete[name])));continuum_err=float(np.max(abs(v-continuum[name])))
   bound=1e-9*norm if name=='concentration' else 1e-6 if name=='temperature' else 1e-10
   checks[name]={'discrete_max_absolute_error':err,'continuum_max_absolute_error':continuum_err,'concentration_scale':norm,'passed':err<=bound and (name!='concentration' or continuum_err/norm<=2e-6)}
  target=TASK/'reference'/path.parent.name if a.mode=='reference' else directory;target.mkdir(parents=True,exist_ok=True);output=target/('reference.h5' if a.mode=='reference' else 'result.h5');write_result(output,problem,values)
  if a.mode=='reference':
   if not all(c['passed'] for c in checks.values()):raise ValueError((str(path),checks))
   write_direct_grading(target,author_policy(TASK))
  grading=TASK/'reference'/path.parent.name/'grading.json';score=grade_case(path,output,grading)['score'] if grading.exists() else None
  report['cases'].append({'case':path.parent.name,'nodes':len(problem.arrays['node_ids']),'seconds':elapsed,'score':score,'checks':checks,'frames':frames,'native_input_sha256':h.hexdigest(),'result_sha256':hashlib.sha256(output.read_bytes()).hexdigest()})
  (TASK/'author/data-evidence'/(a.mode+'-replay.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(path.parent.name,a.mode,score,flush=True)
