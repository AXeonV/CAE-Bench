"""Offline release, partial assembly, CLI isolation and transport recovery."""
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from caeoj_tools import data_cli, data_lock, data_pool as pool, data_sources
import test_data_pool


class ManagementTests(unittest.TestCase):
    def setUp(self):
        fixture = test_data_pool.PoolTests(methodName='runTest')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.root, self.value = fixture.root/'project', fixture.selection
        self.task = self.root/self.value['repository']['path']
        self.task.mkdir(parents=True)
        (self.root/'pyproject.toml').write_text('[project]\nname="fixture"\n')
        (self.task/'instruction.md').write_text('test task')
        pool.write_json(self.task/'data-manifest.json', self.value)
        self.lock = data_lock.create(self.value, fixture.store)
        pool.write_json(self.task/data_lock.LOCK, self.lock)
        self.cache = self.root/'.caeoj/cache'
        self.config = self.root/'data.toml'
        self.config.write_text('default_source="local"\n[sources.local]\ntype="local"\nroot=' +
                               json.dumps(str(fixture.bundle/'repository')) + '\n')

    def cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(io.StringIO()):
            code = data_cli.main([*args, '--root', str(self.root), '--config', str(self.config)])
        return code, json.loads(output.getvalue())

    def fetch(self, *args):
        code, report = self.cli('fetch', '--task', 'task', *args)
        self.assertEqual(code, 0, report)
        return report['tasks'][0]

    def test_full_download_reuse_and_corruption_detection(self):
        first = self.fetch()
        self.assertTrue(first['complete'])
        self.assertTrue(pool.verify(self.task, strict=True)['valid'])
        self.assertGreater(first['downloaded_files'], 0)
        # A ready installation works without the configured source existing.
        shutil.rmtree(self.fixture.bundle/'repository')
        second = self.fetch()
        self.assertEqual(second['downloaded_files'], 0)
        damaged = next((self.task/'cases').rglob('*.h5'))
        damaged.write_bytes(b'damaged')
        code, result = self.cli('verify', '--task', 'task', '--strict')
        self.assertEqual(code, 2)
        self.assertIn('mismatch', result['failures'][0]['error'])
        # --update repairs from the verified object cache without the source.
        repaired = self.fetch('--update')
        self.assertTrue(repaired['complete'])

    def test_partial_kinds_are_exact_and_accumulate_without_removal(self):
        first = self.fetch('--kind', 'cases')
        self.assertFalse(first['complete'])
        self.assertTrue((self.task/'cases/a/problem.json').is_file())
        self.assertFalse((self.task/'reference').exists())
        self.assertFalse((self.task/'samples').exists())
        with self.assertRaises(pool.PoolError):
            pool.verify(self.task, strict=True)
        self.fetch('--kind', 'references')
        self.assertTrue((self.task/'cases/a/problem.json').exists())
        self.assertTrue((self.task/'reference/a/grading.json').exists())
        self.assertFalse((self.task/'samples').exists())
        last = self.fetch('--kind', 'samples')
        self.assertTrue(last['complete'])
        self.assertTrue(pool.verify(self.task, strict=True)['valid'])

    def test_lock_change_blocks_formerly_ready_assembly(self):
        self.fetch()
        changed = deepcopy(self.lock)
        changed['hf_revision'] = 'a'*40
        pool.write_json(self.task/data_lock.LOCK, changed)
        with self.assertRaisesRegex(pool.PoolError, 'Data lock changed'):
            pool.verify(self.task, strict=True)
        pool.write_json(self.task/data_lock.LOCK, self.lock)
        selected = deepcopy(self.value)
        selected['samples'] = {}
        pool.write_json(self.task/'data-manifest.json', selected)
        with self.assertRaisesRegex(pool.PoolError, 'selection changed'):
            data_lock.read(self.task, selected)

    def test_lock_tampering_and_revision_are_rejected(self):
        changed = deepcopy(self.lock)
        name = next(iter(changed['descriptors']))
        changed['descriptors'][name] += ' '
        pool.write_json(self.task/data_lock.LOCK, changed)
        with self.assertRaisesRegex(pool.PoolError, 'digest'):
            data_lock.read(self.task, self.value)
        with self.assertRaisesRegex(pool.PoolError, 'fixed commit'):
            data_sources.HubTransport(self.value, 'main')

    def test_offline_plan_stable_id_and_unregistered_chapter(self):
        code, report = self.cli('fetch', '--problem', self.value['task_id'], '--dry-run')
        self.assertEqual(code, 0, report)
        self.assertGreater(report['tasks'][0]['download_bytes'], 0)
        self.assertFalse(self.cache.exists())
        unregistered = self.task.parent/'unregistered'
        unregistered.mkdir()
        (unregistered/'instruction.md').write_text('pending')
        # Fixtures use chapter ch; production chapter filters accept numeric IDs.
        code, report = self.cli('list')
        self.assertEqual(code, 0, report)
        self.assertEqual({row['status'] for row in report['tasks']}, {'unregistered', 'missing'})
        (self.task/data_lock.LOCK).unlink()
        code, report = self.cli('list', '--task', 'task')
        self.assertEqual(report['tasks'][0]['status'], 'unlocked')

    def test_listing_works_without_numerical_or_hf_dependencies(self):
        env = os.environ.copy()
        env['PYTHONPATH'] = str(Path(data_cli.__file__).resolve().parents[1])
        script = '''import importlib.abc, sys
class BlockNumerical(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'numpy', 'gmsh', 'h5py', 'huggingface_hub'}:
            raise ImportError('Unexpected data-list dependency: ' + fullname)
sys.meta_path.insert(0, BlockNumerical())
from caeoj.cli import main
raise SystemExit(main(sys.argv[1:]))
'''
        result = subprocess.run([sys.executable, '-c', script, 'data', 'list',
                                 '--root', str(self.root), '--task', 'task'],
                                capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['tasks'][0]['status'], 'missing')

    def test_lock_command_never_downloads_payloads(self):
        (self.task/data_lock.LOCK).unlink()
        source = self.fixture.store
        original = source.get
        seen = []

        def metadata_only(name):
            self.assertTrue(name.endswith('/case.json'))
            seen.append(name)
            return original(name)

        with patch.object(source, 'get', side_effect=metadata_only), patch('caeoj_tools.data_cli.pool.LocalStore', return_value=source):
            code, report = self.cli('lock', '--task', 'task')
        self.assertEqual(code, 0, report)
        self.assertTrue(seen)
        self.assertTrue(data_lock.read(self.task, self.value))

    def test_chapter_fetch_reports_failures_without_losing_successful_tasks(self):
        target = self.root/'qbank/00-fixture/sec/task'
        target.parent.mkdir(parents=True)
        shutil.move(self.task, target)
        self.task = target
        pending = target.parent/'pending'
        pending.mkdir()
        (pending/'instruction.md').write_text('not published')
        code, report = self.cli('fetch', '--chapter', '0')
        self.assertEqual(code, 2)
        self.assertEqual([row['task'] for row in report['tasks']], ['task'])
        self.assertTrue(report['tasks'][0]['complete'])
        self.assertEqual(report['failures'][0]['task'], 'pending')
        self.assertTrue(pool.verify(self.task, strict=True)['valid'])

    def test_sftp_resume_and_legacy_scp_resume(self):
        destination = self.fixture.root/'partial.bin'
        destination.write_bytes(b'partial')
        source = {'type': 'scp', 'host': 'user@cluster', 'root': '/data/release one'}
        backend = data_sources.ScpTransport(source)
        clients = {name: str((self.fixture.root/'OpenSSH clients'/(name+'.exe')).resolve())
                   for name in ('sftp', 'scp', 'ssh')}
        with patch('caeoj_tools.data_sources.shutil.which', side_effect=clients.get), \
                patch('caeoj_tools.data_sources.subprocess.run', return_value=SimpleNamespace(returncode=0)) as execute:
            backend.retrieve('qbank/file.h5', destination)
        args, kwargs = execute.call_args
        self.assertEqual(args[0][0], clients['sftp'])
        self.assertIn('reget "/data/release one/qbank/file.h5"', kwargs['input'])
        self.assertIn('-oStrictHostKeyChecking=yes', args[0])
        backend = data_sources.ScpTransport({**source, 'transport': 'scp'})
        destination.write_bytes(b'a'*(backend.BLOCK+19))

        def resumed(command, **kwargs):
            self.assertEqual(command[0], clients['ssh'])
            self.assertIn('skip=1', command[-1])
            self.assertEqual(kwargs['stdout'].tell(), backend.BLOCK)
            kwargs['stdout'].write(b'end')
            return SimpleNamespace(returncode=0)

        with patch('caeoj_tools.data_sources.shutil.which', side_effect=clients.get), \
                patch('caeoj_tools.data_sources.subprocess.run', side_effect=resumed):
            backend.retrieve('qbank/file.h5', destination)
        self.assertEqual(destination.stat().st_size, backend.BLOCK+3)

    def test_missing_openssh_preserves_partial_file(self):
        destination = self.fixture.root/'partial.bin'
        original = b'a'*(data_sources.ScpTransport.BLOCK+19)
        for protocol, partial in (('sftp', True), ('scp', False), ('scp', True)):
            with self.subTest(protocol=protocol, partial=partial):
                if partial:
                    destination.write_bytes(original)
                elif destination.exists():
                    destination.unlink()
                backend = data_sources.ScpTransport({'host': 'cluster', 'root': '/data', 'transport': protocol})
                with patch('caeoj_tools.data_sources.shutil.which', return_value=None):
                    with self.assertRaisesRegex(pool.PoolError, 'install OpenSSH'):
                        backend.retrieve('file.h5', destination)
                if partial:
                    self.assertEqual(destination.read_bytes(), original)
                else:
                    self.assertFalse(destination.exists())

    def test_retries_preserve_partial_and_never_expose_unverified_objects(self):
        planned = data_lock.plan(self.task, self.value, self.lock)
        name, entry = next(iter(planned['files'].items()))
        remote_name = self.value['repository']['path']+'/'+entry['source']
        original = self.fixture.store.get(remote_name)
        calls = []

        class Interrupted:
            def retrieve(inner, source, target):
                calls.append(source)
                if len(calls) == 1:
                    target.write_bytes(original.read_bytes()[:3])
                    raise pool.PoolError('interrupted')
                self.assertEqual(target.read_bytes(), original.read_bytes()[:3])
                shutil.copyfile(original, target)

        with data_lock.metadata_store(self.value, self.lock) as metadata:
            store = data_sources.VerifiedStore(self.value, self.lock, metadata, planned, Interrupted(), self.cache, retries=2)
            with patch('caeoj_tools.data_sources.time.sleep'):
                cached = store.get(remote_name)
            self.assertTrue(pool.matches(cached, entry))
        self.assertEqual(len(calls), 2)

    def test_hf_uses_fixed_revision_and_only_requested_file(self):
        revision = 'b'*40
        transport = data_sources.HubTransport(self.value, revision)
        original = self.fixture.root/'hub-file'
        original.write_bytes(b'data')
        destination = self.fixture.root/'downloaded'
        with patch('huggingface_hub.hf_hub_download', return_value=str(original)) as download:
            transport.retrieve('qbank/file.h5', destination)
        self.assertEqual(destination.read_bytes(), b'data')
        self.assertEqual(download.call_args.kwargs['revision'], revision)
        self.assertEqual(download.call_args.args[1], 'qbank/file.h5')

    def test_unsafe_remote_and_configuration_credentials_are_rejected(self):
        with self.assertRaises(pool.PoolError):
            data_sources.ScpTransport({'host': '-oProxyCommand=bad', 'root': '/data'})
        self.config.write_text('default_source="hf"\n[sources.hf]\ntype="hf"\ntoken="secret"\n')
        with self.assertRaisesRegex(pool.PoolError, 'credentials'):
            data_sources.configuration(self.config)


if __name__ == '__main__':
    unittest.main()
