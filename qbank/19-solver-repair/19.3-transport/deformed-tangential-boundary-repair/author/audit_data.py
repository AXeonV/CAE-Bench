"""Audit actual formal declarations, reference coverage and grading boundaries."""
from pathlib import Path
import json,tempfile,sys
import numpy as np,h5py
from caeoj.sdk import load_problem
from caeoj.case_grading import grade_case
sys.path.insert(0,str(Path(__file__).parents[1]/'extension/caeoj_task_ext'))
from deformed_tangential import check
W=Path('/work');pool=W/'pool-source';report={}
for case in sorted((pool/'cases').iterdir()):
 p=load_problem(case/'problem.json');errors=[];check(p,errors)
 if errors:raise ValueError((case.name,errors))
 ref=pool/'reference'/case.name;g=ref/'grading.json'
 assert grade_case(case/'problem.json',ref/'reference.h5',g)['score']==1
 with h5py.File(ref/'reference.h5') as h:arrays={k:h[k][:] for k in h}
 policy=json.loads(g.read_text())['checks'][0]['policy']['quantities'];checks={}
 for quantity in ['velocity','pressure']:
  for factor in [.99,1.01]:
   data={k:v.copy() for k,v in arrays.items()};base=data[quantity].flat[0];rule=policy[quantity]['rule']
   data[quantity].flat[0]+=factor*(rule['atol']+rule['rtol']*abs(base))
   with tempfile.TemporaryDirectory() as tmp:
    out=Path(tmp)/'result.h5'
    with h5py.File(out,'w') as h:
     for k,v in data.items():h[k]=v
    score=grade_case(case/'problem.json',out,g)['score'];assert score==int(factor<1),(case.name,quantity,factor,score)
   checks[f'{quantity}_{factor}']=score
 report[case.name]={'declared_model':p.manifest['physics']['model'],'frames':len(p.arrays['times']),'points':len(p.arrays['probe_ids']),'self_grade':1,'threshold_boundaries':checks}
(W/'actual-data-audit.json').write_text(json.dumps(report,indent=2))
print('All 12 declarations/references and 48 actual pointwise threshold mutations passed')
