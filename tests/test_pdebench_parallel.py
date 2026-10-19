"""No paid Jobs: source ownership, terminal budgeting and exact pool union."""
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import unittest


def module(name):
    path=Path(__file__).resolve().parents[1]/'src/utils/PDEBench'/name
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


class ParallelTests(unittest.TestCase):
    def test_real_frozen_plan_owns_every_remaining_span_once(self):
        root=Path(__file__).resolve().parents[1]/'qbank/design/reviews/pdebench-parallel-20261019'
        plan=json.loads((root/'plan.json').read_text());frozen=json.loads((root/'frozen-full-report.json').read_text())
        worker=module('hf_parallel_archive.py');worker.validate_plan(plan,frozen)
        missing=copy.deepcopy(plan);missing['workers'][0]['batches'].pop()
        repeated=copy.deepcopy(plan);repeated['workers'][0]['batches'].append(repeated['workers'][1]['batches'][0])
        for invalid in [missing,repeated]:
            with self.assertRaises(ValueError):worker.validate_plan(invalid,frozen)
        for w in plan['workers']:
            report={'worker':w['worker'],'plan_sha256':'a','verified_cases':w['source_rows'],
                'batches':[{'source_file':b['file'],'first':b['first'],'cases':b['count']} for b in w['batches']]}
            worker.check_worker(report,w,'a')
            report['batches'][0]['first']+=1
            with self.assertRaises(ValueError):worker.check_worker(report,w,'a')

    def test_cancel_request_or_exposed_hardware_cannot_release_hold(self):
        launcher=module('hf_parallel_launch.py')
        raw={'status':{'stage':'CANCELED'},'flavor':'cpu-basic','createdAt':'2026-10-18T14:46:50.893Z',
            'expose':[],'ssh':False}
        self.assertEqual(launcher.terminal_observation_bound(raw,'Sun, 18 Oct 2026 17:22:52 GMT',167),.026386)
        self.assertEqual(launcher.terminal_observation_bound({**raw,'expose':{'ports':[]},'ssh':{'enabled':False}},'Sun, 18 Oct 2026 17:22:52 GMT',167),.026386)
        for changes in [{'expose':{'ports':[8000]}},{'ssh':{'enabled':True}},{'status':{'stage':'RUNNING'}},{'expose':[8000]},{'ssh':True},{'flavor':'cpu-upgrade'}]:
            with self.assertRaises(ValueError):launcher.terminal_observation_bound({**raw,**changes},'Sun, 18 Oct 2026 17:22:52 GMT',167)
        with self.assertRaises(ValueError):launcher.terminal_observation_bound(raw,'Sun, 18 Oct 2026 13:22:52 GMT',167)

    def test_union_keeps_base_and_disjoint_workers_and_rejects_rebinding(self):
        worker=module('hf_parallel_archive.py')
        base={'old':{'sha256':'a','transport':{'path':'original'}}}
        incoming={'new':{'sha256':'b','transport':{'path':'worker1'}}}
        union=worker.union_entries(base,incoming)
        self.assertEqual(set(union),{'old','new'});self.assertEqual(set(base),{'old'})
        self.assertEqual(worker.union_entries(union,base),union)
        with self.assertRaises(ValueError):worker.union_entries(union,{'old':{'sha256':'a','transport':{'path':'changed'}}})

    def test_staging_changes_only_one_assignment_and_preserves_literals(self):
        launcher=module('hf_parallel_launch.py')
        source="PAYLOAD = ''\nx = \"PAYLOAD = unchanged\"\n"
        result=launcher.replace_assignment(source,'PAYLOAD','a\\nb')
        self.assertIn('x = "PAYLOAD = unchanged"',result)
        scope={};exec(result,scope);self.assertEqual(scope['PAYLOAD'],'a\\nb')
        with self.assertRaises(ValueError):launcher.replace_assignment(source,'MISSING','x')


if __name__=='__main__':unittest.main()
