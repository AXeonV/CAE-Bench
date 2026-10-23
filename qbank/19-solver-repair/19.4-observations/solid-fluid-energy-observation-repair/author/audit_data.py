"""Validate all actual inputs/results and task-specific declaration failures."""
import copy,importlib.util,json,tempfile
from pathlib import Path
from caeoj.sdk import load_problem,load_result
from caeoj.storage import write_hdf5
from caeoj.case_grading import grade_case
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('contract',TASK/'extension/caeoj_task_ext/energy_observation.py');ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
def checked(path):
 p=load_problem(path);errors=[];ext.check(p,errors)
 if errors:raise ValueError(errors)
 return p
report={'cases':[],'samples':[],'negative_variants':[]}
for path in sorted((TASK/'cases').glob('*/problem.json')):
 p=checked(path);d=TASK/'reference'/path.parent.name;load_result(p,d/'reference.h5');grade=grade_case(path,d/'reference.h5',d/'grading.json');assert grade['score']==1
 report['cases'].append({'case':path.parent.name,'model':p.manifest['physics']['model'],'frames':len(p.arrays['times']),'score':grade['score']})
for path in sorted((TASK/'samples').glob('*/input/problem.json')):
 d=path.parent.parent;checked(path);grade=grade_case(path,d/'output/result.h5',d/'reference/grading.json');assert grade['score']==1;report['samples'].append({'sample':d.name,'score':1})
original=load_problem(TASK/'cases/05-rz-normal-standard/problem.json')
def reject(name,mutate):
 m=copy.deepcopy(original.manifest);a={k:v.copy() for k,v in original.arrays.items()};mutate(m,a)
 with tempfile.TemporaryDirectory(dir=TASK/'cases') as tmp:
  d=Path(tmp);(d/'problem.json').write_text(json.dumps(m));write_hdf5(d/'input.h5',a)
  try:checked(d/'problem.json')
  except (ValueError,RuntimeError) as e:report['negative_variants'].append({'name':name,'rejected':True,'error':type(e).__name__});return
  raise AssertionError('Accepted malformed '+name)
reject('rz_swirl_padding',lambda m,a:a['velocity_coefficients'].__setitem__((0,0,8),1.))
reject('rz_zeta_temperature',lambda m,a:a['temperature_coefficients'].__setitem__((0,0,3),1.))
reject('float_mesh_integer',lambda m,a:m['physics']['parameters']['nx'].__setitem__('value',4.))
reject('zero_density',lambda m,a:m['physics']['parameters']['density_fluid'].__setitem__('value',0.))
reject('wrong_units',lambda m,a:m['outputs']['advection_power'].__setitem__('unit','J'))
reject('invalid_identity',lambda m,a:a['experiment_ids'].__setitem__(0,2))
reject('nonzero_initial_time',lambda m,a:a['initial_time'].__setitem__(0,1.))
report['complete']=True;(TASK/'author/data-evidence/data-audit.json').write_text(json.dumps(report,indent=2)+'\n',newline='\n');print({k:len(v) for k,v in report.items() if isinstance(v,list)})
