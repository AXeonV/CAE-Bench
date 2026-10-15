"""Closed-domain energy and turbulence declarations, sampling and statistics.

This module implements a public I/O contract, not a flow solver.
"""
import numpy as np

from .mesh_geometry import boundary_geometry, exterior_facets

# family, energy, method, analysis; the model is physical opt-in, never a task ID.
MODELS = {}
for _family in ('lowmach', 'inviscid', 'compressible'):
    for _analysis in ('steady', 'transient'):
        MODELS[f'fluid-energy-{_family}-laminar-{_analysis}-v1'] = (_family, True, 'laminar', _analysis)
for _family, _energy in (('incompressible', False), ('lowmach', True)):
    for _method, _analysis in (('rans', 'steady'), ('urans', 'transient'), ('resolved', 'statistics')):
        MODELS[f'fluid-energy-{_family}-{_method}-{_analysis}-v1'] = (_family, _energy, _method, _analysis)
for _family, _energy in (('isothermal', False), ('compressible', True)):
    MODELS[f'fluid-energy-{_family}-rans-steady-v1'] = (_family, _energy, 'rans', 'steady')


def parameter_units(model):
    family, energy, method, analysis = MODELS[model]
    gas = family in ('inviscid', 'compressible', 'isothermal')
    p = {'reference_temperature': 'K', 'minimum_temperature': 'K', 'maximum_temperature': 'K'}
    if gas:
        p.update(specific_gas_constant='J/(kg.K)')
        if analysis == 'steady': p['mean_density'] = 'kg/m3'
        if family == 'inviscid' and analysis == 'steady': p['isentropic_reference_density'] = 'kg/m3'
        if energy: p['heat_capacity_ratio'] = '1'
    else: p.update(density='kg/m3', reference_pressure='Pa')
    if family != 'inviscid':
        p.update(reference_viscosity='Pa.s', viscosity_exponent='1')
        if gas: p['bulk_viscosity'] = 'Pa.s'
    if energy:
        if not gas: p.update(thermal_expansion='1/K', heat_capacity='J/(kg.K)')
        if family != 'inviscid': p.update(reference_conductivity='W/(m.K)', conductivity_exponent='1')
    if analysis != 'steady': p.update(time_start='s', time_end='s')
    if analysis == 'statistics': p.update(statistics_start='s', statistics_end='s', statistics_step='s')
    return p


def fluid_energy_properties(problem, temperature, pressure=None):
    """Return physical rho, mu, k, cp at T [K], gas absolute p [Pa].

    Boussinesq density remains rho0; buoyancy is a separate force described by
    the protocol. No eddy viscosity or closure is selected by this helper.
    """
    model = problem.manifest['physics']['model']; family, energy, _, _ = MODELS[model]
    p = {k: v['value'] for k, v in problem.manifest['physics']['parameters'].items()}
    t = np.asarray(temperature, dtype=float)
    if np.any(~np.isfinite(t)) or np.any(t < p['minimum_temperature']) or np.any(t > p['maximum_temperature']):
        raise ValueError('Temperature outside declared validity interval')
    if family in ('inviscid', 'compressible', 'isothermal'):
        if pressure is None: raise ValueError('Absolute pressure required for ideal gas')
        pressure = np.asarray(pressure, dtype=float)
        if np.any(~np.isfinite(pressure)) or np.any(pressure <= 0): raise ValueError('Positive finite absolute pressure required')
        rho = pressure / (p['specific_gas_constant'] * t)
        cp = p['heat_capacity_ratio'] * p['specific_gas_constant'] / (p['heat_capacity_ratio'] - 1) if energy else None
    else:
        rho = np.full_like(t, p['density']); cp = p.get('heat_capacity')
    with np.errstate(over='raise', invalid='raise', divide='raise', under='raise'):
        mu = p['reference_viscosity'] * (t / p['reference_temperature']) ** p['viscosity_exponent'] if family != 'inviscid' else np.zeros_like(t)
        conductivity = p['reference_conductivity'] * (t / p['reference_temperature']) ** p['conductivity_exponent'] if energy and family != 'inviscid' else np.zeros_like(t)
    return {'density': rho, 'dynamic_viscosity': mu, 'conductivity': conductivity, 'heat_capacity': cp}


def fluid_energy_condition_values(problem, condition, parameter, time):
    """Read a numeric parameter at physical time; shape is [N,*components]."""
    v = condition['data'][parameter]
    if 'value' in v:
        n = len(problem.arrays[problem.manifest['locations'][condition['location']]['ids']])
        return np.full((n, 1), v['value'], dtype=float)
    if 'field' not in v: raise ValueError('Expected numeric condition parameter')
    spec = problem.manifest['fields'][v['field']]
    times = problem.arrays[problem.manifest['time_axes'][spec['time_axis']]]
    values = problem.arrays[spec['array']]
    if len(times) == 1: return values[0].copy()
    if time < times[0] or time > times[-1]: raise ValueError('Temporal extrapolation forbidden')
    i = min(int(np.searchsorted(times, time, side='right')) - 1, len(times) - 2)
    w = (time - times[i]) / (times[i + 1] - times[i])
    return (1 - w) * values[i] + w * values[i + 1]


def fluid_energy_statistics(times, velocity, temperature=None):
    """Equal-weight mean and central products of public instantaneous samples.

    velocity shape [S,N,D]; optional temperature [S,N,1]. Population denominator
    S, not S-1; no density weighting. Returns arrays without an output time axis.
    """
    times = np.asarray(times); u = np.asarray(velocity, dtype=float)
    if times.ndim != 1 or len(times) < 2 or not np.all(np.isfinite(times)) or np.any(np.diff(times) <= 0) or u.ndim != 3 or len(u) != len(times) or not np.all(np.isfinite(u)):
        raise ValueError('Finite increasing times and finite [S,N,D] velocity required')
    if not np.allclose(np.diff(times), np.diff(times)[0], rtol=1e-10, atol=1e-12): raise ValueError('Statistics samples must be equally spaced')
    mean = u.mean(axis=0); du = u - mean
    result = {'velocity': mean, 'velocity_covariance': np.einsum('sni,snj->nij', du, du) / len(times)}
    if temperature is not None:
        t = np.asarray(temperature, dtype=float)
        if t.shape != (*u.shape[:2], 1) or not np.all(np.isfinite(t)): raise ValueError('Temperature must be finite [S,N,1]')
        mt = t.mean(axis=0); dt = t - mt
        result.update(temperature=mt, temperature_variance=(dt * dt).mean(axis=0), turbulent_heat_flux=(du * dt).mean(axis=0))
    return result


def check_fluid_energy(problem, errors):
    """Check after generic validation; append E_FLUID diagnostics, never repair."""
    from .validation import issue
    m = problem.manifest; physics = m.get('physics', {}); model = physics.get('model', '')
    if not model.startswith('fluid-energy-'): return
    def fail(path, expected, actual, message='Invalid fluid-energy declaration.'):
        errors.append(issue('E_FLUID', path, expected, actual, message))
    if model not in MODELS:
        fail('$.physics.model', sorted(MODELS), model); return
    if any(k in m for k in ('contract_version', 'profile', 'analysis', 'materials')):
        fail('$', 'physics only; no cfd-2.1 quartet', 'conflicting physical declarations'); return
    family, energy, method, analysis = MODELS[model]; gas = family in ('inviscid', 'compressible', 'isothermal')
    d = m['spatial_dimension']; locs = m['locations']; arrays = problem.arrays
    if d not in (2, 3) or (method in ('urans', 'resolved') and d != 3) or (method != 'laminar' and energy and d != 3) or (family == 'isothermal' and d != 3):
        fail('$.spatial_dimension', 'supported model dimension; see FLUID-ENERGY', d)
    params = physics['parameters']; expected = parameter_units(model)
    if set(params) != set(expected): fail('$.physics.parameters', sorted(expected), sorted(params)); return
    p = {}
    nonnegative = {'thermal_expansion', 'bulk_viscosity'}
    signed = {'viscosity_exponent', 'conductivity_exponent', 'time_start', 'time_end', 'statistics_start', 'statistics_end'}
    for name, unit in expected.items():
        item = params[name]; p[name] = item['value']
        if item['unit'] != unit: fail('$.physics.parameters.' + name + '.unit', unit, item['unit'])
        if name not in signed and (p[name] < 0 if name in nonnegative else p[name] <= 0): fail('$.physics.parameters.' + name, 'nonnegative' if name in nonnegative else 'positive', p[name])
    if not p['minimum_temperature'] <= p['reference_temperature'] <= p['maximum_temperature'] or p['minimum_temperature'] >= p['maximum_temperature']:
        fail('$.physics.parameters', '0 < Tmin <= Tref <= Tmax; Tmin < Tmax', 'temperature interval')
    if 'heat_capacity_ratio' in p and p['heat_capacity_ratio'] <= 1: fail('$.physics.parameters.heat_capacity_ratio', '>1', p['heat_capacity_ratio'])
    if family == 'lowmach' and p['thermal_expansion'] * max(abs(p['minimum_temperature'] - p['reference_temperature']), abs(p['maximum_temperature'] - p['reference_temperature'])) > .1:
        fail('$.physics.parameters.thermal_expansion', 'beta*max|T-Tref| <= 0.1 (Boussinesq)', p['thermal_expansion'])
    if errors: return
    try:
        endpoints = fluid_energy_properties(problem, np.array([p['minimum_temperature'], p['maximum_temperature']]), 1. if gas else None)
        for quantity, value in endpoints.items():
            if value is not None and np.any(~np.isfinite(value)):
                fail('$.physics.parameters', 'finite material response throughout validity interval', quantity)
    except (FloatingPointError, OverflowError, ValueError) as exc:
        fail('$.physics.parameters', 'representable material response on validity interval', str(exc))
    if errors: return
    start = p.get('time_start', 0.); end = p.get('time_end', 0.)
    if analysis != 'steady' and start >= end: fail('$.physics.parameters.time_end', '> time_start', end)
    if analysis == 'statistics':
        a, b, step = p['statistics_start'], p['statistics_end'], p['statistics_step']
        count = (b - a) / step
        if not start <= a < b <= end or not np.isfinite(count) or count < 1 or count > 100000 or not np.isclose(count, round(count), rtol=0, atol=1e-9):
            fail('$.physics.parameters', 'start <= statistics_start < statistics_end <= end; integer 1..100000 intervals', 'statistics grid')
    if len(m['meshes']) != 1: fail('$.meshes', 'one fixed fluid mesh', list(m['meshes'])); return
    mesh_name = next(iter(m['meshes'])); mesh = problem.meshes[mesh_name]
    if mesh['dimension'] != d or 'connectivity' not in mesh: fail('$.meshes', 'full-dimensional geometry-enabled mesh', mesh['dimension']); return
    try: exterior = exterior_facets(mesh, d)
    except ValueError as exc: fail('$.meshes', 'first-order connected manifold cells', str(exc)); return
    def region(name, dimension):
        loc = locs.get(name, {})
        return loc.get('kind') == 'mesh' and loc.get('mesh') == mesh_name and loc.get('entity') == 'element' and loc.get('dimension') == dimension
    domains = [name for name in locs if region(name, d) and set(map(int, arrays[locs[name]['ids']])) == mesh['elements'][d]]
    if len(domains) != 1: fail('$.locations', 'exactly one complete fluid domain location', domains); return
    domain = domains[0]
    quantities = {'velocity': ('m/s', 'vector'), 'pressure': ('Pa', 'scalar')}
    if energy: quantities['temperature'] = ('K', 'scalar')
    if gas: quantities['density'] = ('kg/m3', 'scalar')
    if analysis == 'statistics':
        quantities['velocity_covariance'] = ('m2/s2', 'tensor')
        if energy: quantities.update(temperature_variance=('K2', 'scalar'), turbulent_heat_flux=('K.m/s', 'vector'))
    all_inputs = dict(quantities, acceleration=('m/s2', 'vector'), heat_source=('W/m3', 'scalar'), heat_flux=('W/m2', 'scalar'), turbulent_kinetic_energy=('m2/s2', 'scalar'), turbulence_length_scale=('m', 'scalar'))
    used_fields = set()
    for name, spec in m['fields'].items():
        q = spec['quantity']; path = '$.fields.' + name
        if q not in all_inputs: fail(path + '.quantity', sorted(all_inputs), q); continue
        unit, kind = all_inputs[q]
        if (spec['unit'], spec['kind'], spec['dtype'], spec['value_kind']) != (unit, kind, 'float64', 'average'): fail(path, (unit, kind, 'float64', 'average'), spec)
        if not (region(spec['location'], d) or region(spec['location'], d - 1)): fail(path + '.location', 'mesh cell/facet location', spec['location'])
        sampling = spec.get('sampling', {})
        if sampling.get('space') != 'piecewise_constant' or sampling.get('time') not in ('constant', 'linear') or sampling.get('extrapolation') != 'forbid': fail(path + '.sampling', 'piecewise_constant / constant|linear / forbid', sampling)
        times = arrays[m['time_axes'][spec['time_axis']]]
        if sampling.get('time') == 'constant' and len(times) != 1: fail(path + '.time_axis', 'one time for constant signal', times.tolist())
        if sampling.get('time') == 'linear' and len(times) < 2: fail(path + '.time_axis', 'at least two linear samples', times.tolist())
        vals = arrays[spec['array']]
        if q in ('density', 'turbulence_length_scale') and np.any(vals <= 0): fail(path, 'positive values', 'nonpositive')
        if q == 'turbulent_kinetic_energy' and np.any(vals < 0): fail(path, 'nonnegative values', 'negative')
        if q == 'temperature' and (np.any(vals < p['minimum_temperature']) or np.any(vals > p['maximum_temperature'])): fail(path, 'temperature validity interval', 'out of range')
    if errors: return
    temperature_anchor = False
    boundary_seen = set(); initial_seen = set(); source_seen = set(); thermal_seen = set()
    for i, c in enumerate(m['conditions']):
        path = f'$.conditions[{i}]'; role, op, var, name = (c[k] for k in ('role', 'operator', 'variable', 'location')); data = c['data']
        specs = None
        if role == 'boundary' and var == 'velocity' and op == ('slip_wall' if family == 'inviscid' else 'moving_wall'):
            specs = {'impermeable': ('option', 'yes')} if family == 'inviscid' else {'value': ('m/s', 'vector')}
            if not region(name, d - 1): fail(path + '.location', 'exterior facets', name)
            else:
                tags = {frozenset(mesh['connectivity'][int(tag)][1]) for tag in arrays[locs[name]['ids']]}
                if not tags <= exterior.keys() or tags & boundary_seen: fail(path + '.location', 'disjoint exterior facets', name)
                boundary_seen |= tags
                if family != 'inviscid' and 'value' in data and 'field' in data['value']:
                    values = arrays[m['fields'][data['value']['field']]['array']]
                    try:
                        _, normals, _ = boundary_geometry(problem, name)
                        if np.any(abs(np.einsum('tnd,nd->tn', values, normals)) > 1e-10 * np.maximum(1., np.linalg.norm(values, axis=-1))): fail(path, 'tangential wall velocity', 'nonzero normal velocity')
                    except ValueError as exc: fail(path, 'valid boundary geometry', str(exc))
        elif role == 'boundary' and var == 'temperature' and energy and family != 'inviscid' and op in ('temperature', 'outward_heat_flux'):
            if op == 'temperature': temperature_anchor = True
            specs = {'value': ('K', 'scalar')} if op == 'temperature' else {'value': ('W/m2', 'scalar')}
            if not region(name, d - 1): fail(path + '.location', 'exterior facets', name)
            else:
                tags = {frozenset(mesh['connectivity'][int(tag)][1]) for tag in arrays[locs[name]['ids']]}
                if not tags <= exterior.keys() or tags & thermal_seen: fail(path, 'disjoint exterior thermal facets', name)
                thermal_seen |= tags
        elif role == 'initial' and op == 'assign' and analysis != 'steady':
            allowed = {'velocity', 'temperature', 'density'} & quantities.keys()
            if method == 'urans': allowed |= {'turbulent_kinetic_energy', 'turbulence_length_scale'}
            if var in allowed:
                specs = {'value': all_inputs[var]}
                if name != domain or var in initial_seen: fail(path, 'one full-domain initial condition per variable', name)
                initial_seen.add(var)
        elif role == 'source' and op == 'assign' and var in ('acceleration', 'heat_source') and (var == 'acceleration' or (energy and not (family == 'inviscid' and analysis == 'steady'))):
            specs = {'value': all_inputs[var]}
            if name != domain or var in source_seen: fail(path, 'at most one full-domain source per variable', name)
            source_seen.add(var)
        if specs is None: fail(path, 'supported role/variable/operator combination', (role, var, op)); continue
        if set(data) != set(specs): fail(path + '.data', sorted(specs), sorted(data)); continue
        for key, (unit, kind) in specs.items():
            value = data[key]; dp = path + '.data.' + key
            if unit == 'option':
                if value != {'option': kind}: fail(dp, {'option': kind}, value)
                continue
            if 'value' in value:
                if kind != 'scalar' or value.get('unit') != unit: fail(dp, f'{kind} in {unit}; vectors require field', value)
                numeric = value['value']
                if unit == 'K' and not p['minimum_temperature'] <= numeric <= p['maximum_temperature']: fail(dp, 'temperature validity interval', numeric)
                if var in ('density', 'turbulence_length_scale') and numeric <= 0: fail(dp, 'positive', numeric)
                if var == 'turbulent_kinetic_energy' and numeric < 0: fail(dp, 'nonnegative', numeric)
            elif 'field' in value:
                used_fields.add(value['field']); field = m['fields'][value['field']]
                expected_quantity = var if var != 'temperature' or op != 'outward_heat_flux' else 'heat_flux'
                if (field['unit'], field['kind'], field['quantity'], field['location']) != (unit, kind, expected_quantity, name): fail(dp, (unit, kind, expected_quantity, name), field)
                times = arrays[m['time_axes'][field['time_axis']]]
                if role == 'initial' and times.tolist() != [start]: fail(dp, f'one initial sample at {start}', times.tolist())
                elif role != 'initial' and analysis == 'steady' and times.tolist() != [0.]: fail(dp, 'steady sample [0]', times.tolist())
                elif role != 'initial' and len(times) > 1 and (times[0] > start or times[-1] < end): fail(dp, 'linear time samples covering [start,end]', times.tolist())
            else: fail(dp, 'typed scalar constant or field', value)
    if boundary_seen != exterior.keys(): fail('$.conditions', 'all exterior facets covered once by velocity conditions', 'incomplete wall coverage')
    if energy and family != 'inviscid' and thermal_seen != exterior.keys(): fail('$.conditions', 'all exterior facets covered once thermally', 'incomplete thermal coverage')
    if energy and family != 'inviscid' and analysis == 'steady' and not temperature_anchor:
        fail('$.conditions', 'at least one prescribed-temperature facet for steady thermal state', 'no temperature anchor')
    required_initial = ({'velocity', 'temperature', 'density'} & quantities.keys()) if analysis != 'steady' else set()
    if method == 'urans': required_initial |= {'turbulent_kinetic_energy', 'turbulence_length_scale'}
    if initial_seen != required_initial: fail('$.conditions', sorted(required_initial), sorted(initial_seen), 'Incorrect physical initial state.')
    if set(m['fields']) != used_fields: fail('$.fields', 'only condition-referenced input fields', sorted(set(m['fields']) - used_fields))
    present = set()
    for name, spec in m['outputs'].items():
        path = '$.outputs.' + name; q = spec['quantity']; present.add(q)
        if q not in quantities: fail(path + '.quantity', sorted(quantities), q); continue
        if (spec['unit'], spec['kind'], spec['dtype'], spec['value_kind'], spec['location']) != (*quantities[q], 'float64', 'average', domain): fail(path, 'canonical unit/kind, float64 domain average', spec)
        times = arrays[m['time_axes'][spec['time_axis']]]
        if analysis == 'steady' and times.tolist() != [0.]: fail(path + '.time_axis', '[0]', times.tolist())
        if analysis == 'statistics' and times.tolist() != [p['statistics_end']]: fail(path + '.time_axis', '[statistics_end]', times.tolist())
        if analysis == 'transient' and (times[0] < start or times[-1] > end): fail(path + '.time_axis', 'within [start,end]', times.tolist())
    if present != quantities.keys(): fail('$.outputs', sorted(quantities), sorted(present), 'All public common observables required.')
