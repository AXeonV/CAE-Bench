"""Check public/private task separation and Harbor score aggregation."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TASK = 'heat-conduction'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


sys.path.insert(0, str(ROOT / 'src/utils'))
try:
    import publish_dist as publisher
    prepare = module('prepare_harbor', ROOT / 'src/utils/prepare_harbor.py')
finally:
    sys.path.pop(0)
judge = module('harbor_judge', ROOT / 'tasks/heat-conduction/harbor/tests/judge.py')


class HarborTests(unittest.TestCase):
    def setUp(self):
        (ROOT / 'runs').mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=ROOT / 'runs')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        files, _ = publisher.collect_materials(TASK)
        for name, data in files.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        source = ROOT / 'tasks' / TASK
        task = self.root / 'tasks' / TASK
        cases = sorted((source / 'cases').iterdir())[:2]
        for case in cases:
            shutil.copytree(case, task / 'cases' / case.name)
            shutil.copytree(source / 'reference' / case.name, task / 'reference' / case.name)
        shutil.copytree(source / 'author', task / 'author')
        shutil.copyfile(source / 'judge-config.json', task / 'judge-config.json')
        shutil.copytree(source / 'harbor', task / 'harbor')

    def prepared(self):
        publisher.publish(TASK, root=self.root)
        return Path(prepare.prepare(TASK, self.root)['task_directory'])

    def test_prepare_requires_published_materials(self):
        with self.assertRaisesRegex(ValueError, 'publish_dist.py'):
            prepare.prepare(TASK, self.root)

    def test_build_context_contains_only_public_release(self):
        directory = self.prepared()
        self.assertEqual(directory, self.root / 'runs/harbor/tasks' / TASK)
        self.assertEqual({p.name for p in (directory / 'environment').iterdir()}, {'Dockerfile', 'agent.zip'})
        with zipfile.ZipFile(directory / 'environment/agent.zip') as bundle:
            self.assertFalse(any('/reference/' in p or '/author/' in p or '/cases/' in p for p in bundle.namelist()))
        self.assertEqual(len(list((directory / 'tests/reference').glob('*/reference.npz'))), 2)
        self.assertTrue((directory / 'solution/baseline.py').is_file())
        config = tomllib.loads((directory / 'task.toml').read_text())
        self.assertEqual(config['verifier']['environment_mode'], 'separate')
        self.assertEqual(config['verifier']['network_mode'], 'no-network')
        self.assertEqual(config['artifacts'], ['/app/submission'])
        archive = self.root / 'dist' / f'{TASK}-agent.zip'
        self.assertEqual((directory / 'environment/agent.zip').read_bytes(), archive.read_bytes())
        published_mtime = archive.stat().st_mtime_ns
        for path in directory.rglob('*.sh'):
            self.assertNotIn(b'\r\n', path.read_bytes())
        jobs = self.root / 'runs/harbor/jobs'
        jobs.mkdir()
        (jobs / 'keep.log').write_text('keep')
        (directory / 'obsolete.txt').write_text('old')
        prepare.prepare(TASK, self.root)
        self.assertEqual(archive.stat().st_mtime_ns, published_mtime)
        self.assertFalse((directory / 'obsolete.txt').exists())
        self.assertEqual((jobs / 'keep.log').read_text(), 'keep')

    def test_actual_grader_aggregates_pass_and_fail(self):
        directory = self.prepared()
        private = directory / 'tests'
        logs = self.root / 'judge-logs'
        names = sorted(p.name for p in (private / 'cases').iterdir())

        def execution(work, timeout, case_logs):
            with np.load(private / 'reference' / case_logs.name / 'reference.npz') as data:
                arrays = {key: data[key].copy() for key in data.files}
            if case_logs.name == names[1]:
                arrays['temperature'] += 0.02
            np.savez(work / 'result.npz', **arrays)
            return None

        with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
                patch.object(judge, 'freeze_submission', return_value=True), \
                patch.object(judge, 'execute', side_effect=execution), \
                patch.object(judge.os, 'chown', create=True):
            judge.main()
        report = json.loads((logs / 'report.json').read_text())
        self.assertEqual([row['score'] for row in report['cases']], [1, 0])
        self.assertEqual(report['score'], 1)
        self.assertEqual(report['total_cases'], 2)
        self.assertEqual(float((logs / 'reward.txt').read_text()), 0.5)

    def test_bad_reference_is_infrastructure_error_without_reward(self):
        directory = self.prepared()
        private = directory / 'tests'
        reference = next((private / 'reference').glob('*/reference.npz'))
        reference.write_bytes(b'invalid NPZ')
        logs = self.root / 'judge-logs'
        with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
                patch.object(judge, 'execute') as execute:
            with self.assertRaises(Exception):
                judge.main()
        execute.assert_not_called()
        self.assertFalse((logs / 'reward.txt').exists())


if __name__ == '__main__':
    unittest.main()
