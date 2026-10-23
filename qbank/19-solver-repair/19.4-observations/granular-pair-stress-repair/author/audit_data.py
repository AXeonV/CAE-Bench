"""Audit every real reference and sample against independent pair mechanics."""
import copy,importlib.util,json
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.case_grading import grade_case
Q=Path(__file__).resolve().parents[1]
def mod(n,p):
    s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
c=mod('contract',Q/'extension/caeoj_task_ext/granular_contact.py');ind=mod('independent',Q/'author/independent.py');policy=json.loads((Q/'author/grading-template.json').read_text())['quantities']
report={'reference_producer':'actual repaired LAMMPS run0; audit independently enumerates physical contact pairs','cases':[],'samples':[],'invalid_variants':[]}
for path in sorted((Q/'cases').glob('*/problem.json')):
    p=load_problem(path);errors=[];c.check(p,errors);assert not errors,errors
    ref=Q/'reference'/path.parent.name;y=load_result(p,ref/'reference.h5');expected=ind.solve(p);checks={}
    for k,v in expected.items():
        rule=policy[p.manifest['outputs'][k]['quantity']]['rule'];diff=abs(y[k]-v);ratio=diff/(rule['atol']+rule['rtol']*abs(v));assert (ratio<=1).all(),(path,k);checks[k]={'max_absolute_error':float(diff.max()),'max_tolerance_fraction':float(ratio.max())}
    # Newton's third law is independent of stress reconstruction.
    assert np.linalg.norm(y['force'].sum(axis=1))<1e-7
    if 'particle_virial' in expected and 'pressure_tensor' in expected:
        assert np.allclose(y['particle_virial'].sum(axis=1),y['pressure_tensor'][:,0]*p.manifest['physics']['parameters']['box_length']['value']**3,atol=1e-7,rtol=1e-8)
    assert grade_case(path,ref/'reference.h5',ref/'grading.json')['score']==1
    report['cases'].append({'case':path.parent.name,'particles':len(p.arrays['particle_ids']),'checks':checks,'reference_grade':1,'force_balance':True})
for sample in sorted((Q/'samples').iterdir()):
    assert grade_case(sample/'input/problem.json',sample/'output/result.h5',sample/'reference/grading.json')['score']==1;report['samples'].append({'sample':sample.name,'complete_example_grade':1})
p=load_problem(next((Q/'cases').glob('*/problem.json')))
for name,kind,key,value in [('negative-diameter','array','diameter',-1),('zero-density','array','material_density',0),('excess-speed','array','velocity',1),('wrong-mode','parameter','tally_mode',3),('negative-stiffness','parameter','normal_stiffness',-1),('wrong-length-unit','unit','box_length','mm'),('outside-box','array','position',10)]:
    bad=copy.deepcopy(p)
    if kind=='array':bad.arrays[key][0,0,0]=value
    else:bad.manifest['physics']['parameters'][key]['unit' if kind=='unit' else 'value']=value
    errors=[];c.check(bad,errors);assert errors,name;report['invalid_variants'].append({'variant':name,'rejected':True})
bad=copy.deepcopy(p);bad.manifest['physics']['parameters']['newton_pair']={'value':1,'unit':'1'};errors=[];c.check(bad,errors);assert errors
report['invalid_variants'].append({'variant':'unsupported-newton-on-extra-parameter','rejected':True})
report['complete']=True;(Q/'author/data-evidence/data-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('all cases, examples, pair mechanics, force balance, cross-tally and invalid variants passed')
