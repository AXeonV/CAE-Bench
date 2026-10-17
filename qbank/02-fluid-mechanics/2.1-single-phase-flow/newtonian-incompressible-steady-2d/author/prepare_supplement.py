"""Reproducible Cartesian polygon cases; Lethe is the numerical producer.

Run on a Linux host with gmsh, numpy, h5py and the pinned Lethe installation.
This file builds meshes/configuration and converts output, never solves PDEs.
"""
from pathlib import Path
import argparse, json, os, subprocess, time
import numpy as np
import gmsh


def specifications():
    # Integer coordinates define exact polygonal geometry, not a raster approximation.
    return [
        dict(name='lid-square', boxes=[[0,0,4,4]], drive='lid', nu=0.004),
        dict(name='rotational-force-square', boxes=[[0,0,4,4]], drive='force', force=['-0.01*y','0.01*x']),
        dict(name='opposed-lids', boxes=[[0,0,6,3]], drive='opposed'),
        dict(name='shear-force-slip-channel', boxes=[[0,0,6,3]], drive='force', force=['0.01*y','0'], slip=[4,5]),
        dict(name='side-driven', boxes=[[0,0,5,4]], drive='side'),
        dict(name='lid-step-floor', boxes=[[0,1,3,5],[3,0,6,5]], drive='lid'),
        dict(name='lid-central-pedestal', boxes=[[0,0,6,5]], holes=[[2,0,4,2]], drive='lid'),
        dict(name='lid-square-obstacle', boxes=[[0,0,6,6]], holes=[[2,2,4,4]], drive='lid'),
        dict(name='lid-two-obstacles', boxes=[[0,0,8,5]], holes=[[2,1,3,3],[5,1,6,3]], drive='lid'),
        dict(name='lid-offset-baffle', boxes=[[0,0,6,5]], holes=[[2,0,3,3]], drive='lid'),
        dict(name='force-island-chamber', boxes=[[0,0,6,5]], holes=[[3,2,4,4]], drive='force', force=['-0.01*y','0.01*x']),
        dict(name='lid-L-chamber', boxes=[[0,0,3,6],[3,3,6,6]], drive='lid'),
        dict(name='lid-T-chamber', boxes=[[0,3,8,6],[3,0,5,3]], drive='lid'),
        dict(name='lid-cross-chamber', boxes=[[0,2,8,5],[2,0,5,7]], drive='lid'),
        dict(name='force-three-ribs', boxes=[[0,0,9,5]], holes=[[1,0,2,2],[4,0,5,3],[7,0,8,2]], drive='force', force=['0.01*y','0']),
        dict(name='lid-staggered-islands', boxes=[[0,0,8,6]], holes=[[2,1,3,3],[5,3,6,5]], drive='lid'),
        dict(name='four-wall-circulation', boxes=[[0,0,5,5]], drive='circulation'),
        dict(name='opposed-side-walls', boxes=[[0,0,5,5]], drive='side-opposed'),
        dict(name='force-split-recess', boxes=[[0,2,8,5],[0,0,2,2],[6,0,8,2]], drive='force', force=['0','0.01*x']),
        dict(name='lid-serpentine-chamber', boxes=[[0,4,8,6],[0,2,2,4],[0,0,6,2],[4,2,6,3]], drive='lid', force=['0.01*y','0']),
    ]


def inside(x,y,s):
    return any(a<x<c and b<y<d for a,b,c,d in s['boxes']) and not any(a<x<c and b<y<d for a,b,c,d in s.get('holes',[]))


def build_mesh(s, n, directory):
    xmax=max(b[2] for b in s['boxes']); ymax=max(b[3] for b in s['boxes'])
    cells=[(i,j) for i in range(xmax*n) for j in range(ymax*n) if inside((i+.5)/n,(j+.5)/n,s)]
    vertices=sorted(set(v for i,j in cells for v in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]))
    tags={v:k+1 for k,v in enumerate(vertices)}
    quads=[[tags[v] for v in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]] for i,j in cells]
    edges={}
    for q in quads:
        for a,b in zip(q,q[1:]+q[:1]):
            key=tuple(sorted((a,b)))
            if key in edges: del edges[key]
            else: edges[key]=(a,b)
    groups={1:[],2:[],3:[],4:[],5:[]}
    for a,b in edges.values():
        x1,y1=vertices[a-1]; x2,y2=vertices[b-1]
        tag=1
        if y1==y2==ymax*n: tag=2
        elif y1==y2==0: tag=3
        elif x1==x2==0: tag=4
        elif x1==x2==xmax*n: tag=5
        groups[tag].append((a,b))
    gmsh.initialize(); gmsh.option.setNumber('General.Terminal',0); gmsh.model.add(s['name'])
    for k,e in groups.items():
        if e: gmsh.model.addDiscreteEntity(1,k)
    gmsh.model.addDiscreteEntity(2,100)
    xyz=np.array([(x/n,y/n,0.) for x,y in vertices])
    gmsh.model.mesh.addNodes(2,100,list(range(1,len(vertices)+1)),xyz.ravel())
    offset=1; boundary={}
    for k,e in groups.items():
        if not e: continue
        ids=list(range(offset,offset+len(e))); offset+=len(e)
        gmsh.model.mesh.addElementsByType(k,1,ids,np.array(e).ravel())
        gmsh.model.addPhysicalGroup(1,[k],k)
        points=np.array([[vertices[v-1][0]/n,vertices[v-1][1]/n] for edge in e for v in edge])
        boundary[k]=dict(ids=ids,edges=e,bounds=[points.min(axis=0).tolist(),points.max(axis=0).tolist()])
    cell_ids=list(range(offset,offset+len(quads)))
    gmsh.model.mesh.addElementsByType(100,3,cell_ids,np.array(quads).ravel())
    gmsh.model.addPhysicalGroup(2,[100],100)
    gmsh.option.setNumber('Mesh.MshFileVersion',2.2); gmsh.write(str(directory/'solver.msh'))
    # Input is a simplex mesh so linear nodal acceleration has its public meaning.
    gmsh.model.mesh.removeElements(2,100)
    triangles=[t for a,b,c,d in quads for t in [(a,b,c),(a,c,d)]]
    cell_ids=list(range(offset,offset+len(triangles)))
    gmsh.model.mesh.addElementsByType(100,2,cell_ids,np.array(triangles).ravel())
    gmsh.option.setNumber('Mesh.MshFileVersion',4.1); gmsh.write(str(directory/'mesh.msh'))
    gmsh.finalize()
    return xyz,quads,cell_ids,boundary


def wall_velocity(s,k):
    u=.1; drive=s['drive']
    if drive in ('lid','opposed','same'):
        if k==2:return (u,0.)
        if k==3 and drive in ('opposed','same'):return ((-u if drive=='opposed' else u),0.)
    if drive in ('side','side-opposed'):
        if k==4:return (0.,u)
        if k==5 and drive=='side-opposed':return (0.,-u)
    if drive=='circulation':
        return {2:(u,0.),3:(-u,0.),4:(0.,u),5:(0.,-u)}.get(k,(0.,0.))
    return (0.,0.)


def taper(s,b):
    if s['name']=='lid-square':return '1'
    lo,hi=b['bounds'];axis=0 if hi[0]>lo[0] else 1
    v='x' if axis==0 else 'y'
    return f'min(1,min(({v}-{lo[axis]})/0.5,({hi[axis]}-{v})/0.5))'


def configuration(s,boundary):
    text='''set dimension = 2
subsection simulation control
 set method = steady
 set output name = solution
 set output frequency = 1
 set subdivision = 2
end
subsection physical properties
 subsection fluid 0
  set kinematic viscosity = 0.1
 end
end
subsection mesh
 set type = gmsh
 set file name = solver.msh
end
subsection FEM
 set velocity degree = 2
 set pressure degree = 1
end
subsection non-linear solver
 subsection fluid dynamics
  set tolerance = 1e-10
  set max iterations = 30
  set verbosity = verbose
 end
end
subsection linear solver
 subsection fluid dynamics
  set method = gmres
  set relative residual = 1e-6
  set minimum residual = 1e-12
  set preconditioner = amg
  set max iters = 1000
  set verbosity = verbose
 end
end
'''
    text=text.replace('kinematic viscosity = 0.1',f"kinematic viscosity = {s.get('nu',0.1)}")
    if 'force' in s:
        text+='subsection source term\n subsection fluid dynamics\n  set enable = true\n  set Function expression = '+ '; '.join(s['force']+['0'])+'\n end\nend\n'
    text+=f'subsection boundary conditions\n set number = {len(boundary)}\n'
    for idx,k in enumerate(boundary):
        ux,uy=wall_velocity(s,k)
        if k in s.get('slip',[]):
            text+=f' subsection bc {idx}\n  set id = {k}\n  set type = slip\n end\n'
            continue
        ramp=taper(s,boundary[k])
        text+=f' subsection bc {idx}\n  set id = {k}\n  set type = function\n  subsection u\n   set Function expression = {ux}*({ramp})\n  end\n  subsection v\n   set Function expression = {uy}*({ramp})\n  end\n end\n'
    return text+'end\n'


def main():
    p=argparse.ArgumentParser(); p.add_argument('root',type=Path); p.add_argument('--n',type=int,default=8); p.add_argument('--index',type=int); p.add_argument('--solver',default='lethe-fluid'); args=p.parse_args()
    specs=specifications()
    if args.index is not None:specs=[specs[args.index]]
    for s in specs:
        directory=(args.root/s['name']/f'n{args.n}').resolve(); directory.mkdir(parents=True,exist_ok=True)
        xyz,q,ids,b=build_mesh(s,args.n,directory)
        (directory/'case.prm').write_text(configuration(s,b))
        (directory/'definition.json').write_text(json.dumps(s,indent=2))
        start=time.time()
        env={**os.environ,'OMP_NUM_THREADS':'4','DEAL_II_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'1'}
        cpus=','.join(map(str,sorted(os.sched_getaffinity(0))[:4]))
        with (directory/'solver.log').open('w') as log:
            result=subprocess.run(['/usr/bin/time','-v','-o','resource.txt','taskset','-c',cpus,args.solver,'case.prm'],cwd=directory,env=env,stdout=log,stderr=subprocess.STDOUT)
        (directory/'execution.json').write_text(json.dumps(dict(returncode=result.returncode,seconds=time.time()-start,cells=len(q),nodes=len(xyz)),indent=2))
        print(s['name'],args.n,result.returncode,time.time()-start,flush=True)
        if result.returncode: raise RuntimeError(directory)


if __name__=='__main__':main()
