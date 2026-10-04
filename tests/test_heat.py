"""Heat data quality and solver grading; physics never enters validation.py."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

from caeoj.grading import grade_arrays, grade_files
from caeoj.sdk import load_problem, load_result, read_constant, read_field
from caeoj.smoke import PROJECT_ROOT
from caeoj.validation import check_result, output_support

TASK = PROJECT_ROOT / "tasks/heat-conduction"


def import_author(name):
    spec = importlib.util.spec_from_file_location("heat_" + name, TASK / "author" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


baseline = import_author("baseline")
local_check = import_author("check")


def evaluate(a, u, v):
    # Deliberately independent of the generator's NumPy polynomial calls.
    return sum(a[i, j] * u**i * v**j for i, j in np.ndindex(a.shape))


class HeatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((TASK / "judge-config.json").read_text(encoding="utf-8"))
        cls.cases = []
        for path in sorted((TASK / "cases").glob("*/problem.json")):
            problem = load_problem(path)
            reference_dir = TASK / "reference" / path.parent.name
            reference = load_result(problem, reference_dir / "reference.npz")
            analytic = json.loads((reference_dir / "analytic.json").read_text(encoding="utf-8"))
            coordinates, elements = baseline.read_geometry(problem)
            cls.cases.append((problem, reference, analytic, coordinates, elements))

    def grade(self, problem, temperature, reference):
        arrays = {key: problem.arrays[key] for key in output_support(problem)}
        arrays["temperature"] = temperature
        self.assertTrue(check_result(problem, arrays)["valid"])
        return grade_arrays(problem, arrays, reference, atol=self.config["atol"], rtol=self.config["rtol"])

    def case(self, prefix):
        return next(item for item in self.cases if item[0].path.parent.name.startswith(prefix))

    def test_suite_size_and_boundary_coverage_on_every_side(self):
        self.assertEqual(len(self.cases), 32)
        for side in ("left", "right", "bottom", "top"):
            operators = {c["operator"] for p, *_ in self.cases for c in p.manifest["conditions"]
                         if c["role"] == "boundary" and c["location"] == side}
            self.assertEqual(operators, {"dirichlet", "normal_derivative", "normal_flux", "robin"})

    def test_complete_public_sample_matches_scoring_case_and_passes_grader(self):
        sample = TASK / "samples/01"
        original, reference, *_ = self.case("01")
        for filename in ("problem.json", "input.npz", "mesh.msh", "mesh.geo"):
            self.assertEqual((sample/"input"/filename).read_bytes(), (original.path.parent/filename).read_bytes())
        problem = load_problem(sample/"input/problem.json")
        result = load_result(problem, sample/"output/result.npz")
        np.testing.assert_array_equal(result["node_ids"], np.arange(1, 10, dtype=np.int64))
        np.testing.assert_array_equal(result["temperature"], np.full((1, 9, 1), 4.0))
        self.assertEqual(len(problem.arrays["domain_ids"]), 8)
        report = grade_files(problem.path, sample/"output/result.npz", TASK/"reference"/original.path.parent.name/"reference.npz",
                             atol=self.config["atol"], rtol=self.config["rtol"])
        self.assertEqual(report["score"], 1)
        self.assertEqual(report["fields"]["temperature"]["max_abs_error"], 0)
        saved = json.loads((sample/"verification.json").read_text(encoding="utf-8"))
        self.assertEqual(saved, {"case": original.path.parent.name, **report})

    def test_frozen_inputs_match_advertised_ranges_and_coefficients(self):
        for problem, _, _, coordinates, elements in self.cases:
            with self.subTest(case=problem.path.parent.name):
                p = {key: x["value"] for key, x in problem.manifest["physics"]["parameters"].items()}
                self.assertTrue(0.05 <= p["conductivity"] <= 20)
                for name in ("x0", "y0"):
                    self.assertTrue(-5 <= p[name] <= 5)
                for name in ("length_x", "length_y"):
                    self.assertTrue(0.5 <= p[name] <= 3)
                self.assertTrue(3 <= len(coordinates) <= 20000)
                self.assertTrue(1 <= len(elements[2][0]) <= 40000)
                np.testing.assert_allclose(coordinates.min(axis=0), [p["x0"], p["y0"]], atol=1e-12)
                np.testing.assert_allclose(coordinates.max(axis=0), [p["x0"]+p["length_x"], p["y0"]+p["length_y"]], atol=1e-12)
                for field in problem.manifest["fields"].values():
                    a = problem.arrays[field["array"]]
                    self.assertLessEqual(np.max(np.abs(a)), 10000)
                    self.assertTrue(np.array_equal(a, np.broadcast_to(a[:, :1], a.shape)))
                source = problem.arrays["source_coefficients"][0, 0]
                self.assertTrue(all(source[i,j] == 0 for i,j in np.ndindex(source.shape) if i+j > 2))
                for condition in problem.manifest["conditions"]:
                    if condition["operator"] == "robin":
                        self.assertTrue(0.1 <= condition["data"]["alpha"]["value"] <= 20)
                        self.assertTrue(0.01 <= condition["data"]["beta"]["value"] <= 100)
                if "mean_temperature" in p:
                    self.assertTrue(-20 <= p["mean_temperature"] <= 20)

    def test_mixed_public_sample_uses_sdk_and_passes_independent_solver(self):
        sample = TASK / "samples/02"
        problem = load_problem(sample / "input/problem.json")
        reference = load_result(problem, sample / "output/result.npz")
        boundaries = [c for c in problem.manifest["conditions"] if c["role"] == "boundary"]
        self.assertEqual({c["operator"] for c in boundaries},
                         {"dirichlet", "normal_derivative", "normal_flux", "robin"})
        expected = {"left": [1, 1, 0, 0, 0], "right": [1, 0, 0, 0, 0],
                    "bottom": [1, 0, 0, 0, 0], "top": [3, 1, 0, 0, 0]}
        for condition in boundaries:
            values = read_field(problem, condition["data"]["coefficients"])
            self.assertEqual(values.shape, (1, 2, 5))
            np.testing.assert_array_equal(values, np.broadcast_to(expected[condition["location"]], values.shape))
            if condition["operator"] == "robin":
                self.assertEqual(read_constant(condition["data"]["alpha"]), 1.0)
                self.assertEqual(read_constant(condition["data"]["beta"]), 1.0)
        coordinates, _ = baseline.read_geometry(problem)
        expected_temperature = (1 + coordinates[:, 0] + coordinates[:, 1])[None, :, None]
        np.testing.assert_allclose(reference["temperature"], expected_temperature, atol=1e-14, rtol=0)
        self.assertEqual(self.grade(problem, baseline.solve(problem), reference)["score"], 1)
        saved = json.loads((sample / "verification.json").read_text(encoding="utf-8"))
        private_reference = TASK / "reference" / saved["case"] / "reference.npz"
        report = grade_files(problem.path, sample / "output/result.npz", private_reference,
                             atol=self.config["atol"], rtol=self.config["rtol"])
        self.assertEqual(report["score"], 1)
        self.assertEqual(saved, {"case": saved["case"], **report})

    def test_every_reference_is_analytic_value_at_correct_gmsh_tag(self):
        for problem, reference, analytic, coordinates, _ in self.cases:
            with self.subTest(case=problem.path.parent.name):
                p = {key: x["value"] for key, x in problem.manifest["physics"]["parameters"].items()}
                u, v = ((coordinates - [p["x0"], p["y0"]]) / [p["length_x"], p["length_y"]]).T
                expected = evaluate(np.array(analytic["temperature_coefficients"]), u, v)
                np.testing.assert_allclose(reference["temperature"][0, :, 0], expected, atol=1e-12, rtol=0)
                self.assertEqual(set(reference), {"temperature", "node_ids", "times"})
                self.assertNotIn("temperature", problem.arrays)

    def test_continuous_source_matches_independent_finite_difference_laplacian(self):
        u, v = np.array([0.17, 0.41, 0.83]), np.array([0.76, 0.29, 0.55])
        h = 0.002
        for problem, _, analytic, *_ in self.cases:
            with self.subTest(case=problem.path.parent.name):
                a = np.array(analytic["temperature_coefficients"])
                t = lambda x, y: evaluate(a, x, y)
                # Five-point second derivative is exact through degree five.
                duu = (-t(u+2*h, v)+16*t(u+h, v)-30*t(u, v)+16*t(u-h, v)-t(u-2*h, v))/(12*h*h)
                dvv = (-t(u, v+2*h)+16*t(u, v+h)-30*t(u, v)+16*t(u, v-h)-t(u, v-2*h))/(12*h*h)
                p = {key: x["value"] for key, x in problem.manifest["physics"]["parameters"].items()}
                q = evaluate(problem.arrays["source_coefficients"][0, 0], u, v)
                np.testing.assert_allclose(q, -p["conductivity"]*(duu/p["length_x"]**2+dvv/p["length_y"]**2), atol=2e-7, rtol=1e-8)

    def test_every_boundary_equation_matches_analytic_temperature_and_outward_normal(self):
        s, h = np.array([0.13, 0.57, 0.91]), 0.00002
        for problem, _, analytic, *_ in self.cases:
            p = {key: x["value"] for key, x in problem.manifest["physics"]["parameters"].items()}
            a = np.array(analytic["temperature_coefficients"])
            t = lambda x, y: evaluate(a, x, y)
            for c in problem.manifest["conditions"]:
                if c["role"] != "boundary":
                    continue
                with self.subTest(case=problem.path.parent.name, side=c["location"]):
                    side = c["location"]
                    u = np.zeros_like(s) if side == "left" else np.ones_like(s) if side == "right" else s
                    v = np.zeros_like(s) if side == "bottom" else np.ones_like(s) if side == "top" else s
                    if side in ("left", "right"):
                        derivative = (t(u-2*h,v)-8*t(u-h,v)+8*t(u+h,v)-t(u+2*h,v))/(12*h*p["length_x"])
                    else:
                        derivative = (t(u,v-2*h)-8*t(u,v-h)+8*t(u,v+h)-t(u,v+2*h))/(12*h*p["length_y"])
                    if side in ("left", "bottom"):
                        derivative *= -1
                    operator = c["operator"]
                    expected = t(u,v) if operator == "dirichlet" else derivative if operator == "normal_derivative" else -p["conductivity"]*derivative if operator == "normal_flux" else c["data"]["alpha"]["value"]*t(u,v)+c["data"]["beta"]["value"]*derivative
                    key = problem.manifest["fields"][c["data"]["coefficients"]["field"]]["array"]
                    coeff = problem.arrays[key][0, 0]
                    g = sum(coeff[i]*s**i for i in range(5))
                    np.testing.assert_allclose(g, expected, atol=3e-9, rtol=1e-9)

    def test_pure_neumann_compatibility_and_domain_mean(self):
        for problem, _, analytic, *_ in self.cases:
            p = {key: x["value"] for key, x in problem.manifest["physics"]["parameters"].items()}
            if "mean_temperature" not in p:
                continue
            with self.subTest(case=problem.path.parent.name):
                a = problem.arrays["source_coefficients"][0, 0]
                source_integral = sum(a[i,j]/((i+1)*(j+1)) for i,j in np.ndindex(a.shape))*p["length_x"]*p["length_y"]
                flux_integral = 0.0
                for c in problem.manifest["conditions"]:
                    if c["role"] != "boundary":
                        continue
                    coeff = problem.arrays[c["data"]["coefficients"]["field"]][0, 0]
                    integral = sum(coefficient/(i+1) for i,coefficient in enumerate(coeff))
                    factor = -p["conductivity"] if c["operator"] == "normal_derivative" else 1
                    length = p["length_y"] if c["location"] in ("left", "right") else p["length_x"]
                    flux_integral += factor * length * integral
                self.assertAlmostEqual(source_integral, flux_integral, places=10)
                z,w = np.polynomial.legendre.leggauss(4)
                u,v = np.meshgrid((z+1)/2, (z+1)/2)
                mean = np.sum(evaluate(np.array(analytic["temperature_coefficients"]),u,v)*w[:,None]*w[None,:]/4)
                self.assertAlmostEqual(mean, p["mean_temperature"], places=12)

    def test_independent_p1_solver_passes_all_cases_and_refinement_reduces_error(self):
        errors = {}
        for problem, reference, *_ in self.cases:
            with self.subTest(case=problem.path.parent.name):
                report = self.grade(problem, baseline.solve(problem), reference)
                self.assertEqual(report["score"], 1)
                errors[problem.path.parent.name] = report["fields"]["temperature"]["max_abs_error"]
        self.assertLess(errors["30-bubble-refined"], errors["29-bubble-coarser"]/5)
        self.assertLess(errors["07-zero-boundary-bubble"], errors["29-bubble-coarser"]/2)

    def test_wrong_physics_is_structurally_valid_but_scores_zero(self):
        for prefix, mistake in (("07", "source"), ("11", "flux"), ("05", "conductivity"), ("13", "robin"), ("18", "mean")):
            original, reference, *_ = self.case(prefix)
            problem = deepcopy(original)
            with self.subTest(mistake=mistake):
                if mistake == "source":
                    problem.arrays["source_coefficients"][:] = 0
                elif mistake == "flux":
                    for c in problem.manifest["conditions"]:
                        if c["operator"] == "normal_flux":
                            problem.arrays[c["data"]["coefficients"]["field"]] *= -1
                elif mistake == "conductivity":
                    problem.manifest["physics"]["parameters"]["conductivity"]["value"] = 1
                elif mistake == "robin":
                    for c in problem.manifest["conditions"]:
                        if c["operator"] == "robin":
                            c["data"]["beta"]["value"] *= 4
                else:
                    problem.manifest["physics"]["parameters"]["mean_temperature"]["value"] += 1
                self.assertEqual(self.grade(original, baseline.solve(problem), reference)["score"], 0)

    def test_fixed_heat_threshold_inside_and_outside(self):
        problem, reference, *_ = self.case("25")
        for error, score in ((0.01, 1), (0.010001, 0)):
            candidate = reference["temperature"].copy()
            candidate[0, -1, 0] = error
            self.assertEqual(self.grade(problem, candidate, reference)["score"], score)

    def test_invalid_reference_is_infrastructure_error_even_if_program_would_fail(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "runs") as directory:
            root = Path(directory)
            import shutil
            source = self.case("01")[0].path.parent
            shutil.copytree(source, root/"cases"/source.name)
            shutil.copy(TASK/"judge-config.json", root/"judge-config.json")
            # Missing reference: the program path is deliberately also invalid.
            report = local_check.check(root/"missing.py", root/"report.json", root)
            self.assertEqual(report["cases"][0]["status"], "reference_error")
            self.assertIsNone(report["score"])


if __name__ == "__main__":
    unittest.main()
