"""Configure the installed native PyClaw solver; no PDE/source implementation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from clawpack import pyclaw, riemann

data=np.load('native-input.npz');nx,ny=data['q'].shape[1:];L=data['lengths']
solver=pyclaw.ClawSolver2D(riemann.shallow_bathymetry_fwave_2D)
solver.fwave=True
solver.dimensional_split=True;solver.order=2;solver.limiters=pyclaw.limiters.tvd.MC
solver.cfl_desired=.8;solver.cfl_max=.9
solver.bc_lower[:]=[pyclaw.BC.wall,pyclaw.BC.wall]
solver.bc_upper[:]=[pyclaw.BC.wall,pyclaw.BC.wall]
# External states fill ghost cells only. Native rpn2 splits incoming/outgoing
# fluctuations at the reservoir/interior interface; interior cells are never reset.
def reservoir_lower(state,dim,t,qbc,auxbc,num_ghost):
    assert dim.name=='x'
    h=float(np.interp(t,data['reservoir_times'],data['reservoir_depth']))
    qbc[0,:num_ghost,:]=h
    qbc[1:,:num_ghost,:]=0.
solver.bc_lower[0]=pyclaw.BC.custom
solver.user_bc_lower=reservoir_lower
domain=pyclaw.Domain([pyclaw.Dimension(0.,float(L[0]),nx,name='x'),pyclaw.Dimension(0.,float(L[1]),ny,name='y')])
solver.aux_bc_lower[:]=[pyclaw.BC.extrap,pyclaw.BC.extrap]
solver.aux_bc_upper[:]=[pyclaw.BC.extrap,pyclaw.BC.extrap]
state=pyclaw.State(domain,3,1);state.aux[0,:,:]=data['bed'];state.problem_data.update(grav=float(data['gravity']),dry_tolerance=1e-10,sea_level=0.);state.q[:]=data['q'];solution=pyclaw.Solution(state,domain)
solver.setup(solution);frames=[]
for t in data['times']:
    solver.evolve_to_time(solution,float(t));frames.append(solution.state.q.copy())
np.savez('native-output.npz',q=frames,times=data['times'],x=state.grid.x.centers,y=state.grid.y.centers)
module=Path(riemann.shallow_bathymetry_fwave_2D.__file__)
Path('native-runtime.json').write_text(json.dumps({'riemann_module':str(module),'riemann_binary_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'frames':len(frames),'numerical_validation':False},indent=2))
