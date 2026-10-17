"""Public release isolation, reproducibility and standalone checker usability."""
from caeoj.storage import write_hdf5
from caeoj.validation import read_hdf5
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from caeoj_tools.author import PROJECT_ROOT
from task_fixtures import project_fixture
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
        self.project = project_fixture(self.root/"project", ["heat-conduction-steady-2d", "heat-conduction-transient-2d"])

    def extracted_bundle(self):
        report = publisher.publish("heat-conduction-steady-2d", self.root / "dist", self.project)
        extracted = self.root / "agent"
        with zipfile.ZipFile(report["archive"]) as bundle:
            bundle.extractall(extracted)
        return extracted, report

    def test_manifest_reproducibility_and_public_only_contents(self):
        first = publisher.publish("heat-conduction-steady-2d", self.root, self.project)
        second = publisher.publish("heat-conduction-steady-2d", self.root, self.project)
        self.assertEqual(first["sha256"], second["sha256"])
        with zipfile.ZipFile(first["archive"]) as bundle:
            names = bundle.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertIn("src/caeoj/problem.schema.json", names)
            self.assertIn("src/caeoj/storage.py", names)
            self.assertIn("qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/01/output/result.h5", names)
            self.assertIn("qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/02/output/result.h5", names)
            self.assertFalse(any(part in {"author", "cases", "__pycache__", "runs", ".git"}
                                 for name in names for part in Path(name).parts))
            self.assertFalse(any(name.endswith(("baseline.py", "TEST-CASES.md")) for name in names))
            self.assertNotIn("src/caeoj/examples.py", names)
            self.assertNotIn("src/caeoj/smoke.py", names)
            self.assertFalse(any(name.endswith("verification.json") for name in names))
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
            ["validate-input", "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/01/input/problem.json"],
            ["validate-output", "--input", "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/01/input/problem.json",
             "--output", "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/01/output/result.h5"],
            ["validate-input", "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/02/input/problem.json"],
            ["validate-output", "--input", "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/02/input/problem.json",
             "--output", "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/02/output/result.h5"],
        ]
        for command in commands:
            execution = subprocess.run([sys.executable, "-m", "caeoj", *command], cwd=root, env=env,
                                       capture_output=True, text=True, timeout=30)
            self.assertEqual(execution.returncode, 0, execution.stderr)
            self.assertTrue(json.loads(execution.stdout)["valid"])
        module = subprocess.run([sys.executable, "-c", "import caeoj; print(caeoj.__file__)"],
                                cwd=root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(Path(module.stdout.strip()).resolve(), (root / "src/caeoj/__init__.py").resolve())
        help_result = subprocess.run([sys.executable, "-m", "caeoj", "--help"],
                                     cwd=root, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("validate-output", help_result.stdout)
        self.assertNotIn("make-cases", help_result.stdout)
        self.assertNotIn("smoke", help_result.stdout)
        for sample in ("01", "02"):
            execution = subprocess.run(
                [sys.executable, "-m", "caeoj", "grade", "--input",
                 f"qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/{sample}/input/problem.json", "--output",
                 f"qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/{sample}/output/result.h5", "--grading",
                 f"qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/{sample}/reference/grading.json"],
                cwd=root, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(execution.returncode, 0, execution.stderr)
            self.assertEqual(json.loads(execution.stdout)["score"], 1)

    def test_unlisted_files_never_enter_release(self):
        root, _ = self.extracted_bundle()
        for name in (".env", "src/caeoj/secret.py", "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/author/baseline.py",
                     "src/caeoj/examples.py", "src/caeoj/smoke.py",
                     "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/01/verification.json",
                     "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/01/input/notes.txt"):
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("PRIVATE MATERIAL", encoding="utf-8")
        files, _ = publisher.collect_materials("heat-conduction-steady-2d", root)
        self.assertFalse(any(b"PRIVATE MATERIAL" in data for data in files.values()))

    def test_quantity_policy_runs_from_extracted_bundle_with_varying_logical_names(self):
        root, _ = self.extracted_bundle()
        task = root / 'qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d'
        policy = {'version': 2, 'quantities': {'temperature': {'unit': 'K', 'rule': {
            'metric': 'pointwise', 'time': 'per_time', 'components': 'per_component',
            'atol': .01, 'rtol': 0}}}}
        from caeoj_tools.grading_policy import write_direct_grading
        for reference in (task/'samples').glob('*/reference'):
            write_direct_grading(reference, policy)
        path = task / 'samples/02/input/problem.json'
        manifest = json.loads(path.read_text(encoding='utf-8'))
        manifest['outputs']['other_name'] = manifest['outputs'].pop('temperature')
        path.write_text(json.dumps(manifest))
        released = publisher.publish('heat-conduction-steady-2d', self.root / 'quantity-dist', root)
        extracted = self.root / 'quantity-agent'
        with zipfile.ZipFile(released['archive']) as bundle:
            bundle.extractall(extracted)
        env = os.environ.copy(); env['PYTHONPATH'] = str(extracted / 'src')
        task_path = task.relative_to(root)
        for sample in ('01', '02'):
            sample_path = task_path / f'samples/{sample}'
            command = [sys.executable, '-m', 'caeoj', 'grade', '--input', str(sample_path / 'input/problem.json'),
                '--output', str(sample_path / 'output/result.h5'),
                '--grading', str(sample_path / 'reference/grading.json')]
            result = subprocess.run(command, cwd=extracted, env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertIn('evaluation_sha256', report)
            self.assertEqual(report['score'], 1)

    def test_invalid_public_output_does_not_replace_existing_release(self):
        root, _ = self.extracted_bundle()
        release = publisher.publish("heat-conduction-steady-2d", self.root / "new-dist", root)
        archive = Path(release["archive"])
        before = archive.read_bytes()
        result = root / "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples/01/output/result.h5"
        arrays = read_hdf5(result)
        arrays["temperature"] = arrays["temperature"][0]
        write_hdf5(result, arrays)
        with self.assertRaises(ContractError):
            publisher.publish("heat-conduction-steady-2d", self.root / "new-dist", root)
        self.assertEqual(archive.read_bytes(), before)

    def test_bad_task_names_and_missing_samples_fail(self):
        for name in ("../heat-conduction-steady-2d", "/tmp", "heat-conduction-steady-2d/author"):
            with self.assertRaises(ValueError):
                publisher.collect_materials(name, self.project)
        root, _ = self.extracted_bundle()
        shutil.rmtree(root / "qbank/01-prescribed-pdes/1.1-elliptic/heat-conduction-steady-2d/samples")
        with self.assertRaisesRegex(ValueError, "No complete public samples"):
            publisher.collect_materials("heat-conduction-steady-2d", root)

    def test_public_preflight_uses_staged_binding_and_checks_hook(self):
        from caeoj_tools.assembly import validate_public_runtime
        files, _ = publisher.collect_materials('heat-conduction-steady-2d', self.project)
        key='src/caeoj_bundle/runtime.json'
        data=json.loads(files[key])
        data['extensions']['task.broken']={'version':1,'requires':[], 'check':'caeoj_task_ext.probe:check'}
        data['tasks']['heat-conduction-steady-2d']=['task.broken']
        files[key]=json.dumps(data).encode()
        files['src/caeoj_task_ext/__init__.py']=b''
        files['src/caeoj_task_ext/probe.py']=b'def other(): pass\n'
        with self.assertRaisesRegex(ValueError,'probe:check'):
            validate_public_runtime(files)

    def test_multitask_package_switches_contracts_without_reinstallation(self):
        tasks = ['heat-conduction-steady-2d', 'heat-conduction-transient-2d']
        result = publisher.publish(tasks, self.root/'multi-dist', self.project)
        extracted = self.root/'multi-agent'
        with zipfile.ZipFile(result['archive']) as bundle:
            manifest = json.loads(bundle.read('MANIFEST.json'))
            self.assertEqual(manifest['tasks'], sorted(tasks))
            bundle.extractall(extracted)
        code = r"""
import json
from pathlib import Path
from caeoj.sdk import load_problem
from caeoj.grading_policy import load_policy
from caeoj.runtime import describe
paths = sorted(Path('qbank').glob('*/*/*/samples/01/input/problem.json'))
assert len(paths)==2
for path in paths+paths[::-1]:
    problem=load_problem(path)
    assert describe(problem.manifest)['scope']=='task-contract'
    sample=path.parent.parent
    from caeoj.case_grading import prepare_case
    prepare_case(problem, path.parent.parent/'reference/grading.json')
    from caeoj.case_grading import grade_case
    result=grade_case(path,sample/'output/result.h5',sample/'reference/grading.json')
    assert result['score']==1,result
print('multi-task: four alternating reads and grades passed')
"""
        environment = {**os.environ,'PYTHONPATH':str(extracted/'src')}
        execution=subprocess.run([sys.executable,'-c',code],cwd=extracted,env=environment,
                                 capture_output=True,text=True,timeout=30)
        self.assertEqual(execution.returncode,0,execution.stdout+execution.stderr)
        self.assertIn('four alternating',execution.stdout)


class DomainPublishTests(unittest.TestCase):
    def test_radiation_and_microstructure_bundle_with_disposable_samples(self):
        from importlib import import_module
        import numpy as np
        from caeoj.sdk import load_problem, write_result
        from caeoj_tools.grading_policy import author_policy, write_direct_grading
        from caeoj_tools.task_paths import task_directory
        with tempfile.TemporaryDirectory() as temporary:
            root = project_fixture(Path(temporary)/'project', [])
            tasks = []
            for domain in ('radiation', 'microstructure'):
                fixture = import_module(domain+'_fixture').fixture
                for slug in import_module('caeoj_ext.'+domain).models():
                    source = task_directory(slug, PROJECT_ROOT)
                    task = root/source.relative_to(PROJECT_ROOT)
                    sample = task/'samples/01'
                    path, manifest = fixture(sample/'input', slug)
                    for name in ('instruction.md', 'DATA.md'):
                        shutil.copyfile(source/name, task/name)
                    problem = load_problem(path)
                    values = {s['array']: np.zeros((
                        len(problem.arrays[manifest['time_axes'][s['time_axis']]]),
                        len(problem.arrays[manifest['locations'][s['location']]['ids']]),
                        *s['component_shape'])) for s in manifest['outputs'].values()}
                    write_result(sample/'output/result.h5', problem, values)
                    write_result(sample/'reference/reference.h5', problem, values)
                    write_direct_grading(sample/'reference', author_policy(source, problem))
                    tasks.append(slug)
            report = publisher.publish(tasks, Path(temporary)/'dist', root)
            with zipfile.ZipFile(report['archive']) as bundle:
                manifest = json.loads(bundle.read('MANIFEST.json'))
                self.assertEqual(manifest['tasks'], sorted(tasks))
                self.assertEqual(len(tasks), 15)
                self.assertFalse(any('author' in Path(name).parts for name in bundle.namelist()))
                runtime = json.loads(bundle.read('src/caeoj_bundle/runtime.json'))
                self.assertEqual(set(runtime['extensions']), {'radiation.nuclear', 'microstructure.phase_field'})


if __name__ == "__main__":
    unittest.main()
