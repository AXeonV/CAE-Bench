"""Direct-source safety and real package consumption, without PDE solvers/LLMs."""
from argparse import Namespace
from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import h5py
import numpy as np
from utils.PDEBench.selection import make_selection, validate_selection, CATALOG
from utils.PDEBench.pipeline import workspace_init, prepare_entry, verify, cache_lock
from utils.PDEBench.storage import Budget, NetworkBudget, PreparationError
from utils.PDEBench.checks import source_reference
from utils.PDEBench.models import BY_TASK
from utils.publish_dist import publish
from utils.prepare_harbor import prepare
from caeoj.sdk import load_problem


class DirectTests(unittest.TestCase):
    def entries(self):
        return [{'task': 'advection-1d', 'source_id': 255674, 'index': i, 'frames': [0, 1, 2],
                 'role': role, 'id': name} for i, role, name in [(0, 'sample', '01'), (1, 'case', '001')]]

    def test_offline_plan_rejects_overlap_wrong_family_and_stale_policy(self):
        entries = self.entries()
        selection = make_selection(entries)
        self.assertEqual(validate_selection(selection), selection)
        entries[1]['index'] = 0
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            make_selection(entries)
        entries = self.entries(); entries[0]['source_id'] = 0
        with self.assertRaisesRegex(ValueError, 'belong'):
            make_selection(entries)
        for bad in ([0, 0], [1], [0, -1], [0, True]):
            entries = self.entries(); entries[0]['frames'] = bad
            with self.assertRaises(ValueError): make_selection(entries)
        selection['entries'][0]['source']['md5'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'Frozen'): validate_selection(selection)

    def test_execution_freeze_includes_dockerfile_and_assemblers(self):
        selection = make_selection(self.entries())
        original = Path.read_bytes
        for target in ('src/utils/harbor/environment/Dockerfile', 'src/utils/harbor/instruction.md',
                       'src/utils/publish_dist.py', 'docs/CONTRACT.md'):
            def changed(path):
                value = original(path)
                return value+b'changed' if path == ROOT/target else value
            with self.subTest(target=target), patch.object(Path, 'read_bytes', changed):
                with self.assertRaisesRegex(ValueError, 'Frozen'): validate_selection(selection)

    def test_blocked_source_never_produces_reference_or_example(self):
        from utils.PDEBench.models import source_files
        catalog = json.loads(CATALOG.read_text())
        src = source_files(BY_TASK['reaction-diffusion-1d'], catalog)[0]
        entries = [{'task': 'reaction-diffusion-1d', 'source_id': src['id'], 'index': 0,
                    'frames': [0, 1], 'role': 'sample', 'id': '01'}]
        selection = make_selection(entries)
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as tmp:
            base = Path(tmp); workspace = base/'workspace'; disk = Budget([base], 100_000_000)
            workspace_init(workspace, selection, disk)
            path = base/'source.h5'
            with h5py.File(path, 'w') as h:
                h['tensor'] = np.full((1, 2, 1024), .25)
                h['x-coordinate'] = (np.arange(1024)+.5)/1024
                h['t-coordinate'] = [0., 1.]
            @contextmanager
            def source(*args, **kwargs):
                with h5py.File(path, 'r') as h: yield h
            with patch('utils.PDEBench.pipeline.open_source', source):
                record = prepare_entry(workspace, selection['entries'][0], base/'cache', disk, None, 1, NetworkBudget(0))
            self.assertTrue(record['input_ready']); self.assertFalse(record['reference_ready'])
            report = verify(workspace, selection)
            self.assertFalse(report['assembly_ready'])
            task = next(workspace.glob('qbank/*/*/reaction-diffusion-1d'))
            self.assertTrue((task/'samples/01/reference/candidate.h5').is_file())
            self.assertFalse((task/'samples/01/reference/grading.json').exists())
            self.assertFalse((task/'samples/01/output/result.h5').exists())

    def test_network_retry_charge_cannot_exceed_limit(self):
        budget = NetworkBudget(8)
        budget.admit(5)
        with self.assertRaisesRegex(PreparationError, 'before request'): budget.admit(5)
        self.assertEqual(budget.report()['charged_body_bytes_upper'], 5)

    def test_real_conversion_examples_packages_resume_and_tamper(self):
        selection = make_selection(self.entries())
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as tmp:
            base = Path(tmp); workspace = base/'workspace'
            disk = Budget([base], 100_000_000); network = NetworkBudget(0)
            workspace_init(workspace, selection, disk)
            path = base/'source.h5'
            x = (np.arange(1024)+.5)/1024
            with h5py.File(path, 'w') as h:
                # Numerically synthetic fixture: pipeline integrity, not a PDE accuracy claim.
                data = np.stack([np.tile(np.sin(2*np.pi*x)+i, (3, 1)) for i in range(2)]).astype('f4')
                h['tensor'] = data; h['x-coordinate'] = x.astype('f4'); h['t-coordinate'] = [0., .01, .02]
            @contextmanager
            def source(*args, **kwargs):
                with h5py.File(path, 'r') as h: yield h
            with patch('utils.PDEBench.pipeline.open_source', source):
                for e in selection['entries']:
                    if e['role'] == 'case':
                        import shutil
                        original_copy = shutil.copytree
                        def interrupted(src, dst, *args, **kwargs):
                            if Path(src).name == 'reference': raise OSError('injected case installation interruption')
                            return original_copy(src, dst, *args, **kwargs)
                        with patch('utils.PDEBench.pipeline.shutil.copytree', interrupted):
                            with self.assertRaisesRegex(OSError, 'installation interruption'):
                                prepare_entry(workspace, e, base/'cache', disk, None, 1, network)
                    prepare_entry(workspace, e, base/'cache', disk, None, 1, network)
                # No network or source access on a complete re-run.
                with patch('utils.PDEBench.pipeline.read_entry', side_effect=AssertionError('unexpected read')):
                    reused = prepare_entry(workspace, selection['entries'][0], base/'cache', disk, None, 1, network)
                    self.assertTrue(reused['reused'])
            report = verify(workspace, selection)
            self.assertEqual(report['status'], 'verified')
            artifact = publish('advection-1d', root=workspace)
            assembled = prepare('advection-1d', root=workspace)
            self.assertEqual(assembled['cases'], 1)
            import zipfile
            with zipfile.ZipFile(artifact['archive']) as z:
                self.assertFalse(any('/cases/' in n or '/evidence/' in n or 'candidate.h5' in n for n in z.namelist()))
                self.assertTrue(any('/samples/01/output/result.h5' in n for n in z.namelist()))
            case = next(workspace.glob('qbank/*/*/advection-1d/cases/001/input.h5'))
            with h5py.File(case, 'a') as h: h['initial_state'][0, 0, 0] += 1
            with self.assertRaisesRegex(PreparationError, 'changed'): verify(workspace, selection)

    def test_redirect_body_cannot_bypass_budget(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread
        import signal
        previous = signal.signal(signal.SIGPIPE, signal.SIG_IGN)
        from utils.PDEBench.storage import RangeReader
        hits = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                hits.append(self.path)
                self.send_response(302)
                self.send_header('Location', '/followed')
                self.send_header('Content-Length', '1000000')
                self.end_headers()
                try: self.wfile.write(b'x'*1000000)
                except (BrokenPipeError, ConnectionResetError): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = Thread(target=server.serve_forever, daemon=True); worker.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                source = {'id': 1, 'bytes': 8, 'md5': 'pinned',
                          'url': f'http://127.0.0.1:{server.server_port}/source'}
                budget = NetworkBudget(9)
                with RangeReader(source, Path(tmp), Budget([tmp], 10000), block_size=8, network=budget) as reader:
                    with self.assertRaisesRegex(PreparationError, 'refusing full download'): reader.read(8)
                self.assertEqual(hits, ['/source'])
                self.assertEqual(budget.received, 0)
        finally:
            server.shutdown(); server.server_close(); worker.join()
            signal.signal(signal.SIGPIPE, previous)

    def test_interrupted_initialization_resumes_owned_files_only(self):
        selection = make_selection(self.entries())
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as tmp:
            workspace = Path(tmp)/'workspace'; disk = Budget([tmp], 100_000_000)
            original = Path.write_bytes
            count = [0]
            def failing(path, data):
                count[0] += 1
                if count[0] == 2: raise OSError('injected interruption')
                return original(path, data)
            with patch.object(Path, 'write_bytes', failing):
                with self.assertRaisesRegex(OSError, 'interruption'): workspace_init(workspace, selection, disk)
            self.assertTrue((workspace/'initializing.json').exists())
            workspace_init(workspace, selection, disk)
            self.assertTrue((workspace/'workspace.json').is_file())
            self.assertFalse((workspace/'initializing.json').exists())

    def test_future_sorption_values_are_not_treated_as_initial_constraints(self):
        from utils.PDEBench.pipeline import read_entry
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); path = base/'source.h5'
            with h5py.File(path, 'w') as h:
                group = h.create_group('0000')
                group['data'] = np.stack([np.full((1024, 1), .1), np.linspace(.1, .9, 1024)[:, None]])
                group['grid/x'] = (np.arange(1024)+.5)/1024
                group['grid/t'] = [0., 1.]
            @contextmanager
            def source(*args, **kwargs):
                with h5py.File(path, 'r') as h: yield h
            entry = {'task': 'diffusion-sorption-1d', 'index': 0, 'frames': [0, 1], 'source': {}}
            with patch('utils.PDEBench.pipeline.open_source', source):
                _, _, _, values = read_entry(entry, base/'cache', Budget([base], 100_000_000), None, 1, NetworkBudget(0))
            self.assertGreater(values['concentration'][1].max(), .2)

    def test_workspace_and_cache_concurrent_operations_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with cache_lock(Path(tmp)):
                with self.assertRaisesRegex(PreparationError, 'active'):
                    with cache_lock(Path(tmp)): pass


if __name__ == '__main__': unittest.main()
