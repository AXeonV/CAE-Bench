"""Temporary declaration fixtures, never physical references or formal cases."""
from pathlib import Path
import json

import h5py
import numpy as np
from caeoj_ext.radiation import models, shape, labels


def fixture(base, slug):
    base = Path(base); base.mkdir(parents=True, exist_ok=True)
    c = models()[slug]
    defaults = dict(group_count=2, particle=1, precursor_count=2,
                    generation_time=.001, nuclide_count=3)
    p = {k: defaults[k] for k in c['parameters']}
    arrays = {'marker': np.array([0.])}
    axes = {'static': 'marker'}
    if c['transient']:
        arrays['requested_times'] = np.array([0., .5, 1.])
        axes['requests'] = 'requested_times'
    if any(r['axis'] == 'control' for r in c['records'].values()):
        arrays['control_times'] = np.array([0., .25, 1.])
        axes['control'] = 'control_times'
    locs = {}
    for name, s in c['locations'].items():
        count = {'system':1, 'layers':2, 'probes':2, 'precursors':2, 'nuclides':3}[name]
        ids = np.array([3, 19], dtype='int64') if name in ('layers', 'probes') else np.arange(count, dtype='int64')
        arrays[name+'_ids'] = ids
        locs[name] = dict(kind=s['kind'], ids=name+'_ids')
        if s['kind'] == 'points':
            arrays[name+'_coordinates'] = np.array([[.3], [1.7]])
            locs[name]['coordinates'] = name+'_coordinates'
    m = dict(task=slug, spatial_dimension=1, data_file='input.h5', geometries={}, meshes={},
             locations=locs, time_axes=axes, fields={}, outputs={}, conditions=[],
             physics=dict(model='radiation-'+slug+'-v1', parameters={
                 k:dict(value=v, unit=c['parameters'][k]['unit']) for k,v in p.items()}))
    for op, r in c['records'].items():
        data = {}; n = len(arrays[locs[r['location']]['ids']]); t = len(arrays[axes[r['axis']]])
        for key, s in r['data'].items():
            v = np.zeros((t, n, *shape(s, p)))
            if s.get('positive'):
                v[:] = 1.
            if key == 'fraction':
                v[:] = .003
            if key == 'spectrum':
                v[:] = 1 / p['group_count']
            if op == 'branches':
                v[0,0,1,0] = .7; v[0,0,2,1] = .8
            if op == 'products':
                v[0,0,0,2] = .5
            if op == 'nuclides' and key == 'decay':
                v[0,:,0] = [.1, .2, 0.]
            name = op+'_'+key; array = 'payload_'+name
            arrays[array] = v
            m['fields'][name] = dict(array=array, quantity=r['variable'] if key=='value' else key,
                unit=s['unit'], kind=s['kind'], component_shape=shape(s,p), components=labels(s,p),
                dtype='float64', location=r['location'], time_axis=r['axis'], value_kind='point',
                sampling=dict(space='uniform', time='linear' if r['axis']=='control' else 'constant', extrapolation='forbid'))
            data[key] = {'field':name}
        m['conditions'].append(dict(operator=op, role=r['role'], variable=r['variable'], location=r['location'], data=data))
    for q, s in c['outputs'].items():
        m['outputs']['observation_'+q] = dict(array='answer_'+q, quantity=q, unit=s['unit'], kind=s['kind'],
            component_shape=shape(s,p), components=labels(s,p), dtype='float64', location=s['location'],
            time_axis=c['output_axis'], value_kind='point')
    with h5py.File(base/'input.h5', 'w') as h:
        for key, value in arrays.items():
            h[key] = value
    path = base/'problem.json'; path.write_text(json.dumps(m), encoding='utf-8')
    return path, m
