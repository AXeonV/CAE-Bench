"""Exercise the task-local evidence archive with offline stores and hostile payloads."""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from caeoj_tools import data_pool as pool

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/'qbank/02-fluid-mechanics/2.1-single-phase-flow/newtonian-incompressible-steady-2d/author/evidence_archive.py'
spec = importlib.util.spec_from_file_location('evidence_211', SCRIPT)
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


class EvidenceArchiveTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = self.root/'source'
        source.mkdir()
        self.contents = {'log.txt': b'raw\r\n', 'nested/output.h5': b'\x00\xff\x01'}
        for name, data in self.contents.items():
            (source/name).parent.mkdir(parents=True, exist_ok=True)
            (source/name).write_bytes(data)
        packed = self.root/'packed'
        evidence.pack(source, packed)
        self.repository = self.root/'repository'
        shutil.copytree(packed, self.repository/'evidence')
        (self.repository/'evidence/raw.tar.gz').write_bytes(b'opaque original archive')
        self.index = self.root/'index.json'
        self.value = dict(schema_version=1, repository=dict(repo_id='test/fixtures', revision='a'*40), archives=[
            dict(kind='tree', path='evidence/verification-evidence.tar.gz',
                 **evidence.entry(packed/'verification-evidence.tar.gz'),
                 inventory=dict(path='evidence/inventory.json', **evidence.entry(packed/'inventory.json'))),
            dict(kind='raw', path='evidence/raw.tar.gz', **evidence.entry(self.repository/'evidence/raw.tar.gz'))])
        self.save()
        self.store = pool.LocalStore(self.repository)

    def save(self):
        self.index.write_text(json.dumps(self.value), encoding='utf-8')

    def test_round_trip_preserves_bytes_and_verifies_raw_without_extracting(self):
        destination = self.root/'assembled'
        result = evidence.fetch(self.index, destination, store=self.store, include_raw=True)
        self.assertEqual(result['evidence_files'], 2)
        for name, content in self.contents.items():
            self.assertEqual((destination/name).read_bytes(), content)
        self.assertEqual((destination/'raw/raw.tar.gz').read_bytes(), b'opaque original archive')
        self.assertEqual(evidence.fetch(self.index, destination, store=self.store, include_raw=True), result)
        self.assertEqual(evidence.verify(self.index, destination), result)

    def test_changed_or_unknown_local_files_are_not_overwritten(self):
        destination = self.root/'assembled'
        evidence.fetch(self.index, destination, store=self.store)
        (destination/'log.txt').write_bytes(b'my edit')
        with self.assertRaises(ValueError):
            evidence.fetch(self.index, destination, store=self.store)
        self.assertEqual((destination/'log.txt').read_bytes(), b'my edit')
        (destination/'log.txt').write_bytes(self.contents['log.txt'])
        (destination/'my-notes.txt').write_text('keep')
        with self.assertRaises(ValueError):
            evidence.fetch(self.index, destination, store=self.store)
        self.assertEqual((destination/'my-notes.txt').read_text(), 'keep')

    def test_verified_cache_links_are_allowed_but_assembled_links_are_rejected(self):
        self.value.update(case_commit='b'*40, source_git_commit='c'*40, evidence_files=2)
        release={k:self.value[k] for k in ('schema_version','case_commit','source_git_commit','evidence_files','archives')}
        path=self.repository/'evidence/release.json';path.write_text(json.dumps(release),encoding='utf-8')
        self.value['release_manifest']=dict(path='evidence/release.json',**evidence.entry(path));self.save()
        cache=self.root/'cache';cache.mkdir();native=True
        for source in (self.repository/'evidence').iterdir():
            target=cache/source.name
            try:target.symlink_to(source)
            except OSError:
                # Windows may lack symlink privileges; emulate only cache-link metadata.
                native=False;shutil.copyfile(source,target)
        class CacheStore:
            def get(self,name):return cache/Path(name).name
        original=Path.is_symlink
        def cached_link(p):return p.parent==cache or original(p)
        destination=self.root/'assembled'
        with patch.object(Path,'is_symlink',original if native else cached_link):
            result=evidence.fetch(self.index,destination,store=CacheStore(),include_raw=True)
        self.assertEqual(result['evidence_files'],2)
        self.assertEqual((destination/'log.txt').read_bytes(),self.contents['log.txt'])
        self.assertEqual(evidence.verify(self.index,destination),result)
        target=destination/'log.txt'
        # Allowing the remote cache link must not weaken destination path validation.
        with patch.object(Path,'is_symlink',lambda p:p==target or original(p)):
            with self.assertRaises((ValueError,pool.PoolError)):
                evidence.verify(self.index,destination)

    def test_mutable_revision_and_damaged_archive_fail_before_assembly(self):
        self.value['repository']['revision'] = 'main'
        self.save()
        destination = self.root/'assembled'
        with self.assertRaises(ValueError):
            evidence.fetch(self.index, destination, store=self.store)
        self.value['repository']['revision'] = 'a'*40
        self.save()
        (self.repository/'evidence/verification-evidence.tar.gz').write_bytes(b'corrupt')
        with self.assertRaises(ValueError):
            evidence.fetch(self.index, destination, store=self.store)
        self.assertFalse(destination.exists())

    def test_inventory_digest_and_release_identity_are_checked(self):
        inventory = self.repository/'evidence/inventory.json'
        original = inventory.read_bytes()
        inventory.write_bytes(original+b' ')
        with self.assertRaises(ValueError):
            evidence.fetch(self.index, self.root/'bad-inventory', store=self.store)
        inventory.write_bytes(original)
        self.value.update(case_commit='b'*40, source_git_commit='c'*40, evidence_files=2)
        release = {k:self.value[k] for k in ('schema_version','case_commit','source_git_commit','evidence_files','archives')}
        release['case_commit'] = 'd'*40
        path = self.repository/'evidence/release.json'
        path.write_text(json.dumps(release), encoding='utf-8')
        self.value['release_manifest'] = dict(path='evidence/release.json', **evidence.entry(path))
        self.save()
        with self.assertRaisesRegex(ValueError, 'case_commit'):
            evidence.fetch(self.index, self.root/'bad-release', store=self.store)
        self.assertFalse((self.root/'bad-release').exists())

    def test_bad_member_hash_missing_duplicate_traversal_and_links_are_rejected(self):
        archive = self.repository/'evidence/verification-evidence.tar.gz'
        for mode in ('hash', 'missing', 'duplicate', 'traversal', 'link'):
            with self.subTest(mode=mode):
                with tarfile.open(archive, 'w:gz') as tar:
                    for name, data in self.contents.items():
                        if mode == 'missing' and name.startswith('nested/'):
                            continue
                        if mode == 'hash' and name == 'log.txt':
                            data = b'bad\r\n'
                        info = tarfile.TarInfo(name)
                        info.size = len(data)
                        tar.addfile(info, io.BytesIO(data))
                    if mode == 'duplicate':
                        info = tarfile.TarInfo('log.txt'); info.size = len(self.contents['log.txt'])
                        tar.addfile(info, io.BytesIO(self.contents['log.txt']))
                    elif mode == 'traversal':
                        info = tarfile.TarInfo('../escaped'); info.size = 1
                        tar.addfile(info, io.BytesIO(b'x'))
                    elif mode == 'link':
                        info = tarfile.TarInfo('linked'); info.type = tarfile.SYMTYPE; info.linkname = '/outside'
                        tar.addfile(info)
                self.value['archives'][0].update(evidence.entry(archive))
                self.save()
                destination = self.root/mode
                with self.assertRaises(ValueError):
                    evidence.fetch(self.index, destination, store=self.store)
                self.assertFalse(destination.exists())
                self.assertFalse((self.root/'escaped').exists())


if __name__ == '__main__':
    unittest.main()
