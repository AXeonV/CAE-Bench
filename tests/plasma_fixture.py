"""Disposable protocol payloads, not formal plasma cases or reference solutions."""
import json
from pathlib import Path

import gmsh
import h5py
import numpy as np

from caeoj_ext.plasma import models, component_labels, component_shape


def fixture(base, slug):
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    cfg = models()[slug]
    defaults = dict(end_time=.1, state_count=3, neutral_density=100., elementary_charge=1.,
                    velocity_count=8, velocity_min=-2., velocity_max=2., mass=1., charge=-1.,
                    permittivity=1., injection_energy=1., particle_flux=.01,
                    angular_frequency=1., permeability=1.)
    p = {key: defaults[key] for key in cfg['parameters']}
    if slug == 'magnetized-plasma-slab':
        p.update(permittivity=1e-11, permeability=1e-6, angular_frequency=1e6, mass=9e-31, charge=-1.6e-19)
    arrays = {'initial_time': np.array([0.]), 'output_time': np.array([0.] if cfg.get('steady') else [0., .03, .1])}
    axes = dict(initial='initial_time', output='output_time')
    if cfg['driven']:
        arrays['drive_time'] = np.array([0., .1])
        axes['drive'] = 'drive_time'
    locations = {}
    for key, spec in cfg['locations'].items():
        if spec['kind'] == 'mesh':
            continue
        n = 1 if key == 'system' else 3 if key == 'states' else 2
        arrays[key + '_ids'] = np.arange(n, dtype='int64') if key == 'states' else np.arange(n, dtype='int64') * 7 + 4
        locations[key] = dict(kind=spec['kind'], ids=key + '_ids')
        if spec['kind'] == 'points':
            arrays[key + '_coordinates'] = np.array([[.25], [1.25]])
            locations[key]['coordinates'] = key + '_coordinates'
    meshes = {}
    if cfg['mesh']:
        # Tags deliberately do not follow x order. Both line orientations occur.
        node_tags = [11, 37, 83]
        coordinates = [1., 0., 0., 0., 0., 0., .5, 0., 0.]
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.model.add('plasma_protocol_fixture')
            entity = gmsh.model.addDiscreteEntity(1)
            gmsh.model.mesh.addNodes(1, entity, node_tags, coordinates)
            gmsh.model.mesh.addElementsByType(entity, 1, [101, 173], [11, 83, 37, 83])
            gmsh.option.setNumber('Mesh.MshFileVersion', 4.1)
            gmsh.option.setNumber('Mesh.Binary', 0)
            gmsh.write(str(base / 'mesh.msh'))
        finally:
            gmsh.finalize()
        meshes = {'main': {'file': 'mesh.msh'}}
        for key, ids in [('domain', [11, 37, 83]), ('cells', [101, 173]), ('left', [37]), ('right', [11])]:
            if key not in cfg['locations']:
                continue
            arrays[key + '_ids'] = np.array(ids, dtype='int64')
            locations[key] = dict(kind='mesh', mesh='main', entity=cfg['locations'][key]['entity'], ids=key + '_ids')
            if key == 'cells':
                locations[key]['dimension'] = 1
    manifest = dict(task=slug, spatial_dimension=cfg['spatial_dimension'], data_file='input.h5',
                    geometries={}, meshes=meshes, locations=locations, time_axes=axes, fields={}, outputs={},
                    physics=dict(model=f'plasma-{slug}-v1', parameters={key: dict(value=v, unit=cfg['parameters'][key]['unit']) for key, v in p.items()}),
                    conditions=[])
    for op, rec in cfg['records'].items():
        loc = rec['location']
        count = len(arrays[locations[loc]['ids']])
        data = {}
        for key, spec in rec['data'].items():
            values = np.zeros((len(arrays[axes[spec['axis']]]), count, *component_shape(spec, p)))
            if spec.get('positive') or key in ('mass', 'density'):
                values[:] = 1.
            if key == 'charge':
                values[:] = -1.
            if slug == 'plasma-chemistry' and op == 'initial':
                values[:] = [.1, .1, 0.]
            if slug == 'collisional-states':
                if op == 'population':
                    values[:] = np.array([1., 0., 0.]).reshape(1, 3, 1)
                if op == 'transitions':
                    values[:] = np.array([[0., 2., 0.], [0., 0., 3.], [1., 0., 0.]])
                if op == 'states':
                    values[:] = [[1., 0., 0.], [0., 2., 0.], [0., 0., -3.]]
            if slug == 'vlasov-poisson':
                values[:] = .25
            if op == 'right_potential':
                values[:] = .5
            if op == 'incident':
                values[..., 0, 0] = 1.
            if slug == 'magnetized-plasma-slab' and op == 'layers':
                if key == 'density':
                    values[:] = 1e10
                if key == 'collision_frequency':
                    values[:] = 1e5
            logical = f'{op}_{key}'
            array = 'payload_' + logical
            arrays[array] = values
            manifest['fields'][logical] = dict(array=array, quantity=rec['variable'] if key == 'value' else key,
                unit=spec['unit'], kind=spec['kind'], component_shape=component_shape(spec, p),
                components=component_labels(spec, p, cfg['spatial_dimension']), dtype='float64', location=loc,
                time_axis=spec['axis'], value_kind='average' if loc == 'cells' else 'point',
                sampling=dict(space='piecewise_constant' if loc == 'cells' else 'piecewise_linear' if loc == 'domain' else 'uniform',
                              time='linear' if spec['axis'] == 'drive' else 'constant', extrapolation='forbid'))
            data[key] = {'field': logical}
        manifest['conditions'].append(dict(role=rec['role'], variable=rec['variable'], operator=op, location=loc, data=data))
    for quantity, spec in cfg['outputs'].items():
        manifest['outputs']['request_' + quantity] = dict(array='answer_' + quantity, quantity=quantity,
            unit=spec['unit'], kind=spec['kind'], component_shape=component_shape(spec, p),
            components=component_labels(spec, p, cfg['spatial_dimension']), dtype='float64',
            location=spec['location'], time_axis='output', value_kind='average' if spec['location'] == 'cells' else 'point')
    with h5py.File(base / 'input.h5', 'w') as h5:
        for key, values in arrays.items():
            h5[key] = values
    path = base / 'problem.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    return path, manifest
