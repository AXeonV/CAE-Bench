"""Run genuine Meep, bind actual raw time traces, and independently audit DTFT."""
import argparse,hashlib,importlib.util,json,subprocess,time,uuid
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
from independent import evaluate,continuum,nearfield
TASK=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--image',required=True);p.add_argument('--docker',default='docker');p.add_argument('--resume',action='store_true');p.add_argument('--mode',choices=['reference','defect','validation'],required=True);a=p.parse_args();adapter=module('cyl_adapter',TASK/'public/run_case.py');contract=module('cyl_contract',TASK/'extension/caeoj_task_ext/cylindrical.py');image=json.loads(subprocess.check_output([a.docker,'image','inspect',a.image]))[0]['Id'];report={'mode':a.mode,'image_id':image,'reference_producer':'actual pinned full Meep FDTD plus actual native dft_chunk accumulator; independent trace DTFT is validation only','driver_sha256':hashlib.sha256((TASK/'public/driver.cpp').read_bytes()).hexdigest(),'cases':[]}
 previous=a.dataset/(a.mode+'-report.json');cached={}
 if a.resume and previous.exists():
  saved=json.loads(previous.read_text());assert saved['image_id']==image and saved['driver_sha256']==report['driver_sha256'] and saved['mode']==a.mode,'Cannot resume changed native producer';report=saved;cached={r['case']:r for r in saved['cases']}
 for path in sorted((a.dataset/'cases').glob('*/problem.json')):
  problem=load_problem(path);errors=[];contract.check(problem,errors)
  if errors:raise ValueError(errors)
  if path.parent.name in cached:
   row=cached[path.parent.name];assert all(hashlib.sha256((path.parent/n).read_bytes()).hexdigest()==v for n,v in row['input_assets'].items()),'Input changed during resume';log=a.dataset/'replay'/a.mode/path.parent.name;out=a.dataset/'reference'/path.parent.name/'reference.h5' if a.mode=='reference' else log/'result.h5';assert hashlib.sha256(out.read_bytes()).hexdigest()==row['output_sha256'] and hashlib.sha256((log/'trace.csv').read_bytes()).hexdigest()==row['trace_sha256'],'Result or trace changed during resume';assert grade_case(path,out,a.dataset/'reference'/path.parent.name/'grading.json')['score']==row['score'];print(path.parent.name,a.mode,'reused verified original actual replay',flush=True);continue
  parameters={n:r['value'] for n,r in problem.manifest['physics']['parameters'].items()};payload=adapter.serialize(problem);log=(a.dataset/'replay'/a.mode/path.parent.name).resolve();log.mkdir(parents=True,exist_ok=True)
  container='meep2338-'+uuid.uuid4().hex[:12];cmd=[a.docker,'run','--rm','--name',container,'--network','none','--cpus','4','--memory','4g','--user','1000:1000','-v',str(log)+':/audit','-i',image,'/opt/meep-repair-build/bin/cylindrical-driver','/audit/trace.csv'];start=time.monotonic()
  try:r=subprocess.run(cmd,input=payload,text=True,capture_output=True,timeout=1860)
  except subprocess.TimeoutExpired:
   subprocess.run([a.docker,'rm','--force',container],capture_output=True,text=True);(log/'timeout.json').write_text(json.dumps({'command':cmd,'timeout_seconds':1860,'actual_run_interrupted':True}));raise
  elapsed=time.monotonic()-start
  for name,data in [('payload.txt',payload),('stdout.json',r.stdout),('stderr.log',r.stderr)]: (log/name).write_bytes(data.encode())
  if r.returncode:raise RuntimeError(str(path)+': '+r.stdout+'\n'+r.stderr)
  raw=json.loads(r.stdout);actual=adapter.adapt(r.stdout);trace=np.loadtxt(log/'trace.csv',delimiter=',',skiprows=1);dt=.5/parameters['resolution'];expected=evaluate(trace,dt);n=1080*2*parameters['resolution'];assert len(trace)==n,(path,len(trace),n);assert np.allclose(trace[:,0],np.arange(1,n+1)*dt,rtol=0,atol=1e-12)
  delta=abs(actual['observed_dft'][0,0]-expected);ratio=delta/(1e-10+1e-8*abs(expected));checks={'runtime_within_case_budget':elapsed<1800,'spectrum_max_absolute_error':float(delta.max()),'spectrum_max_tolerance_fraction':float(ratio.max()),'spectrum_independent_passed':bool(np.all(ratio<=1)),'all_flux_finite_positive':bool(np.all(np.isfinite(raw['flux'])) and np.all(np.asarray(raw['flux'])>0)),'dt_passed':raw['dt']==dt,'window_end_passed':raw['time']==n*dt}
  complex_native=np.asarray(raw['fields']);complex_native=complex_native[:,0]+1j*complex_native[:,1];continuous_fields=nearfield(parameters,raw['probe']);checks['continuum_nearfield_max_relative_error']=float(np.max(abs(complex_native-continuous_fields)/abs(continuous_fields)));checks['continuum_total_flux_relative_error']=float(abs(sum(raw['flux'])/sum(continuum(parameters))-1));checks['continuum_physics_corrob_passed']=checks['continuum_nearfield_max_relative_error']<.05 and checks['continuum_total_flux_relative_error']<.15
  target=a.dataset/'reference'/path.parent.name if a.mode=='reference' else log;target.mkdir(parents=True,exist_ok=True);out=target/('reference.h5' if a.mode=='reference' else 'result.h5');write_result(out,problem,actual)
  if a.mode=='reference':
   if not all(checks[k] for k in ['continuum_physics_corrob_passed','runtime_within_case_budget','spectrum_independent_passed','all_flux_finite_positive','dt_passed','window_end_passed']):raise ValueError((path,checks))
   write_direct_grading(target,author_policy(TASK))
  grade=grade_case(path,out,a.dataset/'reference'/path.parent.name/'grading.json');row={'case':path.parent.name,'command':cmd,'elapsed_seconds':elapsed,'score':grade['score'],'checks':checks,'time_samples':n,'frequency':1.,'genuine_surface_integrals':raw['flux'],'input_assets':{name:hashlib.sha256((path.parent/name).read_bytes()).hexdigest() for name in ['problem.json','input.h5','surfaces.msh']},'payload_sha256':hashlib.sha256(payload.encode()).hexdigest(),'trace_sha256':hashlib.sha256((log/'trace.csv').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()};report['cases'].append(row);(a.dataset/(a.mode+'-report.json')).write_text(json.dumps(report,indent=2)+'\n');print(path.parent.name,a.mode,grade['score'],checks,flush=True)
