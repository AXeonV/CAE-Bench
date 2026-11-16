"""Explicit public references: 20 independent cases remain 20 scored cases."""
from contextlib import contextmanager, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from utils.PDEBench.selection import make_selection, validate_selection
from utils.PDEBench.pipeline import workspace_init, prepare_entry, prepare_examples, verify
from utils.PDEBench.storage import Budget, NetworkBudget, PreparationError
from caeoj_tools.public_examples import BINDING, verify_public_examples
from utils.publish_dist import publish
from utils.prepare_harbor import prepare


class PublicExampleTests(unittest.TestCase):
    def entries(self, count=20):
        return [{'task': 'advection-1d', 'source_id': 255674, 'index': i, 'frames': list(range(9)),
                 'role': 'case', 'id': f'{i+1:03d}'} for i in range(count)]

    def aliases(self):
        return {'advection-1d': {'01': {'case': '001'}, '02': {'case': '011'}}}

    def test_invalid_and_duplicate_references_and_selection_binding(self):
        entries = self.entries()
        for aliases in ({'unknown-task': {'01': {'case': '001'}}},
                        {'advection-1d': {'01': {'case': '999'}}},
                        {'advection-1d': {'01': {'case': '001'}, '02': {'case': '001'}}},
                        {'advection-1d': {'../x': {'case': '001'}}},
                        {'advection-1d': {'01': {'case': '001', 'frames': [0]}}}):
            with self.subTest(aliases=aliases), self.assertRaises(ValueError):
                make_selection(entries, examples=aliases)
        selection = make_selection(entries, examples=self.aliases())
        self.assertEqual(validate_selection(selection), selection)
        selection['examples']['advection-1d']['01']['case'] = '002'
        with self.assertRaisesRegex(ValueError, 'Frozen'): validate_selection(selection)
        entries[1]['index'] = 0
        with self.assertRaisesRegex(ValueError, 'Duplicate'): make_selection(entries, examples=self.aliases())

    @contextmanager
    def prepared(self):
        selection = make_selection(self.entries(), examples=self.aliases())
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as tmp:
            base = Path(tmp); workspace = base/'workspace'; disk = Budget([base], 200_000_000)
            workspace_init(workspace, selection, disk)
            source_path = base/'source.h5'
            with h5py.File(source_path, 'w') as h:
                x = (np.arange(1024)+.5)/1024
                h['tensor'] = np.stack([np.tile(np.sin(2*np.pi*x)+i, (9, 1)) for i in range(20)]).astype('f4')
                h['x-coordinate'] = x.astype('f4'); h['t-coordinate'] = np.linspace(0, 1, 9)
            @contextmanager
            def source(*args, **kwargs):
                with h5py.File(source_path, 'r') as h: yield h
            with patch('utils.PDEBench.pipeline.open_source', source):
                for entry in selection['entries']:
                    prepare_entry(workspace, entry, base/'cache', disk, None, 1, NetworkBudget(0))
            with patch('utils.PDEBench.pipeline.open_source', side_effect=AssertionError('example reopens source')):
                prepare_examples(workspace, selection, disk)
                prepare_examples(workspace, selection, disk)
            yield workspace, selection, disk

    def test_twenty_cases_two_public_examples_and_actual_judge_report(self):
        with self.prepared() as (workspace, selection, disk):
            report = verify(workspace, selection)
            self.assertEqual(report['case_count'], 20)
            self.assertEqual(len(report['examples']), 2)
            public = report['public_cases']['advection-1d']
            self.assertEqual([(r['case'], r['sample']) for r in public], [('001', '01'), ('011', '02')])
            task = next(workspace.glob('qbank/*/*/advection-1d'))
            for case, sample in [('001', '01'), ('011', '02')]:
                for name in ('problem.json', 'input.h5', 'mesh.msh'):
                    self.assertEqual((task/'cases'/case/name).read_bytes(), (task/'samples'/sample/'input'/name).read_bytes())
                with h5py.File(task/'samples'/sample/'input/input.h5') as h:
                    self.assertEqual(len(h['times']), 9)
            artifact = publish('advection-1d', root=workspace)
            assembled = prepare('advection-1d', root=workspace)
            self.assertEqual(assembled['cases'], 20); self.assertEqual(assembled['public_cases'], public)
            import zipfile
            with zipfile.ZipFile(artifact['archive']) as bundle:
                self.assertFalse(any('/cases/' in n or '/author/' in n or '/evidence/' in n for n in bundle.namelist()))
                self.assertEqual(sum(n.endswith('/input/problem.json') for n in bundle.namelist()), 2)
            private = Path(assembled['task_directory'])/'tests'
            self.assertEqual(json.loads((private/'selection.json').read_text())['public_cases'], public)
            spec = importlib.util.spec_from_file_location('direct_public_judge', private/'judge.py')
            judge = importlib.util.module_from_spec(spec); spec.loader.exec_module(judge)
            logs = workspace/'judge-control'
            def execute(work, timeout, log_dir):
                # Trusted fixture supplies known results; no model or solver call.
                problem_bytes = (work/'input/problem.json').read_bytes()
                data_bytes = (work/'input/input.h5').read_bytes()
                case = next(p.parent.name for p in (private/'cases').glob('*/problem.json')
                            if p.read_bytes() == problem_bytes and (p.parent/'input.h5').read_bytes() == data_bytes)
                shutil.copyfile(private/'reference'/case/'reference.h5', work/'result.h5')
            with patch.object(judge, 'TESTS', private), patch.object(judge, 'LOGS', logs), \
                 patch.object(judge, 'freeze_submission', return_value=True), \
                 patch.object(judge, 'execute', side_effect=execute), patch.object(judge.os, 'chown'), redirect_stdout(io.StringIO()):
                judge.main()
            scored = json.loads((logs/'report.json').read_text())
            self.assertTrue(scored['complete']); self.assertEqual(scored['total_cases'], 20)
            self.assertEqual(scored['score'], 20); self.assertEqual(scored['public_cases'], public)
            self.assertEqual({r['case']: r['public_sample'] for r in scored['cases'] if 'public_sample' in r}, {'001':'01', '011':'02'})

    def test_reference_time_and_binding_tamper_fail_before_publish_or_assemble(self):
        with self.prepared() as (workspace, selection, disk):
            task = next(workspace.glob('qbank/*/*/advection-1d'))
            targets = [task/'samples/01/input/input.h5', task/'samples/01/reference/reference.h5',
                       task/'samples/01/output/result.h5', task/BINDING]
            for path in targets:
                original = path.read_bytes()
                if path.suffix == '.json':
                    value = json.loads(path.read_text()); value['public_cases'][0]['case'] = '002'
                    path.write_text(json.dumps(value))
                else:
                    with h5py.File(path, 'a') as h:
                        if 'initial_state' in h: h['times'][1] += .001
                        else: h['state'][0, 0, 0] += 1
                with self.subTest(path=path), self.assertRaises((ValueError, PreparationError)):
                    verify(workspace, selection)
                with self.assertRaises(ValueError): publish('advection-1d', root=workspace)
                with self.assertRaises(ValueError): prepare('advection-1d', root=workspace)
                path.write_bytes(original)

    def test_missing_binding_and_unselected_sample_fail_closed(self):
        with self.prepared() as (workspace, selection, disk):
            task = next(workspace.glob('qbank/*/*/advection-1d'))
            marker = task/BINDING; original = marker.read_bytes(); marker.unlink()
            for action in (lambda: verify(workspace, selection), lambda: publish('advection-1d', root=workspace),
                           lambda: prepare('advection-1d', root=workspace)):
                with self.assertRaises(ValueError): action()
            marker.write_bytes(original)
            shutil.copytree(task/'samples/01', task/'samples/03')
            for action in (lambda: verify(workspace, selection), lambda: publish('advection-1d', root=workspace),
                           lambda: prepare('advection-1d', root=workspace)):
                with self.assertRaises(ValueError): action()

    def test_example_interruption_recovers_without_source_access(self):
        with self.prepared() as (workspace, selection, disk):
            task = next(workspace.glob('qbank/*/*/advection-1d'))
            receipt = workspace/'evidence/advection-1d-example-01.json'
            receipt.unlink(); shutil.rmtree(task/'samples/01'); (task/BINDING).unlink()
            from utils.PDEBench import pipeline
            original = pipeline.atomic_json
            def fail_receipt(path, value):
                if path == receipt: raise OSError('injected receipt interruption')
                original(path, value)
            with patch.object(pipeline, 'atomic_json', fail_receipt):
                with self.assertRaisesRegex(OSError, 'receipt interruption'):
                    prepare_examples(workspace, selection, disk)
            self.assertTrue((task/'samples/01/input/problem.json').is_file())
            with patch.object(pipeline, 'open_source', side_effect=AssertionError('source reopened')):
                prepare_examples(workspace, selection, disk)
            self.assertEqual(verify(workspace, selection)['case_count'], 20)
            self.assertFalse(list((workspace/'transactions').glob('*example*')))


if __name__ == '__main__': unittest.main()
