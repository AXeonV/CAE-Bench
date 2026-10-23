"""Generate instantaneous ECM input states and independent algebraic checks.

The checks are not the published solver reference; replay.py produces that by
actually calling the pinned repaired PyBaMM implementation.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json


def make_case(root, name, *, grid=8, rc=0, mode='mixed', seed=1):
    rng = np.random.default_rng(seed)
    n = 12
    mean = rng.uniform(.25, .75, n)
    slope = rng.uniform(.05, .35, n)
    current = rng.uniform(5, 80, n)
    enabled = np.ones(n, dtype=bool)
    coefficients = np.column_stack([rng.uniform(2.8, 4.2, n), rng.uniform(.7, 1.5, n),
                                     rng.uniform(-.1, .1, n), rng.uniform(-.1, .1, n)])
    if mode == 'discharge':
        slope *= -1
    elif mode == 'charge':
        current *= -1
    elif mode == 'disabled':
        enabled[:] = False
        slope[:] = 0
    elif mode == 'uniform':
        slope[:] = 0
    elif mode == 'zero-current':
        current[:] = 0
    elif mode == 'reverse':
        current *= rng.choice([-1, 1], n)
        slope = np.sign(current) * np.abs(slope)
    elif mode == 'mixed':
        current *= rng.choice([-1, 1], n)
        slope *= rng.choice([-1, 1], n)
        enabled[::4] = False
        slope[~enabled] = 0
    elif mode == 'linear-ocv':
        slope *= -1
        coefficients[:, 2:] = 0
    profile = mean[:, None] + slope[:, None] * ((np.arange(grid) + .5) / grid - .5)
    heats = rng.uniform(0, 30, (n, rc+1))
    reversible = rng.uniform(-20, 20, n)
    if mode == 'no-other-heat':
        heats[:] = 0
    if mode == 'no-reversible':
        reversible[:] = 0
    arrays = {'state_ids': np.array([11+13*i+i*i for i in range(n)], dtype='int64'),
              'times': np.array([0.], dtype='float64'), 'current': current[None, :, None],
              'average_soc': mean[None, :, None], 'diffusion_enabled': enabled[None, :, None],
              'soc_profile': profile[None], 'ocv_coefficients': coefficients[None],
              'element_heat': heats[None], 'reversible_heat': reversible[None, :, None]}

    def spec(name, quantity, unit, components, *, output=False, dtype='float64'):
        result = {'array': name, 'quantity': quantity, 'location': 'states', 'time_axis': 'instant',
                  'dtype': dtype, 'kind': 'scalar' if len(components)==1 else 'components',
                  'component_shape': [len(components)], 'components': components, 'unit': unit, 'value_kind': 'point'}
        if not output:
            result['sampling'] = {'space': 'uniform', 'time': 'constant', 'extrapolation': 'forbid'}
        return result

    descriptions = [('current','current','A',['value']), ('average_soc','state_of_charge','1',['value']),
                    ('diffusion_enabled','enabled','1',['value']),
                    ('soc_profile','state_of_charge','1',[f'cell_{i}' for i in range(grid)]),
                    ('ocv_coefficients','voltage_coefficients','V',['c0','c1','c2','c3']),
                    ('element_heat','irreversible_heat_power','W',['value'] if rc==0 else [f'element_{i}' for i in range(rc+1)]),
                    ('reversible_heat','reversible_heat_power','W',['value'])]
    outputs = [('surface_soc','state_of_charge','1'), ('diffusion_overpotential','voltage','V'),
               ('irreversible_heat','irreversible_heat_power','W'), ('total_heat','heat_power','W')]
    manifest = {'task':'diffusion-element-heat-repair','spatial_dimension':1,'data_file':'input.h5',
                'geometries':{},'meshes':{},'conditions':[],
                'physics':{'model':'ecm-diffusion-heat-v1','parameters':{
                    'grid_count':{'value':grid,'unit':'1'},'rc_count':{'value':rc,'unit':'1'}}},
                'locations':{'states':{'kind':'entities','ids':'state_ids'}},'time_axes':{'instant':'times'},
                'fields':{a:spec(a,b,c,d,dtype='bool' if a=='diffusion_enabled' else 'float64') for a,b,c,d in descriptions},
                'outputs':{a:spec(a,b,c,['value'],output=True) for a,b,c in outputs}}
    directory = root/'cases'/name
    directory.mkdir(parents=True, exist_ok=True)
    write_hdf5(directory/'input.h5', arrays)
    write_json(directory/'problem.json', manifest)
    surface = np.where(enabled, mean+slope/2, mean)

    def voltage(s):
        return coefficients[:,0]+coefficients[:,1]*s+coefficients[:,2]*s*s+coefficients[:,3]*s*s*s

    eta = np.where(enabled, voltage(surface)-voltage(mean), 0.)
    irrevers = heats.sum(axis=1)-current*eta
    independent = {a:np.asarray(v).reshape(1,n,1).tolist() for a,v in [
        ('surface_soc',surface),('diffusion_overpotential',eta),('irreversible_heat',irrevers),('total_heat',irrevers+reversible)]}
    (root/'independent-checks').mkdir(exist_ok=True)
    write_json(root/'independent-checks'/(name+'.json'), independent)
    return {'case':name,'grid_count':grid,'rc_count':rc,'mode':mode,'seed':seed,'states':n,
            'origin':'author adaptation of PyBaMM #5859 submodel failure; not original issue trajectory'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    cases=[('01-discharge-public',8,0,'discharge'),('02-disabled-public',8,0,'disabled'),
           ('03-charge',8,0,'charge'),('04-reversed-current',8,0,'reverse'),
           ('05-nonlinear-ocv',17,1,'mixed'),('06-linear-ocv',4,0,'linear-ocv'),
           ('07-zero-current',8,0,'zero-current'),('08-uniform-profile',8,3,'uniform'),
           ('09-no-other-heat',16,0,'no-other-heat'),('10-no-reversible-heat',16,3,'no-reversible'),
           ('11-four-elements',8,3,'mixed'),('12-two-elements',32,1,'discharge'),
           ('13-coarse-grid',4,2,'mixed'),('14-fine-grid',64,2,'mixed'),
           ('15-disabled-rc',17,3,'disabled'),('16-mixed-states',32,2,'mixed')]
    catalog=[make_case(args.output,name,grid=k,rc=rc,mode=mode,seed=731+i) for i,(name,k,rc,mode) in enumerate(cases)]
    write_json(args.output/'catalog.json',catalog)
