"""Attributed rectangular-channel cases; Gmsh identity is explicit in every input."""
from pathlib import Path
import importlib.util,json
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
Q=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('contract',Q/'extension/caeoj_task_ext/wall_energy.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
def mesh_file(path,nx,ny,L,H,skew):
    xy=[]
    for j in range(ny):
        for i in range(nx):
            x=L*i/(nx-1);y=H*j/(ny-1);xy.append([x+skew*np.sin(np.pi*x/L)*np.sin(np.pi*y/H),y,0.])
    xy=np.array(xy);idx=lambda i,j:j*nx+i+1
    edges={1:[(idx(i,0),idx(i+1,0)) for i in range(nx-1)],2:[(idx(i+1,ny-1),idx(i,ny-1)) for i in range(nx-1)],3:[(idx(0,j+1),idx(0,j)) for j in range(ny-1)],4:[(idx(nx-1,j),idx(nx-1,j+1)) for j in range(ny-1)]}
    lines=['$MeshFormat','4.1 0 8','$EndMeshFormat','$Entities','0 4 1 0']
    boxes={1:(0,0,L,0),2:(0,H,L,H),3:(0,0,0,H),4:(L,0,L,H)}
    for tag,(x0,y0,x1,y1) in boxes.items():lines.append(f'{tag} {x0} {y0} 0 {x1} {y1} 0 1 {tag} 0')
    lines.extend([f'1 0 0 0 {L} {H} 0 1 10 4 1 2 3 4','$EndEntities','$Nodes',f'1 {nx*ny} 1 {nx*ny}',f'2 1 0 {nx*ny}'])
    lines.extend(map(str,range(1,nx*ny+1)));lines.extend(' '.join(f'{x:.17g}' for x in row) for row in xy);lines.extend(['$EndNodes','$Elements'])
    total=sum(map(len,edges.values()))+(nx-1)*(ny-1);lines.append(f'5 {total} 1 {total}');tag=1;edge_ids={}
    for group,conn in edges.items():
        lines.append(f'1 {group} 1 {len(conn)}');edge_ids[group]=[]
        for a,b in conn:lines.append(f'{tag} {a} {b}');edge_ids[group].append(tag);tag+=1
    lines.append(f'2 1 3 {(nx-1)*(ny-1)}')
    for j in range(ny-1):
        for i in range(nx-1):lines.append(f'{tag} {idx(i,j)} {idx(i+1,j)} {idx(i+1,j+1)} {idx(i,j+1)}');tag+=1
    lines.append('$EndElements');path.write_text('\n'.join(lines)+'\n');return xy,edge_ids
def make(i,x):
    nx,ny,L,H,skew=x['nx'],x['ny'],x['L'],x['H'],x['skew'];dest=Q/'cases'/f'{i:02d}-{x["name"]}';dest.mkdir(parents=True,exist_ok=True)
    xy,edges=mesh_file(dest/'mesh.msh',nx,ny,L,H,skew)
    v={'density':1.,'heat_capacity':1000.,'viscosity':.01,'conductivity':x.get('k',10.),'velocity':x.get('U',0.),'bottom_temperature':x.get('Th',400.),'top_temperature':x.get('Tc',300.),'bottom_heat_flux':x.get('flux',0.),'boundary_mode':int('flux' in x),'cfl':x.get('cfl',10.),'iterations':x.get('iterations',30000)}
    ids=np.arange(1,nx*ny+1,dtype='int64');inlet=np.arange(1,nx*ny+1,nx,dtype='int64')
    wall=np.concatenate([np.arange(1,nx+1),np.arange((ny-1)*nx+1,ny*nx+1)]).astype('int64')
    y=xy[inlet-1,1];Tin=v['bottom_temperature']+(v['top_temperature']-v['bottom_temperature'])*y/H+x.get('amplitude',0.)*np.sin(np.pi*y/H)
    arrays={'times':np.array([0.]),'node_ids':ids,'wall_ids':wall,'inlet_ids':inlet,'bottom_edge_ids':np.array(edges[1],dtype='int64'),'top_edge_ids':np.array(edges[2],dtype='int64'),'bottom_observation_id':np.array([0],dtype='int64'),'top_observation_id':np.array([0],dtype='int64'),'diagnostic_ids':np.array([0],dtype='int64'),'inlet_temperature':Tin[None,:,None]}
    m={'task':c.TASK,'spatial_dimension':2,'data_file':'input.h5','geometries':{},'meshes':{'channel':{'file':'mesh.msh'}},'conditions':[],
       'physics':{'model':c.MODEL,'parameters':{k:{'value':value,'unit':c.UNITS[k]} for k,value in v.items()}},'locations':c.locations(),'time_axes':{'steady':'times'},'fields':c.fields(),'outputs':c.outputs()}
    write_hdf5(dest/'input.h5',arrays);write_json(dest/'problem.json',m)
    return {'case':dest.name,'origin':'Author-created independent rectangular conduction/advection regression motivated by SU2 issue2347/PR2394, not upstream numerical data.','parameters':x}
if __name__=='__main__':
    cases=[dict(name='skew-conduction',nx=25,ny=17,L=2.,H=1.,skew=.3),dict(name='reverse',nx=29,ny=19,L=1.5,H=1.,skew=-.25,k=6.,Th=280.,Tc=335.),dict(name='scaled',nx=25,ny=21,L=1.6,H=.7,skew=.18,k=4.,Th=360.,Tc=310.),dict(name='thin-layer',nx=33,ny=25,L=2.,H=1.,skew=.3),
           dict(name='orthogonal-flow-coarse',nx=33,ny=17,L=2.,H=1.,skew=0.,U=.1,amplitude=20.,cfl=20.,iterations=10000),dict(name='orthogonal-flow-fine',nx=65,ny=33,L=2.,H=1.,skew=0.,U=.1,amplitude=20.,cfl=20.,iterations=10000),dict(name='skew-flow-coarse',nx=33,ny=17,L=2.,H=1.,skew=.2,U=.1,amplitude=20.,cfl=5.,iterations=20000),dict(name='skew-flow-fine',nx=65,ny=33,L=2.,H=1.,skew=.2,U=.1,amplitude=20.,cfl=5.,iterations=20000),
           dict(name='prescribed-flux',nx=25,ny=17,L=2.,H=1.,skew=.3,flux=1000.),dict(name='zero-flux',nx=25,ny=17,L=2.,H=1.,skew=-.2,Th=300.,Tc=300.,flux=0.)]
    write_json(Q/'author/data-evidence/cases.json',[make(i,x) for i,x in enumerate(cases,1)])
