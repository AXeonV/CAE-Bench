"""Public release isolation, reproducibility and standalone checker usability."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

import numpy as np

from caeoj.smoke import PROJECT_ROOT
from caeoj.validation import ContractError

spec = importlib.util.spec_from_file_location("publish_dist", PROJECT_ROOT / "src/utils/publish_dist.py")
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PublishTests(unittest.TestCase):
    def setUp(self):
        (PROJECT_ROOT / "runs").mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=PROJECT_ROOT / "runs")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def extracted_bundle(self):
        report = publisher.publish("heat-conduction", self.root / "dist")
        extracted = self.root / "agent"
        with zipfile.ZipFile(report["archive"]) as bundle:
            bundle.extractall(extracted)
        return extracted, report

    def test_manifest_reproducibility_and_public_only_contents(self):
        first = publisher.publish("heat-conduction", self.root)
        second = publisher.publish("heat-conduction", self.root)
        self.assertEqual(first["sha256"], second["sha256"])
        with zipfile.ZipFile(first["archive"]) as bundle:
            names = bundle.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertIn("src/caeoj/problem.schema.json", names)
            self.assertIn("tasks/heat-conduction/samples/01/output/result.npz", names)
            self.assertIn("tasks/heat-conduction/samples/02/output/result.npz", names)
            self.assertFalse(any(part in {"author", "cases", "reference", "__pycache__", "runs", ".git"}
                                 for name in names for part in Path(name).parts))
            self.assertFalse(any(name.endswith(("baseline.py", "TEST-CASES.md", "MVP-PLAN.md")) for name in names))
            manifest = json.loads(bundle.read("MANIFEST.json"))
            self.assertEqual(manifest["public_samples"], ["01", "02"])
            self.assertEqual(set(manifest["files"]), set(names) - {"MANIFEST.json"})
            for name, checksum in manifest["files"].items():
                self.assertEqual(checksum, hashlib.sha256(bundle.read(name)).hexdigest())

    def test_extracted_bundle_checks_input_and_output_without_source_checkout(self):
        root, _ = self.extracted_bundle()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "src")
        commands = [
            ["validate-input", "tasks/heat-conduction/samples/01/input/problem.json"],
            ["validate-output", "--input", "tasks/heat-conduction/samples/01/input/problem.json",
             "--output", "tasks/heat-conduction/samples/01/output/result.npz"],
            ["validate-input", "tasks/heat-conduction/samples/02/input/problem.json"],
            ["validate-output", "--input", "tasks/heat-conduction/samples/02/input/problem.json",
             "--output", "tasks/heat-conduction/samples/02/output/result.npz"],
        ]
        for command in commands:
            execution = subprocess.run([sys.executable, "-m", "caeoj", *command], cwd=root, env=env,
                                       capture_output=True, text=True, timeout=30)
            self.assertEqual(execution.returncode, 0, execution.stderr)
            self.assertTrue(json.loads(execution.stdout)["valid"])
        module = subprocess.run([sys.executable, "-c", "import caeoj; print(caeoj.__file__)"],
                                cwd=root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(Path(module.stdout.strip()).resolve(), (root / "src/caeoj/__init__.py").resolve())

    def test_unlisted_files_never_enter_release(self):
        root, _ = self.extracted_bundle()
        for name in (".env", "src/caeoj/secret.py", "tasks/heat-conduction/author/baseline.py",
                     "tasks/heat-conduction/samples/01/input/notes.txt"):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PRIVATE MATERIAL", encoding="utf-8")
        files, _ = publisher.collect_materials("heat-conduction", root)
        self.assertFalse(any(b"PRIVATE MATERIAL" in data for data in files.values()))

    def test_invalid_public_output_does_not_replace_existing_release(self):
        root, _ = self.extracted_bundle()
        release = publisher.publish("heat-conduction", self.root / "new-dist", root)
        archive = Path(release["archive"])
        before = archive.read_bytes()
        result = root / "tasks/heat-conduction/samples/01/output/result.npz"
        with np.load(result, allow_pickle=False) as data:
            arrays = {key: data[key] for key in data.files}
        arrays["temperature"] = arrays["temperature"][0]
        np.savez(result, **arrays)
        with self.assertRaises(ContractError):
            publisher.publish("heat-conduction", self.root / "new-dist", root)
        self.assertEqual(archive.read_bytes(), before)

    def test_bad_task_names_and_missing_samples_fail(self):
        for name in ("../heat-conduction", "/tmp", "heat-conduction/author"):
            with self.assertRaises(ValueError):
                publisher.collect_materials(name)
        with self.assertRaisesRegex(ValueError, "No complete public samples"):
            publisher.collect_materials("echo-field")


if __name__ == "__main__":
    unittest.main()
