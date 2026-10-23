"""Audit all actual data with the independently installed strict public task SDK."""
import copy,json,shutil,tempfile
from pathlib import Path
from caeoj.sdk import load_problem,load_result
from caeoj.runtime import descriptor
from caeoj.storage import write_hdf5
from caeoj.case_grading import grade_case
TASK=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 assert descriptor().get('strict_tasks'),'Install the public task SDK first'
 report={'strict_installed_task_sdk':True,'cases':[]}
 for path in sorted((TASK/'cases').glob('*/problem.json')):
  p=load_problem(path);ref=TASK/'reference'/path.parent.name;load_result(p,ref/'reference.h5');score=grade_case(path,ref/'reference.h5',ref/'grading.json')['score'];assert score==1
  report['cases'].append({'case':path.parent.name,'nodes':len(p.arrays['node_ids']),'reference_self_grade':score})
 fixture=TASK/'cases/01-migration-relative-public';meta=json.loads((fixture/'problem.json').read_text());arrays=load_problem(fixture/'problem.json').arrays;results=[]
 def reject(name,edit):
  m=copy.deepcopy(meta);a={k:v.copy() for k,v in arrays.items()};edit(m,a)
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);(d/'problem.json').write_text(json.dumps(m));write_hdf5(d/'input.h5',a);shutil.copyfile(fixture/'mesh.msh',d/'mesh.msh')
   try:load_problem(d/'problem.json')
   except (ValueError,RuntimeError) as e:results.append({'variant':name,'rejected':True,'exception':type(e).__name__});return
   raise AssertionError('Accepted invalid input: '+name)
 def par(key,value):return lambda m,a:m['physics']['parameters'][key].__setitem__('value',value)
 reject('zero_density',par('density',0));reject('negative_diffusivity',par('diffusivity',-1e-9));reject('fractional_charge',par('ion_charge',.5));reject('excess_charge',par('ion_charge',4));reject('invalid_mode',par('mode',2));reject('invalid_concentration_mode',par('concentration_units',2));reject('combined_migration_soret',par('soret_diffusivity',1e-12));reject('excess_drive',par('ion_charge',3))
 reject('wrong_density_unit',lambda m,a:m['physics']['parameters']['density'].__setitem__('unit','g/cm3'))
 reject('wrong_soret_unit',lambda m,a:m['physics']['parameters']['soret_diffusivity'].__setitem__('unit','kg/(m.s.K)'))
 reject('nonisothermal_migration',lambda m,a:m['conditions'][1]['data']['value'].__setitem__('value',310))
 reject('mass_fraction_above_one',lambda m,a:m['conditions'][4]['data']['value'].__setitem__('value',1.1))
 reject('negative_mass_fraction',lambda m,a:m['conditions'][4]['data']['value'].__setitem__('value',-.1))
 reject('wrong_output_quantity',lambda m,a:m['outputs']['concentration'].__setitem__('quantity','mass_concentration'))
 reject('wrong_output_unit',lambda m,a:m['outputs']['concentration'].__setitem__('unit','kg/m3'))
 reject('extra_boundary',lambda m,a:m['conditions'].append(copy.deepcopy(m['conditions'][0])))
 reject('wrong_top_operator',lambda m,a:m['conditions'][5].__setitem__('operator','zero_total_diffusive_thermal_flux'))
 reject('missing_nodes',lambda m,a:a.__setitem__('node_ids',a['node_ids'][:-1]))
 reject('wrong_edge_membership',lambda m,a:a.__setitem__('bottom_ids',a['top_ids'].copy()))
 reject('wrong_time',lambda m,a:a['times'].__setitem__(0,1.))
 report['negative_variants']=results
 (TASK/'author/data-evidence/data-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':len(report['cases']),'negative_variants':len(results)}))
