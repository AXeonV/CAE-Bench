"""Transient interpretation, independent series checks and numerical budgets."""
from caeoj.storage import write_hdf5
from copy import copy, deepcopy
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

import numpy as np

from grading_fixtures import evaluate_arrays, pointwise_policy
from caeoj.case_grading import grade_case
from caeoj.sdk import load_problem, load_result
from caeoj.validation import check_result, output_support, validate_input

PROJECT = Path(__file__).resolve().parents[1]
from task_fixtures import task_fixture, project_fixture
TASK = task_fixture('heat-conduction-transient-2d')


def author(name):
    spec = importlib.util.spec_from_file_location('transient_'+name, TASK/'author'/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


baseline, oracle = author('baseline'), author('oracle')


class TransientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((TASK/'judge-config.json').read_text(encoding='utf-8'))
        # Historical absolute-error physics regression, independent of release score.
        cls.policy = pointwise_policy(atol=0.02, rtol=0)
        cls.cases = {}
        for path in sorted((TASK/'cases').glob('*/problem.json')):
            p = load_problem(path)
            ref = TASK/'reference'/path.parent.name
            cls.cases[path.parent.name] = (p, load_result(p, ref/'reference.h5'),
                                          json.loads((TASK/'author/data-evidence/reference'/path.parent.name/'analytic.json').read_text(encoding='utf-8')))

    def case(self, prefix):
        return next(data for name, data in self.cases.items() if name.startswith(prefix))

    def test_local_author_memory_budget_remains_available_and_matches_harbor(self):
        # author/check.py is an independent live consumer of this legacy key.
        # Removing it just because the shared judge does not read it breaks
        # local runs; keep the two existing execution paths consistent.
        container = tomllib.loads((TASK/'harbor/task.toml').read_text(encoding='utf-8'))
        self.assertEqual(self.config['memory_mb'], container['environment']['memory_mb'])
        self.assertEqual(self.config['memory_mb'], 1024)

    def grade(self, problem, values, reference):
        arrays = {key: problem.arrays[key] for key in output_support(problem)} | {'temperature': values}
        self.assertTrue(check_result(problem, arrays)['valid'])
        return evaluate_arrays(problem, arrays, reference, policy=self.policy)

    def test_suite_ranges_mesh_scale_and_boundary_coverage(self):
        self.assertEqual(len(self.cases), 24)
        coverage = {name: set() for name in ('left', 'right', 'bottom', 'top')}
        largest = 0
        for name, (p, ref, certificate) in self.cases.items():
            with self.subTest(case=name):
                self.assertTrue(validate_input(p.path)['valid'])
                parameters = {key: item['value'] for key, item in p.manifest['physics']['parameters'].items()}
                self.assertTrue(0.05 <= parameters['conductivity'] <= 20)
                self.assertTrue(0.5 <= parameters['volumetric_heat_capacity'] <= 20)
                lengths = [parameters['length_x'], parameters['length_y']]
                self.assertTrue(all(0.5 <= l <= 3 for l in lengths))
                self.assertLessEqual(max(lengths)/min(lengths), 3)
                self.assertLessEqual(abs(parameters['x0']), 5)
                self.assertLessEqual(abs(parameters['y0']), 5)
                self.assertTrue(9 <= len(p.arrays['node_ids']) <= 8000)
                self.assertTrue(8 <= len(p.arrays['domain_ids']) <= 16000)
                largest = max(largest, len(p.arrays['node_ids']))
                self.assertTrue(6 <= len(p.arrays['times']) <= 12)
                self.assertLessEqual(p.arrays['times'][-1], 4000)
                self.assertGreaterEqual(parameters['conductivity']/parameters['volumetric_heat_capacity']*
                                        p.arrays['times'][1]/max(lengths)**2, 0.003-1e-15)
                self.assertLessEqual(np.max(np.abs(p.arrays['initial_temperature'])), 10)
                self.assertGreater(certificate['minimum_triangle_area_m2'], 0)
                for c in p.manifest['conditions']:
                    if c['role'] == 'boundary':
                        coverage[c['location']].add(c['operator'])
                        self.assertEqual(c['data']['value']['value'], 0)
                        if c['operator'] == 'robin':
                            self.assertTrue(0.1 <= c['data']['alpha']['value'] <= 10)
                            self.assertTrue(0.05 <= c['data']['beta']['value'] <= 20)
        self.assertGreaterEqual(largest, 7900)
        for ops in coverage.values():
            self.assertEqual(ops, {'dirichlet', 'normal_derivative', 'normal_flux', 'robin'})

    def test_initial_and_output_axes_remain_distinct_and_exact(self):
        for p, ref, _ in self.cases.values():
            np.testing.assert_array_equal(p.arrays['initial_times'], [0.0])
            self.assertEqual(p.manifest['fields']['initial_temperature']['time_axis'], 'initial')
            self.assertEqual(p.manifest['outputs']['temperature']['time_axis'], 'output')
            self.assertEqual(ref['temperature'].shape, (len(p.arrays['times']), len(p.arrays['node_ids']), 1))
            np.testing.assert_array_equal(ref['temperature'][:1], p.arrays['initial_temperature'])
            self.assertNotIn('initial_times', ref)
            invalid = dict(ref, times=ref['times']+1e-6)
            self.assertFalse(check_result(p, invalid)['valid'])

    def test_series_and_quadrature_convergence_records(self):
        for _, _, record in self.cases.values():
            certificate = record['reference']
            self.assertLessEqual(certificate['series_tail_bound_K'], 1e-10)
            self.assertTrue(all(c['max_difference_K'] <= 5e-9
                                for c in certificate['quadrature_refinements'][-2:]))
            self.assertTrue(all(np.all(np.diff(r) > 0) for r in certificate['axis_frequencies']))

    def test_axis_roots_boundary_equations_and_orthonormality(self):
        def condition(op):
            return {'operator': op, 'data': {'alpha': {'value': 2.3}, 'beta': {'value': 0.7}}}
        ops = ['dirichlet', 'normal_derivative', 'normal_flux', 'robin']
        z, w = np.polynomial.legendre.leggauss(160)
        for left in ops:
            for right in ops:
                a = oracle.axis_modes(condition(left), condition(right), 1.7, 12)
                basis = a.values((z+1)/2)
                np.testing.assert_allclose(basis.T@(basis*w[:, None]/2), np.eye(12), atol=1e-12, rtol=0)
                for end, op, sign in ((0.0, left, -1), (1.0, right, 1)):
                    value = a.values(end)
                    normal = -sign*a.frequencies*np.sin(a.frequencies*end-a.phases)/(1.7*a.norms)
                    residual = value if op == 'dirichlet' else 2.3*value+0.7*normal if op == 'robin' else normal
                    np.testing.assert_allclose(residual, 0, atol=5e-11, rtol=0)
                self.assertTrue(np.all(a.frequencies >= np.arange(12)*np.pi-1e-12))

    def test_insulated_affine_initial_matches_independent_known_cosine_series(self):
        p, ref, _ = self.case('24')
        xy, _ = baseline.read_geometry(p)
        parameters = {key: item['value'] for key, item in p.manifest['physics']['parameters'].items()}
        u, v = ((xy-[parameters['x0'], parameters['y0']])/
                [parameters['length_x'], parameters['length_y']]).T
        n = np.arange(1, 202, 2, dtype=np.float64)
        kappa = parameters['conductivity']/parameters['volumetric_heat_capacity']
        for i, t in enumerate(p.arrays['times'][1:], 1):
            xsum = (np.cos(np.pi*u[:, None]*n)/n**2)@np.exp(-kappa*t*(n*np.pi/parameters['length_x'])**2)
            ysum = (np.cos(np.pi*v[:, None]*n)/n**2)@np.exp(-kappa*t*(n*np.pi/parameters['length_y'])**2)
            expected = 0.2-8/math.pi**2*xsum+4/math.pi**2*ysum
            np.testing.assert_allclose(ref['temperature'][i, :, 0], expected, atol=1e-8, rtol=0)

    def test_higher_order_and_more_modes_reproduce_difficult_references(self):
        for prefix in ('13', '23'):
            p, ref, _ = self.case(prefix)
            xy, elements = baseline.read_geometry(p)
            values, certificate = oracle.reference(p, xy, elements, orders=(10, 12, 14), min_modes=64)
            np.testing.assert_allclose(values, ref['temperature'], atol=1e-8, rtol=0)
            self.assertLess(certificate['series_tail_bound_K'], 1e-10)

    def test_fixed_time_refinement_and_adaptive_error_control(self):
        p, ref, _ = self.case('08')
        coarse, _ = baseline.solve(p, dt=0.002)
        fixed, _ = baseline.solve(p)
        fine, _ = baseline.solve(p, dt=0.00005)
        self.assertGreater(np.max(np.abs(coarse-fine)), 20*np.max(np.abs(fixed-fine)))
        self.assertEqual(self.grade(p, fixed, ref)['score'], 1)
        adaptive, strict = baseline.solve(p, time_mode='adaptive')
        _, loose = baseline.solve(p, time_mode='adaptive', atol=0.002, rtol=0.002)
        self.assertGreater(strict['accepted_steps'], loose['accepted_steps'])
        self.assertEqual(self.grade(p, adaptive, ref)['score'], 1)

    def test_implicit_solver_is_not_limited_by_explicit_lumped_cfl(self):
        p, ref, _ = self.case('23')
        values, stats = baseline.solve(p)
        self.assertGreater(stats['largest_step_s'], stats['lumped_explicit_stable_step_bound_s'])
        self.assertEqual(self.grade(p, values, ref)['score'], 1)

    def test_wrong_capacity_and_wrong_robin_are_physics_not_format_errors(self):
        p, ref, _ = self.case('13')
        for mistake in ('capacity', 'robin'):
            wrong = copy(p)
            wrong.manifest = deepcopy(p.manifest)
            if mistake == 'capacity':
                wrong.manifest['physics']['parameters']['volumetric_heat_capacity']['value'] *= 2
            else:
                for condition in wrong.manifest['conditions']:
                    if condition['role'] == 'boundary':
                        condition['operator'] = 'normal_derivative'
            values, _ = baseline.solve(wrong)
            self.assertEqual(self.grade(p, values, ref)['score'], 0)
        repeated = np.repeat(p.arrays['initial_temperature'], len(p.arrays['times']), axis=0)
        self.assertEqual(self.grade(p, repeated, ref)['score'], 0)

    def test_public_samples_have_random_format_outputs_and_no_references(self):
        for sample in ('01', '02'):
            directory = TASK/'samples'/sample
            p = load_problem(directory/'input/problem.json')
            result = load_result(p, directory/'output/result.h5')
            for key in output_support(p):
                np.testing.assert_array_equal(result[key], p.arrays[key])
            self.assertEqual(json.loads((directory/'example.json').read_text()), {'kind': 'format'})
            self.assertFalse((directory/'reference').exists())
            self.assertGreater(np.ptp(result['temperature']), 0)

    def test_standalone_baseline_passes_private_reference(self):
        with tempfile.TemporaryDirectory(dir=PROJECT/'runs') as tmp:
            directory = Path(tmp)
            (directory/'solve.py').write_bytes((TASK/'author/baseline.py').read_bytes())
            env = os.environ.copy()
            env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', PYTHONUTF8='1')
            p = TASK/'samples/02/input/problem.json'
            process = subprocess.run([sys.executable, str(directory/'solve.py'), '--input', str(p),
                                      '--output', str(directory/'result.h5')], cwd=directory, env=env,
                                     capture_output=True, timeout=self.config['timeout_seconds'])
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(grade_case(p, directory/'result.h5', TASK/'reference/15-four-operators/grading.json')['score'], 1)

    def test_public_release_excludes_author_formulas_and_resources(self):
        spec = importlib.util.spec_from_file_location('transient_publish', PROJECT/'src/utils/publish_dist.py')
        publisher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(publisher)
        with tempfile.TemporaryDirectory() as temporary:
            project = project_fixture(temporary, ['heat-conduction-transient-2d'])
            files, samples = publisher.collect_materials('heat-conduction-transient-2d', project)
        self.assertEqual(samples, ['01', '02'])
        for path in files:
            self.assertFalse(set(Path(path).parts) & {'author', 'cases'})
            self.assertFalse(path.endswith(('DESIGN.md', 'TEST-CASES.md', 'verification.json')))

    def test_valid_boundary_only_mesh_has_no_unknowns_to_time_integrate(self):
        catalog, mesh = author('catalog'), author('mesh')
        with tempfile.TemporaryDirectory(dir=PROJECT/'runs') as tmp:
            directory = Path(tmp)
            mesh.generate_mesh(catalog.Case('boundary-only', 'zero', nx=1, ny=4), directory)
            ids, _, _, groups = mesh.read_mesh(directory/'mesh.msh')
            m = json.loads((TASK/'samples/01/input/problem.json').read_text(encoding='utf-8'))
            arrays = {'node_ids': ids, 'times': np.array([0, .003, .007, .016, .035, .08], dtype=np.float64),
                      'initial_times': np.array([0.0], dtype=np.float64),
                      'initial_temperature': np.zeros((1, len(ids), 1), dtype=np.float64)}
            for name, loc in m['locations'].items():
                if name != 'nodes':
                    group = loc['physical_group']
                    arrays[loc['ids']] = groups[group['dimension'], group['tag']]
            (directory/'problem.json').write_text(json.dumps(m), encoding='utf-8')
            write_hdf5(directory / 'input.h5', arrays)
            p = load_problem(directory/'problem.json')
            self.assertEqual(len(ids), 10)
            self.assertEqual(len(arrays['domain_ids']), 8)
            for mode in ('fixed', 'adaptive'):
                values, stats = baseline.solve(p, time_mode=mode)
                self.assertEqual(stats['accepted_steps'], 0)
                np.testing.assert_array_equal(values, np.zeros((6, 10, 1)))


if __name__ == '__main__':
    unittest.main()
