"""Declaration checks for system networks; no trajectory or reference solvers."""
from functools import lru_cache
from importlib.resources import files
import json
import math
import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def incidence(ids, endpoints):
    """Return tail-positive incidence in declared ID order, allowing parallel edges.

    IDs and endpoints must be int64 arrays. No implied ground node or ID=position.
    """
    ids, endpoints = np.asarray(ids), np.asarray(endpoints)
    if any(x.dtype.kind != 'i' or x.dtype.itemsize != 8 for x in (ids, endpoints)):
        raise ValueError('Node IDs and endpoint references must be int64')
    if ids.ndim != 1 or endpoints.ndim != 2 or endpoints.shape[1] != 2:
        raise ValueError('Expected IDs[N] and endpoints[E,2]')
    rows = {int(tag): i for i, tag in enumerate(ids)}
    if len(rows) != len(ids):
        raise ValueError('Node IDs must be unique')
    b = np.zeros((len(ids), len(endpoints)))
    for e, (tail, head) in enumerate(endpoints):
        if int(tail) not in rows or int(head) not in rows:
            raise ValueError('Endpoints must reference actual node IDs')
        if tail == head:
            raise ValueError('Self loops are outside this contract')
        b[rows[int(tail)], e], b[rows[int(head)], e] = 1., -1.
    return b


def check(problem, errors):
    from caeoj.validation import issue
    m, a = problem.manifest, problem.arrays
    model = m.get('physics', {}).get('model', '')
    slug = model.removeprefix('systems-').removesuffix('-v1')
    cfg = models().get(slug)

    def fail(path, expected, actual):
        if isinstance(actual, np.ndarray):
            actual = actual.tolist() if actual.size < 16 else list(actual.shape)
        errors.append(issue('E_SYSTEMS', path, expected, actual,
                            'Declaration violates this system-network DATA contract.'))

    if cfg is None or model != 'systems-'+slug+'-v1':
        fail('$.physics.model', 'registered system-network model', model)
        return
    if m['spatial_dimension'] != 1:
        fail('$.spatial_dimension', 1, m['spatial_dimension'])
    if 'task' in m and m['task'] != slug:
        fail('$.task', slug, m['task'])
    if any(k in m for k in ('profile', 'contract_version', 'analysis', 'materials')):
        fail('$', 'physics-only declaration', 'mixed profile')
    if m['meshes'] or m['geometries']:
        fail('$.meshes/geometries', 'empty objects; system identity is entities', 'geometry supplied')
    if set(m['physics']) != {'model', 'parameters'}:
        fail('$.physics', ['model', 'parameters'], list(m['physics']))
    parameters = m['physics'].get('parameters', {})
    if set(parameters) != set(cfg['parameters']):
        fail('$.physics.parameters', list(cfg['parameters']), list(parameters))
        return
    for key, spec in cfg['parameters'].items():
        v = parameters[key]
        x = v.get('value')
        try:
            valid = type(x) in (int, float) and math.isfinite(x) and x > 0
        except OverflowError:
            valid = False
        if set(v) != {'value', 'unit'} or v.get('unit') != spec['unit'] or not valid:
            fail('$.physics.parameters.'+key, 'positive finite scalar '+spec['unit'], v)
    locs = m['locations']
    expected_locations = {'nodes', 'edges'} if cfg['network'] else {'systems'}
    if set(locs) != expected_locations:
        fail('$.locations', sorted(expected_locations), list(locs))
        return
    for name, loc in locs.items():
        n = len(a[loc['ids']])
        lower, upper = (2, 128) if name == 'nodes' else (1, 256) if name == 'edges' else (1, 32)
        if loc['kind'] != 'entities' or not lower <= n <= upper:
            fail('$.locations.'+name, f'entities {lower}..{upper}', loc)
    axes = {'static', 'load', 'response'} | ({'control'} if cfg.get('control') else set())
    if set(m['time_axes']) != axes:
        fail('$.time_axes', sorted(axes), list(m['time_axes']))
        return
    time = {k: a[v] for k, v in m['time_axes'].items()}
    if not np.array_equal(time['static'], [0.]):
        fail('$.time_axes.static', '[0.0]', time['static'])
    if not 2 <= len(time['load']) <= 256 or time['load'][0] != 0:
        fail('$.time_axes.load', '2..256 strictly increasing, from 0', time['load'])
    if len(time['response']) > 256 or time['response'][0] < 0 or time['response'][-1] > time['load'][-1]:
        fail('$.time_axes.response', '1..256 in [0,t_end]', time['response'])
    if cfg.get('control'):
        t = time['control']
        if not 2 <= len(t) <= 256 or t[0] != 0 or t[-1] != time['load'][-1]:
            fail('$.time_axes.control', '2..256, from 0 to exact load endpoint', t)
    if errors:
        return
    used, seen, values = set(), set(), {}
    for i, condition in enumerate(m['conditions']):
        path = f'$.conditions[{i}]'
        op = condition['operator']
        spec = cfg['records'].get(op)
        if spec is None or op in seen:
            fail(path+'.operator', 'one record per declared operator', op)
            continue
        seen.add(op)
        required = dict(role=spec['role'], location=spec['location'], variable='system_data')
        for k, v in required.items():
            if condition[k] != v:
                fail(path+'.'+k, v, condition[k])
        if set(condition) != {'role', 'variable', 'operator', 'location', 'data'}:
            fail(path, 'five declared condition keys', list(condition))
        if set(condition['data']) != set(spec['data']):
            fail(path+'.data', list(spec['data']), list(condition['data']))
            continue
        for key, fs in spec['data'].items():
            ref = condition['data'][key]
            if set(ref) != {'field'}:
                fail(path+'.data.'+key, 'explicit field reference', ref)
                continue
            name = ref['field']
            used.add(name)
            s = m['fields'][name]
            expected = dict(quantity=key, unit=fs['unit'], dtype=fs['dtype'],
                            kind='scalar' if fs['shape'] == [1] else 'components',
                            component_shape=fs['shape'], components=fs['labels'],
                            location=spec['location'], time_axis=spec['axis'], value_kind='point',
                            sampling=dict(space='uniform', time={'static':'constant', 'load':'linear', 'control':'previous'}[spec['axis']], extrapolation='forbid'))
            for k, v in expected.items():
                if s.get(k) != v:
                    fail('$.fields.'+name+'.'+k, v, s.get(k))
            data = a[s['array']]
            if fs['positive'] and np.any(data <= 0) or fs['nonnegative'] and np.any(data < 0):
                fail(path+'.data.'+key, 'positive' if fs['positive'] else 'nonnegative', data)
            values[op, key] = data
    if seen != set(cfg['records']):
        fail('$.conditions', list(cfg['records']), sorted(seen))
    if used != set(m['fields']):
        fail('$.fields', 'exactly referenced fields', sorted(set(m['fields'])-used))
    if errors:
        return
    if cfg['network']:
        endpoints = values['edge_properties', 'endpoints'][0]
        ids = a[locs['nodes']['ids']]
        try:
            incidence(ids, endpoints)
        except ValueError as exc:
            fail('$.conditions.edge_properties.endpoints', 'actual distinct node IDs', str(exc))
            return
        neighbours = {int(tag): set() for tag in ids}
        for tail, head in endpoints:
            neighbours[int(tail)].add(int(head))
            neighbours[int(head)].add(int(tail))
        visited, pending = set(), [int(ids[0])]
        while pending:
            node = pending.pop()
            if node in visited:
                continue
            visited.add(node)
            pending.extend(neighbours[node]-visited)
        if visited != set(neighbours):
            fail('$.conditions.edge_properties.endpoints', 'connected undirected graph', sorted(visited))
    if slug in ('geared-torsional-network', 'deadzone-transmission-network'):
        ratio = values['edge_properties', 'ratio']
        if np.any(abs(ratio) < .1) or np.any(abs(ratio) > 10):
            fail('$.conditions.edge_properties.ratio', '0.1 <= abs(n) <= 10', ratio)
    if slug == 'distributed-pipe-network' and np.any(values['driving', 'injection'][0] != 0):
        fail('$.conditions.driving.injection', 'zero injection at t=0', values['driving', 'injection'][0])
    present, count = set(), 0
    for name, s in m['outputs'].items():
        q = s['quantity']
        os = cfg['outputs'].get(q)
        if os is None:
            fail('$.outputs.'+name+'.quantity', list(cfg['outputs']), q)
            continue
        present.add(q)
        expected = dict(dtype='float64', kind='scalar' if os['shape'] == [1] else 'components',
                        component_shape=os['shape'], components=os['labels'], unit=os['unit'],
                        location=os['location'], time_axis='response', value_kind='point')
        for k, v in expected.items():
            if s.get(k) != v:
                fail('$.outputs.'+name+'.'+k, v, s.get(k))
        if 'sampling' in s:
            fail('$.outputs.'+name, 'no sampling', s['sampling'])
        count += len(time['response'])*len(a[locs[s['location']]['ids']])*math.prod(s['component_shape'])
    if present != set(cfg['outputs']):
        fail('$.outputs', 'all required quantities', sorted(present))
    if max(count, sum(a[s['array']].size for s in m['fields'].values())) > 2000000:
        fail('$.fields/outputs', '<=2000000 numeric components in each', 'excess')
