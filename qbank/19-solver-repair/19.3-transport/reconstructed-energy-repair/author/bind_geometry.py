"""Bind the documented fixed public geometry, never reference solution values."""
from pathlib import Path
import hashlib,json,re
import numpy as np
from caeoj.sdk import load_problem
Q=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    lines=(Q/'public/flatplate.su2').read_text().splitlines();row=next(i for i,line in enumerate(lines) if line.startswith('NPOIN'));n=int(lines[row].split('=')[1])
    points=np.array([[float(v) for v in line.split()[:2]] for line in lines[row+1:row+1+n]])
    row=next(i for i,line in enumerate(lines) if line.strip()=='MARKER_TAG= wall');nwall=int(lines[row+1].split('=')[1]);ids=np.unique([int(v) for line in lines[row+2:row+2+nwall] for v in line.split()[1:3]]);ids=ids[np.argsort(points[ids,0])]
    arrays={'node_coordinates':points,'wall_coordinates':points[ids]};values={}
    for name in ['node_coordinates','wall_coordinates']:
        x=np.array(arrays[name],dtype='<f8',copy=True);x[x==0]=0.;values[name]=hashlib.sha256(x.tobytes()).hexdigest()
    for path in sorted((Q/'cases').glob('*/problem.json')):
        p=load_problem(path)
        if p.manifest['physics']['parameters']['operation']['value']==1:
            for name in arrays:assert np.array_equal(p.arrays[name],arrays[name]),(path,name)
    path=Q/'extension/caeoj_task_ext/reconstruction.py';text=path.read_text();text=re.sub(r'^FIXTURE_COORDINATES = .*$', 'FIXTURE_COORDINATES = '+repr(values),text,flags=re.M);path.write_text(text,encoding='utf-8',newline='\n')
    (Q/'author/data-evidence/fixed-geometry-binding.json').write_text(json.dumps({'mesh_sha256':hashlib.sha256((Q/'public/flatplate.su2').read_bytes()).hexdigest(),'coordinate_arrays_sha256':values,'normalization':'little-endian float64, numerical zero normalized for checksum only'},indent=2)+'\n')
