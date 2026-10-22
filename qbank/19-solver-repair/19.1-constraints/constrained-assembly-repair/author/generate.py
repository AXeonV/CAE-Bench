"""Prepare task inputs and independent mechanics checks, not solver references.

Reference HDF5 files must subsequently be produced by the pinned upstream
Chrono implementation using replay.py. The exact-Jacobian calculations here
are independent verification, never labelled as upstream numerical outputs.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
from caeoj.storage import write_hdf5
from caeoj.validation import write_json

TASK = Path(__file__).resolve().parents[1]


def kinematics(q, edges, fixed, masses):
    jac = np.zeros((len(edges), 3 * len(q)))
    directions, lengths = [], []
    for k, (a, b) in enumerate(edges):
        delta = q[b] - q[a]
        length = np.linalg.norm(delta)
        unit = delta / length
        if not fixed[a]: jac[k, 3*a:3*a+3] = -unit
        if not fixed[b]: jac[k, 3*b:3*b+3] = unit
        directions.append(unit)
        lengths.append(length)
    inverse_mass = np.repeat(np.where(fixed, 0., 1. / masses), 3)
    return jac, inverse_mass, np.array(directions), np.array(lengths)


def make_case(name, positions, edges, *, fixed=None, masses=None, gravity=(0, -9.81, 0),
              forces=None, velocities=None, action=4, target_ratio=1., seed=1, note=''):
    q = np.asarray(positions, dtype='float64')
    n = len(q)
    fixed = np.array(fixed if fixed is not None else [True] + [False]*(n-1), dtype=bool)
    masses = np.array(masses if masses is not None else np.ones(n), dtype='float64')
    jac, inverse_mass, directions, lengths = kinematics(q, edges, fixed, masses)
    rng = np.random.default_rng(seed)
    v = np.array(velocities if velocities is not None else rng.normal(size=(n, 3)), dtype='float64')
    v[fixed] = 0.
    gram = (jac * inverse_mass) @ jac.T
    condition = float(np.linalg.cond(gram)) if len(edges) else None
    if len(edges) and condition > 100:
        raise ValueError((name, 'condition', condition))
    if action == 4 and len(edges):
        v = (v.ravel() - inverse_mass * (jac.T @ np.linalg.solve(gram, jac @ v.ravel()))).reshape(n, 3)
    f = np.asarray(forces if forces is not None else np.zeros((n, 3)), dtype='float64')
    f[fixed] = 0.
    ids = np.array([7 + 17*i + 3*i*i for i in range(n)], dtype='int64')
    arrays = {'body_ids': ids, 'times': np.array([0.]), 'mass': masses[None, :, None],
              'fixed': fixed[None, :, None], 'position': q[None, :, :],
              'velocity': v[None, :, :], 'force': f[None, :, :]}
    locations = {'bodies': {'kind': 'entities', 'ids': 'body_ids'}}
    if edges:
        locations['links'] = {'kind': 'entities', 'ids': 'link_ids'}
        arrays.update(link_ids=np.array([103 + i*23 for i in range(len(edges))], dtype='int64'),
                      endpoints=np.array([[ids[a], ids[b]] for a, b in edges], dtype='int64')[None, :, :],
                      length=(lengths * target_ratio)[None, :, None])

    def spec(name, location, dtype, count, unit, quantity=None, output=False):
        record = {'array': name, 'quantity': quantity or name, 'location': location,
                  'time_axis': 'state', 'dtype': dtype, 'kind': 'scalar' if count == 1 else 'vector' if count == 3 else 'components',
                  'component_shape': [count], 'unit': unit, 'value_kind': 'point'}
        record['components'] = ['value'] if count == 1 else list('xyz') if count == 3 else ['first', 'second']
        if not output: record['sampling'] = {'space': 'uniform', 'time': 'constant', 'extrapolation': 'forbid'}
        return record

    fields = {name: spec(name, 'bodies', dtype, count, unit) for name, dtype, count, unit in [
        ('mass', 'float64', 1, 'kg'), ('fixed', 'bool', 1, '1'), ('position', 'float64', 3, 'm'),
        ('velocity', 'float64', 3, 'm/s'), ('force', 'float64', 3, 'N')]}
    if edges:
        fields.update(endpoints=spec('endpoints', 'links', 'int64', 2, '1'),
                      length=spec('length', 'links', 'float64', 1, 'm'))
    if action == 4:
        outputs = {'acceleration': spec('acceleration', 'bodies', 'float64', 3, 'm/s^2', output=True)}
        if edges:
            outputs['reaction'] = spec('reaction', 'links', 'float64', 3, 'N', 'reaction_force', output=True)
        external = f + masses[:, None] * gravity
        acceleration = (inverse_mass * external.ravel())
        if edges:
            curvature = np.array([np.dot(v[b] - v[a], v[b] - v[a]) / length
                                  for (a, b), length in zip(edges, lengths)])
            multipliers = np.linalg.solve(gram, -curvature - jac @ acceleration)
            acceleration += inverse_mass * (jac.T @ multipliers)
            exact = {'acceleration': acceleration.reshape(n, 3).tolist(),
                     'reaction': (multipliers[:, None] * directions).tolist()}
        else:
            exact = {'acceleration': acceleration.reshape(n, 3).tolist()}
    elif action == 2:
        outputs = {'velocity': spec('velocity', 'bodies', 'float64', 3, 'm/s', output=True)}
        projected = v.ravel() - inverse_mass * (jac.T @ np.linalg.solve(gram, jac @ v.ravel()))
        exact = {'velocity': projected.reshape(n, 3).tolist()}
    else:
        outputs = {'position': spec('position', 'bodies', 'float64', 3, 'm', output=True)}
        center = int(np.flatnonzero(fixed)[0])
        moving = int(np.flatnonzero(~fixed)[0])
        answer = q.copy()
        answer[moving] = q[center] + (q[moving] - q[center]) * target_ratio
        exact = {'position': answer.tolist()}
    parameters = {'action': {'value': action, 'unit': '1'}}
    parameters.update({'gravity_' + axis: {'value': float(value), 'unit': 'm/s^2'} for axis, value in zip('xyz', gravity)})
    manifest = {'task': 'constrained-assembly-repair', 'spatial_dimension': 3, 'data_file': 'input.h5',
                'geometries': {}, 'meshes': {}, 'locations': locations, 'time_axes': {'state': 'times'},
                'fields': fields, 'outputs': outputs, 'conditions': [],
                'physics': {'model': 'constrained-assembly-v1', 'parameters': parameters}}
    return {'name': name, 'manifest': manifest, 'arrays': arrays, 'exact': exact,
            'condition': condition, 'note': note, 'action': action}


def cases():
    zero = (0., 0., 0.)
    out = []
    add = lambda *a, **kw: out.append(make_case(*a, **kw))
    add('01-pendulum-public', [[0,0,0],[.6,-.8,0]], [(0,1)], velocities=[[0,0,0],[1.6,1.2,0]],
        note='Public moving pendulum; centripetal acceleration and vector reaction.')
    add('02-position-public', [[.1,.2,-.3],[.9,-.4,.3]], [(0,1)], gravity=zero, velocities=np.zeros((2,3)),
        action=1, target_ratio=.9, note='Public position assembly from an incompatible initial guess.')
    add('03-resting-load', [[0,0,0],[.6,-.8,0]], [(0,1)], velocities=np.zeros((2,3)), note='At-rest non-regression.')
    add('04-zero-gravity', [[0,0,0],[0,1.7,0]], [(0,1)], gravity=zero, velocities=[[0,0,0],[3,0,1]], note='Pure curvature force without gravity.')
    add('05-two-link-chain', [[0,0,0],[1,0,0],[1,1.2,.4]], [(0,1),(1,2)], masses=[1,1,3], seed=4,
        note='Shared moving endpoint and unequal masses require a coupled solve.')
    add('06-free-triangle', [[0,0,0],[1,0,0],[.3,1.1,.4]], [(0,1),(1,2),(2,0)], fixed=[False]*3,
        masses=[.7,2,4], gravity=(1,-3,2), seed=6, note='Unanchored closed constraint network with global free translation.')
    add('07-two-anchors', [[0,0,0],[1,1,0],[1,0,.6]], [(0,2),(1,2)], fixed=[True,True,False], seed=7,
        note='Two independent constraints reduce one body motion to an intersection tangent.')
    add('08-branched-tree', [[0,0,0],[1,0,0],[1,1,0],[1,0,1]], [(0,1),(1,2),(1,3)], masses=[1,.2,5,1.3], seed=8,
        note='Branch coupling and mass weighting; not a repeated single pendulum.')
    add('09-disconnected-free-body', [[0,0,0],[0,-1,0],[2,1,.5]], [(0,1)], forces=[[0,0,0],[1,0,0],[4,2,-3]], seed=9,
        note='Constrained and unconstrained active bodies in the same system.')
    add('10-fixed-second-endpoint', [[.2,-1.3,.7],[.1,.2,.3]], [(0,1)], fixed=[False,True], masses=[2,1], seed=10,
        note='Force acts on the fixed second endpoint; tests sign and global frame.')
    add('11-long-scale', [[0,0,0],[3,-4,0]], [(0,1)], velocities=[[0,0,0],[2.4,1.8,0]], masses=[1,4],
        note='Length-scale sensitivity of constraint differencing at 5 m.')
    add('12-short-scale', [[0,0,0],[0,.2,0]], [(0,1)], velocities=[[0,0,0],[2,0,1]], masses=[1,.2],
        note='Small radius and high curvature acceleration.')
    add('13-free-system', [[.2,.4,-.1],[1,2,3]], [], fixed=[False,False], masses=[.3,4], forces=[[2,-1,3],[-4,8,1]], seed=13,
        note='No constraints; retains force-over-mass behavior.')
    add('14-loaded-network', [[0,0,0],[1,.2,.3],[1.5,1.2,.7]], [(0,1),(1,2)], masses=[1,2,3],
        forces=[[0,0,0],[4,-2,5],[-3,6,2]], gravity=(2,-7,1), seed=14, note='External load, non-axis gravity and coupled force balance.')
    add('15-spatial-chain', [[0,0,0],[.6,.3,.8],[1.4,-.2,1.4],[1.8,.7,2.1]], [(0,1),(1,2),(2,3)],
        masses=[1,1.1,2.3,.8], seed=15, note='Three coupled spatial constraints.')
    q = [[0,0,0],[1,0,0],[1,1,0],[1,0,1],[2,1,.3],[2,.2,1.3],[2,1.2,1.4],[3,1.3,1.5]]
    add('16-larger-tree', q, [(0,1),(1,2),(1,3),(2,4),(3,5),(4,6),(6,7)], masses=[1,1,2,3,.8,1.5,2.2,.9], seed=16,
        note='Eight-body branched tree tests accumulation across several coupled constraints.')
    add('17-position-outward', [[.4,-.3,.5],[1.1,.1,.2]], [(1,0)], fixed=[False,True], gravity=zero,
        velocities=np.zeros((2,3)), action=1, target_ratio=1.1, note='Outward position correction and reversed endpoint order.')
    add('18-velocity-single', [[0,0,0],[.5,-1,.4]], [(0,1)], gravity=zero, action=2, seed=18,
        note='Remove normal velocity while preserving tangent motion.')
    add('19-velocity-coupled', [[0,0,0],[1,.2,.3],[1.3,1.2,.4]], [(0,1),(1,2)], gravity=zero,
        masses=[1,.4,4], action=2, seed=19, note='Simultaneous mass-weighted velocity projection.')
    add('20-velocity-free-network', [[0,0,0],[1,.2,.3],[1.3,1.2,.4]], [(0,1),(1,2)], fixed=[False]*3, gravity=zero,
        masses=[.8,2,4], action=2, seed=20, note='Projection preserves free-system momentum with unequal masses.')
    return out


def generate(destination):
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Refusing to overwrite an existing dataset')
    records = []
    for case in cases():
        directory = destination / 'cases' / case['name']
        directory.mkdir(parents=True)
        write_json(directory / 'problem.json', case['manifest'])
        write_hdf5(directory / 'input.h5', case['arrays'])
        checks = destination / 'independent-checks'
        checks.mkdir(exist_ok=True)
        write_json(checks / (case['name'] + '.json'), case['exact'])
        records.append({key: case[key] for key in ('name', 'condition', 'note', 'action')})
    write_json(destination / 'cases.json', {'cases': records, 'public_cases': [records[0]['name'], records[1]['name']]})
    print(json.dumps({'inputs': len(records), 'references': 0, 'output': str(destination)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    generate(args.output)
