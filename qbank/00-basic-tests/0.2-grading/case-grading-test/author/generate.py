"""Deterministic infrastructure data, with independently specified P1 witnesses."""
import argparse
from copy import deepcopy
from pathlib import Path

import gmsh
import numpy as np

from caeoj.case_grading import direct_config, prepare_case
from caeoj.sdk import load_problem, write_result
from caeoj.storage import write_hdf5
from caeoj.validation import GMSH_LOCK, write_json
from caeoj_tools.grading_policy import author_policy

TASK = Path(__file__).resolve().parents[1]
CASES = [('01-full', 'full'), ('02-x', 'x'), ('03-y', 'y'), ('04-xy', 'xy'),
         ('05-two-checks', 'split'), ('06-full-and-probes', 'combined')]
SAMPLES = [('01', 'full'), ('02', 'split')]


def make_input(directory, seed):
    directory.mkdir(parents=True)
    width, height = 2.+seed/10, 1.+seed/20
    xy = np.array([[0., 0.], [width, 0.], [width, height], [0., height]])
    tags = [42, 7, 91, 13]
    with GMSH_LOCK:
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.model.add('case-grading-test')
            entity = gmsh.model.addDiscreteEntity(2)
            gmsh.model.mesh.addNodes(2, entity, tags, np.column_stack((xy, np.zeros(4))).ravel())
            gmsh.model.mesh.addElementsByType(entity, 2, [211, 503], [42, 7, 91, 42, 91, 13])
            gmsh.option.setNumber('Mesh.MshFileVersion', 4.1)
            gmsh.option.setNumber('Mesh.Binary', 0)
            gmsh.write(str(directory/'mesh.msh'))
        finally:
            gmsh.finalize()
    # IDs follow the contract; their row order differs from mesh insertion order.
    ids = np.array([7, 13, 42, 91], dtype='int64')
    times = np.array([0., .3+seed/100, 1.1+seed/100], dtype='float64')
    coordinates = {tag: point for tag, point in zip(tags, xy)}
    points = np.array([coordinates[int(tag)] for tag in ids])
    values = np.empty((3, 4, 2), dtype='float64')
    for i, t in enumerate(times):
        x, y = points.T
        values[i,:,0] = 1.+seed*.7+2*t+3*x*y/(width*height)
        values[i,:,1] = -2.+seed*.2-t+4*x-2*y
    spec = dict(array='velocity', quantity='velocity', location='nodes', time_axis='response',
                dtype='float64', kind='vector', component_shape=[2], components=['x','y'],
                unit='m/s', value_kind='point')
    manifest = dict(task='case-grading-test', spatial_dimension=2, data_file='input.h5',
                    geometries={}, meshes={'main': {'file':'mesh.msh'}},
                    locations={'nodes':dict(kind='mesh', mesh='main', entity='node', ids='node_ids')},
                    time_axes={'response':'times'}, fields={'velocity':spec},
                    outputs={'velocity':deepcopy(spec)}, conditions=[])
    write_json(directory/'problem.json', manifest)
    write_hdf5(directory/'input.h5', dict(node_ids=ids, times=times, velocity=values))
    return width, height, ids, times, values


def make_reference(input_dir, reference_dir, seed, mode, geometry, policy):
    width, height, ids, times, values = geometry
    reference_dir.mkdir(parents=True)
    checks = []
    if mode in ('full','combined'):
        problem = load_problem(input_dir/'problem.json')
        write_result(reference_dir/'reference.h5', problem, {'velocity':values})
        checks += direct_config(policy)['checks']
    if mode != 'full':
        # Five points on x=width/2; diagonal and exterior boundary included.
        eta = np.array([0., .25, .5, .75, 1.])
        points = np.column_stack((np.full(5,width/2),eta*height))
        cells = np.where(eta <= .5,211,503).astype('int64')
        observation_ids = np.array([901, 17, 620, 8, 333],dtype='int64')
        write_hdf5(reference_dir/'observations.h5', dict(points=points, ids=observation_ids,
                     times=times, cells=cells))
        # Hand-derived weights on BL, BR, TR, TL, independent of evaluator code.
        weights = np.array([[.5,.5,0.,0.],[.5,.25,.25,0.],[.5,0.,.5,0.],
                            [.25,0.,.5,.25],[0.,0.,.5,.5]])
        rows = [list(ids).index(tag) for tag in [42,7,91,13]]
        expected = np.einsum('pn,tnk->tpk',weights,values[:,rows,:])
        groups = [['x'],['y']] if mode == 'split' else [['x','y'] if mode == 'xy' else ['y'] if mode == 'y' else ['x']]
        refs = dict(ids=observation_ids,times=times)
        for labels in groups:
            key = ''.join(labels)
            refs[key] = expected[:,:,[['x','y'].index(label) for label in labels]]
            checks.append(dict(id='probes-'+key,evaluator='field.sample_points',source_output='velocity',
                components=labels,observations=dict(file='observations.h5',points='points',ids='ids',times='times',cells='cells'),
                reference=dict(file='probe-reference.h5',array=key,ids='ids',times='times',unit='m/s'),
                rule=deepcopy(policy['default'])))
        write_hdf5(reference_dir/'probe-reference.h5',refs)
    write_json(reference_dir/'grading.json',dict(version=1,checks=checks))
    prepared = prepare_case(load_problem(input_dir/'problem.json'),reference_dir/'grading.json')
    assert prepared.evaluate({'node_ids':ids,'times':times,'velocity':values})['score']==1


def generate(destination):
    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('Use an empty destination; generated data is never overwritten')
    policy = author_policy(TASK)
    for seed,(name,mode) in enumerate(CASES,1):
        inp = destination/'cases'/name
        geometry = make_input(inp,seed)
        make_reference(inp,destination/'reference'/name,seed,mode,geometry,policy)
    for seed,(name,mode) in enumerate(SAMPLES,21):
        sample = destination/'samples'/name
        geometry = make_input(sample/'input',seed)
        make_reference(sample/'input',sample/'reference',seed,mode,geometry,policy)
        write_result(sample/'output/result.h5',load_problem(sample/'input/problem.json'),{'velocity':geometry[-1]})
    return {'cases':len(CASES),'samples':len(SAMPLES)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    print(generate(parser.parse_args().output))
