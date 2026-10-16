"""Public electrochemical declaration checks; no integrator or reference solver."""
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
    slug = model.removeprefix('electrochemistry-').removesuffix('-v1')
    cfg = models().get(slug)

    def fail(path, expected, actual):
        if isinstance(actual, np.ndarray):
            actual = actual.tolist() if actual.size < 20 else list(actual.shape)
        errors.append(issue('E_ELECTROCHEMISTRY', path, expected, actual, 'Declaration violates this electrochemical DATA contract.'))

    if cfg is None or model != 'electrochemistry-'+slug+'-v1':
        fail('$.physics.model', 'registered electrochemical model', model)
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
    expected_axes = {'initial','observe','drive'} if cfg['dynamic'] else {'state'}
    if set(m['time_axes']) != expected_axes:
        fail('$.time_axes', sorted(expected_axes), list(m['time_axes']))
        return
    times = {name: arrays[key] for name,key in m['time_axes'].items()}
    if cfg['dynamic']:
        if not np.array_equal(times['initial'], [0.]):
            fail('$.time_axes.initial', '[0.0]', times['initial'])
        obs = times['observe']
        if len(obs)>129 or obs[0]<0 or obs[-1]<=0:
            fail('$.time_axes.observe','1..129 frames, first>=0, last>0',obs)
        drive=times['drive']
        if not 2<=len(drive)<=129 or drive[0]!=0 or drive[-1]!=obs[-1]:
            fail('$.time_axes.drive','2..129 frames exactly covering [0,H]',drive)
    else:
        obs=times['state']
        if not np.array_equal(obs,[0.]):
            fail('$.time_axes.state','single [0.0] marker',obs)
    if errors:
        return
    if slug in ('ionic-equilibrium','blocking-pnp'):
        for name,x in [('left',0.),('right',p['length'])]:
            if not np.array_equal(arrays[locs[name]['coordinates']],[[x]]):
                fail('$.locations.'+name,'endpoint x='+str(x),arrays[locs[name]['coordinates']])
    if 'probes' in locs:
        x=arrays[locs['probes']['coordinates']]
        strict=slug=='electrode-diffusion'
        if np.any(x<0) or np.any(x>p['length']) or strict and (np.any(x==0) or np.any(x==p['length'])):
            fail('$.locations.probes','internal points' if strict else 'points in [0,L]',x)
    if slug=='electrode-diffusion' and not np.array_equal(arrays[locs['electrode']['coordinates']],[[0.]]):
        fail('$.locations.electrode','x=0',arrays[locs['electrode']['coordinates']])
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
            expected = dict(quantity=r['variable'] if key=='value' else key,unit=s['unit'],location=r['location'],time_axis=r['axis'],dtype='float64',kind=s['kind'],component_shape=shape(s,p),components=labels(s,p),value_kind='point',sampling=dict(space='uniform',time='linear' if r['axis']=='drive' else 'constant',extrapolation='forbid'))
            if set(fs) != set(expected)|{'array'}:
                fail('$.fields.'+name, 'exact descriptor keys', list(fs))
            for k,v in expected.items():
                if fs.get(k) != v:
                    fail('$.fields.'+name+'.'+k, v, fs.get(k))
            v = arrays[fs['array']]
            if s.get('positive') and np.any(v<=0) or s.get('nonnegative') and np.any(v<0) or s.get('integral') and np.any(v!=np.floor(v)) or 'lower' in s and np.any(v<s['lower']) or 'upper' in s and np.any(v>s['upper']) or 'upper_exclusive' in s and np.any(v>=s['upper_exclusive']):
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
        expected=dict(quantity=q,unit=spec['unit'],location=spec['location'],time_axis='observe' if cfg['dynamic'] else 'state',dtype='float64',kind=spec['kind'],component_shape=shape(spec,p),components=labels(spec,p),value_kind='point')
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
    if slug in ('ionic-equilibrium','blocking-pnp'):
        from fractions import Fraction
        charge=values['ions']['charge'][0,0]
        concentration=values['initial']['value'][0,0] if cfg['dynamic'] else values['ions']['reservoir'][0,0]
        if not (np.any(charge>0) and np.any(charge<0)):
            fail('$.conditions.ions.charge','at least one positive and one negative species',charge)
        if sum(Fraction.from_float(float(ci))*int(zi) for ci,zi in zip(concentration,charge)) != 0:
            fail('$.conditions.initial/reservoir','exact electroneutrality of stored binary64 values','nonzero sum z*c')
        # Long-double evaluation avoids intermediate overflow for ordinary extreme scales.
        for end in ('left','right'):
            v=values[end]['value']
            if cfg['dynamic'] and np.any(v[0]!=0):
                fail('$.conditions.'+end,'initial potential exactly 0',v[0])
            with np.errstate(over='ignore',divide='ignore',invalid='ignore'):
                dimensionless=np.abs(v.astype(np.longdouble)*np.longdouble(p['faraday'])/np.longdouble(p['gas_constant'])/np.longdouble(p['temperature']))*np.max(np.abs(charge))
            if np.any(~np.isfinite(dimensionless)) or np.any(dimensionless>20):
                fail('$.conditions.'+end,'max abs(z F phi/(RT)) <=20','excess potential')
    if slug=='capacitive-redox' and np.any(np.max(values['initial']['value'],axis=-1)<=0):
        fail('$.conditions.initial','positive total R/O inventory per cell','empty cell')
    if slug=='particle-battery':
        if not np.array_equal(arrays[locs['electrodes']['ids']],[0,1]):
            fail('$.locations.electrodes','IDs exactly [0,1]',arrays[locs['electrodes']['ids']])
        radii=values['particles']['radius'][0,:,0]
        for i,e in enumerate(('negative','positive')):
            x=arrays[locs[e+'_probes']['coordinates']]
            if np.any(x<0) or np.any(x>radii[i]):
                fail('$.locations.'+e+'_probes','0<=r<=corresponding radius',x)
        if np.any(values['current']['value'][0]!=0):
            fail('$.conditions.current','J(0) exactly 0',values['current']['value'][0])
