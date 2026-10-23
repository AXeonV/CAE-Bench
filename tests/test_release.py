import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from caeoj_tools.release import build, extract, verify


def digest(value):
    return hashlib.sha256(value).hexdigest()


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.prefix = 'qbank/01-science/01-test/test-task'
        self.task = self.source / self.prefix
        self.task.mkdir(parents=True)
        self.output = self.root / 'release'
        files = {'cases/a/problem.json': b'{}', 'cases/a/input.h5': b'input',
                 'reference/a/grading.json': b'{}', 'reference/a/reference.h5': b'reference',
                 'samples/01/input/problem.json': b'{}', 'samples/01/input/input.h5': b'input',
                 'samples/01/reference/grading.json': b'{}', 'samples/01/reference/reference.h5': b'reference'}
        records = {n: {'sha256': digest(v), 'size_bytes': len(v)} for n, v in files.items()}
        descriptor = {'input': {'complete': True}, 'reference': {'complete': True},
                      'files': {n.replace('cases/a/', 'input/').replace('reference/a/', 'reference/'): r
                                for n, r in records.items() if not n.startswith('samples/')}}
        descriptor['case_id'] = 'case-one'
        for group in ('input', 'reference'):
            descriptor[group]['files'] = [n for n in descriptor['files'] if n.startswith(group + '/')]
        raw = json.dumps(descriptor)
        selection = {'case_id': 'case-one', 'case': {'path': 'pool/cases/one/case.json', 'sha256': digest(raw.encode())}}
        manifest = {'task_id': 'caeoj-test', 'cases': {'a': selection}, 'samples': {'01': selection}}
        receipt = {'scope': {'cases': ['a'], 'samples': ['01']}, 'files': records,
                   'descriptors': {'pool/cases/one/case.json': raw},
                   'selection_sha256': digest((json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())}
        for name, value in files.items():
            path = self.task / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(value)
        for name, value in {'data-manifest.json': manifest, '.data-assembly.json': receipt,
                            'judge-config.json': {}}.items():
            (self.task / name).write_text(json.dumps(value))
        (self.task / 'instruction.md').write_text('task')
        (self.task / 'DATA.md').write_text('data')
        self.archive = self.root / 'agent.zip'
        self.public = {f'{self.prefix}/instruction.md': b'task', f'{self.prefix}/DATA.md': b'data', 'src/tool.py': b'print(1)'}
        self.make_public()
        license_path = self.root / 'LICENSE'; license_path.write_text('license')
        self.plan = {'release_id': 'fixture', 'tasks': [{'task': 'test-task', 'chapter': '01', 'title': 'test',
                     'source_root': str(self.source), 'task_path': self.prefix, 'public_archive': str(self.archive),
                     'profile': 'snapshot-unqualified', 'limitations': ['not numerical qualification'],
                     'license_files': [str(license_path)]}], 'excluded': []}
        self.plan_path = self.root / 'plan.json'

    def make_public(self, extra=None):
        with zipfile.ZipFile(self.archive, 'w') as z:
            for n, value in self.public.items(): z.writestr(n, value)
            z.writestr('MANIFEST.json', json.dumps({'files': {n: digest(v) for n, v in self.public.items()}}))
            if extra: z.writestr(*extra)

    def run_build(self):
        self.plan_path.write_text(json.dumps(self.plan))
        return build(self.plan_path, self.output)

    def test_release_cli_and_extract_without_source(self):
        catalog = self.run_build()
        self.assertEqual(catalog['tasks'][0]['task_id'], 'caeoj-test')
        self.assertNotIn(str(self.source), (self.output / 'catalog.json').read_text())
        shutil.rmtree(self.source); self.archive.unlink()
        target = self.root / 'extracted'
        result = subprocess.run([sys.executable, '-I', str(self.output / 'release.py'), '--root', str(self.output),
                                 'extract', 'test-task', str(target)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((target / self.prefix / 'reference/a/reference.h5').read_bytes(), b'reference')
        self.assertEqual((target / 'src/tool.py').read_bytes(), b'print(1)')
        self.assertTrue(verify(self.output)['verified_files'] > 3)
        with self.assertRaises(ValueError): extract(self.output, 'test-task', target)

    def test_missing_selected_file(self):
        (self.task / 'reference/a/reference.h5').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'): self.run_build()
        self.assertFalse((self.output / 'SHA256SUMS.json').exists())

    def test_receipt_cannot_omit_descriptor_asset(self):
        p = self.task / '.data-assembly.json'; r = json.loads(p.read_text()); del r['files']['cases/a/input.h5']; p.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError, 'omits'): self.run_build()

    def test_asset_digest_corruption(self):
        (self.task / 'reference/a/reference.h5').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'digest'): self.run_build()

    def test_duplicate_tasks(self):
        self.plan['tasks'].append(dict(self.plan['tasks'][0]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'): self.run_build()

    def test_unsafe_task_path(self):
        self.plan['tasks'][0]['task_path'] = '../outside'
        with self.assertRaisesRegex(ValueError, 'Unsafe'): self.run_build()

    def test_public_traversal(self):
        self.make_public(('../outside', b'bad'))
        with self.assertRaisesRegex(ValueError, 'Unsafe'): self.run_build()

    def test_public_duplicate(self):
        self.make_public(('src/tool.py', b'bad'))
        with self.assertRaisesRegex(ValueError, 'Duplicate'): self.run_build()

    def test_public_manifest_corruption(self):
        self.make_public(('other', b'not in manifest'))
        with self.assertRaisesRegex(ValueError, 'manifest'): self.run_build()

    def test_public_stale_statement(self):
        self.public[f'{self.prefix}/instruction.md'] = b'old'; self.make_public()
        with self.assertRaisesRegex(ValueError, 'conflict'): self.run_build()

    def test_public_cannot_include_private_cases(self):
        self.public[f'{self.prefix}/cases/a/input.h5'] = b'input'; self.make_public()
        with self.assertRaisesRegex(ValueError, 'private cases'): self.run_build()

    def test_public_private_directory_collision(self):
        self.public[f'{self.prefix}/cases'] = b'file instead of directory'; self.make_public()
        with self.assertRaisesRegex(ValueError, 'file/directory collision'): self.run_build()

    def test_output_cannot_be_inside_source(self):
        self.output = self.task / 'release'
        with self.assertRaisesRegex(ValueError, 'disjoint'): self.run_build()

    def test_output_cannot_contain_plan(self):
        self.output = self.root
        with self.assertRaisesRegex(ValueError, 'input plan'): self.run_build()

    def test_duplicate_stable_task_ids(self):
        second = self.source / 'qbank/01-science/01-test/other-task'
        shutil.copytree(self.task, second)
        self.plan['tasks'].append(dict(self.plan['tasks'][0], task='other-task', task_path='qbank/01-science/01-test/other-task'))
        with self.assertRaisesRegex(ValueError, 'duplicate stable task_id'): self.run_build()

    def test_receipt_extra_asset_rejected(self):
        p = self.task / '.data-assembly.json'; r = json.loads(p.read_text())
        (self.task / 'cases/a/extra').write_bytes(b'bad')
        r['files']['cases/a/extra'] = {'sha256': digest(b'bad'), 'size_bytes': 3}; p.write_text(json.dumps(r))
        with self.assertRaisesRegex(ValueError, 'exact descriptor'): self.run_build()

    def test_stale_manifest_identity_rejected(self):
        p = self.task / 'data-manifest.json'; m = json.loads(p.read_text()); m['cases']['a']['case_id'] = 'stale'; p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError, 'selection digest'): self.run_build()

    def test_public_receipt_rejected(self):
        name = f'{self.prefix}/.data-assembly.json'
        self.public[name] = (self.task / '.data-assembly.json').read_bytes(); self.make_public()
        with self.assertRaisesRegex(ValueError, 'private cases'): self.run_build()

    def test_extract_target_inside_release_rejected(self):
        self.run_build()
        with self.assertRaisesRegex(ValueError, 'contain'): extract(self.output, 'test-task', self.output / 'extracted')

    def test_format_sample_without_numerical_reference(self):
        mp = self.task / 'data-manifest.json'; rp = self.task / '.data-assembly.json'
        m = json.loads(mp.read_text()); r = json.loads(rp.read_text())
        descriptor = json.loads(r['descriptors']['pool/cases/one/case.json'])
        descriptor['example_kind'] = 'format'; descriptor['example'] = 'reference/reference.h5'
        descriptor['case_id'] = 'case-format'
        raw = json.dumps(descriptor)
        r['descriptors']['pool/cases/format/case.json'] = raw
        m['samples']['01'] = {'case_id': 'case-format', 'case': {'path': 'pool/cases/format/case.json', 'sha256': digest(raw.encode())}, 'kind': 'format'}
        for name in list(r['files']):
            if name.startswith('samples/01/reference/'): del r['files'][name]
        output = self.task / 'samples/01/output/result.h5'; output.parent.mkdir(); output.write_bytes(b'reference')
        r['files']['samples/01/output/result.h5'] = {'sha256': digest(b'reference'), 'size_bytes': 9}
        r['selection_sha256'] = digest((json.dumps(m, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode())
        mp.write_text(json.dumps(m)); rp.write_text(json.dumps(r))
        self.run_build()
        target = self.root / 'extract-format'; extract(self.output, 'test-task', target)
        self.assertTrue((target / self.prefix / 'samples/01/output/result.h5').exists())
        self.assertFalse((target / self.prefix / 'samples/01/reference/grading.json').exists())

    def test_final_asset_corruption(self):
        self.run_build(); (self.output / 'qbank.zip').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'digest'): verify(self.output)

    def test_resource_configuration_is_frozen_privately(self):
        resource = self.task / 'harbor/task.toml'; resource.parent.mkdir()
        content = b'[environment]\ncpus = 7\nmemory_mb = 12345\n'
        resource.write_bytes(content)
        catalog = self.run_build()
        self.assertEqual(catalog['tasks'][0]['files']['harbor/task.toml']['sha256'], digest(content))
        with zipfile.ZipFile(self.output / 'qbank.zip') as archive:
            self.assertEqual(archive.read(self.prefix + '/harbor/task.toml'), content)
        target = self.root / 'resource-workspace'; extract(self.output, 'test-task', target)
        self.assertEqual((target / self.prefix / 'harbor/task.toml').read_bytes(), content)

    def test_resource_configuration_cannot_be_public(self):
        self.public[self.prefix + '/harbor/task.toml'] = b'[environment]\ncpus = 7\n'; self.make_public()
        with self.assertRaisesRegex(ValueError, 'private cases'): self.run_build()

    def test_source_symlink_rejected(self):
        source = self.task / 'cases/a/input.h5'; other = self.root / 'linked.h5'; source.rename(other)
        try: source.symlink_to(other)
        except OSError: self.skipTest('symlink creation unavailable')
        with self.assertRaisesRegex(ValueError, 'Links'): self.run_build()


if __name__ == '__main__': unittest.main()
