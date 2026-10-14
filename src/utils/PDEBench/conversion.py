"""Structured Gmsh/JSON/HDF5 conversion and an exact advection reference."""
from caeoj.storage import write_hdf5
import hashlib
import json
from pathlib import Path

import gmsh
import numpy as np

from caeoj.sdk import load_problem, load_result, write_result
from caeoj.validation import GMSH_LOCK
from .models import constant, parameters
from .storage import PreparationError, atomic_json, digest


def check_reference_initial(model, problem, values):
    """Compare t=0 on the explicitly identified output entities, including subsets."""
    manifest=problem.manifest
    for output,initial,_,_ in model.fields:
        if not initial:continue
        field=manifest['fields'][initial]
        expected=problem.arrays[field['array']]
        initial_ids=problem.arrays[manifest['locations'][field['location']]['ids']]
        output_ids=problem.arrays[manifest['locations'][manifest['outputs'][output]['location']]['ids']]
        if not np.array_equal(initial_ids,output_ids):
            positions=np.searchsorted(initial_ids,output_ids)
            if (np.any(positions>=len(initial_ids)) or
                not np.array_equal(initial_ids[positions],output_ids)):
                raise PreparationError('Reference output entities are not in the initial location')
            expected=expected[:,positions,:]
        if not np.array_equal(values[output][0:1],expected):
            raise PreparationError('Reference t=0 does not match the contracted initial data')


def make_mesh(path, shape, bounds, sparse=False):
    """Bulk-build aligned line/quad/hex cells, with C-order IDs and side groups."""
    dimension = len(shape)
    edges = [np.linspace(lo, hi, n+1) for n, (lo, hi) in zip(shape, bounds)]
    grid = np.meshgrid(*edges, indexing='ij')
    coords = np.zeros((np.prod([n+1 for n in shape]), 3))
    for axis, values in enumerate(grid): coords[:, axis] = values.ravel()
    node_ids = np.arange(1, len(coords)+1, dtype=np.int64)
    if sparse: node_ids = 100 + 3*node_ids
    lattice = node_ids.reshape(tuple(n+1 for n in shape))
    offsets = {1: [(0,), (1,)], 2: [(0,0),(1,0),(1,1),(0,1)],
               3: [(0,0,0),(1,0,0),(1,1,0),(0,1,0),
                   (0,0,1),(1,0,1),(1,1,1),(0,1,1)]}[dimension]
    connectivity = np.stack([lattice[tuple(slice(o, o+n) for o,n in zip(off, shape))].ravel()
                             for off in offsets], axis=1)
    ids = np.arange(1, len(connectivity)+1, dtype=np.int64)
    if sparse: ids = 100 + 3*ids
    sides = {}
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.model.add('pdebench-grid')
            domain = gmsh.model.addDiscreteEntity(dimension, 1)
            gmsh.model.mesh.addNodes(dimension, domain, node_ids.tolist(), coords.ravel().tolist())
            gmsh.model.mesh.addElementsByType(domain, {1:1,2:3,3:5}[dimension], ids.tolist(), connectivity.ravel().tolist())
            gmsh.model.addPhysicalGroup(dimension, [domain], 1, 'domain')
            next_element = int(ids[-1])+1
            for axis in range(dimension):
                for upper in (0,1):
                    side_name = (('left','right'),('bottom','top'),('front','back'))[axis][upper]
                    face = np.take(lattice, shape[axis] if upper else 0, axis=axis)
                    side_nodes = np.unique(face)
                    tag = 2 + axis*2 + upper
                    entity = gmsh.model.addDiscreteEntity(dimension-1, tag)
                    if dimension == 1:
                        conn = face.reshape(1,1)
                    elif dimension == 2:
                        conn = np.stack([face[:-1], face[1:]], axis=1)
                    else:
                        conn = np.stack([face[:-1,:-1].ravel(),face[1:,:-1].ravel(),
                                         face[1:,1:].ravel(),face[:-1,1:].ravel()],axis=1)
                    tags = np.arange(next_element,next_element+len(conn),dtype=np.int64)
                    next_element += len(conn)
                    gmsh.model.mesh.addElementsByType(entity,{1:15,2:1,3:3}[dimension],tags.tolist(),conn.ravel().tolist())
                    gmsh.model.addPhysicalGroup(dimension-1,[entity],tag,side_name)
                    sides[side_name] = (tag,side_nodes)
            gmsh.option.setNumber('Mesh.MshFileVersion',4.1)
            gmsh.option.setNumber('Mesh.Binary',0)
            gmsh.option.setNumber('Mesh.SaveAll',1)
            gmsh.write(str(path))
        finally:
            gmsh.finalize()
    return ids, sides


def field(name, quantity, unit, components, model, location='domain', axis='initial'):
    vector = quantity in ('velocity','momentum','forcing','mass_weighted_velocity')
    return {'array':name,'quantity':quantity,'location':location,'time_axis':axis,
            'dtype':'float64','kind':'vector' if vector else 'scalar',
            'component_shape':[components],
            'components':list('xyz'[:components]) if vector else ['value'],
            'unit':unit,'value_kind':'point' if model.points or location!='domain' else 'average'}


def advection_average(initial, times, speed, length=1.):
    """Integrate a periodic piecewise-constant initial field over shifted cells."""
    u = np.asarray(initial,dtype=np.float64).reshape(-1)
    n = len(u)
    dx = length/n
    integral = np.concatenate(([0.], np.cumsum(u)*dx))
    def primitive(x):
        turns = np.floor(x/length)
        r = x-turns*length
        cell = np.minimum((r/dx).astype(np.int64),n-1)
        return turns*integral[-1]+integral[cell]+u[cell]*(r-cell*dx)
    edges = np.arange(n+1)*dx
    result = np.stack([np.diff(primitive(edges-speed*t))/dx for t in times])
    result[0] = u
    return result[...,None]


def build_input(model, source, coords, times, values, destination, variant=0, config=None):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    shape = tuple(len(c) for c in coords)
    for name,value in values.items():
        if value.shape[1:-1] != shape:
            raise PreparationError(f"Source spatial shape mismatch for {name}: {value.shape}, {shape}")
    initial_values=values;initial_shape=shape;sample_axes=None
    if model.model=='reaction_diffusion_2d' and config is not None:
        from .source_audit import fhn_initial
        initial_shape,sample_axes,initial_values=fhn_initial(coords,values,config)
    all_ids,sides = make_mesh(destination/'mesh.msh',initial_shape,model.bounds, sparse=bool(variant%2))
    ids=all_ids if sample_axes is None else all_ids.reshape(initial_shape)[np.ix_(*sample_axes)].ravel()
    arrays = {'times':np.asarray(times,dtype=np.float64)}
    locations = {}
    if model.points:
        arrays['point_ids'] = np.arange(len(ids),dtype=np.int64)
        points = np.meshgrid(*coords,indexing='ij')
        arrays['point_coordinates'] = np.stack([p.ravel() for p in points],axis=1)
        locations['domain'] = {'kind':'points','ids':'point_ids','coordinates':'point_coordinates'}
    else:
        arrays['cell_ids'] = ids
        locations['domain'] = {'kind':'mesh','mesh':'main','entity':'element',
                               'dimension':model.dimension,'ids':'cell_ids',
                               'physical_group':{'dimension':model.dimension,'tag':1}}
    initial_location='domain'
    if sample_axes is not None:
        initial_location='initial_domain'
        arrays['initial_cell_ids']=all_ids
        locations['initial_domain']={**locations['domain'],'ids':'initial_cell_ids'}
        locations['domain'].pop('physical_group')
    if model.model=='darcy_flow_2d':
        arrays['coefficient_ids']=ids.copy()
        points=np.meshgrid(*coords,indexing='ij')
        arrays['coefficient_coordinates']=np.stack([p.ravel() for p in points],axis=1)
        locations['coefficient_samples']={'kind':'points','ids':'coefficient_ids','coordinates':'coefficient_coordinates'}
    metadata = {'task':model.task,'spatial_dimension':model.dimension,'data_file':'input.h5',
                'geometries':{},'meshes':{'main':{'file':'mesh.msh'}},'locations':locations,
                'time_axes':{'output':'times'},'fields':{},'outputs':{},
                'physics':{'model':model.model,'parameters':parameters(model,source)},'conditions':[]}
    def condition(role,variable,operator,data,loc='domain'):
        metadata['conditions'].append({'role':role,'variable':variable,'location':loc,
                                       'operator':operator,'data':data})
    def add(name,quantity,unit,c,data,loc='domain',axis='initial'):
        arrays[name]=np.asarray(data,dtype=np.float64)
        metadata['fields'][name]=field(name,quantity,unit,c,model,loc,axis)
    steady = model.model=='darcy_flow_2d'
    if not steady:
        arrays['initial_times']=np.array([0.],dtype=np.float64)
        metadata['time_axes']['initial']='initial_times'
    for output,initial,unit,c in model.fields:
        metadata['outputs'][output]=field(output,output,unit,c,model,axis='output')
        if model.model.startswith('compressible_') and output in ('velocity','pressure'):
            metadata['outputs'][output]['quantity']='mass_weighted_velocity' if output=='velocity' else 'conservative_pressure'
        if initial:
            add(initial,output,unit,c,initial_values[output][0:1].reshape(1,-1,c),initial_location)
            if initial_location=='initial_domain':metadata['fields'][initial]['value_kind']='average'
            condition('initial',output,'project_preserve_snapshot' if model.points else 'assign',{'value':{'field':initial}},initial_location)
    periodic = model.model in ('advection_1d','burgers_1d','reaction_diffusion_1d') or (
        model.model.startswith('compressible_') and 'trans' not in source['filename'] and not source['filename'].startswith('Sod'))
    if periodic:
        variable = 'fluid_state' if model.model.startswith('compressible_') else 'state'
        condition('boundary',variable,'periodic',
                  {'period_'+axis:constant(hi-lo,'m') for axis,(lo,hi) in zip('xyz',model.bounds)})
    else:
        for side,(tag,nodes) in sides.items():
            arrays[side+'_ids']=nodes
            locations[side]={'kind':'mesh','mesh':'main','entity':'node','ids':side+'_ids',
                             'physical_group':{'dimension':model.dimension-1,'tag':tag}}
        if steady:
            add('diffusivity','diffusivity','m2/s',1,values['diffusivity'].reshape(1,-1,1),loc='coefficient_samples',axis='output')
            condition('material','state','assign',{'value':{'field':'diffusivity'}},'coefficient_samples')
            condition('source','state','assign',{'value':metadata['physics']['parameters']['source_strength']})
            for side in sides:condition('boundary','state','cell_coupled_dirichlet',
                                       {'external_value':constant(0,'1'),'cell_weight':constant(.5,'1')},side)
        elif model.model=='diffusion_sorption_1d':
            condition('boundary','concentration','cell_coupled_dirichlet',
                      {'external_value':constant(1,'1'),'cell_weight':constant(.5,'1')},'left')
            condition('boundary','concentration','outlet_cell_coupling',
                      {'length':constant(.0005,'m')},'right')
        elif model.model=='reaction_diffusion_2d':
            for side in sides:
                for variable in ('activator','inhibitor'):
                    condition('boundary',variable,'normal_flux',{'value':constant(0,'m/s')},side)
        elif model.model=='shallow_water_2d':
            add('initial_momentum','momentum','m2/s',2,np.zeros((1,len(ids),2)))
            condition('initial','momentum','assign',{'value':{'field':'initial_momentum'}})
            for side in sides: condition('boundary','depth_momentum','extrapolate',{'order':constant(0,'1')},side)
        elif model.points:
            add('initial_tracer','tracer','1',1,values['tracer'][0:1].reshape(1,-1,1))
            add('forcing','forcing','m/s2',2,values['forcing'].reshape(1,-1,2))
            condition('initial','tracer','assign',{'value':{'field':'initial_tracer'}})
            condition('source','velocity','tracer_force',{'value':{'field':'forcing'}})
            arrays['condition_times']=np.array([0.]);metadata['time_axes']['conditions']='condition_times'
            for side,(_,nodes) in sides.items():
                name='wall_velocity_'+side
                add(name,'velocity','m/s',2,np.zeros((1,len(nodes),2)),side,'conditions')
                condition('boundary','velocity','dirichlet',{'value':{'field':name}},side)
            condition('boundary','kinematic_pressure','mean',{'value':constant(0,'m2/s2')})
        else:
            for side in sides: condition('boundary','fluid_state','extrapolate',{'order':constant(0,'1')},side)
    write_hdf5(destination / 'input.h5', arrays)
    atomic_json(destination/'problem.json',metadata)
    problem=load_problem(destination/'problem.json')
    return problem


def write_analytic_reference(problem,path):
    initial=problem.arrays['initial_state']
    speed=problem.manifest['physics']['parameters']['velocity']['value']
    values=advection_average(initial,problem.arrays['times'],speed)
    write_result(path,problem,{'state':values})
    load_result(problem,path)
    return {'method':'exact_periodic_piecewise_constant_cell_integrals',
            'model':'advection_1d','kind':'analytic','floating_point_roundoff_only':True}


def input_identity(problem):
    """Bind reference evidence to the actual input files and current contract."""
    path=problem.path
    return {name:digest(path.parent/name) for name in ('problem.json','input.h5','mesh.msh')}
