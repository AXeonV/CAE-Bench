"""Semiconductor declaration checks only; no physical or reference solver."""
from functools import lru_cache
from importlib.resources import files
import json
import math

import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def component_shape(spec, parameters):
    return [parameters['mode_count'] if x == 'm' else x for x in spec['shape']]


def check(problem, errors):
    """Check exactly the public DATA declarations after neutral structure checks."""
    from caeoj.validation import issue
    m, a = problem.manifest, problem.arrays

    def fail(path, expected, actual):
        errors.append(issue('E_SEMICONDUCTOR', path, expected, actual,
                            'Declaration violates this semiconductor DATA contract.'))

    model = m.get('physics', {}).get('model', '')
    slug = model.removesuffix('-v1')
    cfg = models().get(slug)
    if cfg is None or model != slug + '-v1':
        fail('$.physics.model', 'registered semiconductor model', model)
        return
    if 'task' in m and m['task'] != slug:
        fail('$.task', slug, m['task'])
    if m['spatial_dimension'] != 1:
        fail('$.spatial_dimension', 1, m['spatial_dimension'])
    if m['meshes'] or m['geometries']:
        fail('$.meshes/geometries', 'empty objects', [m['meshes'], m['geometries']])
    if any(k in m for k in ('profile', 'analysis', 'materials', 'contract_version')):
        fail('$', 'physics only', 'mixed declaration')
    p = {}

    def value_range(path, value, spec):
        if spec.get('positive') and np.any(value <= 0):
            fail(path, 'strictly positive', value)
        if spec.get('lower') is not None and np.any(value < spec['lower']):
            fail(path, '>= ' + str(spec['lower']), value)
        if spec.get('upper') is not None and np.any(value > spec['upper']):
            fail(path, '<= ' + str(spec['upper']), value)

    params = m['physics'].get('parameters', {})
    if set(params) != set(cfg['parameters']):
        fail('$.physics.parameters', sorted(cfg['parameters']), sorted(params))
        return
    for key, spec in cfg['parameters'].items():
        v = params[key]
        x = v.get('value')
        types = (int,) if spec.get('integer') else (int, float)
        if set(v) != {'value', 'unit'} or type(x) not in types or v.get('unit') != spec['unit']:
            fail('$.physics.parameters.' + key, spec, v)
            continue
        value_range('$.physics.parameters.' + key, np.asarray(x), spec)
        p[key] = x
    if errors:
        return
    locs = m['locations']
    if set(locs) != set(cfg['locations']):
        fail('$.locations', sorted(cfg['locations']), sorted(locs))
        return
    for name, spec in cfg['locations'].items():
        l = locs[name]
        if l['kind'] != spec['kind']:
            fail('$.locations.' + name + '.kind', spec['kind'], l['kind'])
            continue
        keys = {'kind', 'ids', 'coordinates'} if l['kind'] == 'points' else {'kind', 'ids'}
        if set(l) != keys:
            fail('$.locations.' + name, sorted(keys), sorted(l))
        n = len(a[l['ids']])
        if not spec['minimum'] <= n <= spec['maximum']:
            fail('$.locations.' + name, [spec['minimum'], spec['maximum']], n)
    axes = {'static'} | {s['axis'] for s in cfg['inputs'].values()} | {s['axis'] for s in cfg['outputs'].values()}
    if set(m['time_axes']) != axes:
        fail('$.time_axes', sorted(axes), sorted(m['time_axes']))
        return
    for name in axes & {'static', 'initial'}:
        if not np.array_equal(a[m['time_axes'][name]], [0.]):
            fail('$.time_axes.' + name, '[0.0]', a[m['time_axes'][name]])
    if cfg['transient']:
        obs, drive = (a[m['time_axes'][n]] for n in ('observe', 'drive'))
        if not 1 <= len(obs) <= 256 or obs[0] < 0 or not 0 < obs[-1] <= 1:
            fail('$.time_axes.observe', '1..256 times in [0,tend], 0<tend<=1', obs)
        if not 2 <= len(drive) <= 512 or drive[0] != 0 or drive[-1] != obs[-1]:
            fail('$.time_axes.drive', '2..512 times from 0 to observe[-1]', drive)
        if slug in ('semiconductor-minority-diffusion', 'semiconductor-drift-transient') and obs[0] <= 0:
            fail('$.time_axes.observe', 'strictly positive output times', obs)
    if errors:
        return
    if 'profile' in locs:
        x = a[locs['profile']['coordinates']][:, 0]
        if np.any(np.diff(x) <= 0) or x[0] != 0 or x[-1] != p['length']:
            fail('$.locations.profile', 'strictly increasing x from 0 to L', x)
        cx = a[locs['contacts']['coordinates']][:, 0]
        if not np.array_equal(cx, [0., p['length']]):
            fail('$.locations.contacts', 'coordinates exactly [0,L]', cx)
        rx = a[locs['receivers']['coordinates']][:, 0]
        if np.any(rx <= 0) or np.any(rx >= p['length']):
            fail('$.locations.receivers', '0<x<L', rx)
    if 'modes' in locs:
        ids = a[locs['modes']['ids']]
        if not np.array_equal(ids, np.arange(p['mode_count'])):
            fail('$.locations.modes', 'IDs exactly 0..mode_count-1', ids)
    values = {}
    fields = m['fields']
    if len(fields) != len(cfg['inputs']):
        fail('$.fields', 'one field per required input quantity', len(fields))
    quantities = {}
    for name, spec in fields.items():
        q = spec['quantity']
        if q not in cfg['inputs'] or q in quantities:
            fail('$.fields.' + name + '.quantity', 'unique required input quantity', q)
            continue
        quantities[q] = name
        target = cfg['inputs'][q]
        shape = component_shape(target, p)
        expected = dict(dtype='float64', kind='scalar', component_shape=shape, components=['value'],
                        location=target['location'], time_axis=target['axis'], unit=target['unit'],
                        value_kind='point', sampling=dict(space='piecewise_linear' if target['location'] == 'profile' else 'uniform',
                                                        time='linear' if target['axis'] == 'drive' else 'constant', extrapolation='forbid'))
        for k, v in expected.items():
            if spec.get(k) != v:
                fail('$.fields.' + name + '.' + k, v, spec.get(k))
        values[q] = a[spec['array']]
        value_range('$.fields.' + name, values[q], target)
    if set(quantities) != set(cfg['inputs']):
        fail('$.fields', sorted(cfg['inputs']), sorted(quantities))
    seen = set()
    for i, cond in enumerate(m['conditions']):
        q = cond['variable']
        path = '$.conditions[' + str(i) + ']'
        if q not in quantities or q in seen:
            fail(path, 'one record per input quantity', q)
            continue
        seen.add(q)
        s = cfg['inputs'][q]
        role = 'initial' if s['axis'] == 'initial' else 'boundary' if s['location'] == 'contacts' else 'material' if q in ('doping', 'thickness', 'mass', 'band_edge') else 'source'
        expected = dict(role=role, variable=q, location=s['location'], operator='prescribed', data={'value': {'field': quantities[q]}})
        if cond != expected:
            fail(path, expected, cond)
    if seen != set(cfg['inputs']):
        fail('$.conditions', sorted(cfg['inputs']), sorted(seen))
    present = set()
    total = 0
    for name, spec in m['outputs'].items():
        q = spec['quantity']
        target = cfg['outputs'].get(q)
        if target is None:
            fail('$.outputs.' + name + '.quantity', sorted(cfg['outputs']), q)
            continue
        present.add(q)
        shape = component_shape(target, p)
        scalar = shape == [1] and q != 'wavefunction'
        expected = dict(dtype='float64', kind='scalar' if scalar else 'components', component_shape=shape,
                        components=['value'] if scalar else ['c'+str(i+1) for i in range(math.prod(shape))],
                        location=target['location'], time_axis=target['axis'], unit=target['unit'], value_kind='point')
        for key, v in expected.items():
            if spec.get(key) != v:
                fail('$.outputs.' + name + '.' + key, v, spec.get(key))
        if 'sampling' in spec:
            fail('$.outputs.' + name, 'no output sampling', spec['sampling'])
        total += len(a[locs[target['location']]['ids']]) * len(a[m['time_axes'][target['axis']]]) * math.prod(shape)
    if present != set(cfg['outputs']):
        fail('$.outputs', sorted(cfg['outputs']), sorted(present))
    if total > 2000000 or sum(v.size for v in values.values()) > 2000000:
        fail('$.fields/outputs', '<=2000000 scalar components each', total)
    if errors:
        return
    if slug == 'semiconductor-drift-transient':
        for carrier in ('electron', 'hole'):
            initial = values['initial_' + carrier][0, [0, -1], 0]
            contact = values['contact_' + carrier][0, :, 0]
            if np.any(abs(initial-contact) > 1e-12 * abs(contact)):
                fail('$.fields.initial_' + carrier, 'initial endpoints match t=0 contacts to rtol 1e-12', initial)
    if slug == 'semiconductor-minority-diffusion':
        limit = .01 * p['majority_density']
        if np.max(values['initial_excess']) > limit or p['lifetime'] * np.max(values['generation']) > limit:
            fail('$.fields', 'low injection sufficient bound <=0.01 p0', limit)
    if slug == 'semiconductor-landauer' and np.any(np.diff(values['energy'][0, :, 0]) <= 0):
        fail('$.fields.energy', 'strictly increasing energies', values['energy'])
    if slug == 'semiconductor-effective-mass':
        length = float(np.sum(values['thickness']))
        x = a[locs['receivers']['coordinates']][:, 0]
        if np.any(x <= 0) or np.any(x >= length):
            fail('$.locations.receivers', '0<x<sum(thickness)', x)
