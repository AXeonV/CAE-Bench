"""Temporary protocol payloads only, never numerical reference solutions."""
from pathlib import Path
import json
import h5py
import numpy as np
from caeoj_ext.semiconductor import models, component_shape


def fixture(base, slug):
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    cfg = models()[slug]
    defaults = dict(length=1e-6, temperature=300., permittivity=1e-10, intrinsic_density=1e16,
                    tau_n=1e-6, tau_p=2e-6, mobility_n=.1, mobility_p=.04,
                    radiative=1e-16, auger_n=1e-42, auger_p=1e-42,
                    trap_density=1e17, capture_n=1e-15, capture_p=2e-15, n1=1e16, p1=1e16,
                    diffusivity=.01, lifetime=1e-6, majority_density=1e21,
                    temperature_left=300., temperature_right=280., chemical_left=1e-20,
                    chemical_right=0., degeneracy=2, mode_count=2)
    p = {k: defaults[k] for k in cfg['parameters']}
    arrays = {'marker': np.array([0.])}
    axes = {'static': 'marker'}
    if cfg['transient']:
        axes.update(initial='marker', drive='drive_times', observe='observation_times')
        arrays.update(drive_times=np.array([0., 1e-7, 1e-6]), observation_times=np.array([2e-7, 1e-6]))
    locs = {}
    for name, spec in cfg['locations'].items():
        n = 3 if name in ('profile', 'spectrum', 'receivers') else 1 if name == 'system' else 2
        ids = np.arange(n, dtype='int64') if name == 'modes' else np.array([7+11*i for i in range(n)], dtype='int64')
        arrays[name+'_ids'] = ids
        locs[name] = dict(kind=spec['kind'], ids=name+'_ids')
        if spec['kind'] == 'points':
            x = np.array([0., .4e-6, 1e-6]) if name == 'profile' else np.array([0., 1e-6]) if name == 'contacts' else np.array([.9e-6, .25e-6, .25e-6])
            if slug == 'semiconductor-effective-mass': x = np.array([1e-9, 1.5e-9, 3e-9])
            arrays[name+'_x'] = x[:, None]
            locs[name]['coordinates'] = name+'_x'
    manifest = dict(task=slug, spatial_dimension=1, data_file='input.h5', geometries={}, meshes={},
                    locations=locs, time_axes=axes, fields={}, outputs={}, conditions=[],
                    physics=dict(model=slug+'-v1', parameters={k: dict(value=v, unit=cfg['parameters'][k]['unit']) for k,v in p.items()}))
    for q, spec in cfg['inputs'].items():
        n = len(arrays[locs[spec['location']]['ids']])
        t = len(arrays[axes[spec['axis']]])
        value = 0.
        if q.startswith('initial_') and q != 'initial_occupation' or q.startswith('contact_') and q != 'contact_potential': value = 1e16
        value = dict(initial_occupation=.3, surface_velocity=10., thickness=2e-9,
                     mass=9.1093837e-32, transmission=.5).get(q, value)
        values = np.full((t, n, 1), value, dtype='float64')
        if q == 'energy':values[0,:,0]=[-2e-20, 0., 2e-20]
        name, key = 'input_'+q, 'payload_'+q
        arrays[key] = values
        manifest['fields'][name] = dict(array=key, quantity=q, location=spec['location'], time_axis=spec['axis'],
            dtype='float64', kind='scalar', component_shape=[1], components=['value'], unit=spec['unit'], value_kind='point',
            sampling=dict(space='piecewise_linear' if spec['location']=='profile' else 'uniform',
                          time='linear' if spec['axis']=='drive' else 'constant', extrapolation='forbid'))
        role='initial' if spec['axis']=='initial' else 'boundary' if spec['location']=='contacts' else 'material' if q in ('doping','thickness','mass','band_edge') else 'source'
        manifest['conditions'].append(dict(role=role, variable=q, location=spec['location'], operator='prescribed', data={'value':{'field':name}}))
    for q, spec in cfg['outputs'].items():
        shape=component_shape(spec,p)
        scalar=q!='wavefunction'
        manifest['outputs']['observation_'+q]=dict(array='result_'+q, quantity=q, location=spec['location'], time_axis=spec['axis'], dtype='float64', kind='scalar' if scalar else 'components', component_shape=shape, components=['value'] if scalar else ['c'+str(i+1) for i in range(shape[0])], unit=spec['unit'], value_kind='point')
    with h5py.File(base/'input.h5','w') as h:
        for key,v in arrays.items():h[key]=v
    path=base/'problem.json'
    path.write_text(json.dumps(manifest),encoding='utf-8')
    return path,manifest
