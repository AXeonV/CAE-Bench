"""Equation tasks allow at most 0.1% outlier spatial points per field and time."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

import numpy as np

from caeoj.grading import grade_arrays
from caeoj.grading_policy import load_policy, validate_policy
from caeoj.sdk import load_problem
from caeoj_tools.task_paths import task_directory
from caeoj.validation import output_support

ROOT = Path(__file__).resolve().parents[1]


class EquationPolicyTests(unittest.TestCase):
    def test_all_families_keep_original_tolerances_and_cover_outputs(self):
        tolerances = {
            'advection-1d': (.1, .1), 'burgers-1d': (.1, .1),
            'reaction-diffusion-1d': (.05, .1), 'diffusion-sorption-1d': (.02, .2),
            'reaction-diffusion-2d': (.1, .2), 'darcy-flow-2d': (1e-5, .2),
            'shallow-water-2d': (.1, .1), 'compressible-navier-stokes-1d': (.1, .2),
            'compressible-navier-stokes-2d': (.1, .2), 'compressible-navier-stokes-3d': (.1, .2),
            'incompressible-navier-stokes-2d': (.1, .2)}
        for family, (atol, rtol) in tolerances.items():
            task = task_directory(family, ROOT)
            with self.subTest(task=task.name):
                policy = load_policy(task / 'author/grading-template.json')
                from utils.PDEBench.models import BY_TASK
                fields = {item[0] for item in BY_TASK[family].fields}
                self.assertEqual(set(policy['fields']), fields)
                for node in policy['fields'].values():
                    self.assertEqual(node, {'metric': 'violation_fraction', 'time': 'per_time',
                        'components': 'joint', 'count': 'spatial_points', 'atol': atol, 'rtol': rtol, 'limit': .001})
                config = json.loads((task / 'judge-config.json').read_text())
                self.assertNotIn('atol', config)
                self.assertNotIn('rtol', config)
                self.assertGreater(config['timeout_seconds'], 0)

    def test_exact_fraction_boundary_and_component_union(self):
        p = load_problem(ROOT / 'qbank/00-basic-tests/0.1-io/smoke-test/cases/09-vector-2d/problem.json')
        spec = p.manifest['outputs']['velocity']
        loc = p.manifest['locations'][spec['location']]
        p.arrays[loc['ids']] = np.arange(1, 1001, dtype=np.int64)
        p.arrays[p.manifest['time_axes'][spec['time_axis']]] = np.array([0., 1.])
        ref = {key: p.arrays[key].copy() for key in output_support(p)}
        ref[spec['array']] = np.zeros((2, 1000, 2))
        actual = deepcopy(ref)
        policy = {'version': 1, 'fields': {'velocity': {
            'metric': 'violation_fraction', 'time': 'per_time', 'components': 'joint',
            'count': 'spatial_points', 'atol': .1, 'rtol': .2, 'limit': .001}}}
        validate_policy(policy, p)
        # One spatial point with both components wrong: exactly 0.1%, accepted.
        actual['velocity'][1, 0, :] = .2
        self.assertEqual(grade_arrays(p, actual, ref, policy=policy)['score'], 1)
        # Two distinct points wrong even in different components: 0.2%, rejected.
        actual['velocity'][1, 1, 0] = .2
        report = grade_arrays(p, actual, ref, policy=policy)
        self.assertEqual(report['score'], 0)
        self.assertEqual(report['fields']['velocity']['groups'][1]['failed_values'], 2)
        # Another good time cannot dilute a bad time's fraction.
        self.assertEqual(report['fields']['velocity']['groups'][1]['value'], .002)
        # A tiny count still cannot bypass structural invalidity.
        actual['velocity'][1, 0, 0] = np.nan
        self.assertEqual(grade_arrays(p, actual, ref, policy=policy)['status'], 'invalid_output')


if __name__ == '__main__':
    unittest.main()
