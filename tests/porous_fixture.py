"""Disposable porous protocol fixtures, not benchmark cases or physical references."""
from collections import Counter
from itertools import combinations
from pathlib import Path
import json

import gmsh
import h5py
import numpy as np

from caeoj_ext.porous import labels, models


def fixture(base, slug):
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    cfg = models()[slug]
    coordinates = {11 + 7 * (4 * j + i): [float(i), float(j), 0.]
                   for j in range(4) for i in range(4)}
    node = lambda i, j: 11 + 7 * (4 * j + i)
    triangles = {}
    for j in range(3):
        for i in range(3):
            for vertices in [(node(i,j), node(i+1,j), node(i+1,j+1)),
                             (node(i,j), node(i+1,j+1), node(i,j+1))]:
                triangles[201 + 3 * len(triangles)] = vertices
    edges = Counter(tuple(sorted(edge)) for vertices in triangles.values()
                    for edge in combinations(vertices, 2))
    exterior = {501 + 5*i: edge for i, (edge, count) in enumerate(edges.items()) if count == 1}
    fracture = {901: (node(1,1), node(2,1))} if cfg['family'] == 'fracture' else {}
    gmsh.initialize([], readConfigFiles=False)
    try:
        gmsh.option.setNumber('General.Terminal', 0)
        gmsh.model.add('disposable_porous_protocol')
        surface = gmsh.model.addDiscreteEntity(2)
        gmsh.model.mesh.addNodes(2, surface, list(coordinates), np.array(list(coordinates.values())).ravel())
        gmsh.model.mesh.addElementsByType(surface, 2, list(triangles), np.array(list(triangles.values())).ravel())
        for tag, vertices in {**exterior, **fracture}.items():
            curve = gmsh.model.addDiscreteEntity(1)
            gmsh.model.mesh.addElementsByType(curve, 1, [tag], list(vertices))
        gmsh.option.setNumber('Mesh.MshFileVersion', 4.1)
        gmsh.option.setNumber('Mesh.Binary', 0)
        gmsh.write(str(base / 'mesh.msh'))
    finally:
        gmsh.finalize()
    arrays, locations = {}, {}

    def location(name, tags, entity, dimension=None):
        arrays[name + '_ids'] = np.array(sorted(tags), dtype=np.int64)
        locations[name] = dict(kind='mesh', mesh='main', entity=entity, ids=name + '_ids')
        if dimension is not None:
            locations[name]['dimension'] = dimension

    location('domain', coordinates, 'node')
    location('cells', triangles, 'element', 2)
    location('fixed', [node(0,j) for j in range(4)], 'node')
    location('boundary', exterior, 'element', 1)
    if fracture:
        location('fractures', fracture, 'element', 1)
    if cfg['family'] == 'pore':
        arrays['mean_ids'] = np.array([7], dtype=np.int64)
        locations['mean'] = dict(kind='aggregate', source='cells', operation='mean', ids='mean_ids')
    axes = dict(steady='steady_times') if cfg['steady'] else dict(initial='initial_times', response='requested_times', loads='loading_times')
    arrays.update(steady_times=np.array([0.]), initial_times=np.array([0.]),
                  requested_times=np.array([.2, 1.]), loading_times=np.array([0., .4, 1.]))
    parameter_values = dict(start_time=0., end_time=1., density=1000., viscosity=.001,
                            gravity_x=0., gravity_y=-9.81, pressure_mean=0., density_w=1000., density_n=700.,
                            viscosity_w=.001, viscosity_n=.002, reference_pressure=1e5,
                            pressure_min=1e4, pressure_max=1e6, compressibility_w=1e-9, compressibility_n=2e-9)
    manifest = dict(task=slug, spatial_dimension=2, data_file='input.h5', geometries={},
                    meshes=dict(main=dict(file='mesh.msh')), locations=locations, time_axes=axes,
                    fields={}, outputs={}, physics=dict(model=f'porous-{slug}-v1', parameters={
                        key: dict(value=parameter_values[key], unit=s['unit']) for key, s in cfg['parameters'].items()}), conditions=[])

    def record(op, site=None):
        rule = cfg['records'][op]
        site = site or dict(cells='cells', domain='domain', nodes='fixed', facets='boundary', fractures='fractures')[rule['where']]
        data = {}
        for key, spec in rule['data'].items():
            if 'option' in spec:
                data[key] = dict(option=spec['option'])
                continue
            axis = 'steady' if cfg['steady'] else 'initial' if rule['static'] else 'loads'
            count = len(arrays[locations[site]['ids']])
            values = np.zeros((len(arrays[axes[axis]]), count, *spec['shape']), dtype=np.float64)
            if spec['kind'] == 'tensor':
                values[:] = np.eye(2) * (1e-5 if key == 'hydraulic_conductivity' else 1e-10)
            elif spec.get('positive'):
                values[:] = 1e-3
            if 'lower' in spec:
                values[:] = max(spec['lower'], .1)
            if key == 'porosity':
                values[:] = .3
            if key in ('retention_n',):
                values[:] = 2.
            if key in ('residual_w', 'residual_n', 'residual_water'):
                values[:] = .05
            if key in ('wetting_pressure',) or key == 'value' and 'pressure' in rule['variable']:
                values[:] = 1e5
            if rule['variable'] == 'pressure_head':
                values[:] = 0.
            if key == 'wetting_saturation':
                values[:] = .5
            if key == 'capillary_scale':
                values[:] = 1000.
            if key == 'tangential_permeability':
                values[:] = 1e-8
            if key in ('longitudinal_dispersivity', 'transverse_dispersivity'):
                values[:] = .1 if key.startswith('long') else .01
            name = op + '_' + key
            array = 'payload_' + name
            arrays[array] = values
            element = locations[site]['entity'] == 'element'
            manifest['fields'][name] = dict(array=array, quantity=rule['variable'] if key == 'value' else key,
                unit=spec['unit'], kind=spec['kind'], component_shape=spec['shape'], components=labels(spec),
                dtype='float64', location=site, time_axis=axis, value_kind='average' if element else 'point',
                sampling=dict(space='piecewise_constant' if element else 'piecewise_linear',
                              time='constant' if len(values) == 1 else 'linear', extrapolation='forbid'))
            data[key] = dict(field=name)
        manifest['conditions'].append(dict(role=rule['role'], variable=rule['variable'], location=site, operator=op, data=data))

    for op, rule in cfg['records'].items():
        if rule['required']:
            record(op)
    for quantity, spec in cfg['outputs'].items():
        manifest['outputs']['requested_' + quantity] = dict(array='answer_' + quantity, quantity=quantity,
            unit=spec['unit'], kind=spec['kind'], component_shape=spec['shape'], components=labels(spec),
            dtype='float64', location=spec['where'], time_axis='steady' if cfg['steady'] else 'response', value_kind='average')
    used = set(axes.values()) | {s['ids'] for s in locations.values()} | {s['array'] for s in manifest['fields'].values()}
    with h5py.File(base / 'input.h5', 'w') as h:
        for key in used:
            h[key] = arrays[key]
    path = base / 'problem.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    return path, manifest


def replace_manifest(path, manifest):
    path.write_text(json.dumps(manifest), encoding='utf-8')
