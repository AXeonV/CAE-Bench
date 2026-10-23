"""Compare actual independent Elmer nodal samples against actual ASPECT references."""
from pathlib import Path
import json,subprocess,sys
import h5py
import numpy as np
W=Path('/work');report={}
for case in ['09-wedge-negative','10-wedge-positive','11-wedge-static']:
 with h5py.File(W/'formal/reference'/case/'reference.h5') as h:reference={k:h[k][:] for k in ['velocity','pressure']}
 levels={}
 for level in ['h02','h01']:
  vel=[];pressure=[];offset=[]
  for frame in range(5):
   root=W/'independent-formal'/case/f't{frame}-{level}'
   if not (root/'mesh/flow.result').exists():raise RuntimeError(f'Missing actual independent run: {root}')
   subprocess.run([sys.executable,str(W/'read_elmer.py'),str(root)],check=True,stdout=subprocess.DEVNULL)
   y=json.loads((root/'native-probe-values.json').read_text())
   vel.append([p['velocity'] for p in y['samples']]);pressure.append([[p['pressure']] for p in y['samples']]);offset.append(y['surface_pressure_mean_removed'])
  vel=np.array(vel);pressure=np.array(pressure)
  levels[level]={'velocity':vel,'pressure':pressure}
  report.setdefault(case,{})[level]={'max_velocity_difference':float(np.max(abs(reference['velocity']-vel))),'max_pressure_difference':float(np.max(abs(reference['pressure']-pressure))),'largest_removed_pressure_offset':max(map(abs,offset)),'frames':5,'points':vel.shape[1]}
 report[case]['independent_refinement_change']={k:float(np.max(abs(levels['h02'][k]-levels['h01'][k]))) for k in ['velocity','pressure']}
 (W/'independent-formal-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
