from pathlib import Path
import json
import numpy as np,h5py
from caeoj.sdk import load_problem
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'public'))
from run_case import native
W=Path('/work');report={}
for name in ['02-annulus-public','09-wedge-negative','10-wedge-positive','11-wedge-static','12-annulus-reverse']:
 case=W/'formal/cases'/name;p=load_problem(case/'problem.json')
 m=json.loads(json.dumps(p.manifest));current=m['physics']['parameters']['refinement']['value']
 m['physics']['parameters']['refinement']['value']=4 if current==3 else 5
 y=native(m,p.arrays,'/work/aspect-reference.native',W/'formal-convergence'/name)
 with h5py.File(W/'formal/reference'/name/'reference.h5') as h:ref={k:h[k][:] for k in ['velocity','pressure']}
 report[name]={'formal_refinement':current,'check_refinement':m['physics']['parameters']['refinement']['value'],**{k+'_max_change':float(abs(y[k]-ref[k]).max()) for k in y}}
 (W/'formal-convergence-report.json').write_text(json.dumps(report,indent=2));print(name,report[name],flush=True)
