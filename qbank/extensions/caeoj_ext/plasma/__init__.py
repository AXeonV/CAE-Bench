"""Plasma declarations only: shapes, identities, sampling and stated constraints.

No field solve, trajectory integration, chemistry or numerical reference lives here.
"""
from functools import lru_cache
from importlib.resources import files
import json
import math

import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def component_shape(spec, parameters):
    sizes = {'S': parameters.get('state_count'), 'Nv': parameters.get('velocity_count')}
    return [sizes[x] if isinstance(x, str) else x for x in spec['shape']]


def component_labels(spec, parameters, dimension):
    shape = component_shape(spec, parameters)
    if 'labels' in spec:
        return spec['labels']
    if spec['kind'] == 'scalar':
        return ['value']
    axes = ['x', 'y', 'z'][:dimension]
    if spec['kind'] == 'vector':
        return axes
    if spec['kind'] == 'tensor':
        return [a + b for a in axes for b in axes]
    if spec['shape'] == ['S', 'S']:
        return [f'from_{i}_to_{j}' for i in range(shape[0]) for j in range(shape[1])]
    if spec['shape'] == ['Nv']:
        return [f'v{i}' for i in range(shape[0])]
    return [f'c{i+1}' for i in range(math.prod(shape))]


def check(problem, errors):
    from caeoj.validation import issue

    m, arrays = problem.manifest, problem.arrays
    name = m.get('physics', {}).get('model', '')
    slug = name.removeprefix('plasma-').removesuffix('-v1')
    cfg = models().get(slug)

    def fail(path, expected, actual):
        if isinstance(actual, np.ndarray):
            actual = actual.tolist() if actual.size < 16 else {'shape': list(actual.shape)}
        errors.append(issue('E_PLASMA', path, expected, actual,
                            'Declaration violates the plasma DATA contract.'))

    def expect(actual, expected, path):
        if actual != expected:
            fail(path, expected, actual)

    if cfg is None or name != f'plasma-{slug}-v1':
        fail('$.physics.model', 'registered plasma declaration', name)
        return
    expect(m['spatial_dimension'], cfg['spatial_dimension'], '$.spatial_dimension')
    if 'task' in m:
        expect(m['task'], slug, '$.task')
    if any(k in m for k in ('profile', 'contract_version', 'analysis', 'materials')):
        fail('$', 'physics-only declaration', 'mixed profile')
    given = m['physics'].get('parameters', {})
    if set(given) != set(cfg['parameters']):
        fail('$.physics.parameters', list(cfg['parameters']), list(given))
        return
    p = {}
    for key, spec in cfg['parameters'].items():
        item = given[key]
        x = item.get('value')
        numeric = type(x) is int if spec.get('integer') else type(x) in (int, float)
        if set(item) != {'value', 'unit'} or item.get('unit') != spec['unit'] or not numeric:
            fail('$.physics.parameters.' + key, spec, item)
            continue
        if ('lower' in spec and x < spec['lower']) or ('upper' in spec and x > spec['upper']):
            fail('$.physics.parameters.' + key, spec, item)
        if spec.get('lower') == 0 and x == 0:
            fail('$.physics.parameters.' + key, 'strictly positive', x)
        if key in ('charge', 'velocity_min') and x >= 0:
            fail('$.physics.parameters.' + key, 'strictly negative', x)
        p[key] = x
    if errors:
        return

    expected_axes = {'initial', 'output'} | ({'drive'} if cfg['driven'] else set())
    if set(m['time_axes']) != expected_axes:
        fail('$.time_axes', sorted(expected_axes), list(m['time_axes']))
        return
    axes = {key: arrays[value] for key, value in m['time_axes'].items()}
    if not np.array_equal(axes['initial'], [0.]):
        fail('$.time_axes.initial', '[0.0]', axes['initial'])
    if cfg.get('steady'):
        if not np.array_equal(axes['output'], [0.]):
            fail('$.time_axes.output', '[0.0] storage marker', axes['output'])
    else:
        for key, maximum in [('output', 65)] + ([('drive', 129)] if cfg['driven'] else []):
            t = axes[key]
            if not (2 <= len(t) <= maximum and t[0] == 0 and t[-1] == p['end_time']):
                fail('$.time_axes.' + key, f'2..{maximum} frames from 0 to end_time', t)

    locs = m['locations']
    if set(locs) != set(cfg['locations']):
        fail('$.locations', list(cfg['locations']), list(locs))
        return
    for key, spec in cfg['locations'].items():
        loc = locs[key]
        expect(loc['kind'], spec['kind'], '$.locations.' + key + '.kind')
        count = len(arrays[loc['ids']])
        if not spec.get('minimum', 1) <= count <= spec['maximum']:
            fail('$.locations.' + key, 'declared count range', count)
        if spec['kind'] == 'mesh':
            expect(loc.get('mesh'), 'main', '$.locations.' + key + '.mesh')
            expect(loc.get('entity'), spec['entity'], '$.locations.' + key + '.entity')
            if spec['entity'] == 'element':
                expect(loc.get('dimension'), 1, '$.locations.' + key + '.dimension')
    if errors:
        return
    mesh_info = None
    if m['geometries']:
        fail('$.geometries', 'empty', list(m['geometries']))
    if cfg['mesh']:
        if set(m['meshes']) != {'main'}:
            fail('$.meshes', 'one main interval mesh', list(m['meshes']))
            return
        mesh_info = _interval(problem, locs, fail)
    elif m['meshes']:
        fail('$.meshes', 'empty', list(m['meshes']))
    if slug == 'collisional-states' and not np.array_equal(arrays[locs['states']['ids']], np.arange(p['state_count'])):
        fail('$.locations.states.ids', '0..S-1', arrays[locs['states']['ids']])
    if errors:
        return

    referenced, seen, values = set(), set(), {}

    def typed(item, spec, location, quantity, path):
        if set(item) == {'value', 'unit'}:
            if spec['kind'] != 'scalar' or item['unit'] != spec['unit'] or type(item['value']) not in (int, float):
                fail(path, 'typed scalar of declared unit', item)
                return None
            a = np.full((1, len(arrays[locs[location]['ids']]), 1), item['value'])
        elif set(item) == {'field'}:
            key = item['field']
            referenced.add(key)
            field = m['fields'][key]
            cell = location == 'cells'
            expected = dict(quantity=quantity, unit=spec['unit'], kind=spec['kind'],
                            component_shape=component_shape(spec, p),
                            components=component_labels(spec, p, cfg['spatial_dimension']),
                            location=location, time_axis=spec['axis'], dtype='float64',
                            value_kind='average' if cell else 'point',
                            sampling=dict(space='piecewise_constant' if cell else 'piecewise_linear' if location == 'domain' else 'uniform',
                                          time='linear' if spec['axis'] == 'drive' else 'constant', extrapolation='forbid'))
            for k, v in expected.items():
                expect(field.get(k), v, '$.fields.' + key + '.' + k)
            a = arrays[field['array']]
        else:
            fail(path, 'field reference or scalar constant', item)
            return None
        if spec.get('positive') and np.any(a <= 0):
            fail(path, 'strictly positive', a)
        if 'lower' in spec and np.any(a < spec['lower']):
            fail(path, f">={spec['lower']}", a)
        return a

    for i, condition in enumerate(m['conditions']):
        path = f'$.conditions[{i}]'
        op = condition['operator']
        spec = cfg['records'].get(op)
        if spec is None or op in seen:
            fail(path + '.operator', 'one of each required operator', op)
            continue
        seen.add(op)
        for key in ('role', 'variable', 'location'):
            expect(condition[key], spec[key], path + '.' + key)
        if condition['location'] != spec['location']:
            continue
        if set(condition['data']) != set(spec['data']):
            fail(path + '.data', list(spec['data']), list(condition['data']))
            continue
        values[op] = {key: typed(condition['data'][key], fs, spec['location'],
                                 spec['variable'] if key == 'value' else key, path + '.data.' + key)
                      for key, fs in spec['data'].items()}
    if seen != set(cfg['records']):
        fail('$.conditions', list(cfg['records']), sorted(seen))
    if referenced != set(m['fields']):
        fail('$.fields', 'exactly referenced fields', sorted(set(m['fields']) - referenced))
    if errors:
        return

    present, size = set(), 0
    for key, field in m['outputs'].items():
        quantity = field['quantity']
        spec = cfg['outputs'].get(quantity)
        path = '$.outputs.' + key
        if spec is None:
            fail(path + '.quantity', list(cfg['outputs']), quantity)
            continue
        present.add(quantity)
        expected = dict(unit=spec['unit'], kind=spec['kind'], component_shape=component_shape(spec, p),
                        components=component_labels(spec, p, cfg['spatial_dimension']), location=spec['location'],
                        time_axis='output', dtype='float64', value_kind='average' if spec['location'] == 'cells' else 'point')
        for k, v in expected.items():
            expect(field.get(k), v, path + '.' + k)
        if 'sampling' in field:
            fail(path + '.sampling', 'absent on outputs', field['sampling'])
        size += len(axes[field['time_axis']]) * len(arrays[locs[field['location']]['ids']]) * math.prod(field['component_shape'])
    if present != set(cfg['outputs']):
        fail('$.outputs', list(cfg['outputs']), sorted(present))
    input_size = sum(arrays[s['array']].size for s in m['fields'].values())
    if max(size, input_size) > 4_000_000:
        fail('$.fields/outputs', 'at most 4000000 components each', [input_size, size])
    if errors:
        return
    with np.errstate(over='ignore', invalid='ignore', divide='ignore', under='ignore'):
        _constraints(slug, p, values, problem, mesh_info, fail)


def _interval(problem, locs, fail):
    mesh = problem.meshes['main']
    cells = mesh['elements'][1]
    if mesh['dimension'] != 1 or not cells or any(mesh['elements'][d] for d in (0, 2, 3)):
        fail('$.meshes.main', 'first order interval lines only', mesh['dimension'])
        return None
    if np.any(mesh['coordinates'][:, 1:] != 0):
        fail('$.meshes.main', 'global x axis, y=z=0', 'off-axis coordinates')
    intervals, used = [], set()
    for tag in cells:
        typ, conn = mesh['connectivity'][tag]
        if typ != 1:
            fail('$.meshes.main', 'Gmsh line type 1', typ)
            return None
        a, b = sorted(conn, key=lambda n: mesh['node_coordinates'][n][0])
        xa, xb = mesh['node_coordinates'][a][0], mesh['node_coordinates'][b][0]
        if not xa < xb:
            fail('$.meshes.main', 'positive line length', tag)
        used.update(conn)
        intervals.append((xa, xb, a, b, tag))
    intervals.sort()
    if len(intervals) < 2 or any(a[3] != b[2] for a, b in zip(intervals, intervals[1:])) or used != mesh['nodes']:
        fail('$.meshes.main', 'connected nonoverlapping chain with no unused nodes', 'invalid interval topology')
    for key, expected in [('domain', mesh['nodes']), ('cells', set(cells))]:
        if set(map(int, problem.arrays[locs[key]['ids']])) != expected:
            fail('$.locations.' + key, 'complete mesh support', 'subset')
    for key, node in [('left', intervals[0][2]), ('right', intervals[-1][3])]:
        if key in locs and not np.array_equal(problem.arrays[locs[key]['ids']], [node]):
            fail('$.locations.' + key, 'unique geometric endpoint', problem.arrays[locs[key]['ids']])
    return intervals


def _constraints(slug, p, values, problem, intervals, fail):
    def require(condition, path, expected, actual='invalid values'):
        if not condition:
            fail(path, expected, actual)

    for op in ('particles', 'species'):
        if op in values and 'charge' in values[op]:
            require(np.all(values[op]['charge'] != 0), '$.conditions.' + op, 'nonzero particle charges')
    if slug in ('charged-orbits', 'relativistic-orbits'):
        g = values['electric']['gradient']
        require(np.array_equal(g, np.swapaxes(g, -1, -2)), '$.conditions.electric.gradient', 'symmetric matrices')
        a = np.max(abs(values['particles']['charge']) / values['particles']['mass'])
        magnetic = np.linalg.norm(values['magnetic']['value'])
        gradient = np.max(np.linalg.norm(g, axis=(-2, -1)))
        require(p['end_time'] * a * magnetic <= 200 and p['end_time'] * np.sqrt(a * gradient) <= 100,
                '$.conditions', 'orbit frequency and gradient scales within DATA limits')
        if slug == 'relativistic-orbits':
            electric = values['electric']
            offset = electric['offset'] - np.einsum('tnij,tnj->tni', g, electric['origin'])
            require(p['end_time'] * a * np.max(np.linalg.norm(offset, axis=-1)) / 299792458 <= 100,
                    '$.conditions.electric', 'relativistic acceleration scale <= 100')
    if slug == 'collisional-states':
        k = values['transitions']['value']
        require(np.all(k >= 0) and np.all(np.diagonal(k, axis1=-2, axis2=-1) == 0),
                '$.conditions.transitions', 'nonnegative rates and zero diagonal')
        require(np.any(values['population']['value'] > 0), '$.conditions.population', 'positive total population')
        require(p['end_time'] * np.max(np.sum(k, axis=-1)) <= 10000,
                '$.conditions.transitions', 'dimensionless exit-rate scale <= 10000')
    if slug == 'plasma-chemistry':
        require(np.any(values['initial']['value'] > 0), '$.conditions.initial', 'nonzero charged population')
        r = values['rates']
        require(p['end_time'] * p['neutral_density'] * np.max(r['ionization'] + r['attachment']) <= 100 and
                p['end_time'] * .01 * p['neutral_density'] * np.max(r['recombination'] + r['neutralization']) <= 10000,
                '$.conditions.rates', 'reaction scales within DATA limits')
    if slug == 'vlasov-poisson':
        f = values['initial']['value'][0]
        loc = problem.manifest['locations']['cells']
        lengths = {entry[4]: entry[1] - entry[0] for entry in intervals}
        weights = np.array([lengths[int(tag)] for tag in problem.arrays[loc['ids']]])
        dv = (p['velocity_max'] - p['velocity_min']) / p['velocity_count']
        density = float(np.sum(np.sum(f, axis=-1) * weights) * dv / sum(weights))
        require(density > 0, '$.conditions.initial', 'strictly positive initial particle inventory', density)
        frequency = np.sqrt(p['charge'] * p['charge'] * density / p['mass'] / p['permittivity'])
        require(p['end_time'] * frequency <= 200 and
                p['end_time'] * max(abs(p['velocity_min']), p['velocity_max']) / sum(weights) <= 1000,
                '$.physics.parameters', 'plasma and transit scales within DATA limits')
    if slug == 'space-charge-beam':
        vl, vr = values['left_potential']['value'].item(), values['right_potential']['value'].item()
        delta = vr - vl
        e = -p['charge']
        vin = math.sqrt(2 * p['injection_energy'] / p['mass'])
        length = intervals[-1][1] - intervals[0][0]
        require(0 < e * delta <= p['injection_energy'], '$.conditions.right_potential', '0 < -q(VR-VL) <= W0')
        if delta > 0:
            ratio = e * p['particle_flux'] * length * length / (p['permittivity'] * vin * delta)
            require(ratio <= .25, '$.physics.parameters.particle_flux', 'moderate space-charge ratio <= 0.25', ratio)
    if slug in ('isothermal-discharge', 'energy-discharge'):
        ids = problem.arrays[problem.manifest['locations']['domain']['ids']]
        for op, node in [('left_reservoir', intervals[0][2]), ('right_reservoir', intervals[-1][3])]:
            index = int(np.searchsorted(ids, node))
            for key, arr in values['initial'].items():
                require(arr[0, index, 0] == values[op][key][0, 0, 0], '$.conditions.' + op + '.' + key,
                        'boundary and physical initial state agree at t=0')
        hmin = min(entry[1] - entry[0] for entry in intervals)
        transport = values['transport']
        diffusion = max(np.max(v) for key, v in transport.items() if key.endswith('_diffusion'))
        mobility = max(np.max(v) for key, v in transport.items() if key.endswith('_mobility'))
        require(p['end_time'] * diffusion / hmin / hmin <= 100000 and
                p['end_time'] * mobility * p['elementary_charge'] * .01 * p['neutral_density'] / p['permittivity'] <= 10000,
                '$.conditions.transport', 'diffusion and charge-relaxation scales within DATA limits')
    if slug == 'cold-plasma-relaxation':
        species = values['species']
        mass, charge = species['mass'], species['charge']
        scale = species['collision_frequency'] + abs(charge) * np.linalg.norm(values['magnetic']['value']) / mass
        scale += np.sqrt(species['density'] * charge * charge / mass / p['permittivity'])
        require(np.all(p['end_time'] * scale <= 200), '$.conditions.species', 'cold-plasma scales <= 200')
    if slug == 'magnetized-plasma-slab':
        edges = np.r_[0., np.cumsum(values['layers']['thickness'].reshape(-1))]
        x = problem.arrays[problem.manifest['locations']['receivers']['coordinates']][:, 0]
        require(np.all((x > 0) & (x < edges[-1])) and not np.any(x[:, None] == edges[None, :]),
                '$.locations.receivers', 'strictly inside individual layers')
        require(np.any(values['incident']['value'] != 0), '$.conditions.incident', 'nonzero incident amplitude')
        omega = p['angular_frequency']
        layers = values['layers']
        nu = layers['collision_frequency'] / omega
        plasma = np.sqrt(layers['density'] * p['charge'] * p['charge'] / p['mass'] / p['permittivity']) / omega
        cyclotron = abs(p['charge'] * values['magnetic']['value'] / p['mass'] / omega)
        incident = np.linalg.norm(values['incident']['value'])
        optical = omega * math.sqrt(p['permittivity'] * p['permeability']) * edges[-1]
        require(1e-14 <= p['permittivity'] <= 1e-8 and 1e-8 <= p['permeability'] <= 1e-4,
                '$.physics.parameters', 'permittivity/permeability within DATA intervals')
        require(np.all((nu >= .001) & (nu <= 100)) and np.all(plasma <= 30) and np.all(cyclotron <= 30)
                and optical <= 100 and 1e-6 <= incident <= 1e6,
                '$.conditions', 'slab frequency, thickness and amplitude scales within DATA limits')
