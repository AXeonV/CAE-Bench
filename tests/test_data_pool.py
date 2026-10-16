"""Pool integrity/transaction tests; fixtures do not certify numerical correctness."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import hashlib
import importlib.util
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from caeoj_tools import data_pool as pool


class PoolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root/'generated'
        self.value = {'schema_version': 2, 'task_id': 'caeoj-000123',
                      'repository': {'repo_id': 'owner/test', 'repo_type': 'dataset', 'path': 'qbank/ch/sec/task'}}
        for name, parameter in (('a', 1), ('b', 2)):
            directory = self.source/'cases'/name
            directory.mkdir(parents=True)
            pool.write_json(directory/'problem.json', {'data_file': 'input.h5', 'geometries': {},
                            'meshes': {'main': {'file': 'mesh.msh'}}, 'parameter': parameter})
            (directory/'input.h5').write_bytes(b'input' + bytes([parameter]))
            (directory/'mesh.msh').write_bytes(b'shared-mesh')
            ref = self.source/'reference'/name
            ref.mkdir(parents=True)
            (ref/'reference.h5').write_bytes(b'answer' + bytes([parameter]))
        shutil.copytree(self.source/'cases/a', self.source/'samples/01/input')
        sample = self.source/'samples/01/output'
        sample.mkdir()
        shutil.copyfile(self.source/'reference/a/reference.h5', sample/'result.h5')
        pool.write_json(self.source/'samples/01/verification.json', {'valid': True})
        self.bundle = self.root/'bundle'
        pool.pack(self.source, self.bundle, self.value)
        self.selection = pool.manifest(self.bundle/'selection.json')
        self.store = pool.LocalStore(self.bundle/'repository')
        self.task = self.root/'task'
        self.task.mkdir()
        pool.write_json(self.task/'data-manifest.json', self.selection)

    def test_pack_deduplicates_samples_and_shared_mesh_and_round_trips(self):
        self.assertEqual(self.selection['samples']['01']['case_id'], self.selection['cases']['a']['case_id'])
        result = pool.assemble(self.task, self.selection, self.store)
        self.assertEqual(result['overlaps'], [['cases/a', 'samples/01']])
        for directory in ('cases', 'reference', 'samples'):
            for f in (self.source/directory).rglob('*'):
                if f.is_file():
                    self.assertEqual(f.read_bytes(), (self.task/f.relative_to(self.source)).read_bytes())
        shared = list((self.bundle/'repository').rglob('pool/shared/*/mesh.msh'))
        self.assertEqual(len(shared), 1)
        self.assertEqual(pool.assemble(self.task, self.selection, self.store)['changed'], 0)
        self.assertTrue(pool.verify(self.task)['valid'])
        with self.assertRaisesRegex(pool.PoolError, 'Overlapping'):
            pool.verify(self.task, strict=True)
        self.assertTrue(pool.verify(self.task, strict=True, samples_only=True)['valid'])

    def test_select_disjoint_bindings_and_descriptor_tampering(self):
        a, b = (self.selection['cases'][n]['case_id'] for n in ('a', 'b'))
        chosen = pool.select(self.selection, self.store, ['01=' + b], ['example=' + a])
        pool.write_json(self.task/'data-manifest.json', chosen)
        pool.assemble(self.task, chosen, self.store)
        self.assertTrue(pool.verify(self.task, strict=True)['valid'])
        with self.assertRaisesRegex(pool.PoolError, 'duplicate inputs'):
            pool.select(self.selection, self.store, [a], [a])
        f = self.store.get(self.value['repository']['path'] + '/' + chosen['cases']['01']['item']['path'])
        f.write_bytes(f.read_bytes() + b' ')
        with self.assertRaisesRegex(pool.PoolError, 'Descriptor SHA'):
            pool.fetch(chosen, self.store)

    def test_modified_files_require_update_and_corrupt_download_never_changes_local(self):
        pool.assemble(self.task, self.selection, self.store)
        path = self.task/'cases/a/input.h5'
        path.write_bytes(b'local modification')
        with self.assertRaisesRegex(pool.PoolError, '--update'):
            pool.assemble(self.task, self.selection, self.store)
        self.assertEqual(path.read_bytes(), b'local modification')
        pool.assemble(self.task, self.selection, self.store, update=True)
        expected = path.read_bytes()
        plan = pool.plan(self.selection, self.store)
        entry = plan['files']['cases/a/input.h5']
        self.store.get(self.value['repository']['path'] + '/' + entry['source']).write_bytes(b'bad')
        with self.assertRaisesRegex(pool.PoolError, 'payload SHA'):
            pool.assemble(self.task, self.selection, self.store, update=True)
        self.assertEqual(path.read_bytes(), expected)

    def test_reselection_removes_only_unchanged_managed_files(self):
        pool.assemble(self.task, self.selection, self.store)
        chosen = deepcopy(self.selection)
        del chosen['cases']['a']
        pool.write_json(self.task/'data-manifest.json', chosen)
        (self.task/'cases/a/user.txt').write_text('keep')
        with self.assertRaisesRegex(pool.PoolError, '--update'):
            pool.assemble(self.task, chosen, self.store)
        (self.task/'cases/a/input.h5').write_bytes(b'edited')
        with self.assertRaisesRegex(pool.PoolError, 'modified old'):
            pool.assemble(self.task, chosen, self.store, update=True)
        shutil.copyfile(self.source/'cases/a/input.h5', self.task/'cases/a/input.h5')
        pool.assemble(self.task, chosen, self.store, update=True)
        self.assertFalse((self.task/'cases/a/problem.json').exists())
        self.assertEqual((self.task/'cases/a/user.txt').read_text(), 'keep')

    def test_partial_download_receipt_cannot_pass_full_benchmark(self):
        pool.assemble(self.task, self.selection, self.store, cases=[], auxiliary=False)
        self.assertTrue(pool.verify(self.task, strict=True, samples_only=True)['valid'])
        with self.assertRaises(pool.PoolError):
            pool.verify(self.task, strict=True)

    def test_transaction_rolls_back_after_mid_commit_failure(self):
        pool.assemble(self.task, self.selection, self.store)
        target = self.task/'cases/a/input.h5'
        target.write_bytes(b'old bytes')
        receipt = (self.task/pool.RECEIPT).read_bytes()
        replace = pool.os.replace
        def fail(source, destination):
            if '/new/cases/a/input.h5' in str(source).replace('\\', '/'):
                raise OSError('simulated commit failure')
            return replace(source, destination)
        with patch.object(pool.os, 'replace', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'simulated'):
                pool.assemble(self.task, self.selection, self.store, update=True)
        self.assertEqual(target.read_bytes(), b'old bytes')
        self.assertEqual((self.task/pool.RECEIPT).read_bytes(), receipt)

    def test_paths_links_and_untrusted_receipt_are_rejected(self):
        for name in ('../outside', '/absolute', 'C:/outside', 'a\\b', 'a/../b', 'CON', 'a./b'):
            with self.subTest(name=name), self.assertRaises(pool.PoolError):
                pool.within(self.root, name)
        pool.write_json(self.task/pool.RECEIPT, {'files': {'README.md': {'size_bytes': 0, 'sha256': '0'*64}}})
        with self.assertRaisesRegex(pool.PoolError, 'outside data'):
            pool.assemble(self.task, self.selection, self.store)

    def test_incomplete_reference_is_explicit_and_never_strict_ready(self):
        shutil.rmtree(self.source/'reference/b')
        new = self.root/'incomplete'
        pool.pack(self.source, new, self.value)
        chosen = pool.manifest(new/'selection.json')
        pool.write_json(self.task/'data-manifest.json', chosen)
        result = pool.assemble(self.task, chosen, pool.LocalStore(new/'repository'))
        self.assertIn('cases/b/reference', result['incomplete'])
        with self.assertRaisesRegex(pool.PoolError, 'Incomplete'):
            pool.verify(self.task, strict=True)

    def test_offline_verification_distrusts_receipt_file_hashes(self):
        pool.assemble(self.task, self.selection, self.store)
        f = self.task/'samples/01/input/input.h5'
        f.write_bytes(b'wrong')
        receipt = pool.checked_json(self.task/pool.RECEIPT)
        receipt['files']['samples/01/input/input.h5'] = pool.identity(f)
        pool.write_json(self.task/pool.RECEIPT, receipt)
        with self.assertRaisesRegex(pool.PoolError, 'SHA/size'):
            pool.verify(self.task, strict=True, samples_only=True)

    @unittest.skipUnless(importlib.util.find_spec('huggingface_hub'), 'maintenance extra required')
    def test_upload_merges_index_skips_same_bytes_and_requires_explicit_updates(self):
        remote = self.root/'remote'
        remote.mkdir()
        state = {'revision': 'initial', 'commits': 0, 'payload_reads': 0}
        class Hub(pool.LocalStore):
            def __init__(self, repo_id, revision='main', cache_dir=None):
                super().__init__(remote)
                self.revision = state['revision']
            def get(self, name):
                if name.endswith(('.h5', '.msh')):
                    state['payload_reads'] += 1
                return super().get(name)
        class API:
            def list_repo_files(self, *args, **kwargs):
                return [p.relative_to(remote).as_posix() for p in remote.rglob('*') if p.is_file()]
            def get_paths_info(self, repo_id, names, **kwargs):
                result = []
                for name in names:
                    data = (remote/name).read_bytes()
                    result.append(SimpleNamespace(path=name, lfs=None,
                        blob_id=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()))
                return result
            def create_commit(self, **kwargs):
                if kwargs['parent_commit'] != state['revision']:
                    raise pool.PoolError('concurrent writer')
                for operation in kwargs['operations']:
                    target = remote/operation.path_in_repo
                    target.parent.mkdir(parents=True, exist_ok=True)
                    content = operation.path_or_fileobj
                    target.write_bytes(content if isinstance(content, bytes) else Path(content).read_bytes())
                state['commits'] += 1
                state['revision'] = str(state['commits'])
                return SimpleNamespace(oid=state['revision'])
        with patch.object(pool, 'HubStore', Hub), patch('huggingface_hub.HfApi', API):
            first = pool.upload(self.bundle)
            self.assertGreater(first['uploaded_files'], 0)
            # Remote-only pool entries must survive later uploads.
            index_file = remote/self.value['repository']['path']/'pool/index.json'
            index = pool.checked_json(index_file)
            index['items']['unrelated'] = {'path': 'pool/unrelated/item.json', 'sha256': '0'*64}
            pool.write_json(index_file, index)
            before = state['payload_reads']
            self.assertEqual(pool.upload(self.bundle)['uploaded_files'], 0)
            self.assertEqual(state['payload_reads'], before)
            self.assertIn('unrelated', pool.checked_json(index_file)['items'])
            pool_file = next((remote/self.value['repository']['path']).rglob('input.h5'))
            pool_file.write_bytes(b'remote modification')
            with self.assertRaisesRegex(pool.PoolError, '--update'):
                pool.upload(self.bundle)
            self.assertGreater(pool.upload(self.bundle, update=True)['uploaded_files'], 0)

    def test_bundle_checks_even_unselected_attachments(self):
        attachment = next((self.bundle/'repository').rglob('verification.json'))
        attachment.write_text('broken')
        with self.assertRaisesRegex(pool.PoolError, 'corrupt payload'):
            pool.validate_bundle(self.bundle)

    def test_bundle_refuses_undeclared_files(self):
        path = self.bundle/'repository'/self.value['repository']['path']/'pool/accidental-secret.txt'
        path.write_text('not part of data')
        with self.assertRaisesRegex(pool.PoolError, 'undeclared'):
            pool.validate_bundle(self.bundle)

    def test_cli_does_not_require_smoke_task_for_data_commands(self):
        from caeoj_tools import cli
        from contextlib import redirect_stdout
        import io
        with patch.object(cli, 'task_directory', side_effect=AssertionError('unrelated smoke lookup')), \
             patch('caeoj_tools.data_pool_cli.run', return_value={'valid': True}), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['data', 'verify', '--task', 'some-other-task']), 0)

    def test_shared_dependency_cycle_and_case_insensitive_destinations(self):
        binding = self.selection['cases']['a']['item']
        f = self.store.get(self.value['repository']['path'] + '/' + binding['path'])
        item = pool.checked_json(f)
        # Cycle detection precedes fetching/checking a recursive descriptor again.
        item['shared_dependencies'] = [binding]
        with self.assertRaisesRegex(pool.PoolError, 'Cyclic'):
            pool.item_files(self.store, self.value['repository']['path'], binding, item, {}, active={binding['path']})
        selected = deepcopy(self.selection)
        selected['cases']['A'] = selected['cases']['a']
        with self.assertRaisesRegex(pool.PoolError, 'Case-insensitive'):
            pool.plan(selected, self.store)

    def test_bound_shared_descriptor_materializes_self_contained_inputs(self):
        selected = deepcopy(self.selection)
        binding = selected['cases']['a']['item']
        prefix = self.value['repository']['path']
        f = self.store.get(prefix + '/' + binding['path'])
        item = pool.checked_json(f)
        shared = item['files'].pop('input/mesh.msh')
        dependency_path = 'pool/shared/mesh-descriptor.json'
        dep = self.bundle/'repository'/prefix/dependency_path
        pool.write_json(dep, {'schema_version': 1, 'files': {'input/mesh.msh': shared}})
        item['shared_dependencies'] = [{'path': dependency_path, 'sha256': pool.digest(dep)}]
        pool.write_json(f, item)
        for group in selected['cases'], selected['samples']:
            for choice in group.values():
                if choice['case_id'] == item['case_id']:
                    choice['item']['sha256'] = pool.digest(f)
        pool.write_json(self.task/'data-manifest.json', selected)
        pool.assemble(self.task, selected, self.store)
        self.assertEqual((self.task/'cases/a/mesh.msh').read_bytes(), b'shared-mesh')
        self.assertTrue(pool.verify(self.task, strict=True, samples_only=True)['valid'])

    def test_source_mutation_during_pack_does_not_advertise_selection(self):
        copy = pool.shutil.copyfile
        def mutate(source, target):
            if Path(source).name == 'input.h5':
                Path(source).write_bytes(b'changed during copy')
            return copy(source, target)
        output = self.root/'unstable'
        with patch.object(pool.shutil, 'copyfile', side_effect=mutate):
            with self.assertRaisesRegex(pool.PoolError, 'Input changed'):
                pool.pack(self.source, output, self.value)
        self.assertFalse((output/'selection.json').exists())


if __name__ == '__main__':
    unittest.main()
