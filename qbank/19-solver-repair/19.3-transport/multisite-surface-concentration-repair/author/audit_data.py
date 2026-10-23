"""Audit every actual case/reference/sample and meaningful invalid declarations."""
import copy,importlib.util,json
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem
from caeoj.storage import read_arrays
from caeoj.case_grading import grade_case
Q=Path(__file__).resolve().parents[1]
def mod(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=mod('contract',Q/'extension/caeoj_task_ext/multisite_flow.py');ind=mod('independent',Q/'author/independent.py');policy=json.loads((Q/'author/grading-template.json').read_text())['quantities']
report={'cases':[],'samples':[],'invalid_variants':[],'reference_producer':'actual fixed Cantera; independent audit uses steady elimination and closed integral'}
occupancy=2 if ind.MULTI else 1
stoich=np.array([[-1,0,0,-occupancy,1],[1,0,0,occupancy,-1],[0,1,0,occupancy,-1]])
atoms=np.array([[1,0],[1,0],[1,0],[0,1],[1,occupancy]])
sites=np.array([0,0,0,1,occupancy]);assert np.all(stoich@atoms==0) and np.all(stoich@sites==0)
report['mechanism_atomic_and_site_balance']=True
for pth in sorted((Q/'cases').glob('*/problem.json')):
 p=load_problem(pth);errors=[];c.check(p,errors);assert not errors,errors
 expected=ind.evaluate(p.arrays);ref=Q/'reference'/pth.parent.name;y=read_arrays(ref/'reference.h5');checks={}
 for k,v in expected.items():
  rule=policy[p.manifest['outputs'][k]['quantity']]['rule'];diff=abs(y[k]-v);fraction=diff/(rule['atol']+rule['rtol']*abs(v));assert (fraction<=1).all(),(pth,k,fraction.max());checks[k]={'max_absolute_error':float(diff.max()),'max_tolerance_fraction':float(fraction.max())}
 assert grade_case(pth,ref/'reference.h5',ref/'grading.json')['score']==1
 report['cases'].append({'case':pth.parent.name,'states':len(p.arrays['state_ids']),'contract':True,'checks':checks,'reference_grade':1})
for sample in sorted((Q/'samples').iterdir()):
 assert grade_case(sample/'input/problem.json',sample/'output/result.h5',sample/'reference/grading.json')['score']==1;report['samples'].append({'sample':sample.name,'complete_example_grade':1})
p=load_problem(next((Q/'cases').glob('*/problem.json')))
variants=[('bad-order','species_order',6),('negative-density','site_density',-1),('zero-desorption','desorption_rate',0),('negative-distance','distance',-1),('bad-composition','inlet_mole_fractions',.99)]
if ind.MULTI:variants+=[('bad-coveragemode','coverage_mode',2),('negative-coverage','initial_coverages',-1)]
for name,k,v in variants:
 bad=copy.deepcopy(p);bad.arrays[k][0,0,0]=v;errors=[];c.check(bad,errors);assert errors,name;report['invalid_variants'].append({'variant':name,'rejected':True})
report['complete']=True;(Q/'author/data-evidence/data-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('all cases, public examples, atom/site balance, and invalid variants passed')
