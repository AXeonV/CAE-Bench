"""Real pool transactions against a local fake Hub; HTTP quota/lost-response faults."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parents[1]/'src/utils/PDEBench'


def module(name):
    spec=importlib.util.spec_from_file_location(name,TOOLS/name);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class LowCommitTests(unittest.TestCase):
    def test_two_atomic_commits_include_prepared_roots_then_real_consumed_verification(self):
        from caeoj_tools import data_pool as pool
        from caeoj_tools.data_pool_shards import publish
        from caeoj.sdk import load_problem,load_result
        from huggingface_hub import HfApi
        spec=importlib.util.spec_from_file_location('pool_fixture',Path(__file__).with_name('test_data_pool.py'))
        fixture_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture_module)
        fixture=fixture_module.PoolTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        physical=fixture.root/'physical';pool.shard_bundle(fixture.bundle,physical)
        selection=pool.manifest(physical/'selection.json')
        archive=module('hf_archive_migrate.py');worker=module('hf_low_commit_worker.py')
        records=[]
        for name in selection['cases']:
            problem=load_problem(fixture.source/'cases'/name/'problem.json')
            result=load_result(problem,fixture.source/'reference'/name/'reference.h5')
            records.append({'local_id':name,'fields':{k:{'mapped_float64':archive.array_sha(v)} for k,v in result.items()}})
        remote=fixture.root/'remote';remote.mkdir();state={'head':'0','commits':[]}
        class Hub(pool.LocalStore):
            def __init__(self,repo_id,revision='main',cache_dir=None):
                super().__init__(remote);self.revision=revision
        class API:
            def repo_info(self,*a,**kw):return SimpleNamespace(sha=state['head'])
            def get_paths_info(self,repo,names,**kw):
                result=[]
                for name in names:
                    path=remote/name
                    if path.exists():
                        data=path.read_bytes();result.append(SimpleNamespace(path=name,size=len(data),lfs=None,
                            blob_id=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()))
                return result
            def preupload_lfs_files(self,**kwargs):pass
            def create_commit(self,**kwargs):
                self_test.assertEqual(kwargs['parent_commit'],state['head'])
                payloads={}
                for op in kwargs['operations']:
                    with op.as_file() as stream:payloads[op.path_in_repo]=stream.read()
                # All operations become visible together, including the root and checkpoint.
                for name,data in payloads.items():
                    path=remote/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                state['head']=str(int(state['head'])+1);state['commits'].append(payloads)
                return SimpleNamespace(oid=state['head'])
        self_test=self
        args=SimpleNamespace(repo_id='owner/test',revision='branch',prefix='progress/w1')
        assignment={'worker':1,'batches':[{'family':'advection','file':'fixture','first':0,'count':2}],'source_rows':2}
        progress={'status':'running','batches':[],'verified_cases':0}
        gate=SimpleNamespace(snapshot=lambda:{})
        transaction=worker.BatchTransaction(API(),pool,publish,args,progress,assignment,assignment['batches'][0],'sha',gate,0)
        checkpoint={'status':'planned','batch_key':'key'};transaction.save(args,checkpoint)
        checkpoint.update(status='prepared',selection=selection,transport_sha256=pool.digest(physical/'transport.json'),
            producer_report={'records':records})
        transaction.save(args,checkpoint);self.assertEqual(len(state['commits']),0)
        with patch.object(pool,'HubStore',Hub),patch.object(__import__('huggingface_hub'),'HfApi',API):
            receipt=transaction.upload(physical,revision='branch')
            self.assertEqual(len(state['commits']),1)
            root=fixture.value['repository']['path']+'/pool/index.json'
            first=state['commits'][0]
            self.assertIn(root,first);self.assertIn('progress/w1/batches/key.json',first)
            self.assertEqual(json.loads(first['progress/w1/batches/key.json'])['status'],'prepared')
            # Simulate a controller crash after prepared publication. Restore
            # its immutable checkpoint and consume at the already accepted head.
            checkpoint=pool.checked_json(remote/'progress/w1/batches/key.json')
            progress=pool.checked_json(remote/'progress/w1/report.json')
            transaction=worker.BatchTransaction(API(),pool,publish,args,progress,assignment,assignment['batches'][0],'sha',gate,0)
            transaction.save(args,checkpoint)
            self.assertEqual(len(state['commits']),1)
            consumed=fixture.root/'real-consumed';consumed.mkdir()
            self.assertEqual(archive.consume(args,checkpoint,receipt['revision'],consumed),2)
            checkpoint.update(status='verified',verified_cases=2,pool_revision=receipt['revision'],elapsed_seconds=1.)
            transaction.save(args,checkpoint)
            self.assertEqual(len(state['commits']),2)
            final=json.loads(state['commits'][1]['progress/w1/report.json'])
            self.assertEqual(final['verified_cases'],2);self.assertEqual(final['status'],'worker_completed')
            # Exact prior transport remains stable even on identical later atomic publication.
            before=pool.checked_json(remote/root)
            publish(physical,revision='branch',atomic=True)
            self.assertEqual(pool.checked_json(remote/root),before)
        self.assertIsNotNone(transaction.saved_result)

    def test_unpublished_regeneration_must_preserve_old_logical_bindings(self):
        from caeoj_tools import data_pool as pool
        worker=module('hf_low_commit_worker.py')
        tx=worker.BatchTransaction(None,pool,None,None,{'batches':[],'verified_cases':0},None,None,'p',None,0)
        tx.expected_selection={'task_id':'task','repository':{'path':'p'},'cases':{'a':{'case_id':'old','sha256':'a'}},'samples':{}}
        state={'status':'prepared','selection':{**tx.expected_selection,'cases':{'a':{'case_id':'changed','sha256':'b'}}},'transport_sha256':'t'}
        with self.assertRaisesRegex(ValueError,'logical case'):tx.save(None,state)
        state['selection']=tx.expected_selection;tx.save(None,state)
        self.assertEqual(tx.pending['selection'],tx.expected_selection)

    def test_prepared_selection_mutation_cannot_become_verified(self):
        from caeoj_tools import data_pool as pool
        worker=module('hf_low_commit_worker.py')
        tx=worker.BatchTransaction(None,pool,None,None,{'batches':[],'verified_cases':0},None,None,'p',None,0)
        state={'status':'prepared','selection':{'a':1},'transport_sha256':'sha'};tx.save(None,state)
        state.update(status='verified',selection={'a':2})
        with self.assertRaisesRegex(ValueError,'binding changed'):tx.save(None,state)

    def test_absent_candidate_reserialization_requires_every_source_array_and_json_hash(self):
        import copy
        worker=module('hf_low_commit_worker.py')
        recipe=dict(kind='archive',family='advection',sources=[{'revision':'fixed'}],first=0,
                    per_file=1,count=1,worker_sha256='fixed-builder')
        record=dict(local_id='00-00000',source_file='fixed-file',sample_index=0,
            fields={'tensor':dict(source='source-array',mapped_float64='mapped-array',original_dtype='<f4',shape=[2,3])},
            source_coordinates_sha256='coords',mapped_coordinates_sha256='mapped-coords',valid_times_sha256='times',
            input_files={'source.json':'provenance','problem.json':'contract','input.h5':'old-container'},
            reference_sha256='old-reference-container',unused_trailing_time_coordinates=1,frames=2,reference_recomputed=False)
        old=dict(recipe=recipe,selection=dict(task_id='task',repository={'path':'p'},
            cases={'00-00000':{'case_id':'old','case':{'sha256':'old'}}},samples={}),producer_report={'records':[record]})
        fresh=copy.deepcopy(old)
        fresh['selection']['cases']['00-00000']={'case_id':'fresh','case':{'sha256':'fresh'}}
        fresh['producer_report']['records'][0]['input_files']['input.h5']='fresh-container'
        fresh['producer_report']['records'][0]['reference_sha256']='fresh-reference-container'
        self.assertEqual(worker.prove_unpublished_regeneration(old,fresh)['all_rows'],1)
        for mutation in ('source', 'mapped_float64'):
            bad=copy.deepcopy(fresh);bad['producer_report']['records'][0]['fields']['tensor'][mutation]='changed'
            with self.assertRaisesRegex(ValueError,'changed source arrays'):worker.prove_unpublished_regeneration(old,bad)
        bad=copy.deepcopy(fresh);bad['producer_report']['records'][0]['input_files']['source.json']='changed'
        with self.assertRaisesRegex(ValueError,'changed source arrays'):worker.prove_unpublished_regeneration(old,bad)
        bad=copy.deepcopy(fresh);bad['recipe']['sources']=[{'revision':'different'}]
        with self.assertRaisesRegex(ValueError,'pinned source'):worker.prove_unpublished_regeneration(old,bad)

    def test_actual_http_hook_covers_429_retries_and_honors_reset(self):
        import httpx
        from huggingface_hub import HfApi,CommitOperationAdd,set_client_factory
        from huggingface_hub.errors import HfHubHTTPError
        from huggingface_hub.utils._http import default_client_factory
        sys.path.insert(0,str(TOOLS));gateway_module=module('hf_commit_gateway.py')
        clock=[0.];gate=gateway_module.CommitGateway(1,'owner/test',100000.,10000.,clock=lambda:clock[0],sleep=lambda t:clock.__setitem__(0,clock[0]+t))
        attempts=[]
        def original(api,**kwargs):
            req=httpx.Request('POST','https://huggingface.co/api/datasets/owner/test/commit/branch')
            gate.request(req);attempts.append(gate.now())
            if len(attempts)==1:
                response=httpx.Response(429,headers={'retry-after':'120'},request=req)
                gate.response(response);raise HfHubHTTPError('quota',response=response)
            return SimpleNamespace(oid='accepted')
        try:
            with patch.object(HfApi,'create_commit',original):
                gate.install();result=HfApi().create_commit(repo_id='owner/test',repo_type='dataset',revision='branch',
                    operations=[CommitOperationAdd(path_in_repo='checkpoint.json',path_or_fileobj=b'{}')],commit_message='test')
                self.assertEqual(result.oid,'accepted');self.assertEqual(len(attempts),2)
                self.assertGreaterEqual(attempts[1]-attempts[0],120)
                self.assertEqual(gate.rate_limits,1)
        finally:set_client_factory(default_client_factory)

    def test_real_sdk_commit_post_goes_through_http_gate_and_quota_recovery(self):
        import httpx
        from huggingface_hub import HfApi,CommitOperationAdd,set_client_factory
        from huggingface_hub.utils._http import default_client_factory
        sys.path.insert(0,str(TOOLS));g=module('hf_commit_gateway.py')
        clock=[0.];gate=g.CommitGateway(2,'owner/test',100000,10000,
            clock=lambda:clock[0],sleep=lambda t:clock.__setitem__(0,clock[0]+t))
        posts=[];preuploads=[];original=HfApi.create_commit
        def respond(request):
            if '/preupload/' in request.url.path:
                preuploads.append(request.url.path)
                files=json.loads(request.content)['files']
                return httpx.Response(200,json={'files':[{'path':x['path'],'uploadMode':'regular','shouldIgnore':False} for x in files]})
            if '/commit/' in request.url.path:
                posts.append(gate.now())
                if len(posts)==1:return httpx.Response(429,headers={'retry-after':'120'},json={'error':'quota'})
                return httpx.Response(200,json={'commitOid':'a'*40,'commitUrl':'https://huggingface.co/datasets/owner/test/commit/'+'a'*40})
            raise AssertionError('Unexpected fake-Hub route '+request.url.path)
        try:
            gate.install()
            set_client_factory(lambda:httpx.Client(transport=httpx.MockTransport(respond),
                event_hooks={'request':[gate.request],'response':[gate.response]}))
            result=HfApi(token=False).create_commit(repo_id='owner/test',repo_type='dataset',revision='branch',parent_commit='b'*40,
                operations=[CommitOperationAdd(path_in_repo='checkpoint.json',path_or_fileobj=b'{}')],commit_message='test')
            self.assertEqual(result.oid,'a'*40);self.assertEqual(len(posts),2)
            self.assertGreaterEqual(posts[1]-posts[0],120);self.assertTrue(preuploads)
            self.assertEqual(gate.rate_limits,1)
        finally:HfApi.create_commit=original;set_client_factory(default_client_factory)

    def test_lost_success_response_is_proven_without_duplicate_post(self):
        import httpx
        from huggingface_hub import HfApi,CommitOperationAdd,set_client_factory
        from huggingface_hub.utils._http import default_client_factory
        sys.path.insert(0,str(TOOLS));g=module('hf_commit_gateway.py')
        now=[0.];gate=g.CommitGateway(1,'owner/test',100000,10000,clock=lambda:now[0],sleep=lambda t:now.__setitem__(0,now[0]+t))
        count=[0];data=b'checkpoint';sha=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
        def lost(api,**kwargs):
            gate.request(httpx.Request('POST','https://huggingface.co/api/datasets/owner/test/commit/branch'))
            count[0]+=1;raise httpx.ReadError('lost success response')
        try:
            with (patch.object(HfApi,'create_commit',lost),patch.object(HfApi,'repo_info',lambda *a,**k:SimpleNamespace(sha='accepted')),
                 patch.object(HfApi,'get_paths_info',lambda *a,**k:[SimpleNamespace(path='checkpoint.json',size=len(data),lfs=None,blob_id=sha)])):
                gate.install();result=HfApi().create_commit(repo_id='owner/test',repo_type='dataset',revision='branch',parent_commit='base',
                    operations=[CommitOperationAdd(path_in_repo='checkpoint.json',path_or_fileobj=data)],commit_message='test')
                self.assertEqual(result.oid,'accepted');self.assertEqual(count[0],1)
        finally:set_client_factory(default_client_factory)


if __name__=='__main__':unittest.main()
