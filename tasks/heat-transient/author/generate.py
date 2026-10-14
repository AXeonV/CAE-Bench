"""Generate transient inputs and converged continuum-series references."""
from caeoj.storage import write_hdf5
import argparse
import json
from pathlib import Path
import shutil

import numpy as np

from caeoj.grading import grade_files
from caeoj.sdk import load_problem, write_result
from caeoj.validation import write_json
from catalog import CASES, SIDES
from mesh import generate_mesh, read_mesh
from oracle import reference

ROOT = Path(__file__).resolve().parents[1]


def scalar_field(name, location, time_axis, unit, value_kind):
    return {'array': name, 'quantity': 'temperature', 'location': location,
            'time_axis': time_axis, 'dtype': 'float64', 'kind': 'scalar',
            'component_shape': [1], 'components': ['value'], 'unit': unit,
            'value_kind': value_kind}


def generate_case(case, destination):
    directory = destination/'cases'/case.name
    generate_mesh(case, directory)
    ids, xy, elements, groups = read_mesh(directory/'mesh.msh')
    from catalog import initial_values
    values = initial_values(case, xy)
    scale = max(case.size)**2*case.capacity/case.k
    arrays = {'node_ids': ids, 'initial_times': np.array([0.0], dtype=np.float64),
              'times': np.array(case.epochs, dtype=np.float64)*scale,
              'initial_temperature': values[None, :, None]}
    locations = {'nodes': {'kind': 'mesh', 'mesh': 'main', 'entity': 'node', 'ids': 'node_ids'}}
    for name, dim, tag in [('domain', 2, 1), *[(s, 1, i) for i, s in enumerate(SIDES, 2)]]:
        arrays[name+'_ids'] = groups[dim, tag]
        locations[name] = {'kind': 'mesh', 'mesh': 'main', 'entity': 'element',
                           'dimension': dim, 'ids': name+'_ids',
                           'physical_group': {'dimension': dim, 'tag': tag}}
    initial = scalar_field('initial_temperature', 'nodes', 'initial', 'K', 'point')
    output = scalar_field('temperature', 'nodes', 'output', 'K', 'point')
    parameters = {}
    for name, value, unit in [('conductivity', case.k, 'W/(m.K)'),
                              ('volumetric_heat_capacity', case.capacity, 'J/(m3.K)'),
                              ('x0', case.origin[0], 'm'), ('y0', case.origin[1], 'm'),
                              ('length_x', case.size[0], 'm'), ('length_y', case.size[1], 'm')]:
        parameters[name] = {'value': value, 'unit': unit}
    conditions = [{'role': 'initial', 'variable': 'temperature', 'location': 'nodes',
                   'operator': 'assign', 'data': {'value': {'field': 'initial_temperature'}}}]
    for i, (side, op) in enumerate(zip(SIDES, case.boundaries)):
        unit = 'K' if op == 'dirichlet' else 'K/m' if op == 'normal_derivative' else 'W/m2'
        data = {'value': {'value': 0.0, 'unit': unit}}
        if op == 'robin':
            data['alpha'] = {'value': case.alpha[i], 'unit': 'W/(m2.K)'}
            data['beta'] = {'value': case.beta[i], 'unit': 'W/(m.K)'}
        conditions.append({'role': 'boundary', 'variable': 'temperature', 'location': side,
                           'operator': op, 'data': data})
    manifest = {'task': 'heat-transient', 'spatial_dimension': 2, 'data_file': 'input.h5',
                'geometries': {'rectangle': {'file': 'mesh.geo', 'format': 'gmsh-geo'}},
                'meshes': {'main': {'file': 'mesh.msh', 'geometry': 'rectangle'}},
                'locations': locations, 'time_axes': {'initial': 'initial_times', 'output': 'times'},
                'fields': {'initial_temperature': initial}, 'outputs': {'temperature': output},
                'physics': {'model': 'transient_heat_conduction', 'parameters': parameters},
                'conditions': conditions}
    write_json(directory/'problem.json', manifest)
    write_hdf5(directory / 'input.h5', arrays, compression="gzip")
    problem = load_problem(directory/'problem.json')
    temperature, certificate = reference(problem, xy, elements)
    reference_dir = destination/'reference'/case.name
    write_result(reference_dir/'reference.h5', problem, {'temperature': temperature})
    cell_vertices = xy[elements[2][1]]
    twice_area = np.abs(np.linalg.det(np.concatenate([np.ones((*cell_vertices.shape[:2], 1)), cell_vertices], axis=2)))
    lengths = np.linalg.norm(cell_vertices[:, [1, 2, 0]]-cell_vertices, axis=2)
    record = {'case': case.name, 'initial_recipe': case.profile,
              'boundary_operators': dict(zip(SIDES, case.boundaries)),
              'nodes': len(ids), 'triangles': len(elements[2][0]),
              'minimum_triangle_area_m2': float(np.min(twice_area)/2),
              'maximum_edge_length_m': float(np.max(lengths)),
              'first_diffusion_length_m': float(np.sqrt(case.k/case.capacity*arrays['times'][1])),
              'output_times_s': arrays['times'].tolist(),
              'reference': certificate}
    write_json(reference_dir/'analytic.json', record)
    return record


def publish_samples(destination):
    config = json.loads((ROOT/'judge-config.json').read_text(encoding='utf-8'))
    # A zero fixture and an independent nonzero mixed-boundary fixture.
    for number, case_name in [('01', '01-zero'), ('02', '15-four-operators')]:
        sample = destination/'samples'/number
        (sample/'input').mkdir(parents=True, exist_ok=True)
        for name in ('problem.json', 'input.h5', 'mesh.msh', 'mesh.geo'):
            shutil.copyfile(destination/'cases'/case_name/name, sample/'input'/name)
        problem = load_problem(sample/'input/problem.json')
        reference_path = destination/'reference'/case_name/'reference.h5'
        output = sample/'output/result.h5'
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(reference_path, output)
        report = grade_files(problem.path, output, reference_path, atol=config['atol'], rtol=config['rtol'])
        if report['score'] != 1:
            raise ValueError('Public output failed its task grader')
        write_json(sample/'verification.json', {'case': case_name, **report})


def generate(destination=ROOT, selected=None):
    destination = Path(destination)
    cases = [case for case in CASES if selected is None or case.name in selected]
    records = [generate_case(case, destination) for case in cases]
    write_json(destination/'reference/catalog.json', records)
    lines = ['# 瞬态测试设计（出题材料）', '',
             '初始配方仅用于生成节点值；连续初始条件始终是该网格上的分片线性场。',
             '所有正时间标答来自连续方程特征函数展开，不来自 baseline。', '',
             '解析解公式见 [DESIGN.md：初始场及解析标答](DESIGN.md#初始场及解析标答)，计算实现见 [author/oracle.py](author/oracle.py)。24 点共用该级数公式，各点的边界条件决定特征函数，初始场决定积分系数。初始节点值的具体配方见 [author/catalog.py](author/catalog.py) 的 `initial_values`。', '',
             '| 测试点 | 初始节点场配方 | 左／右／下／上 | 节点 | 三角形 | 最早输出／末时刻 s |',
             '|---|---|---|---|---|---|']
    for case, record in zip(cases, records):
        lines.append(f"| {case.name} | {case.profile} | {' / '.join(case.boundaries)} | {record['nodes']} | "
                     f"{record['triangles']} | {record['output_times_s'][1]:.6g} / {record['output_times_s'][-1]:.6g} |")
    (destination/'TEST-CASES.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    if selected is None:
        publish_samples(destination)
    return len(cases)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT)
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    print(f'Generated {generate(args.output, args.case)} transient cases in {args.output}')
