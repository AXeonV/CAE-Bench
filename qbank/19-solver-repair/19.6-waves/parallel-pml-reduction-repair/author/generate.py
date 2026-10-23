"""Generate declared meshes/loads; this script never computes a reference wave."""
import argparse,importlib.util,json
from pathlib import Path
import gmsh,numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('wave_contract',TASK/'extension/caeoj_task_ext/parallel_wave.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)

def cases():
    # (x origin,width), source x,z, signed amplitude, observation x,z
    common={'density':2500.,'p_speed':3000.,'s_speed':1500.,'frequency':20.,'time_step':.00025,'processes':3,'wave_branch':0}
    rows=[
      ('01-connected-sh',{},[(0,1600)],[(600,400,1e8),(1000,400,-.5e8)],[(500,400),(800,500),(1100,400)],25,False,'connected mesh: all MPI ranks participate; interfering signed loads'),
      ('02-isolated-master-sh',{},[(0,800),(1600,1600)],[(400,400,1e8),(2400,400,1e8)],[(500,400),(2300,400),(2500,400)],25,False,'master rank has no interfaces, others exchange SH wavefield'),
      ('03-isolated-last-sh',{'time_step':.000125},[(1600,1600),(0,800)],[(400,400,-.75e8),(2400,400,1e8)],[(500,400),(2300,400),(2500,400)],20,False,'last rank has no interfaces, sign change and refined time/space'),
      ('04-isolated-master-pml',{'wave_branch':1,'p_speed':1500.,'s_speed':0.},[(0,800),(1600,1600)],[(400,400,1e8),(2400,400,-.5e8)],[(500,400),(2300,400),(2500,400)],25,True,'acoustic potential with absorbing top/bottom; master rank isolated'),
      ('05-isolated-last-four-pml',{'wave_branch':1,'p_speed':1500.,'s_speed':0.,'processes':4,'density':1000.},[(1600,2400),(0,800)],[(400,400,-1e8),(2800,400,.75e8)],[(500,400),(2700,400),(2900,400)],25,True,'four processes, nonmaster isolated rank and three communicating ranks'),
      ('06-connected-acoustic',{'wave_branch':1,'p_speed':1500.,'s_speed':0.,'frequency':10.},[(0,1600)],[(800,400,1e8)],[(600,400),(1000,400),(800,600)],25,False,'acoustic reflecting walls, lower source frequency, all ranks connected'),
      ('07-serial-sh',{'processes':1,'time_step':.000125,'density':2800.},[(0,800)],[(400,400,.5e8)],[(500,400),(400,500)],20,False,'serial preservation with different density and orthogonal observation'),
      ('08-serial-pml',{'wave_branch':1,'p_speed':1500.,'s_speed':0.,'processes':1,'frequency':10.},[(0,800)],[(400,400,.75e8)],[(500,400),(400,550)],25,True,'serial PML preservation at changed frequency')]
    for name,changes,rects,sources,probes,h,pml,meaning in rows:yield name,{**common,**changes},rects,sources,probes,h,pml,meaning

def mesh(path,rects,h,pml):
    nodes=[];cells=[];regions=[]
    for x0,width in rects:
        nx=width//h;nz=800//h;off=len(nodes)
        for j in range(nz+1):
            for i in range(nx+1):nodes.append((x0+i*h,j*h,0))
        for j in range(nz):
            for i in range(nx):
                q=off+j*(nx+1)+i+1;cells.append((q,q+1,q+nx+2,q+nx+1))
                regions.append(2 if pml and (j<3 or j>=nz-3) else 0)
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('coupons');gmsh.model.addDiscreteEntity(2,1)
        gmsh.model.mesh.addNodes(2,1,list(range(1,len(nodes)+1)),np.array(nodes).ravel())
        gmsh.model.mesh.addElementsByType(1,3,list(range(1,len(cells)+1)),np.array(cells).ravel())
        gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.option.setNumber('Mesh.SaveAll',1);gmsh.write(str(path))
    finally:gmsh.finalize()
    return np.array(regions,dtype='int64')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True,type=Path);a=ap.parse_args();catalog=[]
    for name,p,rects,sources,probes,h,pml,meaning in cases():
        dest=a.output/'cases'/name;dest.mkdir(parents=True,exist_ok=True);regions=mesh(dest/'mesh.msh',rects,h,pml)
        n=round(.8/p['time_step']);arrays={'cell_ids':np.arange(1,len(regions)+1,dtype='int64'),
            'source_ids':np.arange(1,len(sources)+1,dtype='int64'),'source_coordinates':np.array(sources,dtype='float64')[:,:2],
            'source_amplitude':np.array(sources,dtype='float64')[:,2].reshape(1,-1,1),'probe_ids':np.arange(101,101+len(probes),dtype='int64'),
            'probe_coordinates':np.array(probes,dtype='float64'),'static_time':np.array([0.],dtype='float64'),
            'times':-1.2/p['frequency']+np.arange(n,dtype='float64')*p['time_step'],'pml_region':regions.reshape(1,-1,1)}
        ins,outs=contract.descriptions(p['wave_branch']);manifest={'task':contract.TASK,'spatial_dimension':2,'data_file':'input.h5','geometries':{},
            'meshes':{'domain':{'file':'mesh.msh'}},'conditions':[],'physics':{'model':next(k for k,v in contract.MODELS.items() if v==p['wave_branch']),'parameters':{k:{'value':v,'unit':contract.UNITS[k]} for k,v in p.items() if k!='wave_branch'}},
            'locations':contract.locations(),'time_axes':{'static':'static_time','physical':'times'},'fields':ins,'outputs':outs}
        write_json(dest/'problem.json',manifest);write_hdf5(dest/'input.h5',arrays)
        catalog.append({'case':name,'parameters':p,'rectangles':rects,'h':h,'pml':pml,'meaning':meaning,'origin':'author topology/physics adaptation to original SPECFEM2D PR660 collective defect; not original BENCHIE input'})
    write_json(a.output/'catalog.json',catalog)
