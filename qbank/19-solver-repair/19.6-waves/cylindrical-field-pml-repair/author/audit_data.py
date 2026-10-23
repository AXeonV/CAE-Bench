"""Audit actual arrays, independent trace DTFT, and declaration/output failures."""
import argparse,copy,importlib.util,json,shutil,tempfile
from pathlib import Path
import numpy as np,h5py
from caeoj.sdk import load_problem,load_result
from caeoj.storage import write_hdf5
from caeoj.validation import write_json,ContractError
from caeoj.case_grading import grade_case
from independent import evaluate,continuum,nearfield
TASK=Path(__file__).resolve().parents[1]
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,required=True);p.add_argument('--output',type=Path,default=TASK/'author/data-evidence/data-audit.json');a=p.parse_args();contract=module('cyl_contract',TASK/'extension/caeoj_task_ext/cylindrical.py');report={'cases':[],'samples':[],'declaration_variants':[],'output_variants':[]}
 for kind,paths in [('cases',sorted((a.dataset/'cases').glob('*/problem.json'))),('samples',sorted((a.dataset/'samples').glob('*/input/problem.json')))]:
  for path in paths:
   problem=load_problem(path);errors=[];contract.check(problem,errors);assert not errors,errors;ref=(a.dataset/'reference'/path.parent.name) if kind=='cases' else path.parent.parent/'reference';result=load_result(problem,ref/'reference.h5');assert grade_case(path,ref/'reference.h5',ref/'grading.json')['score']==1
   checks={}
   if kind=='cases':
    trace=np.loadtxt(a.dataset/'replay/reference'/path.parent.name/'trace.csv',delimiter=',',skiprows=1);res=problem.manifest['physics']['parameters']['resolution']['value'];expected=evaluate(trace,.5/res);error=abs(expected-result['observed_dft'][0,0]);assert np.all(error<=1e-10+1e-8*abs(expected));params={k:r['value'] for k,r in problem.manifest['physics']['parameters'].items()};physical=nearfield(params,problem.arrays['probe_coordinates'][0]);native=result['observed_dft'][0,0,::2]+1j*result['observed_dft'][0,0,1::2];field_error=float(np.max(abs(native-physical)/abs(physical)));total_error=float(abs(np.sum(result['spectral_flux'])/sum(continuum(params))-1));assert field_error<.05 and total_error<.15,(path,field_error,total_error);checks={'max_independent_DTFT_error':float(error.max()),'all_twelve_components':True,'surface_integrals':result['spectral_flux'].tolist(),'continuum_field_max_relative_error':field_error,'continuum_total_flux_relative_error':total_error,'continuum_check_not_formal_tolerance':True}
   else:assert grade_case(path,path.parent.parent/'output/result.h5',ref/'grading.json')['score']==1
   report[kind].append({'path':str(path),'requests':len(problem.arrays['probe_ids']),'checks':checks})
 original=load_problem(a.dataset/'samples/01/input/problem.json')
 def resolution(m,x):
  m['physics']['parameters']['resolution']['value']=40;x['probe_coordinates']=np.array([[(2*40+1)*(.5/40),.5/40]],dtype='float64')
 mutations=[('mode-positive',True,lambda m,x:m['physics']['parameters']['mode'].update(value=1)),('negative-source',True,lambda m,x:m['physics']['parameters']['source_amplitude'].update(value=-.5)),('radial-PML-two',True,lambda m,x:m['physics']['parameters']['radial_pml'].update(value=2)),('resolution-forty',True,resolution),('float-mode',False,lambda m,x:m['physics']['parameters']['mode'].update(value=-1.)),('bool-mode',False,lambda m,x:m['physics']['parameters']['mode'].update(value=True)),('bad-mode',False,lambda m,x:m['physics']['parameters']['mode'].update(value=0)),('low-resolution',False,lambda m,x:m['physics']['parameters']['resolution'].update(value=20)),('zero-amplitude',False,lambda m,x:m['physics']['parameters']['source_amplitude'].update(value=0)),('fractional-rPML',False,lambda m,x:m['physics']['parameters']['radial_pml'].update(value=1.5)),('extra-parameter',False,lambda m,x:m['physics']['parameters'].update(extra={'value':1.,'unit':'1'})),('wrong-face-order',False,lambda m,x:x.update(face_ids=x['face_ids'][::-1].copy())),('wrong-face-label',False,lambda m,x:x['face_ids'].__setitem__(0,10)),('misaligned-coordinate',False,lambda m,x:x['probe_coordinates'].__iadd__(1e-10)),('nonzero-static-label',False,lambda m,x:x['times'].__setitem__(0,1.)),('component-order',False,lambda m,x:m['outputs']['observed_dft']['components'].reverse()),('flux-point-kind',False,lambda m,x:m['outputs']['spectral_flux'].update(value_kind='point')),('wrong-unit',False,lambda m,x:m['outputs']['time_step'].update(unit='s')),('extra-HDF',False,lambda m,x:x.update(extra=np.array([1.]))) ]
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);shutil.copyfile(original.path.parent/'surfaces.msh',d/'surfaces.msh')
  for name,expected,mutate in mutations:
   m=copy.deepcopy(original.manifest);x={k:v.copy() for k,v in original.arrays.items()};mutate(m,x);write_json(d/'problem.json',m);write_hdf5(d/'input.h5',x);accepted=True
   try:q=load_problem(d/'problem.json');errors=[];contract.check(q,errors);accepted=not errors
   except ContractError:accepted=False
   assert accepted==expected,(name,accepted,expected);report['declaration_variants'].append({'name':name,'accepted':accepted,'expected':expected})
  sample=a.dataset/'samples/01';ref=sample/'reference';input_path=sample/'input/problem.json'
  for name in ['reference','wrong-H-time','wrong-bottom-sign','wrong-end','missing-field','nonfinite']:
   f=d/'result.h5';shutil.copyfile(ref/'reference.h5',f)
   with h5py.File(f,'r+') as h:
    if name=='wrong-H-time':
     values=h['observed_dft'][:];z=values[...,6::2]+1j*values[...,7::2];z*=np.exp(1j*np.pi*(.5/30));values[...,6::2]=z.real;values[...,7::2]=z.imag;h['observed_dft'][...]=values
    if name=='wrong-bottom-sign':values=h['spectral_flux'][:];values[0,2,0]*=-1;h['spectral_flux'][...]=values
    if name=='wrong-end':h['window_end'][...]=0.
    if name=='missing-field':del h['time_step']
    if name=='nonfinite':values=h['spectral_flux'][:];values[0,0,0]=np.nan;h['spectral_flux'][...]=values
   grade=grade_case(input_path,f,ref/'grading.json');assert grade['score']==(1. if name=='reference' else 0.),(name,grade);report['output_variants'].append({'name':name,'score':grade['score'],'status':grade['status']})
 a.output.parent.mkdir(parents=True,exist_ok=True);write_json(a.output,report);print(json.dumps({'cases':len(report['cases']),'samples':len(report['samples']),'declaration_variants':len(report['declaration_variants']),'output_variants':len(report['output_variants'])}))
