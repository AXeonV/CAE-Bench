"""Synthetic archive roundtrip through the real pool; no network or paid Jobs."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

PATH = Path(__file__).resolve().parents[1]/'src/utils/PDEBench/hf_archive_migrate.py'
SPEC = importlib.util.spec_from_file_location('archive_worker', PATH)
WORKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WORKER)


class ArchiveMigrationTests(unittest.TestCase):
    def test_full_plan_covers_each_source_row_once_including_pilot(self):
        sources = [{'family': family, 'file': f'{family}-{i}', 'source_records': 10000}
                   for family, count in (('advection', 8), ('burgers', 12), ('compressible', 5))
                   for i in range(count)]
        plan = WORKER.full_plan({'sources': sources})
        self.assertEqual(len(plan), 250)
        for source in sources:
            rows = list(range(16))
            for batch in plan:
                if batch['file'] == source['file']:
                    rows.extend(range(batch['first'], batch['first']+batch['count']))
            self.assertEqual(rows, list(range(10000)))
        self.assertFalse(WORKER.remaining_time_allows_batch(72*3600-2000, 72*3600))
        self.assertFalse(WORKER.remaining_time_allows_batch(72*3600-3000, 72*3600, 1500))
        self.assertTrue(WORKER.remaining_time_allows_batch(100, 72*3600, 600))

    def test_worker_refuses_local_source_access(self):
        with patch.dict('os.environ', {}, clear=True), self.assertRaises(SystemExit):
            WORKER.main(['--repo-id', 'fixture/data', '--revision', 'test', '--prefix', 'test',
                '--source-revision', 'a'*40, '--source-prefix', 'test'])

    def test_three_families_survive_pack_shard_assemble_without_field_or_row_changes(self):
        from caeoj.sdk import load_problem, load_result
        from caeoj_tools import data_pool as pool
        for family in WORKER.TASKS:
            with self.subTest(family=family), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = {'family': family, 'repo_id': 'fixture/'+family, 'revision': 'a'*40,
                    'file': family+'.hdf5', 'source_lfs_sha256': 'b'*64}
                keys = ['density', 'Vx', 'pressure'] if family == 'compressible' else ['tensor']
                dtype = np.float64 if family == 'compressible' else np.float32
                values = {key: (np.arange(12, dtype=dtype).reshape(3, 4)*.17+i+.001)
                          for i, key in enumerate(keys)}
                times = np.array([0., .125, .25, .375], dtype=np.float32)
                coordinates = np.array([.125, .375, .625, .875])
                records = []
                for row in (0, 1):
                    records.append(WORKER.build_case(root/'source', str(row), source, row,
                        coordinates, times, values, {'file_attributes': {'eta': .001},
                        'filename': 'Eta1.e-8', 'conflict_resolution': 'not inferred'}))
                ident, task = WORKER.TASKS[family]
                value = {'schema_version': 4, 'task_id': ident,
                    'repository': {'repo_id': 'fixture/data', 'repo_type': 'dataset', 'path': task},
                    'pool': {'index': 'pool/index.json'}, 'cases': {}, 'samples': {}}
                pool.pack(root/'source', root/'bundle', value)
                pool.shard_bundle(root/'bundle', root/'physical')
                choice = pool.manifest(root/'physical/selection.json')
                self.assertEqual(len({x['case_id'] for x in choice['cases'].values()}), 2)
                dest = root/'assembled'
                pool.write_json(dest/'data-manifest.json', choice)
                backing = pool.ShardStore(pool.LocalStore(root), 'physical', root/'cache')
                pool.assemble(dest, choice, backing)
                pool.verify(dest, strict=True)
                for row in (0, 1):
                    problem = load_problem(dest/'cases'/str(row)/'problem.json')
                    result = load_result(problem, dest/'reference'/str(row)/'reference.h5')
                    origin = json.loads((dest/'cases'/str(row)/'source.json').read_text())
                    self.assertEqual(origin['sample_index'], row)
                    self.assertEqual(origin['unused_trailing_time_coordinates'], 1)
                    self.assertEqual(origin['metadata']['file_attributes']['eta'], .001)
                    self.assertEqual(origin['metadata']['filename'], 'Eta1.e-8')
                    np.testing.assert_array_equal(problem.arrays['coordinates'][:, 0], coordinates)
                    np.testing.assert_array_equal(problem.arrays['times'], times[:3])
                    for key, original in values.items():
                        np.testing.assert_array_equal(result[key][..., 0], original)
                        np.testing.assert_array_equal(problem.arrays['initial_'+key][0, :, 0], original[0])
                        self.assertEqual(WORKER.array_sha(result[key]), records[row]['fields'][key]['mapped_float64'])


if __name__ == '__main__':
    unittest.main()
