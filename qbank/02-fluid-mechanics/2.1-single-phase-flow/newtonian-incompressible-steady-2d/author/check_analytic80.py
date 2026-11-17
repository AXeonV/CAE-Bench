from pathlib import Path
import argparse,json,sys,time
import numpy as np,h5py
from analytic80 import specifications,make_case,quadrature
import analytic80
p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();root=a.root
policy=json.loads((root/'grading-template.json').read_text());records=json.loads((root/'analytic-validation.json').read_text());report=[]
for row in records:
 s=row['definition'];name=s['name'];s.pop('pressure_shift',None)
 # Independent higher-order integration of the same published formula.
 analytic80.quadrature=lambda points,order=8:quadrature(points,16)
 started=time.monotonic();make_case(s,root/'quadrature16',policy)
 with h5py.File(root/'source/reference'/name/'reference.h5') as lo,h5py.File(root/'quadrature16/reference'/name/'reference.h5') as hi:
  j=json.loads((root/'source/cases'/name/'problem.json').read_text());ratios={}
  for key,f in j['outputs'].items():
   tol=policy['quantities'][f['quantity']]['rule'];x=lo[f['array']][:];y=hi[f['array']][:]
   ratios[key]=float(np.max(np.abs(x-y)/(tol['atol']+tol['rtol']*np.abs(y))))
 assert max(ratios.values())<.25,(name,max(ratios.values()))
 report.append(dict(name=name,max_tolerance_fraction=max(ratios.values()),fields=ratios,seconds=time.monotonic()-started))
(root/'evidence/analytic-quadrature.json').write_text(json.dumps(report,indent=2)+'\n')
print('quadrature',len(report),max(r['max_tolerance_fraction'] for r in report))
