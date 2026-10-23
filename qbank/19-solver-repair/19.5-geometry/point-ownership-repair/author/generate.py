"""Build actual Gmsh inputs adapted from the source defect and targeted regressions."""
import argparse,importlib.util,json
from pathlib import Path
import gmsh
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ownership_contract',TASK/'extension/caeoj_task_ext/ownership.py')
contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)

def mesh(path,vertices,tags,cells,labels,dimension):
    xyz=np.asarray(vertices,float)
    if dimension==2:xyz=np.c_[xyz,np.zeros(len(xyz))]
    gmsh.initialize([],readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('source')
        gmsh.model.addDiscreteEntity(0,10);gmsh.model.mesh.addNodes(0,10,tags,xyz.ravel())
        gmsh.model.mesh.addElementsByType(10,15,list(range(1001,1001+len(tags))),tags)
        gmsh.model.addDiscreteEntity(dimension,20)
        gmsh.model.mesh.addElementsByType(20,2 if dimension==2 else 4,labels,[int(tags[i]) for cell in cells for i in cell])
        gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.option.setNumber('Mesh.SaveAll',1)
        gmsh.write(str(path))
    finally:gmsh.finalize()

def cases():
    tetra=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]],float)
    queries=np.array([[.1,.1,.1],[.5,.5,.5],[1.1,1.1,1.1],[.2,.3,.5],[0,0,0],[.3,0,0],[-.1,.1,.1]])
    triangle=[[0,0],[2,0],[0,1]];tqueries=[[.2,.2],[1.8,.8],[2.2,.3],[-.2,-.1],[0,0],[1,.5],[3,3]]
    rotation=np.array([[.36,-.48,.8],[.8,.6,0],[-.48,.64,.6]])
    assert np.allclose(rotation@rotation.T,np.eye(3))
    two_tetra=np.vstack([tetra,tetra+[2,1,.2]])
    return [
      ('01-tetra-strict-public',3,0,0,tetra,[[0,1,2,3]],queries,'Source three-point mechanism plus closed boundary/vertex regression'),
      ('02-triangle-extrapolation-public',2,1,.25,triangle,[[0,1,2]],tqueries,'Explicit closest option, padded/outside candidates and a closed edge'),
      ('03-strict-ignores-padding',2,0,.5,triangle,[[0,1,2]],tqueries,'Padding creates candidates but must not create strict owners'),
      ('04-tetra-padding-bounds',3,1,.3,tetra,[[0,1,2,3]],[[-.2,.1,.1],[1.4,.1,.1],[1.3,1.3,1.3],[.1,.1,.1]],'Padded closed boxes, no candidate beyond box, not global nearest'),
      ('05-default-tetra-regression',3,2,0,tetra*[1,1.5,2],[[0,1,2,3]],queries,'Four-argument default keeps original extrapolation behavior'),
      ('06-disconnected-triangles-strict',2,0,.1,[[0,0],[1,0],[0,1],[2,0],[3,0],[3,1]],[[0,1,2],[3,4,5]],[[.8,.8],[2.1,.9],[2.8,.2],[0,1],[1.5,.5]],'Two cells and original element identity after library reordering'),
      ('07-two-candidate-triangles',2,1,1,[[0,0],[1,0],[0,1],[1.8,.2],[2.8,.2],[1.8,1.2]],[[0,1,2],[3,4,5]],[[1.3,.5],[1.2,.3],[3.9,.9],[2,.4],[0,0]],'Different cells win genuine closest-candidate competition'),
      ('08-disconnected-tetra-strict',3,0,.4,two_tetra,[[0,1,2,3],[4,5,6,7]],[[.8,.8,.8],[2.8,1.8,1],[2.1,1.1,.3],[1.5,.4,.4],[0,0,0]],'Strict multi-cell ownership with padding and outside-box regressions'),
      ('09-rotated-tetra-strict',3,0,.1,tetra@rotation.T+[3,-4,2],[[0,1,2,3]],queries@rotation.T+[3,-4,2],'Three-dimensional rotation and translation covariance'),
      ('10-small-translated-tetra',3,0,.01,tetra*.02+[17,24,-6],[[0,1,2,3]],queries*.02+[17,24,-6],'Small cells, large translation, preserved strict margin'),
      ('11-default-no-global-search',2,2,0,triangle,[[0,1,2]],[[.2,.2],[1.8,.8],[2.2,.3],[-.2,-.1],[0,0]],'Default rejects noncandidate points despite finite distance to mesh'),
      ('12-two-candidate-tetra',3,1,.8,np.vstack([tetra,tetra+[1.6,.2,.1]]),[[0,1,2,3],[4,5,6,7]],[[1.2,.3,.2],[1.1,.1,.1],[3.6,.1,.1],[1.7,.3,.2],[0,0,0]],'True volumetric closest-candidate competition and contained priority')]

def make(root,item,seed):
    name,d,mode,padding,vertices,cells,queries,meaning=item
    xyz=np.asarray(vertices,float);q=np.asarray(queries,float);rng=np.random.default_rng(seed)
    tags=rng.permutation(np.arange(len(xyz),dtype='int64')*17+7);labels=rng.permutation(np.arange(len(cells),dtype='int64')*29+31)
    arrays={'node_ids':np.sort(tags),'probe_ids':np.arange(len(q),dtype='int64')*19+3,
      'probe_coordinates':q,'times':np.array([0.])}
    manifest={'task':TASK.name,'spatial_dimension':d,'data_file':'input.h5','geometries':{},'meshes':{'source':{'file':'source.msh'}},'conditions':[],
      'physics':{'model':'simplex-ownership-v1','parameters':{'mode':{'value':mode,'unit':'1'},'padding':{'value':padding,'unit':'m'}}},
      'locations':{'nodes':{'kind':'mesh','mesh':'source','entity':'node','ids':'node_ids'},'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}},
      'time_axes':{'instant':'times'},'fields':{},'outputs':contract.descriptions()}
    target=root/'cases'/name;target.mkdir(parents=True,exist_ok=True)
    write_json(target/'problem.json',manifest);write_hdf5(target/'input.h5',arrays)
    mesh(target/'source.msh',xyz,tags,cells,labels,d)
    return {'case':name,'origin':'author adaptation/regression; only first case includes the original report mechanism',
      'mode':mode,'padding':padding,'meaning':meaning,'queries':len(q),'nodes':len(xyz),'cells':len(cells)}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    records=[make(args.output,item,1040+i) for i,item in enumerate(cases())]
    (TASK/'author/data-evidence/cases.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps({'cases':len(records),'queries':sum(r['queries'] for r in records)}))
