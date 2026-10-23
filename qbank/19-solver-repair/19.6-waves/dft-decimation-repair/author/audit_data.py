"""Audit actual arrays, independent trace DTFT, and declaration/output failures."""
import argparse,copy,importlib.util,json,shutil,tempfile
from pathlib import Path
import numpy as np,h5py
from caeoj.sdk import load_problem,load_result
from caeoj.storage import write_hdf5
from caeoj.validation import write_json,ContractError
from caeoj.case_grading import grade_case
from independent import evaluate
TASK=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,default=TASK/'author/data-evidence/data-audit.json');a=p.parse_args();contract=module('dft_contract',TASK/'extension/caeoj_task_ext/dft.py');report={'cases':[],'samples':[],'declaration_variants':[],'output_variants':[]}
 for kind,paths in [('cases',sorted((a.dataset/'cases').glob('*/problem.json'))),('samples',sorted((a.dataset/'samples').glob('*/input/problem.json')))]:
  for path in paths:
   problem=load_problem(path);errors=[];contract.check(problem,errors);assert not errors,errors;ref=(a.dataset/'reference'/path.parent.name) if kind=='cases' else path.parent.parent/'reference';result=load_result(problem,ref/'reference.h5');assert grade_case(path,ref/'reference.h5',ref/'grading.json')['score']==1
   checks={}
   if kind=='cases':
    trace=np.loadtxt(a.dataset/'replay/reference'/path.parent.name/'trace.csv',delimiter=',',skiprows=1);params={k:r['value'] for k,r in problem.manifest['physics']['parameters'].items()};expected,stride=evaluate(trace,problem.arrays['frequency'][0,:,0],params);error=abs(expected-result['observed_dft'][0]);assert np.all(error<=1e-9+1e-8*abs(expected));assert np.all(result['sampling_stride']==stride);checks={'max_independent_DTFT_error':float(error.max()),'stride':stride,'all_four_components':True}
   else:assert grade_case(path,path.parent.parent/'output/result.h5',ref/'grading.json')['score']==1
   report[kind].append({'path':str(path),'requests':len(problem.arrays['probe_ids']),'checks':checks})
 original=load_problem(a.dataset/'samples/01/input/problem.json')
 mutations=[('linear-zero-chi',True,lambda m,x:(m['physics']['parameters']['chi2'].update(value=0.),m['physics']['parameters']['chi3'].update(value=0.))),('explicit-eight',True,lambda m,x:m['physics']['parameters']['decimation'].update(value=8)),('negative-source',True,lambda m,x:m['physics']['parameters']['source_amplitude'].update(value=-.5)),('zero-probe-label',True,lambda m,x:x.update(probe_ids=np.arange(len(x['probe_ids']),dtype='int64'))),('float-resolution',False,lambda m,x:m['physics']['parameters']['resolution'].update(value=20.)),('bool-decimation',False,lambda m,x:m['physics']['parameters']['decimation'].update(value=False)),('low-resolution',False,lambda m,x:m['physics']['parameters']['resolution'].update(value=9)),('zero-source-frequency',False,lambda m,x:m['physics']['parameters']['source_frequency'].update(value=0.)),('extra-parameter',False,lambda m,x:m['physics']['parameters'].update(extra={'value':1.,'unit':'1'})),('fractional-PML-cells',False,lambda m,x:m['physics']['parameters']['pml_width'].update(value=1.025)),('outside-monitor-index',False,lambda m,x:m['physics']['parameters']['monitor_index'].update(value=0)),('odd-cells',False,lambda m,x:(m['physics']['parameters']['length'].update(value=21.),m['physics']['parameters']['resolution'].update(value=15))),('misaligned-coordinate',False,lambda m,x:x['probe_coordinates'].__iadd__(1e-10)),('frequency-order',False,lambda m,x:x.update(frequency=x['frequency'][:,::-1].copy())),('bad-frequency-range',False,lambda m,x:x['frequency'].__setitem__((0,0,0),.01)),('nonzero-static-label',False,lambda m,x:x['times'].__setitem__(0,1.)),('output-component-order',False,lambda m,x:m['outputs']['observed_dft']['components'].reverse()),('wrong-output-unit',False,lambda m,x:m['outputs']['time_step'].update(unit='s')),('extra-HDF-key',False,lambda m,x:x.update(extra=np.array([1.])))]
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp)
  for name,expected,mutate in mutations:
   m=copy.deepcopy(original.manifest);x={k:v.copy() for k,v in original.arrays.items()};mutate(m,x);write_json(d/'problem.json',m);write_hdf5(d/'input.h5',x);accepted=True
   try:q=load_problem(d/'problem.json');errors=[];contract.check(q,errors);accepted=not errors
   except ContractError:accepted=False
   assert accepted==expected,(name,accepted,expected);report['declaration_variants'].append({'name':name,'accepted':accepted,'expected':expected})
  sample=a.dataset/'samples/01';ref=sample/'reference';input_path=sample/'input/problem.json'
  for name in ['reference','wrong-Hy-time','wrong-stride','missing-field','nonfinite']:
   f=d/'result.h5';shutil.copyfile(ref/'reference.h5',f)
   with h5py.File(f,'r+') as h:
    if name=='wrong-stride':h['sampling_stride'][...]=2.
    if name=='missing-field':del h['time_step']
    if name=='nonfinite':x=h['observed_dft'][:];x[0,0,0]=np.nan;h['observed_dft'][...]=x
    if name=='wrong-Hy-time':
     x=h['observed_dft'][:];freq=original.arrays['frequency'][0,:,0];z=(x[0,:,2]+1j*x[0,:,3])*np.exp(1j*np.pi*freq*.025);x[0,:,2]=z.real;x[0,:,3]=z.imag;h['observed_dft'][...]=x
   r=grade_case(input_path,f,ref/'grading.json');assert r['score']==(1 if name=='reference' else 0),(name,r);report['output_variants'].append({'name':name,'score':r['score'],'status':r['status']})
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':len(report['cases']),'samples':len(report['samples']),'declaration_variants':len(mutations),'output_variants':len(report['output_variants']),'passed':True}))
