"""Configure the installed native PyClaw solver; no PDE/source implementation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from clawpack import pyclaw, riemann

data=np.load('native-input.npz');nx,ny=data['q'].shape[1:];L=data['lengths']
solver=pyclaw.ClawSolver2D(riemann.shallow_hlle_2D)
solver.dimensional_split=True;solver.order=2;solver.limiters=pyclaw.limiters.tvd.MC
solver.cfl_desired=.8;solver.cfl_max=.9
solver.bc_lower[:]=[pyclaw.BC.wall,pyclaw.BC.wall]
solver.bc_upper[:]=[pyclaw.BC.wall,pyclaw.BC.wall]
domain=pyclaw.Domain([pyclaw.Dimension(0.,float(L[0]),nx,name='x'),pyclaw.Dimension(0.,float(L[1]),ny,name='y')])
state=pyclaw.State(domain,3);state.problem_data['grav']=float(data['gravity']);state.q[:]=data['q'];solution=pyclaw.Solution(state,domain)
solver.setup(solution);frames=[]
for t in data['times']:
    solver.evolve_to_time(solution,float(t));frames.append(solution.state.q.copy())
np.savez('native-output.npz',q=frames,times=data['times'],x=state.grid.x.centers,y=state.grid.y.centers)
module=Path(riemann.shallow_hlle_2D.__file__)
Path('native-runtime.json').write_text(json.dumps({'riemann_module':str(module),'riemann_binary_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'frames':len(frames),'numerical_validation':False},indent=2))
