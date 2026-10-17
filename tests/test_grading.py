"""Threshold boundaries, exact auxiliary data and grading failure categories."""
from caeoj.storage import write_hdf5
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from caeoj.case_grading import direct_config, grade_case
from caeoj.grading_policy import validate_policy
from grading_fixtures import evaluate_arrays, pointwise_policy
from caeoj.sdk import load_problem
from caeoj_tools.author import PROJECT_ROOT
from task_fixtures import task_fixture
SMOKE = task_fixture("smoke-test")
from caeoj.validation import output_support


class GradingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = SMOKE / "cases/09-vector-2d/problem.json"
        self.problem = load_problem(self.path)
        self.use_problem(self.problem)
        self.policy = pointwise_policy(atol=1e-6, rtol=1e-5)

    def use_problem(self, problem):
        self.problem = problem
        keys = output_support(problem) | {s["array"] for s in problem.manifest["outputs"].values()}
        self.reference = {key: problem.arrays[key].copy() for key in keys}
        self.result = deepcopy(self.reference)

    def grade(self, *, policy=None):
        return evaluate_arrays(self.problem, self.result, self.reference,
                               policy=self.policy if policy is None else policy)

    def test_absolute_threshold_including_equality(self):
        self.reference["velocity"][:] = 0
        for delta, score in ((0, 1), (1e-6 * 0.999, 1), (1e-6, 1),
                             (-1e-6, 1), (1e-6 * 1.001, 0)):
            self.result["velocity"][:] = 0
            self.result["velocity"][0, 0, 0] = delta
            self.assertEqual(self.grade()["score"], score)

    def test_relative_threshold_scales_with_reference(self):
        self.reference["velocity"][:] = 1e6
        for delta, score in ((9, 1), (-9, 1), (11, 0)):
            self.result["velocity"][:] = 1e6 + delta
            self.assertEqual(self.grade()["score"], score)

    def test_all_values_and_fields_must_pass(self):
        p = load_problem(SMOKE / "cases/08-scalars-and-dtypes/problem.json")
        self.use_problem(p)
        self.result["temperature"][0, -1, 0] += 1
        result = self.grade()
        self.assertEqual(result["score"], 0)
        fields = result['checks']['outputs']['fields']
        self.assertEqual(sum(g['failed_values'] for g in fields['temperature']['groups']), 1)
        self.assertEqual(fields['region_label']['failed_values'], 0)

    def test_integer_comparison_is_exact_above_float_precision(self):
        p = load_problem(SMOKE / "cases/08-scalars-and-dtypes/problem.json")
        self.use_problem(p)
        self.reference["region_label"][0, 0, 0] = np.iinfo(np.int64).max
        self.result["region_label"][0, 0, 0] = np.iinfo(np.int64).max - 1
        self.assertEqual(self.grade(policy=pointwise_policy(atol=100, rtol=100))["score"], 0)

    def test_boolean_comparison_is_exact(self):
        p = load_problem(SMOKE / "cases/08-scalars-and-dtypes/problem.json")
        self.use_problem(p)
        self.result["mask"][0, 0, 0] = ~self.result["mask"][0, 0, 0]
        self.assertEqual(self.grade(policy=pointwise_policy(atol=100, rtol=100))["score"], 0)

    def test_ids_and_times_still_require_exact_equality(self):
        self.result["times"] += 1e-12
        result = self.grade(policy=pointwise_policy(atol=1, rtol=1))
        self.assertEqual(result["status"], "invalid_output")
        self.assertEqual(result["score"], 0)

    def test_reference_is_independent_of_input_fields(self):
        self.reference["velocity"][:] = 123
        self.result["velocity"][:] = 123
        self.assertFalse(np.array_equal(self.reference["velocity"], self.problem.arrays["velocity"]))
        self.assertEqual(self.grade()["score"], 1)

    def test_invalid_reference_is_not_an_answer_error(self):
        self.reference["velocity"] = self.reference["velocity"][0]
        result = self.grade()
        self.assertEqual(result["status"], "evaluation_error")
        self.assertIsNone(result["score"])

    def test_invalid_output_and_nonfinite_values(self):
        self.result["velocity"][0, 0, 0] = np.nan
        self.assertEqual(self.grade()["status"], "invalid_output")
        self.result["velocity"][0, 0, 0] = np.inf
        self.assertEqual(self.grade()["score"], 0)

    def test_tolerances_are_explicit_and_finite(self):
        self.result["velocity"][0, 0, 0] += 0.001
        self.assertEqual(self.grade()["score"], 0)
        self.assertEqual(self.grade(policy=pointwise_policy(atol=0.01, rtol=0))["score"], 1)
        for kwargs in ({"atol": -1}, {"rtol": -1}, {"atol": np.nan}, {"rtol": np.inf}):
            with self.assertRaises(ValueError):
                validate_policy(pointwise_policy(**({'atol': 0, 'rtol': 0} | kwargs)))
        with self.assertRaises(ValueError):
            validate_policy({'version': 2, 'default': {'metric': 'pointwise',
                            'time': 'per_time', 'components': 'per_component'}})

    def test_comparison_overflow_stays_wrong_and_json_serializable(self):
        self.reference["velocity"][:] = -1e308
        self.result["velocity"][:] = 1e308
        result = self.grade(policy={'version': 2, 'default': {
            'metric': 'max_abs', 'time': 'per_time', 'components': 'per_component', 'limit': 1e-6}})
        self.assertEqual(result["score"], 0)
        self.assertEqual(result['checks']['outputs']['fields']['velocity']['groups'][0]['value'], 'overflow')
        json.dumps(result, allow_nan=False)

    def test_no_mutation_or_correction(self):
        before_result, before_reference = deepcopy(self.result), deepcopy(self.reference)
        self.grade()
        for key in self.result:
            np.testing.assert_array_equal(self.result[key], before_result[key])
            np.testing.assert_array_equal(self.reference[key], before_reference[key])

    def write_files(self):
        output, reference = self.root / "result.h5", self.root / "reference.h5"
        write_hdf5(output, self.result)
        write_hdf5(reference, self.reference)
        grading = self.root/'grading.json'
        grading.write_text(json.dumps(direct_config(self.policy)), encoding='utf-8')
        return output, reference, grading

    def test_file_grader_and_failure_categories(self):
        output, reference, grading = self.write_files()
        self.assertEqual(grade_case(self.path, output, grading)["score"], 1)
        output.write_bytes(b"invalid")
        self.assertEqual(grade_case(self.path, output, grading)["status"], "invalid_output")
        reference.write_bytes(b"invalid")
        result = grade_case(self.path, output, grading)
        self.assertEqual(result["status"], "evaluation_error")
        self.assertIsNone(result["score"])

    def test_grading_cli_exit_codes_and_json(self):
        output, reference, grading = self.write_files()
        command = [sys.executable, "-m", "caeoj", "grade", "--input", str(self.path),
                   "--output", str(output), "--grading", str(grading)]
        execution = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(execution.returncode, 0, execution.stderr)
        self.assertEqual(json.loads(execution.stdout)["score"], 1)
        self.result["velocity"][0, 0, 0] += 1
        write_hdf5(output, self.result)
        execution = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(execution.returncode, 1)
        self.assertEqual(json.loads(execution.stdout)["score"], 0)
        reference.write_bytes(b"invalid")
        execution = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(execution.returncode, 2)
        self.assertIsNone(json.loads(execution.stdout)["score"])


if __name__ == "__main__":
    unittest.main()
