"""Turbulence-method declarations and public sample statistics."""
import numpy as np
from ..thermal_flow import check_declaration

MODELS = {}
for _family, _energy in (('incompressible', False), ('lowmach', True)):
    for _method, _analysis in (('rans', 'steady'), ('urans', 'transient'), ('resolved', 'statistics')):
        MODELS[f'fluid-energy-{_family}-{_method}-{_analysis}-v1'] = (_family, _energy, _method, _analysis)
for _family, _energy in (('isothermal', False), ('compressible', True)):
    MODELS[f'fluid-energy-{_family}-rans-steady-v1'] = (_family, _energy, 'rans', 'steady')

def fluid_energy_statistics(times, velocity, temperature=None):
    """Equal-weight mean and central products of public instantaneous samples.

    velocity shape [S,N,D]; optional temperature [S,N,1]. Population denominator
    S, not S-1; no density weighting. Returns arrays without an output time axis.
    """
    times = np.asarray(times); u = np.asarray(velocity, dtype=float)
    if times.ndim != 1 or len(times) < 2 or not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0) or u.ndim != 3 or len(u) != len(times) or not np.all(np.isfinite(u)):
        raise ValueError('Finite increasing times and finite [S,N,D] velocity required')
    if not np.allclose(np.diff(times), np.diff(times)[0], rtol=1e-10, atol=1e-12): raise ValueError('Statistics samples must be equally spaced')
    mean = u.mean(axis=0); du = u - mean
    result = {'velocity': mean, 'velocity_covariance': np.einsum('sni,snj->nij', du, du) / len(times)}
    if temperature is not None:
        t = np.asarray(temperature, dtype=float)
        if t.shape != (*u.shape[:2], 1) or not np.all(np.isfinite(t)): raise ValueError('Temperature must be finite [S,N,1]')
        mt = t.mean(axis=0); dt = t - mt
        result.update(temperature=mt, temperature_variance=(dt * dt).mean(axis=0), turbulent_heat_flux=(du * dt).mean(axis=0))
    return result



def check(problem, errors):
    if problem.manifest.get('physics', {}).get('model') in MODELS:
        check_declaration(problem, errors, MODELS)

check_fluid_energy = check
