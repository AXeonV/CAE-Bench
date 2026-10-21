"""Configure the existing Thetis equations; no PDE/source implementation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from thetis import *
import thetis.shallowwater_eq

data=np.load('/work/native-input.npz');mesh=Mesh('/work/native-mesh.msh')
P1=FunctionSpace(mesh,'CG',1);V1=VectorFunctionSpace(mesh,'CG',1)
coords=Function(V1).interpolate(SpatialCoordinate(mesh)).dat.data_ro.copy()
dist,ids=cKDTree(data['x']).query(coords);assert np.max(dist)<1e-9 and len(np.unique(ids))==len(data['x'])
inverse=np.empty(len(ids),int);inverse[ids]=np.arange(len(ids));observed=inverse[data['observed']]
h0=Function(P1);h0.dat.data[:]=data['h'][ids]
u0=Function(V1);u0.dat.data[:]=data['u'][ids]
bathymetry=Function(P1).assign(1.)
# Constant vertical datum: h=1+eta, and physical bed is exactly zero.
physical_constants['g_grav'].assign(float(data['gravity']))
physical_constants['rho0'].assign(float(data['density']))
solver=solver2d.FlowSolver2d(mesh,bathymetry);o=solver.options
o.use_nonlinear_equations=True;o.element_family='dg-dg';o.polynomial_degree=1
o.linear_drag_coefficient=Constant(float(data['drag']))
o.horizontal_viscosity=None;o.coriolis_frequency=None
o.swe_timestepper_type='CrankNicolson';o.timestep=.0005
o.simulation_end_time=float(data['end']);o.simulation_export_time=.0005
o.no_exports=True;o.check_volume_conservation_2d=False
o.swe_timestepper_options.solver_parameters={'snes_type':'newtonls','snes_rtol':1e-9,'snes_atol':1e-10,'snes_max_it':25,'ksp_type':'preonly','pc_type':'lu'}
# Omitted boundary entries are native impermeable land/slip boundaries,
# as in Thetis' official closed 2-D channel example.
solver.assign_initial_conditions(elev=h0-1.,uv=u0)
frames={k:[] for k in ['depth','velocity','water_flux','water_volume']};times=[];raw_elev=[];raw_uv=[]
def export():
    t=solver.simulation_time
    if not any(abs(t-float(v))<1e-9 for v in data['times']):return
    uv=solver.fields.uv_2d;eta=solver.fields.elev_2d
    depth=Function(P1).project(1.+eta);velocity=Function(V1).project(uv);flux=Function(V1).project((1.+eta)*uv)
    h=depth.dat.data_ro[observed].copy();assert np.isfinite(h).all() and np.min(h)>0
    frames['depth'].append(h[:,None]);frames['velocity'].append(velocity.dat.data_ro[observed].copy());frames['water_flux'].append(flux.dat.data_ro[observed].copy());frames['water_volume'].append([[float(assemble((1.+eta)*dx))]])
    times.append(t);raw_elev.append(eta.dat.data_ro.copy());raw_uv.append(uv.dat.data_ro.copy())
    Path('/work/progress.json').write_text(json.dumps({'physical_time':t,'frames':len(times),'numerical_validation':False}))
solver.iterate(export_func=export)
assert len(times)==len(data['times']) and np.allclose(times,data['times'],atol=1e-9,rtol=0)
np.savez('/work/native-output.npz',times=times,**frames)
np.savez('/work/native-dg-fields.npz',elev=raw_elev,velocity=raw_uv,elev_cell_dofs=solver.fields.elev_2d.function_space().cell_node_map().values,velocity_cell_dofs=solver.fields.uv_2d.function_space().cell_node_map().values)
src=Path(thetis.shallowwater_eq.__file__)
Path('/work/native-runtime.json').write_text(json.dumps({'native_module':str(src),'native_module_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'frames':len(times),'native_wall_semantics':'Default closed native land boundaries','point_recovery':'Native L2 projection of DG fields into CG1, sampled on real public nodes; approximate point reconstruction, no accuracy verification.','numerical_validation':False},indent=2))
