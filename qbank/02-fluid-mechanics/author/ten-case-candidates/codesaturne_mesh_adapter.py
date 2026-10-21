"""Finite frozen-case mesh preparation for the existing Code_Saturne reader.

Preprocessing only. This script does not solve a PDE or produce a reference.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import numpy as np
from elmer_flow_mesh import generate
from polytropic_reference import gmsh
from native_closed_cavity import SOCKET,save,digest
from titan_resources import reservation

IMAGE='sha256:e9cae326ea20d5903fdf819f21a58a3bfb179c8c194804724429a5c1979e40d9'
CASE='ch02-2-2-11-01-thermal_cavity'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--snapshot',type=Path,required=True);args=ap.parse_args()
    p=next(args.snapshot.glob('qbank/02-fluid-mechanics/*/newtonian-compressible-steady-3d/author/chapter02-ten-20261020/design.json'));freeze=json.loads((args.snapshot/'qbank/02-fluid-mechanics/author/ten-case-candidates/design-freeze.json').read_text());assert digest(p)==freeze['designs'][p.relative_to(args.snapshot).as_posix()];e=next(e for e in json.loads(p.read_text())['proposed_cases'] if e['design_id']==CASE);s=e['detailed_spec'];assert s['geometry']['operation']=='box' and not s['geometry']['holes']
    job=args.root/'maintenance/code-saturne-case-adapter';job.mkdir(exist_ok=True)
    assert not (job/'mesh-execution.json').exists(),'Finite preprocessing already recorded; inspect before repeating'
    name='ch02cs-preprocess-'+str(time.time_ns())[-9:]
    with reservation(args.root,name):
        save(job/'frozen-design.json',e);m=generate(s);x,c,b=m['x'],m['c'],m['b'];mid=x[b].mean(axis=1);L=s['geometry']['bounding_lengths'];group=np.where(np.isclose(mid[:,0],0.),2,np.where(np.isclose(mid[:,0],L[0]),3,4));assert all(np.any(group==i) for i in [2,3,4])
        gmsh(job/'public-mesh.msh',x,c,b,3)
        lines=['$MeshFormat','2.2 0 8','$EndMeshFormat','$PhysicalNames','4','3 1 "fluid"','2 2 "hot_wall"','2 3 "cold_wall"','2 4 "adiabatic_walls"','$EndPhysicalNames','$Nodes',str(len(x))]
        lines.extend(str(i+1)+' '+' '.join(format(float(v),'.17g') for v in row) for i,row in enumerate(x));lines+=['$EndNodes','$Elements',str(len(c)+len(b))]
        lines.extend(f'{i+1} 4 2 1 1 '+' '.join(str(int(v)+1) for v in row) for i,row in enumerate(c))
        lines.extend(f'{len(c)+i+1} 2 2 {group[i]} {group[i]} '+' '.join(str(int(v)+1) for v in row) for i,row in enumerate(b));lines+=['$EndElements'];(job/'native-mesh.msh').write_text('\n'.join(lines)+'\n')
        np.savez(job/'mesh-identity.npz',x=x,c=c,b=b,thermal_group=group)
        cmd=['docker','--host',SOCKET,'run','--name',name,'--network','none','--cpus','1','--memory','768m','--user',f'{os.getuid()}:{os.getgid()}','-v',str(job)+':/work','-w','/work',IMAGE,'/usr/lib/code_saturne/cs_preprocess','--format','gmsh','--reorient','--out','mesh_input','native-mesh.msh']
        with (job/'preprocessor.log').open('w') as log:cp=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=60)
        record={'case_id':CASE,'image':IMAGE,'command':cmd,'exit':cp.returncode,'script_sha256':digest(Path(__file__)),'nodes':len(x),'cells':len(c),'boundary_faces':len(b),'public_mesh_sha256':digest(job/'public-mesh.msh'),'native_mesh_sha256':digest(job/'native-mesh.msh'),'stage':'Native mesh conversion only; not solver execution or reference.','mapping':'Same node coordinates/connectivity/IDs; public MSH4.1 and native MSH2.2. Physical groups preserve actual frozen hot/cold/adiabatic partitions. Native preprocessor may reorient entities.','numerical_validation':False};save(job/'mesh-execution.json',record);assert cp.returncode==0,'Inspect native preprocessor.log';assert (job/'mesh_input').exists();record['mesh_input_sha256']=digest(job/'mesh_input');save(job/'mesh-execution.json',record);print(json.dumps(record))


if __name__=='__main__':main()
