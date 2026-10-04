"""Standard-file protocol behavior and checker/judge separation."""
from copy import deepcopy
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

import gmsh
import numpy as np

from caeoj.sdk import id_to_row, load_problem, load_result, read_constant, read_field, target_ids, write_result
from caeoj.grading import grade_arrays
from caeoj.smoke import PROJECT_ROOT, run_smoke
from caeoj.validation import ContractError, output_support, read_json, read_npz, validate_input, validate_output, write_json

CASES = PROJECT_ROOT / "tasks/echo-field/cases"


def echo_reference(problem):
    keys = output_support(problem) | {s["array"] for s in problem.manifest["outputs"].values()}
    return {key: problem.arrays[key].copy() for key in keys}


class ContractTests(unittest.TestCase):
    def setUp(self):
        (PROJECT_ROOT / "runs").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "runs")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.copy_case("09-vector-2d")

    def copy_case(self, name):
        self.case = self.root / name
        shutil.copytree(CASES / name, self.case, dirs_exist_ok=True)
        self.path = self.case / "problem.json"
        self.m = read_json(self.path)
        self.a = read_npz(self.case / "input.npz")

    def save(self):
        write_json(self.path, self.m)
        np.savez(self.case / "input.npz", **self.a)

    def codes(self, diagnostics):
        self.assertFalse(diagnostics["valid"], diagnostics)
        return {e["code"] for e in diagnostics["errors"]}

    def bad_input(self, code):
        self.save()
        self.assertIn(code, self.codes(validate_input(self.path)))

    def output(self):
        p = load_problem(self.path)
        arrays = write_result(self.root / "result.npz", p,
                              {s["array"]: p.arrays[s["array"]].copy() for s in p.manifest["outputs"].values()})
        return p, arrays

    def bad_output(self, mutate, code):
        p, arrays = self.output()
        mutate(arrays)
        np.savez(self.root / "bad.npz", **arrays)
        self.assertIn(code, self.codes(validate_output(self.path, self.root / "bad.npz")))

    def test_twelve_real_mesh_and_npz_roundtrips(self):
        for path in sorted(CASES.glob("*/problem.json")):
            with self.subTest(case=path.parent.name):
                p = load_problem(path)
                result = write_result(self.root / "result.npz", p,
                    {s["array"]: p.arrays[s["array"]].copy() for s in p.manifest["outputs"].values()})
                self.assertEqual(grade_arrays(p, result, echo_reference(p))["score"], 1)

    def test_wrong_shape_and_rank(self):
        for change in (lambda x: x.transpose(0, 2, 1), lambda x: x[0], lambda x: x.reshape(-1),
                       lambda x: x[..., None], lambda x: x[:, :-1]):
            self.bad_output(lambda a: a.update(velocity=change(a["velocity"])), "E_SHAPE")

    def test_wrong_dtype_without_casting(self):
        for dtype in ("float32", "int64", "bool", "complex128", "U10"):
            self.bad_output(lambda a: a.update(velocity=a["velocity"].astype(dtype)), "E_DTYPE")

    def test_nonfinite_fields(self):
        for value in (np.nan, np.inf, -np.inf):
            def change(a):
                a["velocity"][0, 0, 0] = value
            self.bad_output(change, "E_FINITE")

    def test_missing_extra_output_keys(self):
        self.bad_output(lambda a: a.pop("velocity"), "E_ARRAYS")
        self.bad_output(lambda a: a.update(extra=np.zeros(1)), "E_ARRAYS")

    def test_output_ids_and_times_are_fixed(self):
        self.bad_output(lambda a: a.update(node_ids=a["node_ids"][::-1]), "E_ORDER")
        self.bad_output(lambda a: a.update(times=a["times"] + 1), "E_ORDER")
        self.bad_output(lambda a: a.update(times=a["times"].astype("datetime64[s]")), "E_DTYPE")
        self.bad_output(lambda a: a.update(node_ids=a["node_ids"].astype("U20")), "E_DTYPE")

    def test_swapped_components_and_rows_are_judge_errors(self):
        for change in (lambda x: x[..., ::-1].copy(), lambda x: x[:, ::-1, :].copy()):
            p, arrays = self.output()
            arrays["velocity"] = change(arrays["velocity"])
            np.savez(self.root / "wrong.npz", **arrays)
            self.assertTrue(validate_output(self.path, self.root / "wrong.npz")["valid"])
            self.assertEqual(grade_arrays(p, arrays, echo_reference(p))["status"], "wrong_answer")

    def test_standard_storage_layout_compression_and_byte_order(self):
        p, arrays = self.output()
        original = arrays["velocity"].copy()
        for array in (np.asfortranarray(original), original.astype(">f8")):
            arrays["velocity"] = array
            np.savez_compressed(self.root / "standard.npz", **arrays)
            self.assertEqual(grade_arrays(p, load_result(p, self.root / "standard.npz"), echo_reference(p))["score"], 1)
            np.testing.assert_array_equal(arrays["velocity"], original)

    def test_object_arrays_and_corrupt_npz(self):
        self.bad_output(lambda a: a.update(velocity=np.array([{}], dtype=object)), "E_NPZ")
        (self.root / "bad.npz").write_bytes(b"not a zip")
        self.assertIn("E_NPZ", self.codes(validate_output(self.path, self.root / "bad.npz")))

    def test_duplicate_or_nested_npz_members(self):
        stream = io.BytesIO()
        np.save(stream, np.zeros(1))
        for entries in (["velocity.npy", "velocity.npy"], ["folder/velocity.npy"], ["metadata.txt"]):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(self.root / "bad.npz", "w") as archive:
                    for entry in entries:
                        archive.writestr(entry, stream.getvalue())
            self.assertIn("E_NPZ", self.codes(validate_output(self.path, self.root / "bad.npz")))

    def test_metadata_missing_unknown_and_types(self):
        original = deepcopy(self.m)
        for change in (lambda m: m.pop("spatial_dimension"),
                       lambda m: m.update(dataset={}), lambda m: m.update(spatial_dimension=2.0),
                       lambda m: m.update(spatial_dimension=True)):
            self.m = deepcopy(original)
            change(self.m)
            self.bad_input("E_SCHEMA")

    def test_duplicate_json_and_overflow(self):
        self.path.write_text('{"task":"echo","task":"other"}', encoding="utf-8")
        self.assertIn("E_DUPLICATE_KEY", self.codes(validate_input(self.path)))
        self.m["physics"] = {"model": "anything", "parameters": {"k": {"value": 1.0, "unit": "1"}}}
        self.save()
        self.path.write_text(self.path.read_text().replace('"value": 1.0', '"value": 1e999'), encoding="utf-8")
        self.assertIn("E_FINITE", self.codes(validate_input(self.path)))

    def test_input_extra_arrays_and_role_collision(self):
        self.a["unused"] = np.zeros(1)
        self.bad_input("E_ARRAYS")
        del self.a["unused"]
        self.m["fields"]["velocity"]["array"] = "node_ids"
        self.bad_input("E_ARRAY")

    def test_id_order_uniqueness_type_and_references(self):
        original = self.a["node_ids"].copy()
        for value, code in ((original[::-1], "E_ID"), (np.full_like(original, original[0]), "E_ID"),
                            (original + 100000, "E_REFERENCE"), (original.astype("float64"), "E_DTYPE")):
            self.a["node_ids"] = value
            self.bad_input(code)

    def test_time_order_and_missing_reference(self):
        self.a["times"] = np.array([1.0, 1.0])
        self.bad_input("E_TIME")
        self.a["times"] = np.array([0.0])
        self.m["fields"]["velocity"]["time_axis"] = "missing"
        self.bad_input("E_REFERENCE")

    def test_vector_tensor_metadata(self):
        self.m["fields"]["velocity"]["components"] = ["y", "x"]
        self.bad_input("E_COMPONENTS")
        self.copy_case("10-full-tensor")
        self.m["outputs"]["stress"]["component_shape"] = [4]
        self.bad_input("E_COMPONENTS")

    def test_package_relative_file_rules(self):
        for value in ("../input.npz", "C:/temp/input.npz", "/input.npz", "foo\\input.npz", "absent.npz", "mesh.msh"):
            self.m["data_file"] = value
            self.bad_input("E_FILE")

    def test_mesh_version_and_topology_dimension(self):
        (self.case / "mesh.msh").write_text("$MeshFormat\n2.2 0 8\n", encoding="ascii")
        self.bad_input("E_MESH")
        self.copy_case("04-tetra-3d")
        self.m["spatial_dimension"] = 2
        self.bad_input("E_DIMENSION")

    def test_geometry_is_a_reference_not_executed_code(self):
        self.m["meshes"]["main"]["geometry"] = "missing"
        self.bad_input("E_REFERENCE")
        self.m["meshes"]["main"]["geometry"] = "shape"
        (self.case / "mesh.geo").write_text("not an executable geometry script", encoding="utf-8")
        self.save()
        self.assertTrue(validate_input(self.path)["valid"])

    def test_physical_group_reference_and_membership(self):
        self.copy_case("11-field-locations")
        self.m["locations"]["left"]["physical_group"]["tag"] = 999
        self.bad_input("E_REFERENCE")
        self.m["locations"]["left"]["physical_group"]["tag"] = 2
        self.a["left_ids"] = self.a["left_ids"][:1]
        self.bad_input("E_ID")

    def test_element_dimension_and_point_value(self):
        self.copy_case("05-mixed-blocks")
        self.m["locations"]["cells"].pop("dimension")
        self.bad_input("E_METADATA")
        self.m["locations"]["cells"]["dimension"] = 2
        self.m["fields"]["cell_temperature"]["value_kind"] = "point"
        self.bad_input("E_METADATA")

    def test_point_coordinate_shape(self):
        self.copy_case("11-field-locations")
        self.a["probe_coordinates"] = self.a["probe_coordinates"][:, :1]
        self.bad_input("E_SHAPE")

    def test_condition_references_and_locations(self):
        self.copy_case("11-field-locations")
        self.m["conditions"][0]["data"]["value"]["field"] = "missing"
        self.bad_input("E_REFERENCE")
        self.m["conditions"][0]["data"]["value"]["field"] = "temperature"
        self.bad_input("E_METADATA")

    def test_nonphysical_values_are_not_checked(self):
        self.copy_case("11-field-locations")
        self.m["physics"]["parameters"]["conductivity"]["value"] = -100
        self.m["conditions"][1]["data"]["value"]["value"] = -99999
        self.a["temperature"][:] = -100000
        self.save()
        self.assertTrue(validate_input(self.path)["valid"])

    def test_protocol_accepts_general_tasks_and_new_output_fields(self):
        self.m["task"] = "heat-or-any-other-pde"
        self.m["fields"] = {}
        del self.a["velocity"]
        self.m["outputs"]["velocity"]["quantity"] = "new_unknown_quantity"
        self.save()
        self.assertTrue(validate_input(self.path)["valid"])

    def test_document_json_and_complete_example_match_protocol(self):
        document = (PROJECT_ROOT / "docs/CONTRACT.md").read_text(encoding="utf-8")
        full_examples = 0
        for source in re.findall(r"```json\n(.*?)\n```", document, flags=re.DOTALL):
            value = json.loads(source)
            if "data_file" in value and "outputs" in value:
                write_json(self.path, value)
                self.assertTrue(validate_input(self.path)["valid"])
                full_examples += 1
        self.assertEqual(full_examples, 1)

    def test_multiple_meshes_and_time_axes(self):
        self.m["meshes"]["second"] = {"file": "mesh.msh"}
        self.m["locations"]["second_nodes"] = {"kind": "mesh", "mesh": "second", "entity": "node", "ids": "second_ids"}
        self.a["second_ids"] = self.a["node_ids"].copy()
        self.a["transient_times"] = np.array([-1.0, 0.0, 2.5])
        self.m["time_axes"]["transient"] = "transient_times"
        self.save()
        self.assertTrue(validate_input(self.path)["valid"])

    def test_point_only_dataset(self):
        self.m["meshes"], self.m["geometries"] = {}, {}
        self.m["locations"]["nodes"] = {"kind": "points", "ids": "node_ids", "coordinates": "coords"}
        self.a["coords"] = np.zeros((len(self.a["node_ids"]), 2), dtype=np.float64)
        self.save()
        self.assertTrue(validate_input(self.path)["valid"])

    def test_embedded_surface_uses_three_dimensional_space(self):
        self.copy_case("02-triangle-2d")
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.open(str(self.case / "mesh.msh"))
            tags, coords, _ = gmsh.model.mesh.getNodes()
            for tag, coord in zip(tags, np.asarray(coords).reshape(-1, 3)):
                gmsh.model.mesh.setNode(int(tag), [coord[0], coord[1], coord[0]], [])
            gmsh.write(str(self.case / "mesh.msh"))
        finally:
            gmsh.finalize()
        self.bad_input("E_DIMENSION")
        self.m["spatial_dimension"] = 3
        self.save()
        self.assertTrue(validate_input(self.path)["valid"])

    def test_sdk_preserves_existing_gmsh_model(self):
        gmsh.initialize([], readConfigFiles=False)
        try:
            gmsh.option.setNumber("General.Terminal", 0)
            gmsh.model.add("solver_model")
            gmsh.model.geo.addPoint(9, 8, 7)
            gmsh.model.geo.synchronize()
            models, entities = gmsh.model.list(), gmsh.model.getEntities()
            load_problem(self.path)
            self.assertEqual(gmsh.model.getCurrent(), "solver_model")
            self.assertEqual(gmsh.model.list(), models)
            self.assertEqual(gmsh.model.getEntities(), entities)
        finally:
            gmsh.finalize()

    def test_reserved_array_keys_are_rejected(self):
        for key in ("file", "allow_pickle"):
            self.m["outputs"]["velocity"]["array"] = key
            self.bad_input("E_SCHEMA")

    def test_sdk_does_not_repair_or_mutate_data(self):
        p, arrays = self.output()
        before = {k: a.copy() for k, a in p.arrays.items()}
        self.assertEqual(id_to_row(target_ids(p, "nodes"))[int(p.arrays["node_ids"][0])], 0)
        with self.assertRaises(ContractError):
            write_result(self.root / "refused.npz", p, {"velocity": arrays["velocity"][0]})
        self.assertFalse((self.root / "refused.npz").exists())
        for key, a in before.items():
            np.testing.assert_array_equal(a, p.arrays[key])

    def test_sdk_reads_constant_and_field_without_guessing_or_converting(self):
        constant = {"value": 3.0, "unit": "cm"}
        self.assertEqual(read_constant(constant), 3.0)
        self.assertEqual(constant["unit"], "cm")
        # Field names may differ from the NPZ key; this is a real valid input.
        self.m["fields"]["flow"] = self.m["fields"].pop("velocity")
        self.save()
        problem = load_problem(self.path)
        values = read_field(problem, {"field": "flow"})
        self.assertIs(values, problem.arrays["velocity"])
        np.testing.assert_array_equal(values, self.a["velocity"])
        self.assertEqual(values.shape, self.a["velocity"].shape)
        self.assertEqual(values.dtype, self.a["velocity"].dtype)
        with self.assertRaisesRegex(KeyError, 'field name, not the NPZ key'):
            read_field(problem, {"field": "velocity"})

    def test_sdk_wrong_data_source_has_actionable_error(self):
        problem = load_problem(self.path)
        with self.assertRaisesRegex(TypeError, 'use read_field'):
            read_constant({"field": "velocity"})
        with self.assertRaisesRegex(TypeError, 'use read_constant'):
            read_field(problem, {"value": 1.0, "unit": "K"})
        with self.assertRaises(TypeError):
            read_constant(1.0)

    def test_cli_json_diagnostics_and_exit_codes(self):
        result = subprocess.run([sys.executable, "-m", "caeoj", "validate-input", str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["valid"])
        result = subprocess.run([sys.executable, "-m", "caeoj", "validate-output", "--input", str(self.path),
                                 "--output", str(self.root / "absent.npz")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["valid"])

    def test_smoke_twelve_processes(self):
        result = run_smoke(CASES, PROJECT_ROOT / "tasks/echo-field/solve.py", self.root / "report.json")
        self.assertEqual(result["passed_cases"], 12)
        self.assertTrue(result["passed"])

    def test_smoke_wrong_values_with_valid_contract(self):
        program = self.root / "wrong.py"
        program.write_text('''import argparse
from caeoj.sdk import load_problem, write_result
p=argparse.ArgumentParser(); p.add_argument("--input"); p.add_argument("--output"); a=p.parse_args()
problem=load_problem(a.input)
fields={s["array"]:problem.arrays[s["array"]].copy() for s in problem.manifest["outputs"].values()}
for s in problem.manifest["outputs"].values():
    if s["kind"] == "vector": fields[s["array"]]=fields[s["array"]][...,::-1].copy()
write_result(a.output,problem,fields)
''', encoding="utf-8")
        result = run_smoke(CASES, program, self.root / "wrong_report.json")
        self.assertEqual(result["passed_cases"], 9)
        self.assertEqual(sum(r["status"] == "wrong_answer" for r in result["cases"]), 3)

    def test_runner_failure_statuses_and_bad_input(self):
        mini = self.root / "mini"
        shutil.copytree(self.case, mini / self.case.name)
        for source, status in (("raise RuntimeError('fail')", "runtime_error"), ("pass", "missing_output"),
                               ("import time; time.sleep(2)", "timeout")):
            program = self.root / "failure.py"
            program.write_text(source, encoding="utf-8")
            result = run_smoke(mini, program, self.root / "failed.json", timeout=0.5)
            self.assertEqual(result["cases"][0]["status"], status)
            self.assertEqual(result["score"], 0)
        (mini / self.case.name / "problem.json").write_text("{}", encoding="utf-8")
        result = run_smoke(mini, program, self.root / "failed.json")
        self.assertEqual(result["cases"][0]["status"], "input_error")
        self.assertIsNone(result["score"])


if __name__ == "__main__":
    unittest.main()
