"""Construct native independent Elmer Stokes inputs using Gmsh; no flow calculation."""
from pathlib import Path
import argparse,json
import h5py
import gmsh

ap=argparse.ArgumentParser();ap.add_argument('--h',type=float,default=.08);ap.add_argument('--slope',type=float,default=-.1);ap.add_argument('--out',required=True);ap.add_argument('--problem');ap.add_argument('--time',type=float,default=1.);a=ap.parse_args()
w=Path(a.out);w.mkdir(parents=True,exist_ok=True)
W,H=2.,.5;k=a.slope;mu=1.;peak=1.
probes=[(.25,.15),(.75,.25),(1.25,.25),(1.75,.15)]
if a.problem:
 problem=Path(a.problem);m=json.loads(problem.read_text());p={k:v['value'] for k,v in m['physics']['parameters'].items()}
 if m['spatial_dimension']!=2 or m['physics']['model']!='deformed-tangential-wedge-v1':raise ValueError('Independent checker is for the documented nonuniform 2D family')
 W,H,k,mu,peak=p['width'],p['height'],p['rate_x']*a.time,p['viscosity'],p['peak_velocity']
 with h5py.File(problem.parent/m['data_file']) as h:probes=h['probe_coordinates'][:].tolist()
gmsh.initialize();gmsh.option.setNumber('General.Terminal',1)
gmsh.model.add('static-current-domain')
corners=[(0,0),(W,0),(W,H+k*W/2),(0,H-k*W/2)]
v=[gmsh.model.geo.addPoint(x,y,0,a.h) for x,y in corners]
edges=[gmsh.model.geo.addLine(v[i],v[(i+1)%4]) for i in range(4)]
surface=gmsh.model.geo.addPlaneSurface([gmsh.model.geo.addCurveLoop(edges)])
pv=[gmsh.model.geo.addPoint(x,y,0,a.h) for x,y in probes]
gmsh.model.geo.synchronize();gmsh.model.mesh.embed(0,pv,2,surface)
for tag,edge in enumerate(edges,1):gmsh.model.addPhysicalGroup(1,[edge],tag)
gmsh.model.addPhysicalGroup(0,v[:3],5)
gmsh.model.addPhysicalGroup(0,[v[3]],6)
gmsh.model.addPhysicalGroup(2,[surface],1)
gmsh.option.setNumber('Mesh.MshFileVersion',2.2);gmsh.model.mesh.generate(2);gmsh.write(str(w/'mesh.msh'));gmsh.finalize()
(w/'probes.json').write_text(json.dumps(probes))
text='''Header
  CHECK KEYWORDS Warn
  Mesh DB "." "mesh"
End
Simulation
  Coordinate System = Cartesian 2D
  Simulation Type = Steady State
  Steady State Max Iterations = 1
  Output Intervals = 1
  Output File = flow.result
  Post File = flow.ep
End
Body 1
  Target Bodies(1) = 1
  Equation = 1
  Material = 1
End
Equation 1
  Active Solvers(1) = 1
  Navier-Stokes = Logical True
End
Material 1
  Density = 1
  Viscosity = 1
End
Solver 1
  Equation = Navier-Stokes
  Procedure = "FlowSolve" "FlowSolver"
  Variable = Flow Solution[Velocity:2 Pressure:1]
  Flow Model = Stokes
  Stabilize = Logical True
  Optimize Bandwidth = Logical True
  Linear System Solver = Direct
  Linear System Direct Method = Umfpack
  Nonlinear System Max Iterations = 1
  Nonlinear System Convergence Tolerance = 1e-12
  Steady State Convergence Tolerance = 1e-12
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Velocity 1 = Variable Coordinate 1
    Real MATC "1-(tx-1)^2"
  Velocity 2 = 0
End
Boundary Condition 2
  Target Boundaries(1) = 2
  Normal-Tangential Velocity = Logical True
  Velocity 1 = 0
End
Boundary Condition 3
  Target Boundaries(1) = 3
  Normal-Tangential Velocity = Logical True
  Velocity 1 = 0
End
Boundary Condition 4
  Target Boundaries(1) = 4
  Normal-Tangential Velocity = Logical True
  Velocity 1 = 0
End
Boundary Condition 5
  Target Boundaries(1) = 5
  Velocity 1 = 0
  Velocity 2 = 0
End
Boundary Condition 6
  Target Boundaries(1) = 6
  Velocity 1 = 0
  Velocity 2 = 0
  Pressure = 0
End
'''
text=text.replace('  Viscosity = 1',f'  Viscosity = {mu}')
text=text.replace('Real MATC "1-(tx-1)^2"',f'Real MATC "{peak}*(1-(2*tx/{W}-1)^2)"')
(w/'case.sif').write_text(text)
