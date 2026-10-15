"""Explicit scalar viscosity responses shared by film and complex-fluid declarations."""
import numpy as np

def viscosity_response(cfg, parameters, shear_rate, temperature=None, structure=None):
    """Declared scalar viscosity in Pa.s; shear rate sqrt(2 D:D), in 1/s."""
    p=parameters; g=np.asarray(shear_rate,dtype=float)
    if np.any(~np.isfinite(g)) or np.any(g<0):raise ValueError('Finite nonnegative shear rate required')
    fam=cfg['family']
    if fam=='thixotropic':
        x=np.asarray(structure,dtype=float)
        if np.any(~np.isfinite(x)) or np.any((x<0)|(x>1)):raise ValueError('Structure must lie in [0,1]')
        mu=p['base_viscosity']+p['structure_viscosity']*x
    elif 'carreau' in fam:
        mu=p['infinite_viscosity']+(p['zero_viscosity']-p['infinite_viscosity'])*(1+(p['time_constant']*g)**2)**((p['power_index']-1)/2)
    else:
        if 'viscosity' not in p and 'solvent_viscosity' not in p:raise ValueError('Model has no scalar viscosity helper')
        mu=np.asarray(p.get('viscosity',p.get('solvent_viscosity')),dtype=float)+np.zeros_like(g)
    if 'temperature_coefficient' in p:
        t=np.asarray(temperature,dtype=float)
        if np.any(~np.isfinite(t)) or np.any(t<=0):raise ValueError('Positive absolute temperature required')
        mu=mu*np.exp(-p['temperature_coefficient']*(t-p['reference_temperature']))
    if np.any(~np.isfinite(mu)) or np.any(mu<=0):raise ValueError('Nonpositive/nonfinite viscosity')
    return mu
