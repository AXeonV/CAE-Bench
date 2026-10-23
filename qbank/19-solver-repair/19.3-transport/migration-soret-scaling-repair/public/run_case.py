"""Convert declared mesh/parameters/BCs, call actual Elmer modules, and store actual fields."""
import argparse,os,subprocess,tempfile
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem,write_result,read_constant
from caeoj.validation import read_mesh
from native_result import read_result
ELMER='/opt/elmer-build/fem/src/ElmerSolver'
MODULES='/opt/elmer-build/fem/src/modules'

def mesh_data(problem):
 m=problem.meshes['main']
 if 'node_coordinates' not in m:m=read_mesh(problem.path.parent/problem.manifest['meshes']['main']['file'],geometry=True)
 return m

def write_native_mesh(problem,directory):
 mesh=mesh_data(problem);ids=problem.arrays['node_ids'];index={int(tag):i+1 for i,tag in enumerate(ids)};body=sorted(mesh['elements'][2]);cells={};parents={}
 directory.mkdir(parents=True,exist_ok=True)
 for i,tag in enumerate(body,1):
  kind,nodes=mesh['connectivity'][tag]
  if kind!=3:raise ValueError('QUAD4 required')
  cells[i]=[index[t] for t in nodes]
  for j in range(4):parents.setdefault(frozenset((nodes[j],nodes[(j+1)%4])),[]).append(i)
 boundaries=[]
 for name,tag in [('bottom',1),('right',2),('top',3),('left',4)]:
  for edge in problem.arrays[name+'_ids']:
   kind,nodes=mesh['connectivity'][int(edge)];adj=parents[frozenset(nodes)]
   if kind!=1 or len(adj)!=1:raise ValueError('Boundary must have one adjacent cell')
   boundaries.append((len(boundaries)+1,tag,adj[0],0,202,*[index[t] for t in nodes]))
 def save(name,rows):
  (directory/name).write_text('\n'.join(' '.join(format(float(x),'.17g') if isinstance(x,(float,np.floating)) else str(int(x)) for x in row) for row in rows)+'\n')
 save('mesh.header',[(len(ids),len(cells),len(boundaries)),(2,),(404,len(cells)),(202,len(boundaries))])
 save('mesh.nodes',[(index[int(tag)],-1,*mesh['node_coordinates'][int(tag)]) for tag in ids])
 save('mesh.elements',[(i,1,404,*nodes) for i,nodes in cells.items()]);save('mesh.boundary',boundaries)

def sif(problem):
 m=problem.manifest;p=m['physics']['parameters'];value=lambda k:read_constant(p[k]);mode=read_constant(p['concentration_units'])
 bc={(c['variable'],c['location']):c for c in m['conditions']}
 boundary=lambda var,side:read_constant(bc[var,side]['data']['value'])
 units_line='  Concentration Units = String "Absolute Mass"\n' if mode==1 else ''
 material='\n'.join('  '+name+' = Real '+format(value(key),'.17g') for name,key in [('Density','density'),('Conc Diffusivity','diffusivity'),('Conc Soret Diffusivity','soret_diffusivity'),('Conc Ion Charge','ion_charge')] if key not in ('soret_diffusivity','ion_charge') or value(key)!=0)
 text=f'''Header
  CHECK KEYWORDS Warn
  Mesh DB "." "mesh"
End
Simulation
  Max Output Level = 3
  Coordinate System = Cartesian 2D
  Simulation Type = Steady State
  Steady State Max Iterations = 2
  Output Intervals = 1
  Output File = "case.result"
End
Constants
  Unit Charge = Real 1.602176634e-19
  Boltzmann Constant = Real 1.380649e-23
End
Body 1
  Equation = 1
  Material = 1
End
Equation 1
  Active Solvers(3) = 1 2 3
  Convection = "Constant"
{units_line}End
'''
 for i,(eq,name,procedure) in enumerate([('Heat Equation','ThermalField','HeatSolve" "HeatSolver'),('Stat Current Solver','ElectricField','StatCurrentSolve" "StatCurrentSolver'),('Advection Diffusion','Conc','AdvectionDiffusion" "AdvectionDiffusionSolver')],1):
  text+=f'''Solver {i}
  Equation = "{eq}"
  Procedure = "{MODULES}/{procedure}"
  Variable = "{name}"
  Variable DOFs = 1
  Linear System Solver = Direct
  Linear System Direct Method = UMFPack
  Nonlinear System Max Iterations = 1
  Steady State Convergence Tolerance = 1.0e-10
'''
  if i==3:
   text+='  Bubbles = False\n  Stabilize = False\n'
  text+='End\n'
 text+=f'''Material 1
{material}
  Heat Conductivity = Real 1.0
  Heat Capacity = Real 1.0
  Electric Conductivity = Real 1.0
  Conc EPotential Field Variable = String "ElectricField"
  Temperature Field Variable = String "ThermalField"
  Reference Temperature = Real {boundary('temperature','bottom'):.17g}
  Convection Velocity 1 = Real 0.0
  Convection Velocity 2 = Real 0.0
End
'''
 for i,side,tag in [(1,'bottom',1),(2,'top',3)]:
  text+=f'Boundary Condition {i}\n  Target Boundaries(1) = {tag}\n'
  for variable,keyword in [('temperature','ThermalField'),('potential','ElectricField'),('concentration','Conc')]:
   if bc[variable,side]['operator']=='dirichlet':text+=f'  {keyword} = Real {boundary(variable,side):.17g}\n'
  text+='End\n'
 return text

def prepare(problem,directory):
 write_native_mesh(problem,directory/'mesh');(directory/'case.sif').write_text(sif(problem),encoding='utf-8',newline='\n')

def run(input_path,output_path):
 problem=load_problem(input_path)
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);prepare(problem,d);env=os.environ.copy();env.update(ELMER_HOME='/opt/elmer-source/fem/src',ELMER_LIB=MODULES);process=subprocess.run([ELMER,'case.sif'],cwd=d,env=env,capture_output=True,text=True)
  if process.returncode or 'ALL DONE' not in process.stdout:raise RuntimeError(f'Trusted Elmer process failed {process.returncode}: {process.stdout[-2000:]} {process.stderr[-2000:]}')
  fields,_=read_result(d/'mesh/case.result')
  values={name:fields[key][None,:,None] for name,key in [('concentration','conc'),('temperature','thermalfield'),('potential','electricfield')]}
 write_result(output_path,problem,values)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.input,a.output)
