"""Produce formal references with actual ASPECT, retain exact base replay separately."""
from pathlib import Path
import json,time
import numpy as np
from caeoj.sdk import load_problem,write_result
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'public'))
sys.path.insert(0,str(Path(__file__).parents[1]/'extension/caeoj_task_ext'))
from run_case import native,configuration
from deformed_tangential import check

W=Path('/work');report=json.loads((W/'formal-replay-report.json').read_text()) if (W/'formal-replay-report.json').exists() else {}
for case in sorted((W/'formal/cases').iterdir()):
 p=load_problem(case/'problem.json');errors=[];check(p,errors)
 if errors:raise ValueError((case.name,errors))
 v={k:x['value'] for k,x in p.manifest['physics']['parameters'].items()}
 for version in ['reference','baseline']:
  target=W/'formal'/('reference' if version=='reference' else 'defect')/case.name;target.mkdir(parents=True,exist_ok=True)
  output=target/('reference.h5' if version=='reference' else 'result.h5')
  cfg=target/'native-replay/input.prm'
  if version in report.get(case.name,{}) and output.exists() and cfg.exists() and cfg.read_text()==configuration(p.manifest,p.arrays['probe_coordinates'],target/'native-replay/native'):
   print(case.name,version,'reuse identical native configuration and retained successful output',flush=True);continue
  t=time.time();fields=native(p.manifest,p.arrays,'/work/aspect-'+version+'.native',target/'native-replay')
  write_result(output,p,fields)
  item={'seconds':time.time()-t,'points':len(p.arrays['probe_ids']),'frames':len(p.arrays['times'])}
  if p.manifest['physics']['model']=='deformed-tangential-parallel-v1':
   exact=np.zeros_like(fields['velocity']);exact[:,:,0]=v['velocity_x']
   rate=v['rate_x']*v['velocity_x']
   if p.manifest['spatial_dimension']==3:exact[:,:,1]=v['velocity_y'];rate+=v['rate_y']*v['velocity_y']
   exact[:,:,-1]=p.arrays['times'][:,None]*rate
   item['analytic_velocity_error']=float(np.max(abs(fields['velocity']-exact)));item['analytic_pressure_error']=float(np.max(abs(fields['pressure'])))
  elif p.manifest['physics']['model']=='deformed-tangential-annulus-v1':
   q=p.arrays['probe_coordinates'];exact=v['angular_speed']*np.column_stack([-q[:,1],q[:,0]])
   item['analytic_velocity_error']=float(np.max(abs(fields['velocity'][0]-exact)));item['analytic_pressure_error']=float(np.max(abs(fields['pressure'])))
  report.setdefault(case.name,{})[version]=item
  (W/'formal-replay-report.json').write_text(json.dumps(report,indent=2))
  print(case.name,version,item,flush=True)
