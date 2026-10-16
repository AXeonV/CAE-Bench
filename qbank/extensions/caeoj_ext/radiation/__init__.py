"""Radiation and nuclear inventory declarations; contains no physical solver."""
from functools import lru_cache
from importlib.resources import files
import json
import math

import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def shape(spec, parameters):
    names = {'g': 'group_count', 'b': 'precursor_count', 'n': 'nuclide_count'}
    return [parameters[names[x]] if isinstance(x, str) else x for x in spec['shape']]


def labels(spec, parameters):
    return ['value'] if spec['kind'] == 'scalar' else [
        'c'+str(i+1) for i in range(math.prod(shape(spec, parameters)))]


def check(problem, errors):
    from caeoj.validation import issue
    m, a = problem.manifest, problem.arrays

    def fail(path, expected, actual):
        if isinstance(actual, np.ndarray):
            actual = actual.tolist() if actual.size <= 16 else {'shape': list(actual.shape)}
        errors.append(issue('E_RADIATION', path, expected, actual,
                            'Declaration violates this radiation DATA contract.'))

    model = m.get('physics', {}).get('model', '')
    slug = model.removeprefix('radiation-').removesuffix('-v1')
    cfg = models().get(slug)
    if cfg is None or model != 'radiation-'+slug+'-v1':
        fail('$.physics.model', 'registered radiation model', model)
        return
    if m['spatial_dimension'] != 1:
        fail('$.spatial_dimension', 1, m['spatial_dimension'])
    if 'task' in m and m['task'] != slug:
        fail('$.task', slug, m['task'])
    if any(k in m for k in ('profile', 'contract_version', 'analysis', 'materials')):
        fail('$', 'physics-only declaration', 'mixed profile')
    if m['meshes'] or m['geometries']:
        fail('$.meshes/geometries', 'empty objects', 'spatial mesh or geometry')
    if set(m['physics']) != {'model', 'parameters'}:
        fail('$.physics', ['model', 'parameters'], list(m['physics']))
    params = m['physics'].get('parameters', {})
    if set(params) != set(cfg['parameters']):
        fail('$.physics.parameters', list(cfg['parameters']), list(params))
        return
    p = {}
    for name, s in cfg['parameters'].items():
        v = params[name]; x = v.get('value')
        if (set(v) != {'value', 'unit'} or v.get('unit') != s['unit'] or
                type(x) not in ((int,) if s.get('integer') else (int, float))):
            fail('$.physics.parameters.'+name, s, v)
            continue
        if (s.get('positive') and x <= 0 or
                'lower' in s and x < s['lower'] or 'upper' in s and x > s['upper']):
            fail('$.physics.parameters.'+name, s, x)
        p[name] = x
    if errors:
        return
    axes = {'static', cfg['output_axis']} | {r['axis'] for r in cfg['records'].values()}
    if set(m['time_axes']) != axes:
        fail('$.time_axes', sorted(axes), list(m['time_axes']))
        return
    if not np.array_equal(a[m['time_axes']['static']], [0.]):
        fail('$.time_axes.static', '[0.0]', a[m['time_axes']['static']])
    if cfg['transient']:
        times = a[m['time_axes']['requests']]
        if len(times) > 256 or times[0] < 0 or times[-1] <= 0:
            fail('$.time_axes.requests', '1..256 frames in [0,t_end], t_end>0', times)
        if 'control' in axes:
            control = a[m['time_axes']['control']]
            if not 2 <= len(control) <= 256 or control[0] != 0 or control[-1] != times[-1]:
                fail('$.time_axes.control', '2..256 frames spanning exactly [0,t_end]', control)
    locs = m['locations']
    if set(locs) != set(cfg['locations']):
        fail('$.locations', list(cfg['locations']), list(locs))
        return
    for name, s in cfg['locations'].items():
        l = locs[name]
        if l['kind'] != s['kind']:
            fail('$.locations.'+name, s['kind'], l['kind'])
        ids = a[l['ids']]
        if not s['minimum'] <= len(ids) <= s['maximum']:
            fail('$.locations.'+name, 'declared count limits', len(ids))
        count = {'system': 1, 'precursors': p.get('precursor_count'),
                 'nuclides': p.get('nuclide_count')}.get(name)
        if count is not None and not np.array_equal(ids, np.arange(count)):
            fail('$.locations.'+name, 'IDs exactly 0..'+str(count-1), ids)
    if errors:
        return

    refs, counts, values = set(), {}, {}
    for i, c in enumerate(m['conditions']):
        path = f'$.conditions[{i}]'
        op = c['operator']; r = cfg['records'].get(op)
        if r is None:
            fail(path+'.operator', list(cfg['records']), op)
            continue
        counts[op] = counts.get(op, 0)+1
        if counts[op] != 1:
            fail(path, 'exactly one complete record for '+op, counts[op])
        for k in ('role', 'variable', 'location'):
            if c[k] != r[k]:
                fail(path+'.'+k, r[k], c[k])
        if set(c['data']) != set(r['data']):
            fail(path+'.data', list(r['data']), list(c['data']))
            continue
        values[op] = {}
        for key, s in r['data'].items():
            ref = c['data'][key]
            if set(ref) != {'field'}:
                fail(path+'.data.'+key, 'field reference only', ref)
                continue
            name = ref['field']; refs.add(name); fs = m['fields'][name]
            expected = dict(quantity=r['variable'] if key == 'value' else key,
                            unit=s['unit'], kind=s['kind'], component_shape=shape(s, p),
                            components=labels(s, p), dtype='float64', location=r['location'],
                            time_axis=r['axis'], value_kind='point',
                            sampling=dict(space='uniform', time='linear' if r['axis'] == 'control'
                                          else 'constant', extrapolation='forbid'))
            for k, v in expected.items():
                if fs.get(k) != v:
                    fail('$.fields.'+name+'.'+k, v, fs.get(k))
            v = a[fs['array']]
            values[op][key] = v
            if s.get('positive') and np.any(v <= 0):
                fail(path+'.data.'+key, 'strictly positive', v)
            if s.get('nonnegative') and np.any(v < 0):
                fail(path+'.data.'+key, 'nonnegative', v)
    if set(counts) != set(cfg['records']):
        fail('$.conditions', 'all required records', sorted(counts))
    if refs != set(m['fields']):
        fail('$.fields', 'exactly referenced fields', sorted(set(m['fields'])-refs))
    if errors:
        return

    if 'layers' in locs:
        with np.errstate(over='ignore', invalid='ignore'):
            bounds = np.r_[0., np.cumsum(values['layers']['width'].ravel())]
        if not np.all(np.isfinite(bounds)) or np.any(np.diff(bounds) <= 0):
            fail('$.conditions.layers', 'finite strictly increasing interfaces', bounds)
        elif 'probes' in locs:
            x = a[locs['probes']['coordinates']][:, 0]
            if np.any(x <= 0) or np.any(x >= bounds[-1]) or np.any(
                    np.min(abs(x[:, None]-bounds[None, :]), axis=1) < 1e-10*bounds[-1]):
                fail('$.locations.probes', 'strict interior with 1e-10 H interface clearance', x)
    if slug == 'neutron-diffusion-critical':
        if np.any(abs(values['medium']['spectrum'].sum(axis=-1)-1) > 1e-12):
            fail('$.conditions.medium.spectrum', 'group sum 1 within 1e-12', 'invalid spectrum')
    if slug == 'point-kinetics':
        if values['precursors']['fraction'].sum() >= 1:
            fail('$.conditions.precursors.fraction', 'sum beta < 1', 'excess')
        if np.any(abs(values['history']['reactivity']) > .5):
            fail('$.conditions.history.reactivity', '|rho| <= 0.5', 'excess')
    if 'network' in slug:
        for op in ('branches', 'products'):
            if op not in values:
                continue
            matrix = values[op]['value'][0, 0]
            if np.any(np.diag(matrix) != 0) or np.any(matrix.sum(axis=0) > 1):
                fail('$.conditions.'+op, 'zero diagonal and column sums <=1', matrix)
        branch = values['branches']['value'][0, 0]
        stable = values['nuclides']['decay'].ravel() == 0
        if np.any(branch[:, stable] != 0):
            fail('$.conditions.branches', 'zero branches from stable nuclides', 'nonzero stable column')
        # Remove all zero-indegree vertices; remaining vertices imply a decay cycle.
        edges = branch > 0
        remaining = set(range(len(branch)))
        while remaining:
            roots = {j for j in remaining if not any(edges[j, k] for k in remaining)}
            if not roots:
                fail('$.conditions.branches', 'acyclic positive decay graph', 'cycle')
                break
            remaining -= roots

    present, output_size = set(), 0
    for name, fs in m['outputs'].items():
        q = fs['quantity']; s = cfg['outputs'].get(q); path = '$.outputs.'+name
        if s is None:
            fail(path+'.quantity', list(cfg['outputs']), q)
            continue
        present.add(q)
        expected = dict(unit=s['unit'], kind=s['kind'], component_shape=shape(s, p),
                        components=labels(s, p), dtype='float64', location=s['location'],
                        time_axis=cfg['output_axis'], value_kind='point')
        for k, v in expected.items():
            if fs.get(k) != v:
                fail(path+'.'+k, v, fs.get(k))
        if 'sampling' in fs:
            fail(path, 'no output sampling', fs['sampling'])
        output_size += (len(a[locs[fs['location']]['ids']]) *
                        len(a[m['time_axes'][fs['time_axis']]]) * math.prod(fs['component_shape']))
    if present != set(cfg['outputs']):
        fail('$.outputs', 'all required quantities', sorted(present))
    if max(output_size, sum(a[fs['array']].size for fs in m['fields'].values())) > 2000000:
        fail('$.fields/outputs', 'each total <=2000000 components', 'excess')
