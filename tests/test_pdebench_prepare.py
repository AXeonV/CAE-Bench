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
from unittest.mock import patch
from contextlib import redirect_stdout
import io

try:
    import h5py
    import requests
    import yaml
except ImportError:
    raise unittest.SkipTest("Install the pdebench optional dependencies for preparation tests")
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from utils.PDEBench.conversion import build_input, check_reference_initial
from utils.PDEBench.models import MODELS, BY_TASK
from utils.PDEBench.sources import Reader
from utils.PDEBench.storage import Budget, PreparationError, RangeReader, digest
from utils.PDEBench.sources import fhn_initial
from caeoj.sdk import load_problem, load_result, write_result
from caeoj_tools.task_paths import task_directory




class RangeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        outer=self
        self.payload=bytes(range(256))*32;self.ignore=False;self.etag='"one"';self.requests=0;self.transient=0
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                outer.requests+=1
                if outer.transient:
                    outer.transient-=1;self.send_response(503);self.end_headers();return
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

    def test_large_reads_coalesce_without_losing_block_resume(self):
        def reader():
            return RangeReader(self.source,self.root,self.budget,block_size=1024,
                               memory_blocks=4,cache_bytes=8192,timeout=2,retries=1)
        with reader() as r:self.assertEqual(r.read(6000),self.payload[:6000])
        first=self.requests
        self.assertLess(first,6)
        with reader() as r:self.assertEqual(r.read(6000),self.payload[:6000])
        self.assertEqual(first,self.requests)
        (self.root/'1/1024.bin').write_bytes(b'bad')
        with reader() as r:self.assertEqual(r.read(6000),self.payload[:6000])
        self.assertGreater(self.requests,first)

    def test_recovers_from_transient_http_failure(self):
        self.transient=1
        with RangeReader(self.source,self.root,self.budget,block_size=1024,
                         memory_blocks=1,cache_bytes=2048,timeout=2,retries=2) as r:
            self.assertEqual(r.read(32),self.payload[:32])
        self.assertEqual(self.requests,2)
        with self.reader() as r:self.assertEqual(r.read(32),self.payload[:32])
        self.assertEqual(self.requests,2)

class ConversionTests(unittest.TestCase):
    def test_ns_metadata_reads_only_actual_selected_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ns.h5'
            with h5py.File(path,'w') as h:
                h.attrs['config']=yaml.safe_dump({'domain_size':[1,1],'grid_size':[4,4],'NU':.01,'velocity_extrapolation':'ZERO','particle_extrapolation':'BOUNDARY','force_extrapolation':'ZERO'})
                h.create_dataset('velocity',shape=(1,5,4,4,2),dtype='f4')
                h.create_dataset('particles',shape=(1,5,4,4,1),dtype='f4')
                h.create_dataset('force',shape=(1,4,4,2),dtype='f4')
                h['particles'][0,1:]=np.nan
                h['velocity'][...,0]=1.5;h['velocity'][...,1]=-2.5
                h.create_dataset('t',data=[[0.,np.nan,.011,.02,.027]],chunks=(1,1),compression='lzf')
            with h5py.File(path,'r') as h:
                reader=Reader(h,BY_TASK['incompressible-navier-stokes-2d'])
                coords,times,_=reader.metadata(0,frames=np.array([0,2,4]))
                np.testing.assert_array_equal(times,[0.,.011,.027])
                np.testing.assert_array_equal(coords[0],[.125,.375,.625,.875])
                values=reader.values(0,[0,2,4])
                self.assertEqual(values['tracer'].shape,(1,4,4,1))
                self.assertTrue(np.isfinite(values['tracer']).all())
                np.testing.assert_array_equal(values['velocity'][...,0],1.5)
                np.testing.assert_array_equal(values['velocity'][...,1],-2.5)
                # A full read would encounter the deliberately invalid,
                # irrelevant frame. Requested time values remain untouched.
                with self.assertRaisesRegex(PreparationError,'Invalid actual source times'):
                    reader.metadata(0)
                for frames in ([1,2],[0,2,2],[0,5]):
                    with self.assertRaisesRegex(PreparationError,'Invalid selected'):
                        reader.metadata(0,frames=np.array(frames))

    def test_ns_metadata_rejects_incompatible_physics(self):
        import yaml
        base={'domain_size':[1,1],'grid_size':[4,4],'NU':.01,'velocity_extrapolation':'ZERO','particle_extrapolation':'BOUNDARY','force_extrapolation':'ZERO'}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'source.h5'
            with h5py.File(p,'w') as h:
                h.create_dataset('velocity',shape=(1,2,4,4,2),dtype='f4')
                h.create_dataset('particles',shape=(1,2,4,4,1),dtype='f4')
                h.create_dataset('force',shape=(1,4,4,2),dtype='f4')
                h['t']=[[0.,.01]]
                for key,value in [('NU',.02),('velocity_extrapolation','PERIODIC'),('enable_gravity',True),('enable_obstacles',True),('domain_size',[512,512])]:
                    with self.subTest(key=key):
                        h.attrs['config']=yaml.safe_dump(dict(base,**{key:value}))
                        with self.assertRaises(PreparationError):Reader(h,BY_TASK['incompressible-navier-stokes-2d']).metadata(0,frames=np.array([0,1]))

    def test_fhn_complete_initial_data_and_output_subset(self):
        model=BY_TASK['reaction-diffusion-2d'];seed=17;n=8
        rng=np.random.RandomState(seed)
        full={name:rng.standard_normal(n*n).reshape(n,n).T.astype('float32').astype(float)
              for name in ('activator','inhibitor')}
        indices=np.array([1,5]);coords=[-1+(indices+.5)*2/n]*2
        values={name:data[np.ix_(indices,indices)][None,...,None] for name,data in full.items()}
        config={'sim':{'xdim':n,'ydim':n,'seed':seed}}
        with tempfile.TemporaryDirectory() as tmp:
            problem=build_input(model,{'filename':'2D_diff-react_NA_NA.h5'},coords,np.array([0.]),values,Path(tmp),1,config)
            self.assertEqual(problem.arrays['initial_activator'].shape,(1,64,1))
            self.assertEqual(len(problem.arrays['cell_ids']),4)
            self.assertEqual(problem.manifest['fields']['initial_activator']['location'],'initial_domain')
            self.assertNotIn('physical_group',problem.manifest['locations']['domain'])
            positions=np.searchsorted(problem.arrays['initial_cell_ids'],problem.arrays['cell_ids'])
            np.testing.assert_array_equal(problem.arrays['initial_activator'][0,positions,0],values['activator'].reshape(-1))
            outputs={name:array.reshape(1,-1,1) for name,array in values.items()}
            check_reference_initial(model,problem,outputs)
            outputs['activator']=outputs['activator']+1.
            with self.assertRaisesRegex(PreparationError,'Reference t=0'):
                check_reference_initial(model,problem,outputs)
        values['activator'][0,0,0,0]+=1
        with self.assertRaisesRegex(PreparationError,'reproduce'):fhn_initial(coords,values,config)

    def test_all_contracts_ascii_and_sparse_numbering(self):
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
                    self.assertEqual((Path(tmp)/'mesh.msh').read_bytes().splitlines()[1],b'4.1 0 8')
                    arrays=problem.arrays
                    self.assertEqual(problem.manifest['physics']['model'],model.model)
                    if model.points:
                        for side in ('left','right','bottom','top'):
                            self.assertEqual(problem.manifest['fields']['wall_velocity_'+side]['location'],side)
                        output={'velocity':values['velocity'].reshape(len(times),-1,2).copy()}
                        check_reference_initial(model,problem,output)
                        output['velocity'][0,0,0]+=1.
                        with self.assertRaisesRegex(PreparationError,'Reference t=0'):
                            check_reference_initial(model,problem,output)
                    else:
                        np.testing.assert_array_equal(arrays['cell_ids'],
                            np.arange(1,np.prod(shape)+1)*(3 if variant else 1)+(100 if variant else 0))
                    self.assertNotIn('source_id',problem.manifest)

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
                reader=Reader(h,BY_TASK['reaction-diffusion-2d'])
                result=reader.values(0,np.array([0,1]))
                self.assertEqual(result['activator'].shape,(2,4,3,1))
                self.assertEqual(result['inhibitor'][1,2,1,0],data[1,1,2,1])
