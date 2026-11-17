"""Import safeguards for the reviewed Solid26 cases using synthetic file bytes."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
IMPORTER_PATH = ROOT / 'qbank/maintenance/authoring/import_reviewed_solids.py'
ROSTER = (
    'elastic-solid-3d', 'elastic-beam', 'elastic-modes', 'elastic-transient',
    'hyperelastic-solid', 'elastic-buckling', 'j2-plasticity',
    'linear-elastic-fracture',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_importer():
    spec = importlib.util.spec_from_file_location('import_reviewed_solids', IMPORTER_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f'cannot load importer at {IMPORTER_PATH}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reviewed_fixture(base):
    """Create the actual manifest/acceptance shape without real solver data."""
    source = base / 'reviewed-source'
    project = base / 'project'
    source.mkdir()
    ordered_tasks = []
    acceptance_cases = []
    for task_index, slug in enumerate(ROSTER):
        source_path = f'qbank/03-solid-mechanics/synthetic/{slug}'
        copied_files = []
        for filename in ('instruction.md', 'DATA.md', 'author/grading-template.json',
                         'judge-config.json', 'harbor/task.toml'):
            protocol = project / source_path / filename
            protocol.parent.mkdir(parents=True, exist_ok=True)
            protocol.write_bytes(f'synthetic protocol {slug} {filename}\n'.encode())
            copied_files.append({'path': filename, 'sha256': digest(protocol)})
        ordered_tasks.append({
            'slug': slug,
            'source_path': source_path,
            'local_path': f'tasks/{slug}',
            'copied_files': copied_files,
        })

        # Two one-case tasks and six four-case tasks make 26 total. Each task
        # has one public case; the remaining 18 cases are held out.
        n_cases = 1 if slug in {'elastic-buckling', 'linear-elastic-fracture'} else 4
        for case_index in range(n_cases):
            case_id = f'{slug}-case-{case_index + 1}'
            role = 'public' if case_index == 0 else 'held-out'
            case_dir = f'cases/{slug}/{case_id}'
            case_root = source / case_dir
            (case_root / 'input').mkdir(parents=True)
            (case_root / 'reference').mkdir(parents=True)
            (case_root / 'reports').mkdir(parents=True)
            files = {
                f'{case_dir}/input/mesh.synthetic': f'input mesh {case_id}\n'.encode(),
                f'{case_dir}/input/problem.synthetic': f'input problem {case_id}\n'.encode(),
                f'{case_dir}/reference/reference.synthetic': f'reference bytes {case_id}\n'.encode(),
                f'{case_dir}/reference/grading.synthetic': f'grading bytes {case_id}\n'.encode(),
                f'{case_dir}/reference/reference-record.json': json.dumps(
                    {'case_id': case_id, 'note': 'synthetic provenance'},
                ).encode(),
            }
            if case_index == 0:
                files[f'{case_dir}/reports/physics-verification.json'] = json.dumps(
                    {'case_id': case_id, 'note': 'synthetic report'},
                ).encode()
            baseline_result = f'reports/solid26/outputs/{slug}/{case_id}/result.synthetic'
            baseline_report = f'reports/solid26/outputs/{slug}/{case_id}/validation.json'
            files[baseline_result] = f'legacy baseline output {case_id}\n'.encode()
            files[baseline_report] = json.dumps({'valid': True, 'synthetic': True}).encode()
            artifact_sha256 = {}
            for relative, payload in files.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                artifact_sha256[relative] = digest(path)
            acceptance_cases.append({
                'task': slug,
                'case_id': case_id,
                'role': role,
                'case_dir': case_dir,
                'input_valid': True,
                'reference_valid': True,
                'baseline_valid': True,
                'grader_score': 1,
                'reference_budget': {'independent_eta': 0.05, 'mesh_eta': 0.1},
                'baseline_result': baseline_result,
                'baseline_report': baseline_report,
                'artifact_sha256': artifact_sha256,
            })

    task_manifest = {'schema_version': 1, 'status': 'local_experiment',
                     'ordered_tasks': ordered_tasks}
    acceptance = {
        'schema_version': 1,
        'status': 'passed',
        'published': False,
        'counts': {'tasks': 8, 'cases': 26, 'public': 8, 'held_out': 18},
        'frozen_anchor_files_unchanged': 52,
        'source_contract_files_unchanged': 40,
        'cases': acceptance_cases,
    }
    (source / 'task-manifest.json').write_text(json.dumps(task_manifest), encoding='utf-8')
    acceptance_path = source / 'reports/solid26/acceptance.json'
    acceptance_path.parent.mkdir(parents=True, exist_ok=True)
    acceptance_path.write_text(json.dumps(acceptance), encoding='utf-8')
    return source, project, task_manifest, acceptance


class ImportReviewedSolidsTests(unittest.TestCase):
    def test_native_tools_load_outside_test_runner_import_paths(self):
        # The Harbor maintenance script uses flat imports from src/utils.
        # A clean process must reach source validation without test path setup.
        with tempfile.TemporaryDirectory() as tmp:
            missing = (Path(tmp) / 'missing-reviewed-source').resolve()
            code = (
                'import importlib.util\n'
                f'spec = importlib.util.spec_from_file_location("importer", {str(IMPORTER_PATH)!r})\n'
                'module = importlib.util.module_from_spec(spec)\n'
                'spec.loader.exec_module(module)\n'
                'try:\n'
                f'    module.build_import({str(missing)!r}, "unused", {str(ROOT)!r}, {{}}, "unused")\n'
                'except FileNotFoundError as error:\n'
                f'    assert error.filename == {str(missing / "task-manifest.json")!r}\n'
            )
            env = dict(os.environ, PYTHONPATH=os.pathsep.join(
                str(ROOT / name) for name in ('src', 'qbank/extensions')))
            result = subprocess.run([sys.executable, '-c', code], cwd=tmp,
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_loads_exact_roster_and_reviewed_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, project, manifest, acceptance = reviewed_fixture(Path(tmp))
            loaded = load_importer().load_reviewed(source, project)
            self.assertEqual(set(loaded), {'task_manifest', 'acceptance'})
            self.assertEqual(loaded['task_manifest'], manifest)
            self.assertEqual(loaded['acceptance'], acceptance)
            tasks = loaded['task_manifest']['ordered_tasks']
            self.assertEqual(tuple(task['slug'] for task in tasks), ROSTER)
            self.assertEqual(acceptance['counts'], {
                'tasks': 8, 'cases': 26, 'public': 8, 'held_out': 18,
            })
            self.assertEqual([sum(row['task'] == task for row in acceptance['cases'])
                              for task in ROSTER], [4, 4, 4, 4, 4, 1, 4, 1])
            for row in acceptance['cases']:
                self.assertEqual(row['grader_score'], 1)
                for eta in row['reference_budget'].values():
                    self.assertTrue(math.isfinite(eta) and 0 <= eta < .2)

    def test_rejects_tampered_declared_source_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, project, _, acceptance = reviewed_fixture(Path(tmp))
            row = acceptance['cases'][0]
            relative = next(path for path in row['artifact_sha256'] if '/input/' in path)
            target = source / relative
            target.write_bytes(target.read_bytes() + b'tampered')
            with self.assertRaises(ValueError):
                load_importer().load_reviewed(source, project)

    def test_rejects_modified_repository_protocol_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, project, manifest, _ = reviewed_fixture(Path(tmp))
            task = manifest['ordered_tasks'][0]
            protocol = project / task['source_path'] / task['copied_files'][0]['path']
            protocol.write_bytes(b'modified project protocol\n')
            with self.assertRaises(ValueError):
                load_importer().load_reviewed(source, project)

    def test_stages_public_first_stable_aliases_and_exact_source_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, project, _, acceptance = reviewed_fixture(Path(tmp))
            loaded = load_importer().load_reviewed(source, project)
            task = loaded['task_manifest']['ordered_tasks'][2]
            rows = [row for row in loaded['acceptance']['cases'] if row['task'] == task['slug']]
            rows.reverse()  # caller order cannot alter alias order
            destination = Path(tmp) / 'stage'
            result = load_importer().stage_task(source, task, rows, destination)

            ordered_rows = sorted(rows, key=lambda row: (row['role'] != 'public', row['case_id']))
            expected_aliases = {
                row['case_id']: f'{index:03d}'
                for index, row in enumerate(ordered_rows, 1)
            }
            self.assertEqual(result['aliases'], expected_aliases)
            for row in ordered_rows:
                case_id = row['case_id']
                alias = expected_aliases[case_id]
                original = source / row['case_dir']
                staged_input = destination / 'cases' / alias
                staged_reference = destination / 'reference' / alias
                for path in (original / 'input').iterdir():
                    self.assertEqual((staged_input / path.name).read_bytes(), path.read_bytes())
                for path in (original / 'reference').iterdir():
                    if path.name == 'reference-record.json':
                        continue
                    self.assertEqual((staged_reference / path.name).read_bytes(), path.read_bytes())
                record = destination / 'author/data-evidence/source-cases' / alias / 'reference-record.original.json'
                self.assertEqual(record.read_bytes(),
                                 (original / 'reference/reference-record.json').read_bytes())
                report = original / 'reports/physics-verification.json'
                archived_report = destination / 'author/data-evidence/source-cases' / alias / 'physics-verification.json'
                if report.exists():
                    self.assertEqual(archived_report.read_bytes(), report.read_bytes())
                else:
                    self.assertFalse(archived_report.exists())
                if row['role'] == 'public':
                    sample = destination / 'samples/001/input'
                    for path in (original / 'input').iterdir():
                        self.assertEqual((sample / path.name).read_bytes(), path.read_bytes())
            self.assertFalse((destination / 'samples/001/output').exists())
            self.assertFalse(any((destination / 'samples').rglob('result.synthetic')))
            self.assertFalse(any((destination / 'samples').rglob('reference-record.json')))

    def test_refuses_preexisting_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, project, _, acceptance = reviewed_fixture(Path(tmp))
            loaded = load_importer().load_reviewed(source, project)
            task = loaded['task_manifest']['ordered_tasks'][2]
            rows = [row for row in acceptance['cases'] if row['task'] == task['slug']]
            destination = Path(tmp) / 'already-there'
            destination.mkdir()
            with self.assertRaises((FileExistsError, ValueError)):
                load_importer().stage_task(source, task, rows, destination)


if __name__ == '__main__':
    unittest.main()
