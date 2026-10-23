"""Build real observation meshes for axisymmetric Meep source adaptations."""
import argparse,importlib.util
from pathlib import Path
import gmsh,numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cyl_contract',TASK/'extension/caeoj_task_ext/cylindrical.py');contract=importlib.util.module_from_spec(spec);spec.loader.exec_module(contract)
def write_mesh(path,R,Z):
 gmsh.initialize([],readConfigFiles=False)
 try:
  gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('observation');gmsh.model.addDiscreteEntity(0,10);gmsh.model.mesh.addNodes(0,10,[1,2,3,4],[0,Z,0,R,Z,0,R,-Z,0,0,-Z,0]);gmsh.model.mesh.addElementsByType(10,15,[1001,1002,1003,1004],[1,2,3,4]);gmsh.model.addDiscreteEntity(1,20);gmsh.model.mesh.addElementsByType(20,1,[11,17,23],[1,2,2,3,3,4]);gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.option.setNumber('Mesh.SaveAll',1);gmsh.write(str(path))
 finally:gmsh.finalize()
def cases():
 base={'radius':2,'half_height':1,'radial_pml':1,'axial_pml':1,'resolution':30,'mode':-1,'source_amplitude':1.}
 rows=[('01-negative-mode-public',{},'negative mode axis/PML defect with independent absolute flux observation'),('02-positive-mode-public',{'mode':1},'positive mode preservation and opposite complex-field handedness'),('03-radial-pml',{'radial_pml':2},'radial PML changed while axial PML retained'),('04-axial-pml',{'axial_pml':2},'axial PML changed independently'),('05-source-geometry',{'radius':3,'half_height':2,'source_amplitude':.5},'original report geometry with physical source amplitude scaling'),('06-grid-resolution',{'resolution':40},'different Yee discretization and time step'),('07-negative-source',{'half_height':2,'mode':1,'source_amplitude':-.75},'source sign affects complex fields and square amplitude affects flux'),('08-cylinder-aspect',{'radius':3,'source_amplitude':.75},'different enclosing surface aspect ratio at fixed source')]
 for name,changes,meaning in rows:yield name,{**base,**changes},meaning
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();catalog=[]
 for name,v,meaning in cases():
  dest=a.output/'cases'/name;dest.mkdir(parents=True,exist_ok=True);res=v['resolution'];arrays={'face_ids':np.array([11,17,23],dtype='int64'),'probe_ids':np.array([7],dtype='int64'),'probe_coordinates':np.array([[(2*res+1)*(.5/res),.5/res]],dtype='float64'),'times':np.array([0.],dtype='float64')};inputs,outputs=contract.descriptions();manifest={'task':contract.TASK,'spatial_dimension':2,'data_file':'input.h5','geometries':{},'meshes':{'observation':{'file':'surfaces.msh'}},'conditions':[],'physics':{'model':contract.MODEL,'parameters':{k:{'value':v,'unit':'1'} for k,v in v.items()}},'locations':contract.locations(),'time_axes':{'instant':'times'},'fields':inputs,'outputs':outputs};write_json(dest/'problem.json',manifest);write_hdf5(dest/'input.h5',arrays);write_mesh(dest/'surfaces.msh',v['radius'],v['half_height']);catalog.append({'case':name,'parameters':v,'meaning':meaning,'origin':'author mechanism adaptation of Meep2338/PR2382 axisymmetric on-axis Er source; not claimed original user input'})
 write_json(a.output/'catalog.json',catalog)
