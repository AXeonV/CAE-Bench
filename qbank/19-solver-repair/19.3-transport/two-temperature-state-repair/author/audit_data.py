"""Audit all actual selected inputs, solver references, public outputs and rejection variants."""
from pathlib import Path
import json,importlib.util,copy
import numpy as np
from caeoj.sdk import load_problem
from caeoj.storage import read_arrays
from caeoj.case_grading import grade_case
Q=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('check',Q/'extension/caeoj_task_ext/plasma_state.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
report={'cases':[],'invalid_variants':[],'reference_producer':'actual fixed Cantera; audit independently recomputes mixture identities'}
for path in sorted((Q/'cases').glob('*/problem.json')):
 p=load_problem(path);errors=[];c.check(p,errors);assert not errors,errors
 a=p.arrays;x=a['mole_fractions'][0];T=a['temperature'][0,:,0];Te=a['final_electron_temperature'][0,:,0];v=a['constraint_value'][0,:,0];m=a['mode'][0,:,0]
 # Independent direct summation of particle partial pressures and masses.
 mw=np.sum(x*np.array([2*15.999,15.999,9.1093837015e-31*6.02214076e26])[None,:],axis=1)
 R=8.31446261815324e3;temps=np.column_stack([T,T,Te]);molar=v/mw
 molar[m==1]=v[m==1]/np.sum(x[m==1]*R*temps[m==1],axis=1)
 cs=x*molar[:,None]
 expected={'pressure':np.sum(cs*R*temps,axis=1)[None,:,None],'electron_pressure':(cs[:,2]*R*Te)[None,:,None],'density':(cs@np.array([31.998,15.999,9.1093837015e-31*6.02214076e26]))[None,:,None],'concentrations':cs[None]}
 ref=Q/'reference'/path.parent.name;values=read_arrays(ref/'reference.h5');checks={}
 for k,target in expected.items():
  atol={'pressure':1e-7,'electron_pressure':1e-7,'density':1e-12,'concentrations':1e-14}[k]
  err=np.abs(values[k]-target);fraction=err/(atol+1e-10*np.abs(target));assert np.all(fraction<=1),(path,k,fraction.max())
  checks[k]={'absolute_error':float(err.max()),'tolerance_fraction':float(fraction.max())}
 assert grade_case(path,ref/'reference.h5',ref/'grading.json')['score']==1
 report['cases'].append({'case':path.parent.name,'states':len(x),'input_contract':True,'independent_reference':checks,'reference_grade':1})
for case in sorted((Q/'samples').iterdir()):
 assert grade_case(case/'input/problem.json',case/'output/result.h5',case/'reference/grading.json')['score']==1
p=load_problem(next((Q/'cases').glob('*/problem.json')))
for name,key,value in [('illegal-mode','mode',2),('negative-T','temperature',-1),('overlarge-Te','final_electron_temperature',100001),('negative-density','constraint_value',-1),('bad-composition','mole_fractions',.9)]:
 bad=copy.deepcopy(p);bad.arrays[key][0,0,0]=value;errors=[];c.check(bad,errors);assert errors,name
 report['invalid_variants'].append({'variant':name,'rejected':True})
report['complete']=True;(Q/'author/data-evidence/data-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('all cases, samples and invalid variants passed')
