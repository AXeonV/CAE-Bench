"""Public species/kinetic declaration checks; no integrator or reference solver."""
from functools import lru_cache
from importlib.resources import files
import json
import math
import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text())


def shape(spec, parameters):
    return [parameters['species_count'] if x == 's' else x for x in spec['shape']]


def labels(spec, parameters):
    return ['value'] if spec['kind'] == 'scalar' else ['c'+str(i+1) for i in range(math.prod(shape(spec, parameters)))]


def check(problem, errors):
    from caeoj.validation import issue
    m, arrays = problem.manifest, problem.arrays
    model = m.get('physics', {}).get('model', '')
    slug = model.removeprefix('species-').removesuffix('-v1')
    cfg = models().get(slug)

    def fail(path, expected, actual):
        if isinstance(actual, np.ndarray):
            actual = actual.tolist() if actual.size < 20 else list(actual.shape)
        errors.append(issue('E_SPECIES', path, expected, actual, 'Declaration violates this species DATA contract.'))

    if cfg is None or model != 'species-'+slug+'-v1':
        fail('$.physics.model', 'registered species model', model)
        return
    if m['spatial_dimension'] != 1:
        fail('$.spatial_dimension', 1, m['spatial_dimension'])
    if 'task' in m and m['task'] != slug:
        fail('$.task', slug, m['task'])
    if m['meshes'] or m['geometries']:
        fail('$.meshes/geometries', 'empty objects', 'geometry present')
    if any(k in m for k in ('profile', 'contract_version', 'analysis', 'materials')):
        fail('$', 'physics-only declaration', 'mixed declaration')
    raw = m['physics']['parameters']
    if set(raw) != set(cfg['parameters']):
        fail('$.physics.parameters', list(cfg['parameters']), list(raw))
        return
    p = {}
    for key, spec in cfg['parameters'].items():
        v = raw[key]
        x = v.get('value')
        if set(v) != {'value','unit'} or v.get('unit') != spec['unit'] or type(x) not in ((int,) if spec.get('integer') else (int,float)):
            fail('$.physics.parameters.'+key, spec, v)
            continue
        if not math.isfinite(x) or spec.get('positive') and x <= 0 or 'lower' in spec and x < spec['lower'] or 'upper' in spec and x > spec['upper'] or 'upper_exclusive' in spec and x >= spec['upper_exclusive']:
            fail('$.physics.parameters.'+key, spec, x)
        p[key] = x
    locs = m['locations']
    if set(locs) != set(cfg['locations']):
        fail('$.locations', list(cfg['locations']), list(locs))
        return
    for name, spec in cfg['locations'].items():
        loc = locs[name]
        if loc['kind'] != spec['kind']:
            fail('$.locations.'+name+'.kind', spec['kind'], loc['kind'])
        n = len(arrays[loc['ids']])
        if not spec['minimum'] <= n <= spec['maximum']:
            fail('$.locations.'+name, 'declared object count limits', n)
    expected_axes = {'initial','observe','boundary'} if cfg['transport'] else {'initial','observe'}
    if set(m['time_axes']) != expected_axes:
        fail('$.time_axes', sorted(expected_axes), list(m['time_axes']))
        return
    times = {name: arrays[key] for name,key in m['time_axes'].items()}
    if not np.array_equal(times['initial'], [0.]):
        fail('$.time_axes.initial', '[0.0]', times['initial'])
    obs = times['observe']
    if len(obs) > 129 or obs[0] < 0 or obs[-1] <= 0:
        fail('$.time_axes.observe', '1..129 frames, first>=0, last>0', obs)
    if cfg['transport']:
        b = times['boundary']
        if not 2 <= len(b) <= 129 or b[0] != 0 or b[-1] != obs[-1]:
            fail('$.time_axes.boundary', '2..129 frames covering exactly [0,H]', b)
    if errors:
        return
    if cfg['transport']:
        x = arrays[locs['knots']['coordinates']][:,0]
        if x[0] != 0 or x[-1] != p['length'] or np.any(np.diff(x) <= 0):
            fail('$.locations.knots', 'strict x order from 0 to L', x)
        for name, endpoint in [('left',0.),('right',p['length'])]:
            x = arrays[locs[name]['coordinates']]
            if not np.array_equal(x, [[endpoint]]):
                fail('$.locations.'+name, 'endpoint x='+str(endpoint), x)
        x = arrays[locs['probes']['coordinates']]
        if np.any(x <= 0) or np.any(x >= p['length']):
            fail('$.locations.probes', 'strictly internal points', x)
    if 'reactions' in locs and len(arrays[locs['reactions']['ids']]) != p['reaction_count']:
        fail('$.locations.reactions', 'reaction_count objects', len(arrays[locs['reactions']['ids']]))
    refs, values, counts = set(), {}, {}
    for i,c in enumerate(m['conditions']):
        path = f'$.conditions[{i}]'
        op = c['operator']
        r = cfg['records'].get(op)
        if r is None:
            fail(path+'.operator', list(cfg['records']), op)
            continue
        counts[op] = counts.get(op,0)+1
        for key in ('role','variable','location'):
            if c[key] != r[key]:
                fail(path+'.'+key, r[key], c[key])
        if set(c['data']) != set(r['data']):
            fail(path+'.data', list(r['data']), list(c['data']))
            continue
        result = {}
        for key,s in r['data'].items():
            d = c['data'][key]
            if set(d) != {'field'}:
                fail(path+'.data.'+key, 'field reference only', d)
                continue
            name = d['field']
            refs.add(name)
            fs = m['fields'][name]
            expected = dict(quantity=r['variable'] if key=='value' else key,unit=s['unit'],location=r['location'],time_axis=r['axis'],dtype='float64',kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),value_kind='point',sampling=dict(space='piecewise_linear' if r['location']=='knots' else 'uniform',time='linear' if r['axis']=='boundary' else 'constant',extrapolation='forbid'))
            if set(fs) != set(expected)|{'array'}:
                fail('$.fields.'+name, 'exact descriptor keys', list(fs))
            for k,v in expected.items():
                if fs.get(k) != v:
                    fail('$.fields.'+name+'.'+k, v, fs.get(k))
            v = arrays[fs['array']]
            if s.get('positive') and np.any(v<=0) or s.get('nonnegative') and np.any(v<0) or s.get('integral') and np.any(v!=np.floor(v)) or 'lower' in s and np.any(v<s['lower']) or 'upper' in s and np.any(v>s['upper']):
                fail(path+'.data.'+key, s, v)
            result[key] = v
        values[op] = result
    for op in cfg['records']:
        if counts.get(op) != 1:
            fail('$.conditions', 'exactly one '+op, counts.get(op,0))
    if refs != set(m['fields']):
        fail('$.fields', 'exactly referenced fields', sorted(set(m['fields'])-refs))
    present, total = set(), 0
    for name,s in m['outputs'].items():
        q=s['quantity']; spec=cfg['outputs'].get(q);path='$.outputs.'+name
        if spec is None:
            fail(path+'.quantity', list(cfg['outputs']), q)
            continue
        present.add(q)
        expected=dict(quantity=q,unit=spec['unit'],location=spec['location'],time_axis='observe',dtype='float64',kind=spec['kind'],component_shape=shape(spec,p),components=labels(spec,p),value_kind='point')
        if set(s) != set(expected)|{'array'}:
            fail(path, 'exact output descriptor keys', list(s))
        for k,v in expected.items():
            if s.get(k) != v:
                fail(path+'.'+k, v, s.get(k))
        total += len(obs)*len(arrays[locs[s['location']]['ids']])*math.prod(s['component_shape'])
    if present != set(cfg['outputs']):
        fail('$.outputs', 'all required quantities', sorted(present))
    if max(total,sum(arrays[s['array']].size for s in m['fields'].values())) > 2000000:
        fail('$.fields/outputs', '<=2000000 numerical components each', 'excess')
    if errors:
        return
    if cfg['transport']:
        for end,index in [('left',0),('right',-1)]:
            if not np.array_equal(values['initial']['value'][0,index],values[end]['value'][0,0]):
                fail('$.conditions.'+end, 'exact initial/boundary compatibility', 'incompatible corner')
    if 'initial_loading' in values:
        with np.errstate(over='ignore'):
            loading=values['initial_loading']['value'].sum(axis=-1)
        if np.any(loading>p['capacity']):
            fail('$.conditions.initial_loading', 'sum loading <= capacity', loading)
    if 'kinetics' in values:
        r = values['kinetics'];alpha=r['reactants'][0];beta=r['products'][0]
        if np.any(alpha.sum(axis=1)<1) or np.any(alpha.sum(axis=1)>4) or np.any(beta.sum(axis=1)<1) or np.any(beta.sum(axis=1)>8) or np.any(np.all(alpha==beta,axis=1)):
            fail('$.conditions.kinetics', 'nontrivial rows, reactant order 1..4, product count 1..8', 'invalid stoichiometry')
        mass=values['species']['molar_mass'][0,0]
        mass=mass/mass.max()
        if np.any(abs((beta-alpha)@mass)>1e-12*((beta+alpha)@mass)):
            fail('$.conditions.kinetics', 'mass balance within declared relative tolerance', 'unbalanced reaction')
    if slug=='adiabatic-combustion':
        t=values['thermal_initial']['value']
        if np.any(t<250) or np.any(t>5000):
            fail('$.conditions.thermal_initial', '250<=T0<=5000 K', t)
        if np.any(np.max(values['initial']['value'],axis=-1)<=0):
            fail('$.conditions.initial', 'positive total concentration in each vessel', 'empty gas')
    if slug=='partition-transfer':
        ids=arrays[locs['vessels']['ids']];links=values['links'];origin=links['origin'].ravel();dest=links['destination'].ravel()
        if np.any(ids>2**53-1) or np.any(origin>2**53-1) or np.any(dest>2**53-1) or not np.all(np.isin(origin,ids)) or not np.all(np.isin(dest,ids)) or np.any(origin==dest):
            fail('$.conditions.links', 'distinct actual vessel IDs <=2^53-1', 'invalid endpoints')
