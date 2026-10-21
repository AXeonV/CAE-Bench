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
# Separate callbacks select the external ghost strip; native Riemann solve
# determines incoming/outgoing fluctuations. Interior states are never reset.
def lower(state,dim,t,qbc,auxbc,num_ghost):
    assert dim.name=='x'
    qbc[0,:num_ghost,:]=1.;qbc[1,:num_ghost,:]=float(data['reservoir_speed']);qbc[2,:num_ghost,:]=0.
def upper(state,dim,t,qbc,auxbc,num_ghost):
    assert dim.name=='x'
    qbc[0,-num_ghost:,:]=1.;qbc[1,-num_ghost:,:]=float(data['reservoir_speed']);qbc[2,-num_ghost:,:]=0.
solver.bc_lower[0]=pyclaw.BC.custom;solver.bc_upper[0]=pyclaw.BC.custom
solver.user_bc_lower=lower;solver.user_bc_upper=upper
domain=pyclaw.Domain([pyclaw.Dimension(0.,float(L[0]),nx,name='x'),pyclaw.Dimension(0.,float(L[1]),ny,name='y')])
solver.aux_bc_lower[:]=[pyclaw.BC.extrap,pyclaw.BC.extrap]
solver.aux_bc_upper[:]=[pyclaw.BC.extrap,pyclaw.BC.extrap]
state=pyclaw.State(domain,3,1);state.aux[0,:,:]=data['bed'];state.problem_data.update(grav=float(data['gravity']),dry_tolerance=1e-10,sea_level=0.);state.q[:]=data['q'];solution=pyclaw.Solution(state,domain)
solver.setup(solution)
consecutive=0;history=[];converged=False
# A convergence stop is part of the native iteration, not accuracy validation.
# Finite cap: 1000 one-second pseudo-time windows. Preserve every residual.
for n in range(1,1001):
    old=solution.state.q.copy()
    solver.evolve_to_time(solution,float(n))
    q=solution.state.q
    assert np.isfinite(q).all() and np.min(q[0])>0.,'Native state is not finite/fully wet'
    scale=np.maximum(1.,np.max(np.abs(q),axis=(1,2)))
    rate=float(np.max(np.max(np.abs(q-old),axis=(1,2))/scale))
    history.append({'iteration':n,'pseudo_time_s':float(n),'relative_change_per_s':rate})
    consecutive=consecutive+1 if rate<1e-8 else 0
    if consecutive>=5:
        converged=True;break
Path('native-convergence.json').write_text(json.dumps({'converged':converged,'criterion':'max component relative state change per 1s <1e-8 for five consecutive windows; 1000-window cap','history':history,'numerical_validation':False},indent=2))
np.savez('native-output.npz',q=[solution.state.q.copy()],times=data['times'],x=state.grid.x.centers,y=state.grid.y.centers)
module=Path(riemann.shallow_bathymetry_fwave_2D.__file__)
Path('native-runtime.json').write_text(json.dumps({'riemann_module':str(module),'riemann_binary_sha256':hashlib.sha256(module.read_bytes()).hexdigest(),'frames':1,'numerical_validation':False},indent=2))
