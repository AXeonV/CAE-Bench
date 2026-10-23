"""Generate the prescribed structured QUAD4 input with the official Gmsh API."""
from pathlib import Path
import gmsh,numpy as np
from caeoj.validation import GMSH_LOCK,read_mesh
SIDES={'bottom':1,'right':2,'top':3,'left':4}
def generate(directory,*,width,length,nx,ny,origin=(0.,0.),sparse=False):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 with GMSH_LOCK:
  gmsh.initialize([],readConfigFiles=False)
  try:
   gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('strip');geo=gmsh.model.geo;x,y=origin;h=min(width/nx,length/ny)
   points=[geo.addPoint(a,b,0,h) for a,b in [(x,y),(x+width,y),(x+width,y+length),(x,y+length)]]
   curves=[geo.addLine(points[i],points[(i+1)%4]) for i in range(4)];surface=geo.addPlaneSurface([geo.addCurveLoop(curves)]);geo.synchronize()
   for i,curve in enumerate(curves):gmsh.model.mesh.setTransfiniteCurve(curve,(nx if i%2==0 else ny)+1)
   gmsh.model.mesh.setTransfiniteSurface(surface);gmsh.model.mesh.setRecombine(2,surface)
   gmsh.model.addPhysicalGroup(2,[surface],1,'domain')
   for name,tag in SIDES.items():gmsh.model.addPhysicalGroup(1,[curves[tag-1]],tag,name)
   gmsh.model.mesh.generate(2)
   if sparse:
    tags=gmsh.model.mesh.getNodes()[0];gmsh.model.mesh.renumberNodes(tags,101+13*np.arange(len(tags),dtype=np.uint64))
    tags=np.concatenate(gmsh.model.mesh.getElements()[1]);gmsh.model.mesh.renumberElements(tags,211+17*np.arange(len(tags),dtype=np.uint64))
   gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.option.setNumber('Mesh.SaveAll',1);gmsh.write(str(directory/'mesh.msh'))
  finally:gmsh.finalize()
 return read_mesh(directory/'mesh.msh',geometry=True)
