"""Audit every input/reference and rejection boundary with the installed public SDK."""
import copy,json,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,load_result
from caeoj.runtime import descriptor
from caeoj.storage import write_hdf5
from caeoj.case_grading import grade_case
TASK=Path(__file__).resolve().parents[1]
def main():
 assert descriptor().get('strict_tasks'), 'Install the public task SDK before this audit.'
 report={'installed_task_sdk':True,'cases':[]}
 for path in sorted((TASK/'cases').glob('*/problem.json')):
  problem=load_problem(path);ref=TASK/'reference'/path.parent.name
  load_result(problem,ref/'reference.h5');grade=grade_case(path,ref/'reference.h5',ref/'grading.json');assert grade['score']==1
  report['cases'].append({'case':path.parent.name,'programs':len(problem.arrays['program_ids']),'reference_self_grade':grade['score']})
 fixture=TASK/'cases/01-hysteretic-public';meta=json.loads((fixture/'problem.json').read_text());arrays=load_problem(fixture/'problem.json').arrays;results=[]
 def reject(name,edit):
  m=copy.deepcopy(meta);a={k:v.copy() for k,v in arrays.items()};edit(m,a)
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);(d/'problem.json').write_text(json.dumps(m));write_hdf5(d/'input.h5',a)
   try:load_problem(d/'problem.json')
   except (ValueError,RuntimeError) as e:results.append({'variant':name,'rejected':True,'exception':type(e).__name__});return
   raise AssertionError('Accepted invalid declaration: '+name)
 reject('unknown_material_kind',lambda m,a:a['material_kind'].__setitem__((0,0,0),2))
 reject('fractional_count',lambda m,a:a['history_count'].__setitem__((0,0,0),1.5))
 reject('hysteretic_four_points',lambda m,a:a['positive_count'].__setitem__((0,0,0),4))
 reject('nonzero_envelope_padding',lambda m,a:a['positive_strain'].__setitem__((0,0,6),.1))
 reject('nonmonotonic_envelope',lambda m,a:a['positive_strain'].__setitem__((0,0,1),a['positive_strain'][0,0,0]/2))
 reject('negative_positive_strength',lambda m,a:a['positive_stress'].__setitem__((0,0,0),-1))
 reject('stiffening_envelope',lambda m,a:a['positive_stress'].__setitem__((0,0,1),1e9))
 reject('zero_pinching',lambda m,a:a['pinching'].__setitem__((0,0,0),0))
 reject('negative_beta',lambda m,a:a['beta'].__setitem__((0,0,0),-1))
 reject('empty_trials',lambda m,a:a['trial_count'].__setitem__((0,0,0),0))
 reject('nonzero_history_padding',lambda m,a:a['history'].__setitem__((0,0,7),.01))
 reject('reversed_committed_history',lambda m,a:a['history'].__setitem__((0,0,1),-a['history'][0,0,1]))
 reject('excess_return_delta',lambda m,a:a['return_delta'].__setitem__((0,0,0),1e-7))
 reject('backward_nontrigger_return',lambda m,a:a['return_delta'].__setitem__((0,0,0),-1e-8))
 reject('nonmonotonic_continuation',lambda m,a:a['continuation'].__setitem__((0,0,1),a['continuation'][0,0,0]))
 reject('scored_at_knot',lambda m,a:a['history'].__setitem__((0,0,1),a['positive_strain'][0,0,0]))
 reject('probe_out_of_bounds',lambda m,a:a['trials'].__setitem__((0,0,0),.2))
 reject('wrong_work_unit',lambda m,a:m['outputs']['work_density'].__setitem__('unit','J'))
 reject('missing_beta',lambda m,a:m['fields'].pop('beta'))
 reject('extra_field',lambda m,a:m['fields'].__setitem__('unpromised',copy.deepcopy(m['fields']['beta'])))
 report['negative_variants']=results
 (TASK/'author/data-evidence/data-audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'cases':len(report['cases']),'negative_variants':len(results)}))
if __name__=='__main__':main()
