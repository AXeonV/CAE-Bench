"""Independent cell-average transport of the specified piecewise-constant IC."""
import argparse
from pathlib import Path
import gmsh
import numpy as np
from caeoj.sdk import load_problem,read_constant,read_field,write_result


def solve(path,output):
    problem=load_problem(path)
    m=problem.manifest
    ids=problem.arrays[m['locations']['cells']['ids']]
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal',0)
        gmsh.open(str(Path(path).resolve().parent/m['meshes']['main']['file']))
        tags,values,_=gmsh.model.mesh.getNodes()
        coordinates=dict(zip(map(int,tags),values.reshape(-1,3)[:,0]))
        centers=[]
        for tag in ids:
            _,nodes,*_=gmsh.model.mesh.getElement(int(tag))
            centers.append(np.mean([coordinates[int(node)] for node in nodes]))
    finally:gmsh.finalize()
    order=np.argsort(centers);inverse=np.argsort(order)
    condition=next(c for c in m['conditions'] if c['role']=='initial')
    initial=read_field(problem,condition['data']['value'])[0,order,0]
    periodic=next(c for c in m['conditions'] if c['operator']=='periodic')
    length=read_constant(periodic['data']['period'])
    speed=read_constant(m['physics']['parameters']['velocity'])
    times=problem.arrays[m['time_axes']['output']]
    start=problem.arrays[m['time_axes']['initial']][0]
    displacement=(times-start)*speed*len(ids)/length
    shift=np.floor(displacement).astype(np.int64);fraction=displacement-shift
    values=np.array([(1-r)*np.roll(initial,int(j))+r*np.roll(initial,int(j)+1)
        for j,r in zip(shift,fraction)],dtype=np.float64)
    key=m['outputs']['state']['array']
    write_result(output,problem,{key:values[:,inverse,None]})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();solve(args.input,args.output)
