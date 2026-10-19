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
        self.value = {'schema_version': 4, 'task_id': 'caeoj-000123',
                      'repository': {'repo_id': 'owner/test', 'repo_type': 'dataset', 'path': 'qbank/ch/sec/task'}}
        from caeoj_tools.author import load_author_module
        from caeoj.sdk import load_problem
        from caeoj.storage import write_hdf5
        from caeoj.validation import output_support
        from caeoj_tools.grading_policy import write_direct_grading
        scratch = self.root/'fixture'
        load_author_module('smoke-test', 'examples').make_cases(scratch)
        for name, parameter in (('a', 1), ('b', 2)):
            directory = self.source/'cases'/name
            shutil.copytree(scratch/'09-vector-2d',directory)
            problem_json = pool.checked_json(directory/'problem.json')
            problem_json.setdefault('physics', {'model':'identity','parameters':{}})['parameters']['parameter']={'value':parameter,'unit':'1'}
            pool.write_json(directory/'problem.json',problem_json)
            problem = load_problem(directory/'problem.json')
            ref = self.source/'reference'/name
            write_hdf5(ref/'reference.h5',{k:problem.arrays[k] for k in output_support(problem)|{v['array'] for v in problem.manifest['outputs'].values()}})
            write_direct_grading(ref, {'version':2,'default':{'metric':'pointwise','time':'per_time','components':'per_component','atol':1e-6,'rtol':0}})
        shutil.copytree(self.source/'cases/a', self.source/'samples/01/input')
        shutil.copytree(self.source/'reference/a',self.source/'samples/01/reference')
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

    def test_pack_reuses_samples_but_keeps_cases_self_contained(self):
        self.assertEqual(self.selection['samples']['01']['case_id'], self.selection['cases']['a']['case_id'])
        result = pool.assemble(self.task, self.selection, self.store)
        self.assertEqual(result['overlaps'], [])
        self.assertEqual(result['public_cases'], [{'case':'a','sample':'01','case_id':self.selection['cases']['a']['case_id']}])
        for directory in ('cases', 'reference', 'samples'):
            for f in (self.source/directory).rglob('*'):
                if f.is_file():
                    if f.name != 'verification.json':
                        self.assertEqual(f.read_bytes(), (self.task/f.relative_to(self.source)).read_bytes())
        self.assertFalse(list((self.bundle/'repository').rglob('shared')))
        self.assertEqual(len(list((self.bundle/'repository').rglob('mesh.msh'))), 2)
        self.assertTrue((self.bundle/'evidence/samples/01/verification.json').is_file())
        self.assertFalse((self.task/'samples/01/verification.json').exists())
        self.assertEqual(pool.assemble(self.task, self.selection, self.store)['changed'], 0)
        self.assertTrue(pool.verify(self.task)['valid'])
        self.assertTrue(pool.verify(self.task, strict=True)['valid'])
        self.assertTrue(pool.verify(self.task, strict=True, samples_only=True)['valid'])

    def test_shards_preserve_case_identity_and_fetch_only_selected_shard(self):
        transport = self.root/'transport'
        catalog = pool.shard_bundle(self.bundle, transport, target_bytes=1024)
        self.assertEqual(len(catalog['shards']), 2)
        backing = pool.LocalStore(self.root)
        store = pool.ShardStore(backing, 'transport', self.root/'extracted')
        selected = {**self.selection, 'cases': {'a':self.selection['cases']['a']}, 'samples':{}}
        pool.write_json(self.task/'data-manifest.json',selected)
        pool.assemble(self.task,selected,store)
        self.assertTrue(pool.verify(self.task,strict=True)['valid'])
        self.assertEqual(len(store.loaded),1)
        self.assertEqual((self.task/'cases/a/input.h5').read_bytes(),(self.source/'cases/a/input.h5').read_bytes())

    def partitioned_fixture(self):
        from caeoj_tools import data_pool_shards as shards
        repo=self.root/'partitioned-repo';prefix=self.value['repository']['path']
        partitions={};selections={};total=0
        for name in ('a','b'):
            source=self.root/('source-'+name)
            shutil.copytree(self.source/'cases'/name,source/'cases'/name)
            shutil.copytree(self.source/'reference'/name,source/'reference'/name)
            raw=self.root/('raw-'+name);pool.pack(source,raw,self.value)
            physical=self.root/('physical-'+name);catalog=pool.shard_bundle(raw,physical)
            batch=pool.digest(physical/'transport.json')
            rel='pool/batches/'+batch
            shutil.copytree(physical,repo/prefix/rel)
            index=pool.checked_json(physical/'index.json')
            transport={'path':rel+'/transport.json',**pool.identity(physical/'transport.json')}
            with tempfile.TemporaryDirectory() as tmp:
                source_store=pool.ShardStore(pool.LocalStore(physical.parent),physical.name,Path(tmp))
                indexed={cid:{**binding,'descriptor':pool.bound(source_store,prefix,binding)} for cid,binding in index['cases'].items()}
            updated,added=shards.stage_plan({},indexed,transport,lambda k:partitions.get(k,{}))
            partitions.update(updated);total+=added
            selections.update(pool.manifest(raw/'selection.json')['cases'])
        root={'schema_version':4,'kind':'partitioned-case-pool','case_count':total,'partitions':{}}
        for key,cases in partitions.items():
            path=repo/prefix/f'pool/partitions/{key}/part.json'
            pool.write_json(path,{'schema_version':1,'cases':cases})
            root['partitions'][key]={'path':path.relative_to(repo/prefix).as_posix(),**pool.identity(path),'case_count':len(cases)}
        pool.write_json(repo/prefix/'pool/index.json',root)
        return repo,{**self.selection,'cases':selections,'samples':{}},root

    def test_partitioned_cross_batch_selection_and_assembly(self):
        from caeoj_tools import data_pool_shards as shards
        repo,value,index=self.partitioned_fixture()
        backing=pool.LocalStore(repo)
        a,b=(value['cases'][k]['case_id'] for k in ('a','b'))
        choice=pool.select(value,backing,['a='+a,'b='+b],[])
        self.assertEqual(pool.consumer_store(value,backing).transports,{})  # Selection reads no TAR payload.
        pool.write_json(self.task/'data-manifest.json',choice)
        pool.assemble(self.task,choice,backing)
        self.assertTrue(pool.verify(self.task,strict=True)['valid'])
        view=pool.consumer_store(value,backing)
        self.assertIsInstance(view,shards.PartitionStore)
        self.assertEqual(len(view.transports),2)
        self.assertEqual(pool.assemble(self.task,choice,backing)['changed'],0)

    def test_listing_partitioned_pool_paginates_without_transport_payloads(self):
        repo, value, index = self.partitioned_fixture()
        backing = pool.LocalStore(repo)
        first = pool.list_cases(value, backing, limit=1)
        second = pool.list_cases(value, backing, offset=first['next_offset'], limit=1)
        self.assertEqual(first['total'], 2)
        self.assertIsNone(second['next_offset'])
        self.assertEqual({first['cases'][0]['case_id'], second['cases'][0]['case_id']},
                         {c['case_id'] for c in value['cases'].values()})
        self.assertEqual(pool.consumer_store(value, backing).transports, {})
        self.assertEqual(pool.list_cases(value, backing, offset=2)['cases'], [])

    def test_listing_direct_pool_and_invalid_page(self):
        page = pool.list_cases(self.selection, self.store, limit=1)
        self.assertEqual(page['total'], 2)
        self.assertEqual(len(page['cases']), 1)
        for kwargs in ({'limit': 0}, {'limit': 1001}, {'offset': -1}):
            with self.assertRaises(pool.PoolError):
                pool.list_cases(self.selection, self.store, **kwargs)

    def test_partitioned_digest_failure_does_not_change_local(self):
        repo,value,index=self.partitioned_fixture()
        entry=next(iter(index['partitions'].values()))
        path=repo/value['repository']['path']/entry['path']
        path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(pool.PoolError,'digest mismatch'):
            pool.assemble(self.task,value,pool.LocalStore(repo))
        self.assertFalse((self.task/'cases').exists())

    def test_partition_merge_keeps_original_transport_and_rejects_changed_case(self):
        from caeoj_tools import data_pool_shards as shards
        cid=self.selection['cases']['a']['case_id'];binding=self.selection['cases']['a']['case']
        binding={**binding,'input_complete':True,'reference_complete':True}
        old={cid:{**binding,'transport':{'path':'old'}}}
        merged,added=shards.stage_plan({}, {cid:binding},{'path':'new'},lambda _:old)
        self.assertEqual(added,0)
        self.assertEqual(merged[shards.bucket(cid)][cid]['transport'],{'path':'old'})
        with self.assertRaisesRegex(pool.PoolError,'Remote case differs'):
            shards.stage_plan({}, {cid:{**binding,'sha256':'0'*64}},{'path':'new'},lambda _:old)

    def test_partition_publish_rejects_bad_selection_and_flags_before_network(self):
        from caeoj_tools import data_pool_shards as shards
        from unittest.mock import Mock
        import sys
        for flaw in ('selection','completeness'):
            with self.subTest(flaw=flaw):
                output=self.root/('invalid-'+flaw)
                catalog=pool.shard_bundle(self.bundle,output)
                if flaw=='selection':
                    value=pool.checked_json(output/'selection.json')
                    value['cases']['a']['case']['sha256']='0'*64
                    pool.write_json(output/'selection.json',value)
                else:
                    index=pool.checked_json(output/'index.json')
                    next(iter(index['cases'].values()))['reference_complete']=False
                    pool.write_json(output/'index.json',index)
                    catalog['index'].update(pool.identity(output/'index.json'))
                    pool.write_json(output/'transport.json',catalog)
                api=Mock(side_effect=AssertionError('Network reached before validation'))
                fake=SimpleNamespace(HfApi=api,CommitOperationAdd=Mock())
                with patch.dict(sys.modules,{'huggingface_hub':fake}),self.assertRaises(pool.PoolError):
                    shards.publish(output)
                api.assert_not_called()

    def test_shards_reject_corrupt_archive_before_assembly(self):
        transport = self.root/'transport'
        catalog = pool.shard_bundle(self.bundle, transport)
        archive = transport/catalog['shards'][0]['archive']['path']
        with archive.open('ab') as stream: stream.write(b'corrupt')
        store = pool.ShardStore(pool.LocalStore(self.root),'transport',self.root/'extracted')
        with self.assertRaisesRegex(pool.PoolError,'Corrupt shard'):
            pool.assemble(self.task,self.selection,store)
        self.assertFalse((self.task/'cases').exists())

    def test_shards_reject_symlink_even_with_updated_archive_digest(self):
        import tarfile
        transport = self.root/'transport'
        catalog = pool.shard_bundle(self.bundle, transport)
        archive = transport/catalog['shards'][0]['archive']['path']
        with tarfile.open(archive,'a') as tar:
            info=tarfile.TarInfo('escape'); info.type=tarfile.SYMTYPE; info.linkname='/etc/passwd'
            tar.addfile(info)
        catalog['shards'][0]['archive'].update(pool.identity(archive))
        pool.write_json(transport/'transport.json',catalog)
        store=pool.ShardStore(pool.LocalStore(self.root),'transport',self.root/'extracted')
        with self.assertRaisesRegex(pool.PoolError,'linked or undeclared'):
            pool.assemble(self.task,self.selection,store)

    def test_select_disjoint_bindings_and_descriptor_tampering(self):
        a, b = (self.selection['cases'][n]['case_id'] for n in ('a', 'b'))
        chosen = pool.select(self.selection, self.store, ['01=' + b], ['example=' + a])
        pool.write_json(self.task/'data-manifest.json', chosen)
        pool.assemble(self.task, chosen, self.store)
        self.assertTrue(pool.verify(self.task, strict=True)['valid'])
        public = pool.select(self.selection, self.store, [a], [a])
        self.assertEqual(len(pool.plan(public,self.store)['public_cases']),1)
        for cases,samples in (([a,a],[]),([],[a,a])):
            with self.assertRaisesRegex(pool.PoolError,'duplicate inputs'):
                pool.select(self.selection,self.store,cases,samples)
        f = self.store.get(self.value['repository']['path'] + '/' + chosen['cases']['01']['case']['path'])
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

    def test_public_pair_does_not_hide_duplicates_within_either_role(self):
        for role in ('cases','samples'):
            value = deepcopy(self.selection)
            source = 'a' if role=='cases' else '01'
            value[role]['duplicate'] = deepcopy(value[role][source])
            result = pool.plan(value,self.store)
            self.assertTrue(result['public_cases'])
            self.assertTrue(result['overlaps'])
            pool.write_json(self.task/'data-manifest.json',value)
            pool.assemble(self.task,value,self.store,update=True)
            with self.assertRaisesRegex(pool.PoolError,'Overlapping'):
                pool.verify(self.task,strict=True)

    def test_same_trajectory_with_different_inputs_is_not_a_public_sample_exception(self):
        value = deepcopy(self.selection)
        for name in ('a','b'):
            binding = value['cases'][name]['case']
            path = self.store.get(value['repository']['path']+'/'+binding['path'])
            item = pool.checked_json(path)
            item['origin']['certificate_identity'] = {'source_id':'one','source_md5':'abc','sample_index':2}
            pool.write_json(path,item)
            binding['sha256'] = pool.digest(path)
        value['samples']['01'] = deepcopy(value['cases']['a'])
        result = pool.plan(value,self.store)
        self.assertIn(['cases/a','cases/b'],result['overlaps'])
        self.assertEqual(len(result['public_cases']),1)

    def test_hf_trajectory_identity_survives_rename_and_revision_change(self):
        value = deepcopy(self.selection)
        value['samples'] = {}
        for name, revision in (('a','rev-one'),('b','rev-two')):
            binding = value['cases'][name]['case']
            path = self.store.get(value['repository']['path']+'/'+binding['path'])
            item = pool.checked_json(path)
            item['origin']['certificate_identity'] = {
                'source_repository':'owner/upstream','source_sha256':'a'*64,
                'sample_index':2,'source_revision':revision,'source_file':name+'.h5'}
            pool.write_json(path,item)
            binding['sha256'] = pool.digest(path)
        result = pool.plan(value,self.store)
        self.assertIn(['cases/a','cases/b'],result['overlaps'])

    def test_pack_preserves_hf_certificate_identity(self):
        certificate = {'source_repository':'owner/upstream','source_sha256':'a'*64,
                       'sample_index':2,'source_revision':'rev-one','source_file':'state.h5',
                       'input_files':{p.name:pool.digest(p) for p in (self.source/'cases/a').iterdir() if p.is_file()}}
        pool.write_json(self.source/'reference/a/certificate.json',certificate)
        fresh = self.root/'hf-bundle'
        pool.pack(self.source,fresh,self.value)
        choice = pool.manifest(fresh/'selection.json')
        item = pool.checked_json(fresh/'repository'/self.value['repository']['path']/choice['cases']['a']['case']['path'])
        self.assertEqual(item['origin']['certificate_identity'],{k:v for k,v in certificate.items() if k!='input_files'})

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
        self.assertEqual((self.task/'cases/a/user.txt').read_text(encoding='utf-8'), 'keep')

    def test_partial_download_receipt_cannot_pass_full_benchmark(self):
        pool.assemble(self.task, self.selection, self.store, cases=[])
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
            index['cases']['unrelated'] = {'path': 'pool/cases/unrelated/case.json', 'sha256': '0'*64}
            pool.write_json(index_file, index)
            before = state['payload_reads']
            self.assertEqual(pool.upload(self.bundle)['uploaded_files'], 0)
            self.assertEqual(state['payload_reads'], before)
            self.assertIn('unrelated', pool.checked_json(index_file)['cases'])
            pool_file = next((remote/self.value['repository']['path']).rglob('input.h5'))
            pool_file.write_bytes(b'remote modification')
            with self.assertRaisesRegex(pool.PoolError, '--update'):
                pool.upload(self.bundle)
            self.assertGreater(pool.upload(self.bundle, update=True)['uploaded_files'], 0)

    def test_evidence_cannot_leak_into_upload_tree(self):
        case = next((self.bundle/'repository').rglob('case.json'))
        desc = pool.checked_json(case)
        desc['attachments'] = {}
        pool.write_json(case, desc)
        binding = {'path': case.relative_to(self.bundle/'repository'/self.value['repository']['path']).as_posix(), 'sha256': pool.digest(case)}
        with self.assertRaisesRegex(pool.PoolError, 'unsupported fields'):
            pool.item_files(self.store, self.value['repository']['path'], binding, desc, {})

    def test_old_selection_format_is_rejected_without_compatibility(self):
        old = deepcopy(self.selection)
        old['schema_version'] = 2
        pool.write_json(self.root/'old-selection.json', old)
        with self.assertRaisesRegex(pool.PoolError, 'schema_version 4'):
            pool.manifest(self.root/'old-selection.json')

    def test_reference_derivation_stays_in_evidence_not_hf(self):
        pool.write_json(self.source/'reference/a/analytic.json', {'formula': 'author only'})
        bundle = self.root/'with-evidence'
        pool.pack(self.source, bundle, self.value)
        self.assertTrue((bundle/'evidence/reference/a/analytic.json').is_file())
        self.assertFalse(list((bundle/'repository').rglob('analytic.json')))
        self.assertFalse(list((bundle/'repository').rglob('verification.json')))
        pool.validate_bundle(bundle)

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

    def test_shared_redirects_and_case_insensitive_destinations_are_rejected(self):
        binding = self.selection['cases']['a']['case']
        f = self.store.get(self.value['repository']['path'] + '/' + binding['path'])
        item = pool.checked_json(f)
        item['files']['input/mesh.msh']['source'] = 'pool/shared/mesh.msh'
        with self.assertRaisesRegex(pool.PoolError, 'redirect'):
            pool.item_files(self.store, self.value['repository']['path'], binding, item, {})
        selected = deepcopy(self.selection)
        selected['cases']['A'] = selected['cases']['a']
        with self.assertRaisesRegex(pool.PoolError, 'Case-insensitive'):
            pool.plan(selected, self.store)

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

    def test_manual_descriptor_cannot_disguise_grading_json_as_submission_example(self):
        binding=self.selection['samples']['01']['case']
        descriptor=self.store.get(self.value['repository']['path']+'/'+binding['path'])
        item=pool.checked_json(descriptor);item['example']='reference/grading.json'
        pool.write_json(descriptor,item)
        for role in ('cases','samples'):
            for choice in self.selection[role].values():
                if choice['case']['path']==binding['path']:choice['case']['sha256']=pool.digest(descriptor)
        with self.assertRaises(ValueError):pool.fetch(self.selection,self.store)

    def test_example_must_belong_to_bound_reference_group(self):
        binding=self.selection['samples']['01']['case']
        descriptor=self.store.get(self.value['repository']['path']+'/'+binding['path'])
        item=pool.checked_json(descriptor);item['example']='input/problem.json'
        with self.assertRaisesRegex(pool.PoolError,'Example'):
            pool.item_files(self.store,self.value['repository']['path'],binding,item,{})


if __name__ == '__main__':
    unittest.main()
