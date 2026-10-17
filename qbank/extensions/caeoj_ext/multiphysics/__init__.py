"""Public coupled-continuum declaration checks, without numerical solvers."""
from functools import lru_cache
from importlib.resources import files
import json
import math
import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def check(problem, errors):
    from caeoj.validation import issue
    m, a = problem.manifest, problem.arrays
    model = m.get('physics', {}).get('model', '')
    slug = model.removeprefix('multiphysics-').removesuffix('-v1')
    cfg = models().get(slug)

    def fail(path, expected, actual):
        if isinstance(actual, np.ndarray):
            actual = actual.tolist() if actual.size < 12 else list(actual.shape)
        errors.append(issue('E_MULTIPHYSICS', path, expected, actual,
                            'Declaration violates this coupled-continuum DATA contract.'))

    if cfg is None or model != 'multiphysics-' + slug + '-v1':
        fail('$.physics.model', 'registered coupled-continuum model', model)
        return
    if set(m['physics']) != {'model', 'parameters'}:
        fail('$.physics', ['model', 'parameters'], list(m['physics']))
    if m['spatial_dimension'] != 1:
        fail('$.spatial_dimension', 1, m['spatial_dimension'])
    if 'task' in m and m['task'] != slug:
        fail('$.task', slug, m['task'])
    if any(k in m for k in ('profile', 'contract_version', 'analysis', 'materials')):
        fail('$', 'physics-only declaration', 'mixed profile')
    if m['geometries'] or m['meshes']:
        fail('$.geometries/meshes', 'empty objects; interval defined by length', 'geometry supplied')
    params = m['physics'].get('parameters', {})
    if set(params) != set(cfg['parameters']):
        fail('$.physics.parameters', list(cfg['parameters']), list(params))
        return
    p = {}
    for key, spec in cfg['parameters'].items():
        value = params[key]
        x = value.get('value')
        if (set(value) != {'value', 'unit'} or value.get('unit') != spec['unit'] or
                type(x) not in (int, float) or not math.isfinite(x)):
            fail('$.physics.parameters.'+key, spec, value)
            continue
        if spec['positive'] and x <= 0 or spec['nonnegative'] and x < 0:
            fail('$.physics.parameters.'+key, spec, x)
        p[key] = x
    if errors:
        return
    if 'biot_alpha' in p and p['biot_alpha'] > 1:
        fail('$.physics.parameters.biot_alpha', '0 < ab <= 1', p['biot_alpha'])
    if slug == 'compliant-tube-wave' and p['wall_thickness']/p['radius'] > .1:
        fail('$.physics.parameters.wall_thickness', 'h/R <= 0.1', p['wall_thickness'])
    if slug == 'thermo-poroelastic-transient':
        # Compare using logs to avoid overflow on otherwise finite declarations.
        gamma = p['fluid_thermal']
        if gamma > 0 and (math.log(p['reference_temperature'])+2*math.log(gamma) >=
                          math.log(p['storage'])+math.log(p['heat_capacity'])):
            fail('$.physics.parameters.fluid_thermal', 'T0 gamma^2 < S c', gamma)
    transient = cfg['mode'] == 'transient'
    harmonic = cfg['mode'] == 'harmonic'
    input_axis, output_axis = ('load', 'response') if transient else ('state', 'state')
    if set(m['time_axes']) != {input_axis, output_axis}:
        fail('$.time_axes', sorted({input_axis, output_axis}), list(m['time_axes']))
        return
    times = a[m['time_axes'][input_axis]]
    response = a[m['time_axes'][output_axis]]
    if transient:
        if not 2 <= len(times) <= 256 or times[0] != 0:
            fail('$.time_axes.load', '2..256 times, first 0', times)
        if len(response) > 256 or response[0] < 0 or response[-1] > times[-1]:
            fail('$.time_axes.response', '1..256 times in [0,t_end]', response)
    elif not np.array_equal(times, [0.]):
        fail('$.time_axes.state', '[0.0] storage marker', times)
    locs = m['locations']
    if set(locs) != {'domain', 'left', 'right'}:
        fail('$.locations', ['domain', 'left', 'right'], list(locs))
        return
    for name in ('left', 'right'):
        loc = locs[name]
        if loc['kind'] != 'entities' or len(a[loc['ids']]) != 1:
            fail('$.locations.'+name, 'one real endpoint entity', loc)
    domain = locs['domain']
    if domain['kind'] != 'points':
        fail('$.locations.domain', 'points', domain)
        return
    coords = a[domain['coordinates']][:, 0]
    if not 2 <= len(coords) <= 2048 or len(np.unique(coords)) != len(coords):
        fail('$.locations.domain', '2..2048 distinct physical points', coords)
    if np.any(coords < 0) or np.any(coords > p['length']):
        fail('$.locations.domain.coordinates', 'x in [0,L]', coords)
    if errors:
        return
    field_type = dict(dtype='float64', kind='components' if harmonic else 'scalar',
                      component_shape=[2] if harmonic else [1],
                      components=['real', 'imag'] if harmonic else ['value'], value_kind='point')
    used, seen, values = set(), set(), {}
    for i, condition in enumerate(m['conditions']):
        path = f'$.conditions[{i}]'
        side = condition['location']
        spec = cfg['boundaries'].get(side)
        if spec is None or side in seen:
            fail(path, 'exactly one record per declared endpoint', side)
            continue
        seen.add(side)
        expected = dict(role='boundary', variable='coupled_boundary', operator='prescribed', location=side)
        for key, x in expected.items():
            if condition[key] != x:
                fail(path+'.'+key, x, condition[key])
        if set(condition) != {'role', 'variable', 'operator', 'location', 'data'}:
            fail(path, 'five declared condition keys', list(condition))
        if set(condition['data']) != set(spec):
            fail(path+'.data', list(spec), list(condition['data']))
            continue
        for key, fs in spec.items():
            ref = condition['data'][key]
            qpath = path+'.data.'+key
            if set(ref) == {'value', 'unit'} and not transient and not harmonic:
                if ref['unit'] != fs['unit'] or type(ref['value']) not in (int, float):
                    fail(qpath, 'typed real scalar constant '+fs['unit'], ref)
                    continue
                v = np.array([ref['value']])
            elif set(ref) == {'field'}:
                name = ref['field']
                used.add(name)
                s = m['fields'][name]
                required = dict(field_type, quantity=key, unit=fs['unit'], location=side,
                                time_axis=input_axis, sampling=dict(space='uniform',
                                time='linear' if transient else 'constant', extrapolation='forbid'))
                for k, x in required.items():
                    if s.get(k) != x:
                        fail('$.fields.'+name+'.'+k, x, s.get(k))
                v = a[s['array']]
                if transient and np.any(v[0] != 0):
                    fail(qpath, 'zero value at t=0, compatible with fixed zero initial state', v[0])
            else:
                fail(qpath, 'field' if transient or harmonic else 'field or typed scalar', ref)
                continue
            values[side, key] = v
    if seen != set(cfg['boundaries']):
        fail('$.conditions', list(cfg['boundaries']), sorted(seen))
    if used != set(m['fields']):
        fail('$.fields', 'exactly referenced fields', sorted(set(m['fields'])-used))
    if errors:
        return
    if slug in ('steady-joule-feedback', 'transient-joule-feedback'):
        slope = p['resistivity_slope']
        for side in ('left', 'right'):
            v = values[side, 'temperature_rise']
            if np.any(v < 0) or np.any(slope*v > .1):
                fail('$.conditions.'+side, 'nonnegative theta, a theta <= 0.1', v)
        voltage = values['right', 'voltage']
        # Log magnitude permits large but finite physically invalid values without warnings.
        nonzero = np.abs(voltage[voltage != 0])
        if np.any(math.log(slope)+math.log(p['electric_conductivity'])+
                  2*np.log(nonzero)-math.log(p['conductivity']) > math.log(.1)):
            fail('$.conditions.right.voltage', 'a sigma0 V^2/k <= 0.1', voltage)
    if slug == 'thermoelectric-leg':
        for side in ('left', 'right'):
            if np.any(values[side, 'temperature'] <= 0):
                fail('$.conditions.'+side+'.temperature', 'positive absolute temperature', values[side, 'temperature'])
    present = set()
    total = 0
    for name, s in m['outputs'].items():
        q = s['quantity']
        os = cfg['outputs'].get(q)
        if os is None:
            fail('$.outputs.'+name+'.quantity', list(cfg['outputs']), q)
            continue
        present.add(q)
        required = dict(field_type, unit=os['unit'], location=os['location'], time_axis=output_axis)
        for key, x in required.items():
            if s.get(key) != x:
                fail('$.outputs.'+name+'.'+key, x, s.get(key))
        if 'sampling' in s:
            fail('$.outputs.'+name, 'no output sampling', s['sampling'])
        total += len(response)*len(a[locs[s['location']]['ids']])*math.prod(s['component_shape'])
    if present != set(cfg['outputs']):
        fail('$.outputs', 'all required quantities', sorted(present))
    if max(total, sum(a[s['array']].size for s in m['fields'].values())) > 2000000:
        fail('$.fields/outputs', 'at most 2000000 numeric components in each', 'excess')
