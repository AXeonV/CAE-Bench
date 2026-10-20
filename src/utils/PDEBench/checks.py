"""Read-only source applicability checks. Never produce or repair PDE solutions."""
import numpy as np
from .storage import PreparationError
from .conversion import check_reference_initial
from .models import parameters


def source_reference(model, problem, values, config):
    """Return source fields and reasons why a candidate cannot yet be graded."""
    arrays = {name: values[name].reshape(len(problem.arrays['times']), -1, n)
              for name, _, _, n in model.fields}
    check_reference_initial(model, problem, arrays)
    blocked = []
    metrics = {}
    if model.model == 'darcy_flow_2d':
        # Do not silently replace published finite-time snapshots with a new steady solve.
        blocked.append('Published Darcy steady-state suitability unresolved; no automatic equilibrium correction')
    if model.points:
        metrics.update(kinematic_viscosity=config['NU'], domain_size=config['domain_size'],
                       grid_size=config['grid_size'], velocity_extrapolation=config['velocity_extrapolation'])
    if model.model == 'reaction_diffusion_2d':
        sim = config.get('sim', {})
        if any(sim.get(k) != v for k, v in [('Du', .001), ('Dv', .005), ('k', .005)]):
            raise PreparationError('Unexpected FHN physical configuration')
    if model.model == 'diffusion_sorption_1d':
        sim = config.get('sim', {})
        expected = {'D': .0005, 'por': .29, 'rho_s': 2880, 'k_f': .00035, 'n_f': .874, 'sol': 1.}
        if any(sim.get(k) != v for k, v in expected.items()):
            raise PreparationError('Unexpected sorption physical configuration')
    if model.model.startswith('compressible_'):
        rho, pressure = arrays['density'][..., 0], arrays['pressure'][..., 0]
        if rho.min() <= 0 or pressure.min() <= 0:
            raise PreparationError('Nonpositive compressible source state')
        metrics.update(minimum_density=float(rho.min()), minimum_pressure=float(pressure.min()))
        if any(c['operator'] == 'periodic' for c in problem.manifest['conditions']):
            means = rho.mean(axis=1)
            drift = float(np.max(abs(means-means[0]))/means[0])
            metrics['relative_mass_drift'] = drift
            if drift > .005:
                raise PreparationError('Source periodic mass drift exceeds existing plausibility bound')
    return arrays, {'producer': 'DaRUS published numerical trajectory', 'metrics': metrics,
                    'blocked': blocked, 'continuum_error_certified': False,
                    'limitations': ['Published precision and source discretization retained; numerical accuracy and provisional grading thresholds are not certified']}


def source_geometry(model, source, coords, times, config):
    """Enforce existing question sizes/time limits before allocating field payloads."""
    shape = tuple(len(c) for c in coords)
    end = {'advection_1d': 2, 'burgers_1d': 2, 'reaction_diffusion_1d': 1,
           'diffusion_sorption_1d': 500, 'reaction_diffusion_2d': 5,
           'shallow_water_2d': 1, 'darcy_flow_2d': 0,
           'inhomogeneous_incompressible_navier_stokes_2d': 4.995}.get(model.model, 1)
    size = 1024 if model.dimension == 1 else 512 if model.points else 128
    if model.model.startswith('compressible_'):
        p = parameters(model, source)
        eta, zeta = p['shear_viscosity']['value'], p['bulk_viscosity']['value']
        trans = 'trans' in source['filename'] or source['filename'].startswith('Sod')
        allowed = (1e-8,) if trans or model.dimension == 3 else (1e-8, .01, .1)
        if eta != zeta or eta not in allowed:
            raise PreparationError('Source viscosity configuration outside existing question')
        size = 1024 if model.dimension == 1 else (512 if eta == 1e-8 else 128)
        if model.dimension == 3: size = 64 if 'Turb' in source['filename'] else 128
        if model.dimension == 1 and trans: end = 2
    if shape != (size,)*model.dimension:
        raise PreparationError(f'Source grid {shape} outside existing question size {(size,)*model.dimension}')
    if not np.isfinite(times).all() or times[0] != 0 or np.any(np.diff(times) <= 0) or times[-1] > end:
        raise PreparationError('Selected actual source times outside existing question')
    if model.model == 'reaction_diffusion_2d':
        sim = config.get('sim', {})
        if (sim.get('xdim'), sim.get('ydim')) != (512, 512):
            raise PreparationError('FHN complete initial grid must be 512x512')
