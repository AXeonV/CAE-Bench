"""Porous declarations, independent counterexamples, policies and public closure.

All numerical payloads are temporary protocol fixtures, not benchmark references.
"""
from copy import deepcopy
from pathlib import Path
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest

import h5py
import numpy as np

from porous_fixture import fixture, replace_manifest
from caeoj_ext.porous import models
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj.sdk import load_problem, write_result
from caeoj.validation import validate_input, validate_output
from caeoj_tools.assembly import runtime_materials
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.task_paths import task_directory

ROOT = Path(__file__).resolve().parents[1]


class PorousContractTests(unittest.TestCase):
    def mutation(self, slug, change, valid=False):
        with tempfile.TemporaryDirectory() as temporary:
            path, manifest = fixture(temporary, slug)
            change(manifest, path.parent)
            replace_manifest(path, manifest)
            result = validate_input(path)
            self.assertEqual(result['valid'], valid, result)
            if not valid:
                self.assertTrue(result['errors'], result)

    @staticmethod
    def edit_field(name, value):
        def edit(manifest, directory):
            key = manifest['fields'][name]['array']
            with h5py.File(directory / 'input.h5', 'r+') as h:
                h[key][:] = value
        return edit

    def test_all_thirteen_models_real_files_and_roundtrip(self):
        for slug in models():
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as temporary:
                path, manifest = fixture(temporary, slug)
                problem = load_problem(path)
                answer = {s['array']: np.zeros((len(problem.arrays[manifest['time_axes'][s['time_axis']]]),
                    len(problem.arrays[manifest['locations'][s['location']]['ids']]), *s['component_shape']))
                    for s in manifest['outputs'].values()}
                output = Path(temporary) / 'protocol-only.h5'
                write_result(output, problem, answer)
                self.assertTrue(validate_output(path, output)['valid'])

    def test_units_types_sampling_and_extra_condition_keys(self):
        edits = [lambda m, b: m['physics']['parameters']['density'].update(value=0.),
                 lambda m, b: m['physics']['parameters']['viscosity'].update(unit='m2/s'),
                 lambda m, b: m['conditions'][0]['data'].update(extra={'value': 0., 'unit':'1'}),
                 lambda m, b: m['fields']['material_permeability'].update(quantity='hydraulic_conductivity'),
                 lambda m, b: m['fields']['initial_pressure_value']['sampling'].update(time='previous'),
                 lambda m, b: m['fields']['volume_source_value']['sampling'].update(space='uniform')]
        for edit in edits:
            with self.subTest(edit=edit):
                self.mutation('darcy-transient', edit)

    def test_tensor_range_symmetry_and_positive_definiteness(self):
        for matrix in ([[1e-10, 1e-11], [0., 1e-10]], [[1e-10, 2e-10], [2e-10, 1e-10]],
                       [[1e-18, 0.], [0., 1e-10]]):
            self.mutation('darcy-steady', self.edit_field('material_permeability', matrix))
        self.mutation('darcy-steady', self.edit_field('material_permeability', [[2e-10, 3e-11], [3e-11, 1e-10]]), True)

    def test_retention_phase_and_transport_cross_field_constraints(self):
        self.mutation('richards-transient', self.edit_field('material_residual_water', .4))
        self.mutation('richards-steady', self.edit_field('material_retention_n', 1.))
        self.mutation('immiscible-two-phase', lambda m,b: (
            self.edit_field('material_residual_w', .45)(m,b),
            self.edit_field('material_residual_n', .45)(m,b)))
        self.mutation('compressible-two-phase', lambda m,b: m['physics']['parameters']['compressibility_n'].update(value=.01))
        self.mutation('porous-tracer', self.edit_field('material_transverse_dispersivity', 1.))
        self.mutation('porous-sorption-decay', self.edit_field('material_distribution_coefficient', -1.))

    def test_missing_required_boundary_and_time_rules(self):
        def remove(m, b):
            c = next(c for c in m['conditions'] if c['operator'] == 'pressure')
            m['conditions'].remove(c)
            name = c['data']['value']['field']
            key = m['fields'].pop(name)['array']
            with h5py.File(b/'input.h5', 'r+') as h:
                del h[key]
        self.mutation('darcy-steady', remove)
        def short_history(m, b):
            with h5py.File(b/'input.h5', 'r+') as h:
                h['loading_times'][-1] = .9
        self.mutation('darcy-transient', short_history)
        def at_zero(m, b):
            with h5py.File(b/'input.h5', 'r+') as h:
                h['requested_times'][0] = 0.
        self.mutation('darcy-transient', at_zero, True)

    def test_constants_and_variable_output_names(self):
        def constant(m, b):
            c = next(c for c in m['conditions'] if c['operator'] == 'volume_source')
            name = c['data']['value']['field']
            key = m['fields'].pop(name)['array']
            c['data']['value'] = dict(value=0., unit='1/s')
            with h5py.File(b/'input.h5', 'r+') as h:
                del h[key]
            s = m['outputs'].pop('requested_pressure')
            s['array'] = 'unrelated_array_name'
            m['outputs']['unrelated_logical_name'] = s
        self.mutation('darcy-steady', constant, True)

    def test_two_continua_can_share_boundary_nodes(self):
        self.mutation('dual-continuum', lambda m,b: None, True)
        def duplicate(m,b):
            m['conditions'].append(deepcopy(next(c for c in m['conditions'] if c['operator'] == 'matrix_pressure')))
        self.mutation('dual-continuum', duplicate)

    def test_pore_complete_boundary_and_mean_declaration(self):
        self.mutation('pore-creeping', lambda m,b: m['locations']['mean'].update(operation='sum'))
        def subset(m,b):
            with h5py.File(b/'input.h5','r+') as h:
                tags = h['boundary_ids'][()][:-1]
                del h['boundary_ids']
                h['boundary_ids'] = tags
        self.mutation('pore-creeping', subset)

    def test_unsupported_models_and_output_location(self):
        self.mutation('darcy-steady', lambda m,b: m['outputs']['requested_pressure'].update(location='domain', value_kind='point'))
        self.mutation('darcy-steady', lambda m,b: m['physics'].update(model='porous-unknown-v1'))

    def test_all_policy_bindings_and_exact_tolerance_boundary(self):
        for slug, cfg in models().items():
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as temporary:
                path, m = fixture(temporary, slug)
                problem = load_problem(path)
                policy = task_policy(task_directory(slug, ROOT), problem)
                bound = resolve_policy(policy, problem)
                ref = {problem.manifest['locations'][s['location']]['ids']: problem.arrays[problem.manifest['locations'][s['location']]['ids']]
                       for s in m['outputs'].values()}
                ref.update({m['time_axes'][s['time_axis']]: problem.arrays[m['time_axes'][s['time_axis']]] for s in m['outputs'].values()})
                for name, spec in m['outputs'].items():
                    shape = (len(problem.arrays[m['time_axes'][spec['time_axis']]]),
                             len(problem.arrays[m['locations'][spec['location']]['ids']]), *spec['component_shape'])
                    ref[spec['array']] = np.zeros(shape)
                for name, spec in m['outputs'].items():
                    actual = deepcopy(ref)
                    tolerance = bound['fields'][name]['atol']
                    actual[spec['array']][:] = tolerance
                    self.assertEqual(grade_arrays(problem, actual, ref, policy=policy)['score'], 1)
                    actual[spec['array']].flat[0] = np.nextafter(tolerance, np.inf)
                    self.assertEqual(grade_arrays(problem, actual, ref, policy=policy)['score'], 0)
                    nonzero = deepcopy(ref)
                    for field in m['outputs'].values():
                        nonzero[field['array']][:] = 8.
                    actual = deepcopy(nonzero)
                    rule = bound['fields'][name]
                    limit = rule['atol'] + rule['rtol'] * 8.
                    actual[spec['array']][:] = np.nextafter(8. + limit, 8.)
                    self.assertEqual(grade_arrays(problem, actual, nonzero, policy=policy)['score'], 1)
                    actual[spec['array']].flat[0] = np.nextafter(8. + limit, np.inf)
                    self.assertEqual(grade_arrays(problem, actual, nonzero, policy=policy)['score'], 0)
                bad_ref = deepcopy(ref)
                bad_ref.pop(next(iter(m['outputs'].values()))['array'])
                self.assertIsNone(grade_arrays(problem, ref, bad_ref, policy=policy)['score'])

    def test_resource_configs_are_consumed(self):
        sys.path.insert(0, str(ROOT/'src/utils'))
        import prepare_harbor
        template = (ROOT/'src/utils/harbor/task.toml').read_text()
        for slug, cfg in models().items():
            task = task_directory(slug, ROOT)
            config = json.loads((task/'judge-config.json').read_text())
            overrides = tomllib.loads((task/'harbor/task.toml').read_text())
            merged = tomllib.loads(prepare_harbor.task_config(template, overrides, judge_config=config, case_count=7))
            self.assertEqual(config['timeout_seconds'], cfg['timeout'])
            self.assertIsNone(config['max_output_bytes'])
            self.assertEqual(merged['environment']['cpus'], 4)
            self.assertEqual(merged['environment']['memory_mb'], 4096)
            self.assertEqual(merged['verifier']['timeout_sec'], max(1200, 300+7*(cfg['timeout']+60)))

    def test_public_runtime_closure_is_isolated_and_keeps_checks(self):
        tasks = {s: task_directory(s, ROOT) for s in models()}
        materials, runtime = runtime_materials(tasks, ROOT)
        self.assertEqual(set(runtime['extensions']), {'porous.flow_transport'})
        self.assertFalse(any(any(part in name for part in ('caeoj_tools', 'maintenance', '/author/', '/cases/', '/reference/')) for name in materials))
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name, data in materials.items():
                target = directory/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            path, manifest = fixture(directory/'fixture', 'darcy-steady')
            away = directory/'away'
            away.mkdir()
            code = '''
from pathlib import Path
import json,sys
import caeoj,caeoj_ext.porous
from caeoj.validation import validate_input
path=Path(sys.argv[1])
assert Path(caeoj.__file__).is_relative_to(path.parent.parent/'src')
assert Path(caeoj_ext.porous.__file__).is_relative_to(path.parent.parent/'src')
assert validate_input(path)['valid']
m=json.loads(path.read_text());m['physics']['parameters']['viscosity']['unit']='wrong'
path.write_text(json.dumps(m));result=validate_input(path)
assert not result['valid'] and 'E_POROUS' in {e['code'] for e in result['errors']},result
'''
            result = subprocess.run([sys.executable, '-c', code, str(path)], cwd=away,
                env={**os.environ, 'PYTHONPATH': str(directory/'src')}, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_single_task_implicit_identity_does_not_accept_another_model(self):
        materials, _ = runtime_materials({'darcy-steady': task_directory('darcy-steady', ROOT)}, ROOT)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name, data in materials.items():
                target = directory/name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            for slug in ('darcy-steady', 'richards-steady'):
                path, m = fixture(directory/slug, slug)
                del m['task']
                replace_manifest(path, m)
            code = '''
from pathlib import Path
import sys
from caeoj.validation import validate_input
base=Path(sys.argv[1])
assert validate_input(base/'darcy-steady/problem.json')['valid']
r=validate_input(base/'richards-steady/problem.json')
assert not r['valid'] and 'E_POROUS' in {e['code'] for e in r['errors']},r
'''
            result = subprocess.run([sys.executable, '-c', code, str(directory)], cwd=directory,
                env={**os.environ, 'PYTHONPATH': str(directory/'src')}, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
