"""Public granular declarations; no trajectories, force solver or reference data."""
from functools import lru_cache
from importlib.resources import files
import json
import math
import numpy as np


@lru_cache(maxsize=1)
def models():
    return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))


def shape(spec, parameters):
    return [parameters['bin_count'] if x == 'K' else x for x in spec['shape']]


def labels(spec, parameters):
    return (['value'] if spec['kind'] == 'scalar' else ['x','y','z'] if spec['kind'] == 'vector'
            else ['xx','xy','xz','yx','yy','yz','zx','zy','zz'] if spec['kind'] == 'tensor'
            else ['c'+str(i+1) for i in range(math.prod(shape(spec, parameters)))])


def check(problem, errors):
    from caeoj.validation import issue
    m, a = problem.manifest, problem.arrays

    def fail(path, expected, actual):
        errors.append(issue('E_GRANULAR', path, expected, actual,
                            'Declaration violates this granular DATA contract.'))

    model = m.get('physics', {}).get('model', '')
    slug = model.removesuffix('-v1')
    cfg = models().get(slug)
    if cfg is None or model != slug+'-v1':
        fail('$.physics.model', 'registered granular model', model)
        return
    if 'task' in m and m['task'] != slug:
        fail('$.task', slug, m['task'])
    if m['spatial_dimension'] != cfg['dimension']:
        fail('$.spatial_dimension', cfg['dimension'], m['spatial_dimension'])
    if m['meshes'] or m['geometries']:
        fail('$.meshes/geometries', 'empty objects', [m['meshes'], m['geometries']])
    if any(k in m for k in ('profile','analysis','materials','contract_version')):
        fail('$', 'physics only', 'mixed declaration')

    def bounds(path, value, spec):
        if spec.get('lower') is not None and np.any(value < spec['lower']):
            fail(path, '>= '+str(spec['lower']), value)
        if spec.get('upper') is not None and np.any(value > spec['upper']):
            fail(path, '<= '+str(spec['upper']), value)

    p = {}
    params = m['physics'].get('parameters', {})
    if set(params) != set(cfg['parameters']):
        fail('$.physics.parameters', sorted(cfg['parameters']), sorted(params))
        return
    for key, spec in cfg['parameters'].items():
        v = params[key];x = v.get('value')
        if set(v) != {'value','unit'} or type(x) not in ((int,) if spec['integer'] else (int,float)) or v.get('unit') != spec['unit']:
            fail('$.physics.parameters.'+key, spec, v)
            continue
        bounds('$.physics.parameters.'+key, np.asarray(x), spec)
        p[key] = x
    locs = m['locations']
    if set(locs) != set(cfg['locations']):
        fail('$.locations', sorted(cfg['locations']), sorted(locs))
        return
    for name, spec in cfg['locations'].items():
        l = locs[name]
        if set(l) != {'kind','ids'} or l['kind'] != 'entities':
            fail('$.locations.'+name, 'entities with kind and ids only', l)
        n = len(a[l['ids']])
        if not spec['minimum'] <= n <= spec['maximum']:
            fail('$.locations.'+name, [spec['minimum'],spec['maximum']], n)
    axes = {'static','initial','observe'} | ({'drive'} if not cfg['population'] else set())
    if set(m['time_axes']) != axes:
        fail('$.time_axes', sorted(axes), sorted(m['time_axes']))
        return
    for name in ('static','initial'):
        if not np.array_equal(a[m['time_axes'][name]], [0.]):
            fail('$.time_axes.'+name, '[0.0]', a[m['time_axes'][name]])
    obs = a[m['time_axes']['observe']]
    end = obs[-1]
    if not 1 <= len(obs) <= 256 or obs[0] < 0 or not 0 < end <= 10:
        fail('$.time_axes.observe', '1..256 times in [0,tend], 0<tend<=10', obs)
    if not cfg['population']:
        drive = a[m['time_axes']['drive']]
        if not 2 <= len(drive) <= 512 or drive[0] != 0 or drive[-1] != end:
            fail('$.time_axes.drive', '2..512 times from 0 to observe[-1]', drive)
    if errors:
        return
    if cfg['population'] and not np.array_equal(a[locs['bins']['ids']], np.arange(1,p['bin_count']+1)):
        fail('$.locations.bins', 'IDs exactly 1..bin_count', a[locs['bins']['ids']])
    quantities = {};values = {}
    for name, s in m['fields'].items():
        q = s['quantity'];target = cfg['inputs'].get(q)
        if target is None or q in quantities:
            fail('$.fields.'+name+'.quantity', 'unique required input quantity', q)
            continue
        quantities[q] = name
        expected = dict(dtype='float64', kind=target['kind'], component_shape=shape(target,p),
                        components=labels(target,p), unit=target['unit'], location=target['location'],
                        time_axis=target['axis'], value_kind='point', sampling=dict(space='uniform',
                        time='linear' if target['axis']=='drive' else 'constant', extrapolation='forbid'))
        for key, v in expected.items():
            if s.get(key) != v:
                fail('$.fields.'+name+'.'+key, v, s.get(key))
        values[q] = a[s['array']]
        bounds('$.fields.'+name, values[q], target)
    if set(quantities) != set(cfg['inputs']):
        fail('$.fields', sorted(cfg['inputs']), sorted(quantities))
    seen = set()
    for i, cond in enumerate(m['conditions']):
        q = cond['variable'];path = '$.conditions['+str(i)+']'
        if q not in quantities or q in seen:
            fail(path, 'one condition per input quantity', q)
            continue
        seen.add(q);target = cfg['inputs'][q]
        expected = dict(role='initial' if target['axis']=='initial' else 'source' if target['axis']=='drive' else 'material', variable=q, location=target['location'], operator='prescribed', data={'value':{'field':quantities[q]}})
        if cond != expected:
            fail(path, expected, cond)
    if seen != set(cfg['inputs']):
        fail('$.conditions', sorted(cfg['inputs']), sorted(seen))
    present = set();total = 0
    for name, s in m['outputs'].items():
        q = s['quantity'];target = cfg['outputs'].get(q)
        if target is None:
            fail('$.outputs.'+name+'.quantity', sorted(cfg['outputs']), q)
            continue
        present.add(q)
        expected = dict(dtype='float64', kind=target['kind'], component_shape=shape(target,p),
                        components=labels(target,p), unit=target['unit'], location=target['location'],
                        time_axis='observe', value_kind='point')
        for key,v in expected.items():
            if s.get(key) != v:
                fail('$.outputs.'+name+'.'+key, v, s.get(key))
        if 'sampling' in s:
            fail('$.outputs.'+name, 'no output sampling', s['sampling'])
        total += len(obs)*len(a[locs[target['location']]['ids']])*math.prod(shape(target,p))
    if present != set(cfg['outputs']):
        fail('$.outputs', sorted(cfg['outputs']), sorted(present))
    if max(total, sum(v.size for v in values.values())) > 2000000:
        fail('$.fields/outputs', '<=2000000 scalar components each', total)
    if errors:
        return
    if cfg['population']:
        k = np.arange(1,p['bin_count']+1)
        n0 = values['initial_density'][0,:,0]
        phi = p['monomer_volume'] * (k @ n0)
        if phi > .1:
            fail('$.fields.initial_density', 'initial solid fraction <=0.1', phi)
        if slug == 'granular-coagulation':
            kernel = values['collision_kernel'][0,0]
            if np.max(abs(kernel-kernel.T)) > 1e-12*max(1e-30,np.max(abs(kernel))):
                fail('$.fields.collision_kernel', 'symmetric to public tolerance', kernel)
            if end*np.max(kernel)*n0.sum() > 1e5:
                fail('$.fields.collision_kernel', 'tend max(A) sum(n0)<=1e5', 'excess stiffness')
        else:
            rate = values['breakage_rate'][0,:,0];b = values['daughter_count'][0,0]
            if rate[0] != 0 or np.any(np.tril(b) != 0):
                fail('$.fields', 'a1=0 and b_jk=0 for j>=k', 'invalid fragmentation topology')
            if np.any(abs(k@b[:,1:]-k[1:]) > 1e-12*k[1:]):
                fail('$.fields.daughter_count', 'volume-conserving columns', k@b)
            if end*np.max(rate) > 1e5:
                fail('$.fields.breakage_rate', 'tend max(a)<=1e5', 'excess stiffness')
    else:
        mass = values['mass'][0,:,0];radius = values['radius'][0,:,0]
        if end*np.max(values['drag'][0,:,0]/mass) > 1e5:
            fail('$.fields.drag', 'tend max(b/m)<=1e5', 'excess stiffness')
        if slug == 'granular-forced-motion':
            bound = (abs(values['initial_position'][0]) + end*abs(values['initial_velocity'][0])
                     + .5*end**2*np.max(abs(values['external_force']),axis=0)/mass[:,None])
            if np.any(bound > 100):
                fail('$.fields', 'componentwise free-flight input displacement bound<=100 m', bound)
        if slug != 'granular-forced-motion':
            if end*math.sqrt(p['stiffness']/mass.min()) > 1e5 or end*p['normal_damping']/mass.min() > 1e5:
                fail('$.physics.parameters', 'public contact stiffness bounds', 'excess stiffness')
            x = values['initial_position'][0]
            periodic = slug == 'granular-periodic-assembly'
            if periodic:
                length = p['box_length']
                if np.any(x < 0) or np.any(x >= length) or 2*radius.max() >= .49*length:
                    fail('$.fields', 'initial x in [0,L)^3 and 2 max(R)<0.49L', 'invalid periodic representation')
                phi = np.sum(4*math.pi*radius**3/3)/length**3
                if phi > .74:
                    fail('$.fields.radius', 'nominal solid fraction<=0.74', phi)
            for i in range(len(mass)):
                for j in range(i+1,len(mass)):
                    r = x[i]-x[j]
                    if periodic:r = r-length*np.floor(r/length+.5)
                    d = float(np.linalg.norm(r));delta = radius[i]+radius[j]-d
                    if d == 0 or delta > .05*min(radius[i],radius[j]):
                        fail('$.fields.initial_position', 'distinct centers and small overlaps', [i,j,d,delta])
                    if periodic and obs[0] == 0 and abs(delta) < 1e-8*min(radius[i],radius[j]):
                        fail('$.fields.initial_position', 'observation contact margin', [i,j,delta])
        if slug == 'granular-sliding-friction':
            inertia = .4*mass*radius**2
            if end*np.max(values['spin_drag'][0,:,0]/inertia) > 1e5:
                fail('$.fields.spin_drag', 'tend max(bomega/I)<=1e5', 'excess stiffness')
            psum = (len(mass)-1)*(.05*p['stiffness']*radius.max()+2000*math.sqrt(3)*p['normal_damping'])
            if end*p['friction']*psum*np.max(1/mass+radius**2/inertia)/p['slip_speed'] > 1e5:
                fail('$.physics.parameters', 'public regularized sliding stiffness bound<=1e5', 'excess stiffness')
        if slug == 'granular-cohesive-contact':
            if end*math.sqrt(math.pi*p['cohesive_force']/(mass.min()*p['interaction_range'])) > 1e5:
                fail('$.physics.parameters', 'public cohesion stiffness bound<=1e5', 'excess stiffness')
