"""Offline storage/semantic conversion tests; no claim of PDEBench physical validation."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest

try:
    import h5py
    import requests
    import yaml
except ImportError:
    raise unittest.SkipTest("Install the pdebench optional dependencies for preparation tests")
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from utils.PDEBench.conversion import advection_average, build_input
from utils.PDEBench.models import MODELS, BY_TASK
from utils.PDEBench.pipeline import prepare_task
from utils.PDEBench.sources import Reader, frame_indices
from utils.PDEBench.storage import Budget, PreparationError, RangeReader, digest
from caeoj.sdk import load_problem, load_result, write_result


class RangeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        outer=self
        self.payload=bytes(range(256))*32;self.ignore=False;self.etag='"one"';self.requests=0
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                outer.requests+=1
                if outer.ignore:
                    self.send_response(200);self.end_headers();return
                a,b=map(int,self.headers['Range'].removeprefix('bytes=').split('-'))
                b=min(b,len(outer.payload)-1)
                self.send_response(206)
                self.send_header('Content-Range',f'bytes {a}-{b}/{len(outer.payload)}')
                self.send_header('ETag',outer.etag)
                self.send_header('Content-Length',str(b-a+1));self.end_headers()
                self.wfile.write(outer.payload[a:b+1])
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.source={'id':1,'bytes':len(self.payload),'md5':hashlib.md5(self.payload).hexdigest(),
                     'url':f'http://127.0.0.1:{self.server.server_port}/data'}
        self.budget=Budget([self.root],1_000_000)

    def tearDown(self):
        self.server.shutdown();self.thread.join();self.server.server_close();self.tmp.cleanup()

    def reader(self):
        return RangeReader(self.source,self.root,self.budget,block_size=1024,memory_blocks=1,
                           cache_bytes=2048,timeout=2,retries=1)

    def test_ranges_resume_corruption_and_disk_lru(self):
        with self.reader() as r:
            r.seek(100);self.assertEqual(r.read(1300),self.payload[100:1400])
        first=self.requests
        with self.reader() as r:
            r.seek(100);self.assertEqual(r.read(1300),self.payload[100:1400])
        self.assertEqual(first,self.requests)
        (self.root/'1/0.bin').write_bytes(b'bad')
        with self.reader() as r:
            self.assertEqual(r.read(8),self.payload[:8])
            r.seek(6000);self.assertEqual(r.read(8),self.payload[6000:6008])
        self.assertGreater(self.requests,first)
        self.assertLessEqual(sum(p.stat().st_size for p in (self.root/'1').glob('*.bin')),2048)

    def test_refuses_full_download_and_changed_identity(self):
        self.ignore=True
        with self.reader() as r:
            with self.assertRaisesRegex(PreparationError,'refusing full'):r.read(8)
        self.ignore=False
        with self.reader() as r:r.read(8)
        self.etag='"two"'
        with self.reader() as r:
            r.seek(4096)
            with self.assertRaisesRegex(PreparationError,'changed'):r.read(8)

    def test_budget_fails_before_request(self):
        self.budget.limit=1
        with self.assertRaisesRegex(PreparationError,'budget'):
            with self.reader() as r:r.read(8)
        self.assertEqual(self.requests,0)


class ConversionTests(unittest.TestCase):
    def test_all_contracts_ascii_and_sparse_binary(self):
        for model in MODELS:
            for variant in (0,1):
                with self.subTest(task=model.task,variant=variant), tempfile.TemporaryDirectory() as tmp:
                    shape=(3,)*model.dimension
                    coords=[lo+(np.arange(n)+.5)*(hi-lo)/n for n,(lo,hi) in zip(shape,model.bounds)]
                    values={name:np.ones((3,)+shape+(c,)) for name,_,_,c in model.fields}
                    if model.model=='reaction_diffusion_1d':values['state']*=.2
                    if model.model=='diffusion_sorption_1d':values['concentration']*=.1
                    if model.model=='darcy_flow_2d':values['diffusivity']=np.ones((1,)+shape+(1,))
                    if model.points:
                        values['tracer']=np.ones((1,)+shape+(1,));values['forcing']=np.ones((1,)+shape+(2,))
                    name={'advection_1d':'1D_Advection_Sols_beta0.4.hdf5',
                          'burgers_1d':'1D_Burgers_Sols_Nu0.01.hdf5',
                          'reaction_diffusion_1d':'ReacDiff_Nu0.5_Rho1.0.hdf5',
                          'darcy_flow_2d':'2D_DarcyFlow_beta1.0_Train.hdf5'}.get(model.model,
                          'CFD_Rand_Eta0.01_Zeta0.01_periodic_Train.hdf5')
                    times=np.array([0.]) if model.model=='darcy_flow_2d' else np.array([0.,.5,1.])
                    problem=build_input(model,{'filename':name},coords,times,values,Path(tmp),variant)
                    arrays=problem.arrays
                    self.assertEqual(problem.manifest['physics']['model'],model.model)
                    if model.points:
                        for side in ('left','right','bottom','top'):
                            self.assertEqual(problem.manifest['fields']['wall_velocity_'+side]['location'],side)
                    else:
                        np.testing.assert_array_equal(arrays['cell_ids'],
                            np.arange(1,np.prod(shape)+1)*(3 if variant else 1)+(100 if variant else 0))
                    self.assertNotIn('source_id',problem.manifest)

    def test_advection_exact_overlap_not_a_center_value(self):
        initial=np.array([0.,2.,-1.,3.])
        result=advection_average(initial,np.array([0.,.125,.25,1.125]),1.)[...,0]
        np.testing.assert_allclose(result[1],[1.5,1.,.5,1.],atol=1e-14)
        np.testing.assert_allclose(result[2],np.roll(initial,1),atol=1e-14)
        np.testing.assert_allclose(result[1],result[3],atol=1e-14)
        np.testing.assert_allclose(result.sum(axis=1),initial.sum(),atol=1e-14)

    def test_grouped_fhn_axes_and_unused_time_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.h5'
            with h5py.File(path,'w') as h:
                data=np.arange(2*3*4*2).reshape(2,3,4,2)
                h.create_dataset('0000/data',data=data)
                h.create_dataset('0000/grid/x',data=np.arange(4))
                h.create_dataset('0000/grid/y',data=np.arange(3))
                h.create_dataset('0000/grid/t',data=[0.,1.])
            with h5py.File(path,'r') as h:
                reader=Reader(h,BY_TASK['PDEBench_2D_ReactionDiffusion'])
                result=reader.values(0,np.array([0,1]))
                self.assertEqual(result['activator'].shape,(2,4,3,1))
                self.assertEqual(result['inhibitor'][1,2,1,0],data[1,1,2,1])
        np.testing.assert_array_equal(frame_indices(21,9),[0,2,5,7,10,12,15,17,20])


class PipelineTests(unittest.TestCase):
    def fixture(self,root,model_name='PDEBench_1D_Advection'):
        model=BY_TASK[model_name]
        task=root/'tasks'/model.task;task.mkdir(parents=True)
        for name in ('instruction.md','DATA.md'):shutil.copyfile(ROOT/'tasks'/model.task/name,task/name)
        local=root/'local';local.mkdir();files=[]
        labels=[.1,.2,.4,.7,1.,2.,4.,7.] if model.model=='advection_1d' else [.001,.002,.004,.01,.02,.04,.1,.2,.4,1.,2.,4.]
        x=(np.arange(1024)+.5)/1024
        for i,label in enumerate(labels):
            name=(f'1D_Advection_Sols_beta{label}.hdf5' if model.model=='advection_1d' else f'1D_Burgers_Sols_Nu{label}.hdf5')
            p=local/name
            with h5py.File(p,'w') as h:
                u=np.stack([(k+1)*np.sin(2*np.pi*x)+i/20 for k in range(8)]).astype('float32')
                h.create_dataset('tensor',data=np.repeat(u[:,None],5,axis=1))
                h.create_dataset('x-coordinate',data=x.astype('float32'))
                h.create_dataset('t-coordinate',data=[0.,.125,.25,.375,.5,.625])
            files.append({'id':i+1,'filename':name,'directory':model.prefix.rstrip('/'),
                          'bytes':p.stat().st_size,'md5':digest(p,'md5'),'url':'https://invalid.test/'+name})
        catalog={'dataset':'offline-fixture','version':'test','files':files}
        cache=root/'runtime/cache';stage=root/'runtime/staging';budget=Budget([root/'runtime',root/'tasks'],100_000_000)
        return model,task,local,catalog,cache,stage,budget

    def test_real_pipeline_disjoint_resume_and_tamper_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            model,task,local,catalog,cache,stage,budget=self.fixture(Path(tmp))
            kwargs={'local':local,'max_cases':1}
            first=prepare_task(model,catalog,task,cache,stage,budget,**kwargs)
            self.assertEqual(first['status'],'references_prepared')
            selection=json.loads((task/'author/selection.json').read_text())
            sample_keys={(e['source_id'],e['index']) for e in selection['entries'] if e['kind']=='sample'}
            hidden_keys={(e['source_id'],e['index']) for e in selection['entries'] if e['kind']=='case'}
            self.assertFalse(sample_keys&hidden_keys)
            second=prepare_task(model,catalog,task,cache,stage,budget,**kwargs)
            self.assertTrue(all(r['reused'] for r in second['records']))
            (task/'cases/001/input.npz').write_bytes(b'corrupt')
            third=prepare_task(model,catalog,task,cache,stage,budget,**kwargs)
            p=load_problem(task/'cases/001/problem.json')
            result=load_result(p,task/'reference/001/reference.npz')
            np.testing.assert_array_equal(result['state'][0:1],p.arrays['initial_state'])
            with self.assertRaisesRegex(PreparationError,'Frozen selection'):
                prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=2)

    def test_unreviewed_official_values_never_become_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            model,task,local,catalog,cache,stage,budget=self.fixture(Path(tmp),'PDEBench_1D_Burgers')
            result=prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1)
            self.assertEqual(result['status'],'reference_pending')
            self.assertFalse((task/'samples/01/output/result.npz').exists())
            self.assertFalse((task/'reference/001/reference.npz').exists())
            self.assertTrue((task/'cases/001/problem.json').exists())
            self.assertTrue(list(cache.rglob('*.h5')))
            # Refuse full-file checksum mismatch before any conversion.
            catalog['files'][0]['md5']='0'*32
            with self.assertRaisesRegex(PreparationError,'MD5'):
                from utils.PDEBench.sources import open_source
                with open_source(catalog['files'][0],cache,budget,local):pass

    def test_external_review_binds_exact_input_and_failure_preserves_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            model,task,local,catalog,cache,stage,budget=self.fixture(root,'PDEBench_1D_Burgers')
            prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1)
            problem=load_problem(task/'cases/001/problem.json')
            original=digest(task/'cases/001/input.npz')
            external=root/'reviewed'/model.task/'case/001';external.mkdir(parents=True)
            values=np.repeat(problem.arrays['initial_state'],len(problem.arrays['times']),axis=0)
            write_result(external/'reference.npz',problem,{'state':values})
            certificate=json.loads((task/'reference/001/certificate.json').read_text())
            audit={'status':'audited','method':'offline interface fixture only',
                   'error_evidence':{'scope':'test of importer, not a scientific reference'},
                   'contract_sha256':certificate['contract_sha256'],
                   'input_files':certificate['input_files'],'reference_sha256':'0'*64}
            (external/'evidence.json').write_text(json.dumps(audit))
            with self.assertRaisesRegex(PreparationError,'bind'):
                prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1,
                             reference_root=root/'reviewed')
            self.assertEqual(original,digest(task/'cases/001/input.npz'))
            self.assertFalse((task/'reference/001/reference.npz').exists())
            audit['reference_sha256']=digest(external/'reference.npz')
            (external/'evidence.json').write_text(json.dumps(audit))
            report=prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1,
                                reference_root=root/'reviewed')
            self.assertEqual(report['pending_references'],2)
            load_result(problem,task/'reference/001/reference.npz')
            self.assertEqual(original,digest(task/'cases/001/input.npz'))


if __name__=='__main__':unittest.main()
