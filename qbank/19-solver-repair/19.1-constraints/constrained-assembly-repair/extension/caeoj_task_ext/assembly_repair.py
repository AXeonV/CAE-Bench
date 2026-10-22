"""Declaration checks only. Does not compute accelerations or repair states."""
import numpy as np
from caeoj.validation import issue


def check(problem, errors):
    meta, data = problem.manifest, problem.arrays

    def fail(path, expected, actual):
        errors.append(issue('E_ASSEMBLY', path, expected, str(actual), 'Outside the task DATA contract.'))

    if (meta.get('task') != 'constrained-assembly-repair' or meta['spatial_dimension'] != 3
            or meta['meshes'] or meta['geometries'] or meta['conditions']):
        fail('$', '3D discrete assembly declaration', 'unexpected objects')
    physics = meta.get('physics', {})
    parameters = physics.get('parameters', {})
    if physics.get('model') != 'constrained-assembly-v1' or set(parameters) != {'action', 'gravity_x', 'gravity_y', 'gravity_z'}:
        fail('$.physics', 'constrained-assembly-v1 and declared parameters', physics)
        return
    for name, item in parameters.items():
        if item['unit'] != ('1' if name == 'action' else 'm/s^2'):
            fail('$.physics.parameters.' + name, 'declared SI unit', item)
    action = parameters['action']['value']
    if action not in (1, 2, 4):
        fail('$.physics.parameters.action', '1, 2 or 4', action)
        return
    if meta['time_axes'] != {'state': 'times'} or not np.array_equal(data.get('times'), [0.]):
        fail('$.time_axes', 'one instant at t=0', meta['time_axes'])
    ids = data.get('body_ids')
    if ids is None or not 1 <= len(ids) <= 16:
        fail('$.locations.bodies', '1..16 body IDs', ids)
        return
    link_ids = data.get('link_ids', [])
    m = len(link_ids)
    expected_locations = {'bodies': {'kind': 'entities', 'ids': 'body_ids'}}
    if m:
        expected_locations['links'] = {'kind': 'entities', 'ids': 'link_ids'}
    if meta['locations'] != expected_locations or m > 24:
        fail('$.locations', 'body and optional link entities only', meta['locations'])
    descriptions = {
        'mass': ('bodies', 'float64', 1, 'kg', 'mass'),
        'fixed': ('bodies', 'bool', 1, '1', 'fixed'),
        'position': ('bodies', 'float64', 3, 'm', 'position'),
        'velocity': ('bodies', 'float64', 3, 'm/s', 'velocity'),
        'force': ('bodies', 'float64', 3, 'N', 'force')}
    if m:
        descriptions.update(endpoints=('links', 'int64', 2, '1', 'endpoints'),
                            length=('links', 'float64', 1, 'm', 'length'))
    if set(meta['fields']) != set(descriptions):
        fail('$.fields', str(sorted(descriptions)), sorted(meta['fields']))
        return

    def description(name, spec, expected, output=False):
        loc, dtype, count, unit, quantity = expected
        wanted = {'array': name, 'location': loc, 'dtype': dtype, 'kind': 'scalar' if count == 1 else 'vector' if count == 3 else 'components',
                  'component_shape': [count], 'unit': unit, 'quantity': quantity, 'time_axis': 'state', 'value_kind': 'point'}
        wanted['components'] = ['value'] if count == 1 else list('xyz') if count == 3 else ['first', 'second']
        if not output:
            wanted['sampling'] = {'space': 'uniform', 'time': 'constant', 'extrapolation': 'forbid'}
        if spec != wanted:
            fail(('$.outputs.' if output else '$.fields.') + name, wanted, spec)

    for name, desc in descriptions.items():
        description(name, meta['fields'][name], desc)
        if data[name].shape != (1, len(ids) if desc[0] == 'bodies' else m, desc[2]):
            fail('$.fields.' + name, 'declared single-frame shape', data[name].shape)
    if errors:
        return
    mass, fixed = data['mass'][0, :, 0], data['fixed'][0, :, 0]
    q, v, f = [data[name][0] for name in ('position', 'velocity', 'force')]
    if np.all(fixed) or np.any((mass < .2) | (mass > 5)):
        fail('$.fields.mass/fixed', 'positive bounded masses and an active body', 'out of range')
    for name, values, bound in [('position', q, 20), ('velocity', v, 10), ('force', f, 50)]:
        if np.any(np.abs(values) > bound):
            fail('$.fields.' + name, 'absolute component <= ' + str(bound), 'out of range')
    gravity = np.array([parameters['gravity_' + axis]['value'] for axis in 'xyz'])
    if np.linalg.norm(gravity) > 20:
        fail('$.physics.parameters', '|gravity| <= 20', gravity)
    if np.any(v[fixed] != 0) or np.any(f[fixed] != 0):
        fail('$.fields.velocity/force', 'zero on fixed bodies', 'nonzero')
    rows = {int(tag): i for i, tag in enumerate(ids)}
    jacobian = np.zeros((m, 3 * len(ids)))
    for edge in range(m):
        a, b = [rows.get(int(tag)) for tag in data['endpoints'][0, edge]]
        length = data['length'][0, edge, 0]
        if a is None or b is None or a == b or fixed[a] and fixed[b] or not .2 <= length <= 5:
            fail('$.fields.endpoints/length', 'valid distinct endpoints and length', edge)
            continue
        delta = q[b] - q[a]
        norm = np.linalg.norm(delta)
        if norm == 0:
            fail('$.fields.position', 'nonzero link direction', edge)
            continue
        direction = delta / norm
        if not fixed[a]: jacobian[edge, 3*a:3*a+3] = -direction
        if not fixed[b]: jacobian[edge, 3*b:3*b+3] = direction
        if action in (2, 4) and abs(norm - length) > 1e-12:
            fail('$.fields.position', 'distance-compatible input', edge)
        if action == 4 and abs(np.dot(direction, v[b] - v[a])) > 1e-12:
            fail('$.fields.velocity', 'velocity-compatible input', edge)
    if m and not errors:
        inverse_mass = np.repeat(np.where(fixed, 0., 1. / mass), 3)
        condition = np.linalg.cond((jacobian * inverse_mass) @ jacobian.T)
        if not np.isfinite(condition) or condition > 100:
            fail('$.fields.endpoints', 'independent constraints with condition <=100', condition)
    if action == 1:
        if (len(ids) != 2 or m != 1 or np.sum(fixed) != 1 or np.any(gravity) or np.any(f) or np.any(v)):
            fail('$', 'two-body zero-load position regression', 'invalid combination')
        elif not .8 <= np.linalg.norm(q[1] - q[0]) / data['length'][0, 0, 0] <= 1.2:
            fail('$.fields.position', 'distance ratio .8..1.2', 'out of range')
    if action == 2 and (np.any(gravity) or np.any(f)):
        fail('$', 'zero-load velocity regression', 'nonzero load')
    outputs = {'position': descriptions['position']} if action == 1 else {'velocity': descriptions['velocity']} if action == 2 else {
        'acceleration': ('bodies', 'float64', 3, 'm/s^2', 'acceleration')}
    if action == 4 and m:
        outputs['reaction'] = ('links', 'float64', 3, 'N', 'reaction_force')
    if set(meta['outputs']) != set(outputs):
        fail('$.outputs', sorted(outputs), sorted(meta['outputs']))
    else:
        for name, desc in outputs.items():
            description(name, meta['outputs'][name], desc, output=True)
