"""Run genuine Meep, bind actual raw time traces, and independently audit DTFT."""
import argparse,hashlib,importlib.util,json,subprocess,time
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result
from caeoj.case_grading import grade_case
from caeoj_tools.grading_policy import author_policy,write_direct_grading
from independent import evaluate
TASK=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dataset',type=Path,required=True);p.add_argument('--image',required=True);p.add_argument('--docker',default='docker');p.add_argument('--mode',choices=['reference','defect','validation'],required=True);a=p.parse_args();adapter=module('dft_adapter',TASK/'public/run_case.py');contract=module('dft_contract',TASK/'extension/caeoj_task_ext/dft.py');image=json.loads(subprocess.check_output([a.docker,'image','inspect',a.image]))[0]['Id'];report={'mode':a.mode,'image_id':image,'reference_producer':'actual pinned full Meep FDTD plus actual native dft_chunk accumulator; independent trace DTFT is validation only','driver_sha256':hashlib.sha256((TASK/'public/driver.cpp').read_bytes()).hexdigest(),'cases':[]}
 for path in sorted((a.dataset/'cases').glob('*/problem.json')):
  problem=load_problem(path);errors=[];contract.check(problem,errors)
  if errors:raise ValueError(errors)
  parameters={n:r['value'] for n,r in problem.manifest['physics']['parameters'].items()};payload=adapter.serialize(problem);log=(a.dataset/'replay'/a.mode/path.parent.name).resolve();log.mkdir(parents=True,exist_ok=True)
  cmd=[a.docker,'run','--rm','--network','none','--cpus','4','--memory','4g','--user','1000:1000','-v',str(log)+':/audit','-i',image,'/opt/meep-repair-build/bin/dft-driver','/audit/trace.csv'];start=time.monotonic();r=subprocess.run(cmd,input=payload,text=True,capture_output=True,timeout=60);elapsed=time.monotonic()-start
  for name,data in [('payload.txt',payload),('stdout.json',r.stdout),('stderr.log',r.stderr)]: (log/name).write_bytes(data.encode())
  if r.returncode:raise RuntimeError(str(path)+': '+r.stdout+'\n'+r.stderr)
  raw=json.loads(r.stdout);actual=adapter.adapt(r.stdout);trace=np.loadtxt(log/'trace.csv',delimiter=',',skiprows=1);frequency=problem.arrays['frequency'][0,:,0];expected,stride=evaluate(trace,frequency,parameters);n=int((2*parameters['envelope_width']*parameters['cutoff']+parameters['after_sources'])*2*parameters['resolution']);assert len(trace)==n,(path,len(trace),n);assert np.allclose(trace[:,0],np.arange(1,n+1)*(.5/parameters['resolution']),rtol=0,atol=1e-12)
  delta=abs(actual['observed_dft'][0]-expected);ratio=delta/(1e-9+1e-8*abs(expected));checks={'spectrum_max_absolute_error':float(delta.max()),'spectrum_max_tolerance_fraction':float(ratio.max()),'spectrum_independent_passed':bool(np.all(ratio<=1)),'expected_stride':stride,'actual_stride':raw['stride'],'stride_passed':raw['stride']==stride,'dt_passed':raw['dt']==.5/parameters['resolution'],'window_end_passed':raw['final_time']==n*(.5/parameters['resolution'])}
  target=a.dataset/'reference'/path.parent.name if a.mode=='reference' else log;target.mkdir(parents=True,exist_ok=True);out=target/('reference.h5' if a.mode=='reference' else 'result.h5');write_result(out,problem,actual)
  if a.mode=='reference':
   if not all(checks[k] for k in ['spectrum_independent_passed','stride_passed','dt_passed','window_end_passed']):raise ValueError((path,checks))
   write_direct_grading(target,author_policy(TASK))
  grade=grade_case(path,out,a.dataset/'reference'/path.parent.name/'grading.json');row={'case':path.parent.name,'command':cmd,'elapsed_seconds':elapsed,'score':grade['score'],'checks':checks,'time_samples':n,'frequencies':len(frequency),'input_assets':{name:hashlib.sha256((path.parent/name).read_bytes()).hexdigest() for name in ['problem.json','input.h5']},'payload_sha256':hashlib.sha256(payload.encode()).hexdigest(),'trace_sha256':hashlib.sha256((log/'trace.csv').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest()};report['cases'].append(row);(a.dataset/(a.mode+'-report.json')).write_text(json.dumps(report,indent=2)+'\n');print(path.parent.name,a.mode,grade['score'],checks,flush=True)
