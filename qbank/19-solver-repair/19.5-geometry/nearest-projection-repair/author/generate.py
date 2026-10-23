"""Author adaptations of issue1304: real Gmsh inputs, independent checks only."""
import argparse,importlib.util,itertools,json
from pathlib import Path
import gmsh
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
from independent import evaluate
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('projection_contract',TASK/'extension/caeoj_task_ext/projection.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)


def closure(edges,triangles,tetrahedra):
    faces={tuple(sorted(f)) for f in triangles}
    for t in tetrahedra:faces.update(itertools.combinations(sorted(t),3))
    segments={tuple(sorted(e)) for e in edges}
    for f in faces:segments.update(itertools.combinations(f,2))
    return [list(e) for e in sorted(segments)],[list(f) for f in sorted(faces)]


def write_mesh(path,xyz,tags,edges,faces,tetra):
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('source')
        gmsh.model.addDiscreteEntity(0,10);gmsh.model.mesh.addNodes(0,10,tags,xyz.ravel())
        gmsh.model.mesh.addElementsByType(10,15,list(range(1001,1001+len(tags))),tags)
        for dim,kind,items in [(1,1,edges),(2,2,faces),(3,4,tetra)]:
            if not items:continue
            entity=10+dim;gmsh.model.addDiscreteEntity(dim,entity)
            conn=[int(tags[i]) for row in items for i in row]
            gmsh.model.mesh.addElementsByType(entity,kind,list(range(10000*dim+1,10000*dim+1+len(items))),conn)
        gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.option.setNumber('Mesh.SaveAll',1)
        gmsh.write(str(path))
    finally:gmsh.finalize()


def cases():
    tri2=[[0,0],[1,0],[0,1]]
    tetra3=[[0,0,0],[2,0,0],[0,1,0],[0,0,1.5]]
    return [
      ('01-triangle-fallback-public',2,1,tri2,[],[[0,1,2]],[],[[-.1,-.1],[.49,-.01],[.2,.3],[-2,.3],[.8,.8]],'source triangle mechanism plus internal and edge regression'),
      ('02-spatial-cell-public',3,1,tetra3,[],[],[[0,1,2,3]],[[.2,.1,.15],[.2,.1,-.2],[-.3,-.2,-.1],[2.3,.1,0],[0,.3,.4]],'3D interior, outside face/edge/vertex and boundary'),
      ('03-isolated-near-vertex',2,0,[[0,0],[2,0],[1,1]],[[0,1]],[],[],[[1,1.2],[1,-.3],[2.3,-.1],[.2,.05]],'edge projection versus separate closer vertex'),
      ('04-spatial-edge-only',3,0,[[-2,0,0],[2,0,0],[0,2,1],[0,4,1]],[[0,1],[2,3]],[],[],[[0,.4,.2],[0,3,1.2],[-2.4,-.1,0],[.1,1.7,1]],'3D no-face downgrade, two disjoint edge directions'),
      ('05-closer-independent-edge',3,0,[[-5,-5,0],[5,-5,0],[0,5,0],[-10,0,.5],[10,0,.5]],[[3,4]],[[0,1,2]],[],[[0,0,1],[.4,.1,1],[0,-2,-.2],[-10.3,0,.6]],'face closer than every vertex but independent edge closer than face'),
      ('06-far-face-near-node',3,0,[[-3,-3,0],[3,-3,0],[0,3,0],[0,0,1]],[],[[0,1,2]],[],[[0,0,1.2],[.1,.1,1.3],[1,0,-.2]],'standalone vertex versus valid farther face projection'),
      ('07-cell-without-triangles',2,1,[[0,0],[2,0],[0,2],[2,3]],[[0,1],[2,3]],[],[],[[.7,.3],[1.2,2.8],[-.2,1.9],[2.4,3.2]],'2D missing cell connectivity uses nearest primitive'),
      ('08-cell-without-tetrahedra',3,1,[[0,0,0],[2,0,0],[0,2,0],[0,0,3],[2,0,3],[0,2,3]],[],[[0,1,2],[3,4,5]],[],[[.3,.2,.4],[.3,.2,2.6],[-.2,-.3,2.8],[1.4,1.3,.4]],'3D missing volume connectivity and competing disconnected surfaces'),
      ('09-vertices-only',3,1,[[0,0,0],[2,1,1],[-1,2,3]],[],[],[],[[.1,.2,.3],[2.1,1.2,.9],[-1.1,2.2,3.3]],'no edges/faces/cells; genuine nearest-node regression'),
      ('10-nearest-ignores-volume',3,0,tetra3,[],[],[[0,1,2,3]],[[.2,.1,.15],[.1,.2,.3],[.5,.1,.2],[.4,.3,-.2]],'nearest surface projection differs from containing-cell interpolation')]


def make(root,item,seed):
    name,d,mode,vertices,edges,faces,tetra,queries,meaning=item
    xyz=np.asarray(vertices,float);q=np.asarray(queries,float);edges,faces=closure(edges,faces,tetra)
    rng=np.random.default_rng(seed);tags=rng.permutation(np.arange(len(xyz),dtype='int64')*17+7);order=np.argsort(tags)
    vals=np.c_[1+.2*xyz[:,0]-.3*xyz[:,1],rng.uniform(-3,3,len(xyz)),rng.uniform(-10,10,len(xyz))]
    arrays={'node_ids':tags[order],'probe_ids':np.arange(len(q),dtype='int64')*19+3,'probe_coordinates':q,'times':np.array([0.]),'nodal_values':vals[order][None]}
    inputs,outputs=contract.descriptions(d,arrays['node_ids'])
    manifest={'task':TASK.name,'spatial_dimension':d,'data_file':'input.h5','geometries':{},'meshes':{'source':{'file':'source.msh'}},'conditions':[],
      'physics':{'model':'nearest-simplex-state-v1','parameters':{'mode':{'value':mode,'unit':'1'}}},
      'locations':{'nodes':{'kind':'mesh','mesh':'source','entity':'node','ids':'node_ids'},'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}},
      'time_axes':{'instant':'times'},'fields':inputs,'outputs':outputs}
    target=root/'cases'/name;target.mkdir(parents=True,exist_ok=True);write_json(target/'problem.json',manifest);write_hdf5(target/'input.h5',arrays)
    xyz3=np.c_[xyz,np.zeros(len(xyz))] if d==2 else xyz
    write_mesh(target/'source.msh',xyz3,tags,edges,faces,tetra)
    # Exact input identity order is independently preserved in the affine check payload.
    inverse=np.argsort(order)
    payload={'dimension':d,'mode':'nearest' if mode==0 else 'cell','vertices':xyz[order].tolist(),'values':vals[order].tolist(),
      'edges':[[int(inverse[i]) for i in row] for row in edges],'triangles':[[int(inverse[i]) for i in row] for row in faces],
      'tetrahedra':[[int(inverse[i]) for i in row] for row in tetra],'queries':q.tolist()}
    expected=evaluate(payload);out=root/'independent-checks';out.mkdir(exist_ok=True);write_json(out/(name+'.json'),expected)
    return {'case':name,'dimension':d,'mode':mode,'vertices':len(vertices),'queries':len(queries),'meaning':meaning,'seed':seed,'origin':'author adaptation of preCICE issue1304 mechanism; not original coupling application'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    write_json(args.output/'catalog.json',[make(args.output,item,190502+i) for i,item in enumerate(cases())])
