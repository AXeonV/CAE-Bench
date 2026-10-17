"""Porous-media declaration checks. No flow, transport or reference solver."""
from collections import Counter, defaultdict
from functools import lru_cache
from importlib.resources import files
from itertools import combinations
import json

import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def labels(spec):
    return {'scalar': ['value'], 'vector': ['x', 'y'],
            'tensor': ['xx', 'xy', 'yx', 'yy']}[spec['kind']]


def check(problem, errors):
    from caeoj.validation import issue

    m, arrays = problem.manifest, problem.arrays
    model = m.get('physics', {}).get('model', '')
    slug = model.removeprefix('porous-').removesuffix('-v1')
    cfg = models().get(slug)

    def fail(path, expected, actual):
        if isinstance(actual, np.ndarray):
            actual = actual.tolist() if actual.size < 12 else str(actual.shape)
        errors.append(issue('E_POROUS', path, expected, actual,
                            'Declaration does not match this porous-media DATA contract.'))

    if cfg is None or model != f'porous-{slug}-v1':
        fail('$.physics.model', 'registered porous model', model)
        return
    from caeoj import runtime
    installed = runtime.descriptor()
    bound_task = m.get('task')
    if bound_task is None and installed.get('strict_tasks') and len(installed['tasks']) == 1:
        bound_task = next(iter(installed['tasks']))
    if bound_task is not None and bound_task != slug:
        fail('$.physics.model', 'model for installed task ' + bound_task, model)
    if m['spatial_dimension'] != 2:
        fail('$.spatial_dimension', 2, m['spatial_dimension'])
    if any(k in m for k in ('profile', 'contract_version', 'analysis', 'materials')):
        fail('$', 'physics-only declaration', 'mixed declaration')
    parameters = m['physics'].get('parameters', {})
    if set(parameters) != set(cfg['parameters']):
        fail('$.physics.parameters', list(cfg['parameters']), list(parameters))
        return
    p = {}
    for name, spec in cfg['parameters'].items():
        record = parameters[name]
        value = record.get('value')
        if (set(record) != {'value', 'unit'} or record.get('unit') != spec['unit']
                or type(value) not in (int, float)):
            fail('$.physics.parameters.' + name, spec, record)
            continue
        if abs(value) > 1e12 or spec.get('positive') and value <= 0:
            fail('$.physics.parameters.' + name, 'declared finite range', value)
        p[name] = value
    if errors:
        return
    if not cfg['steady'] and not 0 < p['end_time'] - p['start_time'] <= 1e8:
        fail('$.physics.parameters', '0 < tf-t0 <= 1e8 s', p)
    if slug == 'compressible-two-phase':
        low, high, reference = p['pressure_min'], p['pressure_max'], p['reference_pressure']
        if not 0 < low < high or not low <= reference <= high:
            fail('$.physics.parameters', '0 < pmin <= pr <= pmax and pmin<pmax', p)
        for phase in ('w', 'n'):
            if max(abs(p['compressibility_' + phase] * (end - reference))
                   for end in (low, high)) > 20:
                fail('$.physics.parameters.compressibility_' + phase, '|c(p-pr)|<=20 over pressure range', p)
    if errors:
        return

    if set(m['meshes']) != {'main'}:
        fail('$.meshes', 'one main mesh', list(m['meshes']))
        return
    mesh = problem.meshes['main']
    cells = set(mesh['elements'][2])
    if mesh['dimension'] != 2 or not cells or mesh['elements'][0] or mesh['elements'][3]:
        fail('$.meshes.main', 'triangles and line elements only', mesh['dimension'])
        return
    nodes = set()
    facets = defaultdict(list)
    for tag in cells:
        kind, connection = mesh['connectivity'][tag]
        if kind != 2:
            fail('$.meshes.main', 'first-order triangles (type 2)', kind)
            continue
        nodes.update(connection)
        for edge in combinations(connection, 2):
            facets[tuple(sorted(edge))].append(tag)
    if errors:
        return
    if nodes != mesh['nodes'] or len(nodes) > 8000 or len(cells) > 6000:
        fail('$.meshes.main', 'complete used nodes, <=8000 nodes / 6000 cells', [len(nodes), len(cells)])
    if any(len(owner) > 2 for owner in facets.values()):
        fail('$.meshes.main', 'manifold triangle edges', 'more than two owners')
    if np.any(np.abs(mesh['coordinates']) > 1e6):
        fail('$.meshes.main', '|coordinates|<=1e6 m', 'outside range')
    exterior, internal, seen = {}, {}, set()
    for tag in mesh['elements'][1]:
        kind, connection = mesh['connectivity'][tag]
        edge = tuple(sorted(connection))
        owners = facets.get(edge, [])
        if kind != 1 or not owners or edge in seen:
            fail('$.meshes.main', 'unique first-order exported triangle edges', tag)
            continue
        seen.add(edge)
        (exterior if len(owners) == 1 else internal)[tag] = edge
    if set(exterior.values()) != {edge for edge, owner in facets.items() if len(owner) == 1}:
        fail('$.meshes.main', 'every exterior edge exported once', len(exterior))
    if internal and cfg['family'] != 'fracture':
        fail('$.meshes.main', 'no exported internal edges for this model', list(internal))
    adjacency = defaultdict(set)
    for owner in facets.values():
        if len(owner) == 2:
            a, b = owner
            adjacency[a].add(b)
            adjacency[b].add(a)
    visited, stack = set(), [next(iter(cells))]
    while stack:
        tag = stack.pop()
        if tag not in visited:
            visited.add(tag)
            stack.extend(adjacency[tag] - visited)
    if visited != cells:
        fail('$.meshes.main', 'edge-connected triangle domain', 'disconnected')
    locs = m['locations']

    def ids(name):
        return set(map(int, arrays[locs[name]['ids']]))

    for name, entity, tags in [('domain', 'node', nodes), ('cells', 'element', cells)]:
        spec = locs.get(name, {})
        if (spec.get('kind') != 'mesh' or spec.get('mesh') != 'main'
                or spec.get('entity') != entity or ids(name) != tags
                or entity == 'element' and spec.get('dimension') != 2):
            fail('$.locations.' + name, 'complete ' + entity + ' support', spec)
    if errors:
        return
    boundary_nodes = {n for edge in exterior.values() for n in edge}
    if cfg['family'] == 'fracture':
        fs = locs.get('fractures', {})
        if (fs.get('kind') != 'mesh' or fs.get('mesh') != 'main'
                or fs.get('entity') != 'element' or fs.get('dimension') != 1
                or not internal or ids('fractures') != set(internal)):
            fail('$.locations.fractures', 'all nonempty internal fracture edges', fs)
        else:
            degree = Counter(n for edge in internal.values() for n in edge)
            graph = defaultdict(set)
            for a, b in internal.values():
                graph[a].add(b)
                graph[b].add(a)
            seen_nodes = set()
            for node in graph:
                if node in seen_nodes:
                    continue
                component, todo = set(), [node]
                while todo:
                    current = todo.pop()
                    if current not in component:
                        component.add(current)
                        todo.extend(graph[current] - component)
                seen_nodes |= component
                if sum(degree[n] == 1 for n in component) != 2 or any(degree[n] > 2 for n in component):
                    fail('$.locations.fractures', 'open nonbranching curves', sorted(component))
            if set(degree) & boundary_nodes:
                fail('$.locations.fractures', 'strictly interior curves', sorted(set(degree) & boundary_nodes))
    if cfg['family'] == 'pore':
        s = locs.get('mean', {})
        if s.get('kind') != 'aggregate' or s.get('source') != 'cells' or s.get('operation') != 'mean':
            fail('$.locations.mean', 'aggregate mean over cells', s)
    for name, s in locs.items():
        if s['kind'] == 'aggregate':
            if cfg['family'] != 'pore' or name != 'mean':
                fail('$.locations.' + name, 'only the pore mean aggregate', s)
        elif s['kind'] != 'mesh' or s.get('mesh') != 'main':
            fail('$.locations.' + name, 'mesh support on main', s)
        elif s['entity'] == 'element':
            if not (s['dimension'] == 2 and ids(name) <= cells
                    or s['dimension'] == 1 and ids(name) <= set(exterior)
                    or cfg['family'] == 'fracture' and name == 'fractures' and ids(name) == set(internal)):
                fail('$.locations.' + name, 'declared cell / exterior / fracture support', s)
    if errors:
        return

    static_axis = 'steady' if cfg['steady'] else 'initial'
    output_axis = 'steady' if cfg['steady'] else 'response'
    required_axes = {static_axis, output_axis}
    if not required_axes <= set(m['time_axes']):
        fail('$.time_axes', sorted(required_axes), list(m['time_axes']))
        return
    t0 = 0. if cfg['steady'] else p['start_time']
    tf = 0. if cfg['steady'] else p['end_time']
    if not np.array_equal(arrays[m['time_axes'][static_axis]], [t0]):
        fail('$.time_axes.' + static_axis, [t0], arrays[m['time_axes'][static_axis]])
    response = arrays[m['time_axes'][output_axis]]
    if response[0] < t0 or response[-1] > tf:
        fail('$.time_axes.' + output_axis, 'request times within [t0,tf]', response)
    for name, key in m['time_axes'].items():
        if len(arrays[key]) > 101:
            fail('$.time_axes.' + name, '<=101 frames', len(arrays[key]))
    if errors:
        return
    refs, used_axes, counts = set(), set(required_axes), Counter()
    boundary_used = defaultdict(set)
    node_used = defaultdict(set)
    records = {}

    def support(location, where):
        s = locs[location]
        if where in ('cells', 'domain', 'fractures'):
            return location == where
        if where == 'nodes':
            return s.get('entity') == 'node' and ids(location) <= boundary_nodes
        return s.get('entity') == 'element' and s.get('dimension') == 1 and ids(location) <= set(exterior)

    def typed(value, spec, location, static, quantity, path):
        if 'option' in spec:
            if value != {'option': spec['option']}:
                fail(path, {'option': spec['option']}, value)
            return value
        if set(value) == {'value', 'unit'}:
            if (spec['kind'] != 'scalar' or value['unit'] != spec['unit']
                    or type(value['value']) not in (int, float)):
                fail(path, 'typed scalar constant with declared unit', value)
                return None
            data = np.full((1, len(ids(location)), 1), value['value'])
        elif set(value) == {'field'}:
            name = value['field']
            refs.add(name)
            fs = m['fields'][name]
            element = locs[location].get('entity') == 'element'
            expected = dict(quantity=quantity, unit=spec['unit'], kind=spec['kind'],
                            component_shape=spec['shape'], components=labels(spec),
                            dtype='float64', location=location,
                            value_kind='average' if element else 'point')
            for key, wanted in expected.items():
                if fs.get(key) != wanted:
                    fail('$.fields.' + name + '.' + key, wanted, fs.get(key))
            axis = fs['time_axis']
            used_axes.add(axis)
            times = arrays[m['time_axes'][axis]]
            if ((static or len(times) == 1) and axis != static_axis
                    or len(times) > 1 and (times[0] != t0 or times[-1] != tf)):
                fail('$.fields.' + name + '.time_axis', 'static initial axis or full load interval', axis)
            sampling = dict(space='piecewise_constant' if element else 'piecewise_linear',
                            time='constant' if len(times) == 1 else 'linear', extrapolation='forbid')
            if fs.get('sampling') != sampling:
                fail('$.fields.' + name + '.sampling', sampling, fs.get('sampling'))
            data = arrays[fs['array']]
        else:
            fail(path, 'field or typed constant', value)
            return None
        if data.shape[2:] != tuple(spec['shape']):
            return None
        if np.any(np.abs(data) > 1e12):
            fail(path, '|value|<=1e12', 'outside range')
        if spec.get('positive') and np.any(data <= 0):
            fail(path, 'strictly positive', 'nonpositive')
        if 'lower' in spec and np.any(data < spec['lower']):
            fail(path, '>= ' + str(spec['lower']), 'below range')
        if 'upper' in spec and np.any(data > spec['upper']):
            fail(path, '<= ' + str(spec['upper']), 'above range')
        if spec.get('spd'):
            if not np.array_equal(data, data.swapaxes(-1, -2)):
                fail(path, 'symmetric tensor', 'asymmetric')
            else:
                eigenvalues = np.linalg.eigvalsh(data)
                if np.any(eigenvalues <= 0):
                    fail(path, 'positive definite tensor', 'nonpositive eigenvalue')
                if quantity in ('permeability', 'matrix_permeability', 'fracture_permeability'):
                    low, high = 1e-16, 1e-6
                else:
                    low, high = 1e-12, 1e-2
                if np.any(eigenvalues < low) or np.any(eigenvalues > high) or np.any(eigenvalues[..., -1] > 1e6 * eigenvalues[..., 0]):
                    fail(path, 'declared eigenvalue bounds and condition number', 'outside tensor range')
        return data

    for i, c in enumerate(m['conditions']):
        path = f'$.conditions[{i}]'
        op, location = c['operator'], c['location']
        rule = cfg['records'].get(op)
        if rule is None:
            fail(path + '.operator', list(cfg['records']), op)
            continue
        counts[op] += 1
        if (c['role'] != rule['role'] or c['variable'] != rule['variable']
                or not support(location, rule['where'])):
            fail(path, 'declared role, variable and support', c)
            continue
        if rule['where'] in ('domain', 'cells', 'fractures') and counts[op] != 1:
            fail(path, 'exactly one complete record', counts[op])
        if set(c['data']) != set(rule['data']):
            fail(path + '.data', list(rule['data']), list(c['data']))
            continue
        values = {key: typed(c['data'][key], spec, location, rule['static'] or cfg['steady'],
                             c['variable'] if key == 'value' else key, path + '.data.' + key)
                  for key, spec in rule['data'].items()}
        if all(v is not None for v in values.values()):
            records.setdefault(op, []).append((location, values))
        if rule['role'] == 'boundary':
            if rule['where'] == 'nodes':
                tags = ids(location)
                faces = {tag for tag, edge in exterior.items() if set(edge) <= tags}
                if {node for face in faces for node in exterior[face]} != tags:
                    fail(path + '.location', 'complete exterior edge closure', location)
                if node_used[c['variable']] & tags:
                    fail(path + '.location', 'node records do not overlap for the same variable', location)
                node_used[c['variable']].update(tags)
            else:
                faces = ids(location)
            group = (c['variable'].split('_')[0] if cfg['family'] == 'dual' else 'boundary')
            if boundary_used[group] & faces:
                fail(path + '.location', 'no overlapping boundary edges for one variable', location)
            boundary_used[group].update(faces)
    for op, rule in cfg['records'].items():
        if rule['required'] and counts[op] == 0:
            fail('$.conditions', 'required ' + op, 'missing')
    if refs != set(m['fields']):
        fail('$.fields', 'exactly referenced fields', sorted(set(m['fields']) - refs))
    if used_axes != set(m['time_axes']):
        fail('$.time_axes', 'no unused axes', list(m['time_axes']))
    if errors:
        return
    material = records.get('material', [(None, {})])[0][1]
    if cfg['family'] == 'richards' and np.any(material['residual_water'] >= material['porosity']):
        fail('$.conditions.material', 'theta_r < porosity', 'invalid retention range')
    if cfg['family'] == 'two_phase' and np.any(material['residual_w'] + material['residual_n'] > .8):
        fail('$.conditions.material', 'Swr+Snr<=0.8', 'invalid residual sum')
    if cfg['family'] == 'transport' and np.any(material['longitudinal_dispersivity'] < material['transverse_dispersivity']):
        fail('$.conditions.material', 'aL>=aT', 'invalid dispersivity ordering')
    if cfg['family'] == 'pore':
        if boundary_used['boundary'] != set(exterior):
            fail('$.conditions', 'complete pore boundary coverage', 'uncovered boundary')
        if counts['traction'] and p['pressure_mean'] != 0:
            fail('$.physics.parameters.pressure_mean', '0 when traction is present', p['pressure_mean'])
    if set(s['quantity'] for s in m['outputs'].values()) != set(cfg['outputs']) or len(m['outputs']) != len(cfg['outputs']):
        fail('$.outputs', list(cfg['outputs']), [s['quantity'] for s in m['outputs'].values()])
    for name, s in m['outputs'].items():
        expected = cfg['outputs'].get(s['quantity'])
        if expected is None:
            continue
        for key, wanted in dict(location=expected['where'], time_axis=output_axis, dtype='float64',
                                unit=expected['unit'], kind=expected['kind'],
                                component_shape=expected['shape'], components=labels(expected),
                                value_kind='average').items():
            if s.get(key) != wanted:
                fail('$.outputs.' + name + '.' + key, wanted, s.get(key))
    for table in ('fields', 'outputs'):
        size = sum(len(arrays[m['time_axes'][s['time_axis']]]) * len(ids(s['location']))
                   * int(np.prod(s['component_shape'])) for s in m[table].values())
        if size > 5_000_000:
            fail('$.' + table, '<=5e6 declared floating values', size)
