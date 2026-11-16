"""Per-case quantity binding must preserve the public numerical criterion."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

from grading_fixtures import evaluate_arrays
from caeoj.grading_metrics import evaluate_field
from caeoj.grading_policy import resolve_policy, render_policy, validate_policy
from caeoj.sdk import load_problem
from caeoj.validation import output_support

ROOT = Path(__file__).resolve().parents[1]
from task_fixtures import task_fixture
SMOKE = task_fixture('smoke-test')


class QuantityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.problem = load_problem(SMOKE / 'cases/09-vector-2d/problem.json')
        p = self.problem
        spec = p.manifest['outputs'].pop('velocity')
        p.manifest['outputs']['sampled_speed'] = spec
        keys = output_support(p) | {s['array'] for s in p.manifest['outputs'].values()}
        self.reference = {key: p.arrays[key].copy() for key in keys}
        self.reference['velocity'][:] = 0
        self.actual = deepcopy(self.reference)

    def policy(self, quantity='velocity', unit='m/s', **kw):
        rule = dict(metric='pointwise', time='per_time', components='per_component', atol=.125, rtol=0)
        rule.update(kw)
        return {'version': 2, 'quantities': {quantity: {'unit': unit, 'rule': rule}}}

    def test_names_arrays_and_optional_quantities_are_independent(self):
        policy = self.policy()
        # This rule is legal even when pressure is not requested and its input
        # reference parameter is absent: only actual outputs are bound.
        policy['quantities']['pressure'] = self.policy('pressure', 'Pa',
            reference_offset={'parameter': 'pressure_reference'})['quantities']['pressure']
        self.actual['velocity'][:] = .125
        self.assertEqual(evaluate_arrays(self.problem, self.actual, self.reference, policy=policy)['score'], 1)
        self.actual['velocity'][0, 0, 1] = np.nextafter(.125, np.inf)
        report = evaluate_arrays(self.problem, self.actual, self.reference, policy=policy)
        self.assertEqual(report['score'], 0)
        self.assertEqual(set(report['checks']['outputs']['fields']), {'sampled_speed'})
        self.assertEqual(len(report['grading_sha256']), 64)

    def test_all_outputs_with_the_same_quantity_are_checked(self):
        spec = deepcopy(self.problem.manifest['outputs']['sampled_speed'])
        spec['array'] = 'another_array'
        self.problem.manifest['outputs']['another_observation'] = spec
        self.reference['another_array'] = self.reference['velocity'].copy()
        self.actual['another_array'] = self.reference['velocity'].copy() + .25
        report = evaluate_arrays(self.problem, self.actual, self.reference, policy=self.policy())
        self.assertEqual(report['score'], 0)
        self.assertEqual(set(report['checks']['outputs']['fields']), {'sampled_speed', 'another_observation'})

    def test_unknown_quantity_wrong_unit_and_mixed_policy_versions_fail(self):
        for policy in (self.policy('not_velocity'), self.policy(unit='Pa'),
                       {**self.policy(), 'fields': {}}, {'version': 1, 'quantities': {}}):
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                resolve_policy(policy, self.problem)

    def test_case_parameter_offset_is_bound_without_mutating_template(self):
        p = self.problem
        p.manifest['outputs']['sampled_speed'].update(quantity='pressure', unit='Pa')
        p.manifest['physics'] = {'model': 'identity', 'parameters': {
            'pressure_reference': {'value': 100000., 'unit': 'Pa'}}}
        policy = self.policy('pressure', 'Pa', atol=.5, rtol=.1,
                             reference_offset={'parameter': 'pressure_reference'})
        original = deepcopy(policy)
        self.reference['velocity'][:] = 100010.
        self.actual['velocity'][:] = 100011.5
        first = evaluate_arrays(p, self.actual, self.reference, policy=policy)
        self.assertEqual(first['score'], 1)  # error 1.5 == .5 + .1 * 10
        self.actual['velocity'][0, 0, 0] = np.nextafter(100011.5, np.inf)
        self.assertEqual(evaluate_arrays(p, self.actual, self.reference, policy=policy)['score'], 0)
        self.actual['velocity'][:] = 100011.5
        p.manifest['physics']['parameters']['pressure_reference']['value'] = 100005.
        second = evaluate_arrays(p, self.actual, self.reference, policy=policy)
        self.assertEqual(second['score'], 0)  # unchanged error, smaller relative scale
        self.assertEqual(first['grading_sha256'], second['grading_sha256'])
        self.assertNotEqual(first['evaluation_sha256'], second['evaluation_sha256'])
        self.assertEqual(policy, original)
        self.assertIn('physics.parameters.pressure_reference.value', render_policy(policy))

    def test_bad_parameter_is_configuration_error_before_grading(self):
        p = self.problem
        p.manifest['outputs']['sampled_speed'].update(quantity='pressure', unit='Pa')
        policy = self.policy('pressure', 'Pa', reference_offset={'parameter': 'pressure_reference'})
        invalid = [None, {'value': True, 'unit': 'Pa'}, {'value': 1, 'unit': 'K'},
                   {'value': float('inf'), 'unit': 'Pa'}, {'value': 10**400, 'unit': 'Pa'}]
        for constant in invalid:
            p.manifest['physics'] = {'model': 'identity', 'parameters': {'pressure_reference': constant}}
            with self.subTest(constant=constant), self.assertRaises(ValueError):
                evaluate_arrays(p, self.actual, self.reference, policy=policy)
        tree = policy['quantities']['pressure']['rule']
        with self.assertRaises(ValueError):
            validate_policy({'version': 1, 'fields': {'sampled_speed': tree}})

    def test_default_rule_keeps_integer_and_boolean_fields_exact(self):
        p = load_problem(SMOKE / 'cases/08-scalars-and-dtypes/problem.json')
        keys = output_support(p) | {s['array'] for s in p.manifest['outputs'].values()}
        reference = {key: p.arrays[key].copy() for key in keys}
        policy = {'version': 2, 'default': self.policy()['quantities']['velocity']['rule']}
        actual = deepcopy(reference)
        self.assertEqual(evaluate_arrays(p, actual, reference, policy=policy)['score'], 1)
        actual['mask'][0, 0, 0] = ~actual['mask'][0, 0, 0]
        self.assertEqual(evaluate_arrays(p, actual, reference, policy=policy)['score'], 0)
        actual = deepcopy(reference)
        actual['region_label'][0, 0, 0] += 1
        self.assertEqual(evaluate_arrays(p, actual, reference, policy=policy)['score'], 0)

    def test_all_chapter_two_configs_grade_requested_quantities_and_exact_boundaries(self):
        from caeoj.grading_policy import load_policy
        chapter = ROOT / 'qbank/02-fluid-mechanics'
        policies = sorted(path for path in chapter.glob('*/*/author/grading-template.json')
                          if path.relative_to(chapter).parts[0] != '2.13-cfdcodebench')
        self.assertEqual(len(policies), 43)
        for path in policies:
            with self.subTest(task=path.parent.name):
                policy = load_policy(path)
                outputs = {}
                reference = {'ids': np.array([7], dtype=np.int64), 'times': np.array([0.], dtype=np.float64)}
                actual = deepcopy(reference)
                for i, (quantity, entry) in enumerate(policy['quantities'].items()):
                    key = f'array_{i}'
                    outputs[f'observation_{i}'] = dict(array=key, quantity=quantity, location='probe',
                        time_axis='output', dtype='float64', kind='scalar', component_shape=[1],
                        components=['value'], unit=entry['unit'], value_kind='point')
                    rule = entry['rule']
                    offset = 65536. if isinstance(rule.get('reference_offset'), dict) else 0.
                    reference[key] = np.full((1, 1, 1), offset)
                    actual[key] = reference[key] + rule['atol']
                # Numerical grading fixture only: it is not a physical CAE case,
                # a reference solver or material released to candidates.
                manifest = dict(spatial_dimension=2, fields={}, outputs=outputs,
                    locations={'probe': {'kind': 'points', 'ids': 'ids', 'coordinates': 'coordinates'}},
                    time_axes={'output': 'times'}, physics={'model': 'identity', 'parameters': {
                        'pressure_reference': {'value': 65536., 'unit': 'Pa'}}})
                problem = SimpleNamespace(manifest=manifest, arrays={**reference,
                    'coordinates': np.array([[0., 0.]])})
                bound = resolve_policy(policy, problem)
                def accepted():
                    return all(evaluate_field(problem, name, actual[spec['array']], reference[spec['array']], bound['fields'][name])['passed'] for name,spec in outputs.items())
                self.assertTrue(accepted())
                for key in (s['array'] for s in outputs.values()):
                    before = actual[key].copy()
                    actual[key][:] = np.nextafter(actual[key], np.inf)
                    self.assertFalse(accepted())
                    actual[key] = before

    def test_local_smoke_consumes_its_configured_policy(self):
        from caeoj_tools.author import load_author_module
        run_smoke = load_author_module('smoke-test', 'smoke').run_smoke
        with tempfile.TemporaryDirectory() as temporary:
            task = Path(temporary)
            cases = task / 'cases'
            shutil.copytree(SMOKE / 'cases/09-vector-2d', cases / 'one')
            (task / 'judge-config.json').write_text(json.dumps({'timeout_seconds': 10}))
            from caeoj_tools.grading_policy import write_direct_grading
            reference=task/'reference/one';reference.mkdir(parents=True)
            shutil.copyfile(SMOKE/'reference/09-vector-2d/reference.h5',reference/'reference.h5')
            write_direct_grading(reference, {'version':2,'default':{'metric':'pointwise','time':'per_time','components':'per_component','atol':0,'rtol':0}})
            program = task / 'solve.py'
            program.write_text('''import argparse
from caeoj.sdk import load_problem, write_result
p=argparse.ArgumentParser(); p.add_argument('--input'); p.add_argument('--output'); a=p.parse_args()
problem=load_problem(a.input)
write_result(a.output,problem,{s['array']:problem.arrays[s['array']]+1e-7 for s in problem.manifest['outputs'].values()})
''')
            report = run_smoke(cases, program, task / 'report.json')
            self.assertEqual(report['cases'][0]['status'], 'wrong_answer')
            self.assertIn('evaluation_sha256',report['cases'][0])
            # The same 1e-7 error would pass the old hardcoded smoke defaults.
            self.assertFalse(report['passed'])
            (reference/'grading.json').unlink()
            with self.assertRaises((FileNotFoundError,ValueError)):
                run_smoke(cases, program, task/'missing-policy.json')



if __name__ == '__main__':
    unittest.main()
