"""Independent Re=100 centerline comparison, using the pinned upstream table."""
from pathlib import Path
import argparse, json
import numpy as np
from convert_supplement import vtu,sha

p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('table',type=Path);a=p.parse_args()
table=np.loadtxt(a.table)
reports=[]
for n in (16,32,64):
    file=a.root/'runs/lid-square'/f'n{n}'/'solution.00001.00000.vtu'
    raw=vtu(file);mask=np.isclose(raw['xyz'][:,0],2.)
    y=raw['xyz'][mask,1];u=raw['velocity'][mask,0]
    unique=np.unique(y);values=np.array([u[y==v].mean() for v in unique])
    sampled=[]
    for yn in table[:,0]:
        yp=4*yn;cell=min(int(yp*n),4*n-1);start=cell/n
        nodes=start+np.array([0.,.5,1.])/n
        v=np.array([values[np.argmin(abs(unique-node))] for node in nodes])
        t=(yp-start)*n
        sampled.append((2*(t-.5)*(t-1)*v[0]+4*t*(1-t)*v[1]+2*t*(t-.5)*v[2])/.1)
    sampled=np.array(sampled);error=abs(sampled-table[:,1])
    fraction=.1*error/(.001+.01*.1*np.abs(table[:,1]))
    reports.append(dict(n=n,reynolds=100,wall_speed=.1,table_sha256=sha(a.table),raw_vtu_sha256=sha(file),
                        max_normalized_error=float(error.max()),rms_normalized_error=float(np.sqrt(np.mean(error**2))),
                        max_physical_error_m_s=float(.1*error.max()),max_task_tolerance_fraction=float(fraction.max()),
                        rows=[dict(y=float(row[0]),published=float(row[1]),computed=float(value),difference=float(delta))
                              for row,value,delta in zip(table,sampled,error)]))
out=a.root/'evidence/ghia-independent.json';out.write_text(json.dumps(reports,indent=2)+'\n')
print([(r['n'],r['max_normalized_error']) for r in reports])
assert reports[-1]['max_task_tolerance_fraction']<1
