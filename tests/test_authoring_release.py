"""Acceptance-state gates are enforced before reading numerical case payloads."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    import sys
    sys.path.insert(0, str(ROOT / 'src/utils'))
    spec = importlib.util.spec_from_file_location(name, ROOT / f'src/utils/{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class ReleaseGateTests(unittest.TestCase):
    def test_draft_packages_stay_public_and_have_no_scoring_claim(self):
        publisher = module('publish_dist')
        with tempfile.TemporaryDirectory() as directory:
            for task in ('calculix-truss', 'pinnacle-poisson-cg'):
                first = publisher.publish(task, directory, root=ROOT, draft=True)
                second = publisher.publish(task, directory, root=ROOT, draft=True)
                self.assertEqual(first['sha256'], second['sha256'])
                with zipfile.ZipFile(first['archive']) as bundle:
                    manifest = json.loads(bundle.read('MANIFEST.json'))
                    self.assertIs(manifest['draft'], True)
                    self.assertNotIn(f'tasks/{task}/grading.json', bundle.namelist())
                    self.assertFalse(any({'author','reference','cases','pending'} & set(Path(name).parts)
                                         for name in bundle.namelist()))

    def test_unaccepted_task_cannot_publish_or_assemble(self):
        publisher, harbor = module('publish_dist'), module('prepare_harbor')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = root / 'tasks/pilot'
            task.mkdir(parents=True)
            for flag in (False, 'false', 1, None):
                (task / 'authoring-status.json').write_text(json.dumps({'release_ready': flag}))
                with self.subTest(flag=flag):
                    with self.assertRaisesRegex(ValueError, 'not accepted'):
                        publisher.collect_materials('pilot', root=root)
                    with self.assertRaisesRegex(ValueError, 'numerical acceptance'):
                        harbor.prepare('pilot', root=root)


if __name__ == '__main__':
    unittest.main()
