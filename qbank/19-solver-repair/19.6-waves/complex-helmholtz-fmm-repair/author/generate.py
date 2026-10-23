"""Generate geometry and declarations; never generate operator answers."""
from pathlib import Path
import argparse,importlib.util,json
import numpy as np
import gmsh
from scipy.spatial import ConvexHull
from caeoj.storage import write_hdf5
from caeoj.validation import write_json

TASK=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('helmholtz_contract',TASK/'extension/caeoj_task_ext/helmholtz.py');contract=importlib.util.module_from_spec(s);s.loader.exec_module(contract)


def sphere(n):
    i=np.arange(n);z=1-2*(i+.5)/n;angle=i*np.pi*(3-np.sqrt(5));r=np.sqrt(1-z*z)
    return np.column_stack([r*np.cos(angle),r*np.sin(angle),z])


def mesh(path,vertices,seed):
    triangles=ConvexHull(vertices).simplices.copy()
    center=vertices.mean(axis=0)
    for t in triangles:
        if np.dot(np.cross(vertices[t[1]]-vertices[t[0]],vertices[t[2]]-vertices[t[0]]),vertices[t].mean(axis=0)-center)<0:t[1],t[2]=t[2],t[1]
    ids=13+7*np.arange(len(vertices),dtype=np.int64);rng=np.random.RandomState(seed)
    order=rng.permutation(len(ids));faces=rng.permutation(len(triangles))
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('closed-surface');gmsh.model.addDiscreteEntity(2,1)
        gmsh.model.mesh.addNodes(2,1,ids[order].tolist(),vertices[order].ravel().tolist())
        gmsh.model.mesh.addElementsByType(1,2,(1003+11*faces).tolist(),ids[triangles[faces]].ravel().tolist())
        gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.option.setNumber('Mesh.SaveAll',1);gmsh.write(str(path))
    finally:gmsh.finalize()
    return ids


def definitions():
    yield '01-point-real',0,32,1.1,0.,'real-k point interface preservation'
    yield '02-point-complex',0,64,1.3,.4,'complex potential and target gradient, arbitrary complex sources'
    yield '03-attenuated-gradient',0,96,.7,1.2,'strong attenuation, near gradient includes the imaginary-k derivative'
    yield '04-point-far-tree',0,512,3.,.25,'many source leaves and genuine far-field approximation'
    yield '05-point-translated',0,128,1.7,.8,'translated nonuniform complex cloud and targets'
    yield '06-point-near-real',0,48,2.6,0.,'near separated targets with real-k preservation'
    yield '07-boundary-complex',1,18,1.3,.4,'small closed surface: near correction and three strong operators'
    yield '08-boundary-real',1,18,2.2,0.,'real-k strong boundary and exterior potential preservation'
    yield '09-boundary-fine',1,66,1.3,.4,'different surface discretization with FMM far interactions'
    yield '10-affine-surface',1,34,1.9,.8,'convex nonspherical translated surface and complex P1 density'
    yield '11-boundary-resource',1,100,3.,0.,'maximum surface and target count, high real wave number'
    yield '12-scaled-surface',1,66,.75,.6,'geometric scale and nonzero attenuation on a rotated surface'


def generate(output):
    catalog=[]
    for i,(name,op,n,kr,ki,meaning) in enumerate(definitions()):
        dest=output/'cases'/name;dest.mkdir(parents=True,exist_ok=True)
        rng=np.random.RandomState(20261023+i);arrays={'times':np.array([0.],dtype=np.float64)}
        nt=24 if i==3 else 12 if op else 7
        target=3.3*sphere(nt)
        arrays['target_ids']=np.arange(nt,dtype=np.int64)*5+2
        arrays['target_coordinates']=target
        if op==0:
            sources=rng.uniform(-.75,.75,(n,3));strength=rng.uniform(-1,1,(n,2))
            if i==5:arrays['target_coordinates']=1.65*sphere(nt)
            if i==4:sources+=np.array([2.2,-1.3,.5]);arrays['target_coordinates']+=np.array([2.2,-1.3,.5])
            arrays.update(source_ids=np.arange(n,dtype=np.int64)*3+1,source_coordinates=sources,strength=strength[None,:,:])
        else:
            vertices=sphere(n)*1.1
            if i==9:
                vertices=vertices@np.diag([1.1,.8,.7]);vertices+=np.array([2.2,-1.3,.5]);arrays['target_coordinates']+=np.array([2.2,-1.3,.5])
            if i==11:
                theta=.63;rotation=np.array([[np.cos(theta),-np.sin(theta),0],[np.sin(theta),np.cos(theta),0],[0,0,1]])
                vertices=.85*vertices@rotation.T;arrays['target_coordinates']=.85*arrays['target_coordinates']@rotation.T
            arrays['node_ids']=mesh(dest/'surface.msh',vertices,20261023+i)
            arrays['density']=rng.uniform(-1,1,(1,n,2))
        fields,outputs=contract.descriptions(op)
        manifest={'task':contract.TASK,'spatial_dimension':3,'data_file':'input.h5','geometries':{},'meshes':{} if op==0 else {'surface':{'file':'surface.msh'}},'conditions':[],'physics':{'model':contract.MODEL,'parameters':{'operation':{'value':op,'unit':'1'},'wavenumber_real':{'value':kr,'unit':'1/m'},'wavenumber_imag':{'value':ki,'unit':'1/m'}}},'locations':contract.locations(op),'time_axes':{'instant':'times'},'fields':fields,'outputs':outputs}
        write_json(dest/'problem.json',manifest);write_hdf5(dest/'input.h5',arrays)
        catalog.append({'case':name,'meaning':meaning,'origin':'author mechanism adaptation of genuine Bempp complex-k defect, not claimed original issue input','operation':op,'sources_or_nodes':n,'targets':nt,'k':[kr,ki]})
    write_json(output/'catalog.json',catalog)
    return catalog


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);print(json.dumps(generate(p.parse_args().output)))
