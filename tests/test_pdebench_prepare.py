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
from utils.PDEBench.conversion import advection_average, build_input, check_reference_initial
from utils.PDEBench.models import MODELS, BY_TASK
from utils.PDEBench.pipeline import prepare_task
from utils.PDEBench.sources import Reader, frame_indices
from utils.PDEBench.storage import Budget, PreparationError, RangeReader, digest
from utils.PDEBench.references import burgers_average, logistic_diffusion
from utils.PDEBench.source_audit import fhn_initial, audit_reference,transport_residual
from caeoj.sdk import load_problem, load_result, write_result


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
                h.attrs['config']=yaml.safe_dump({'domain_size':[1,1],'grid_size':[4,4]})
                h.create_dataset('velocity',shape=(1,5,4,4,2),dtype='f4')
                h.create_dataset('t',data=[[0.,np.nan,.011,.02,.027]],chunks=(1,1),compression='lzf')
            with h5py.File(path,'r') as h:
                reader=Reader(h,BY_TASK['PDEBench_2D_IncompressibleNavierStokes'])
                coords,times,_=reader.metadata(0,frames=np.array([0,2,4]))
                np.testing.assert_array_equal(times,[0.,.011,.027])
                np.testing.assert_array_equal(coords[0],[.125,.375,.625,.875])
                # A full read would encounter the deliberately invalid,
                # irrelevant frame. Requested time values remain untouched.
                with self.assertRaisesRegex(PreparationError,'Invalid actual source times'):
                    reader.metadata(0)
                for frames in ([1,2],[0,2,2],[0,5]):
                    with self.assertRaisesRegex(PreparationError,'Invalid selected'):
                        reader.metadata(0,frames=np.array(frames))

    def test_transport_witness_discriminates_physical_domain_scale(self):
        n=256;x=(np.arange(n)+.5)/n
        first=np.sin(2*np.pi*x)[:,None]*np.ones((1,n))
        second=np.sin(2*np.pi*(x-.001))[:,None]*np.ones((1,n))
        velocity=np.zeros((2,n,n,2));velocity[...,0]=1.
        tracer=np.stack([first,second]);times=np.array([.005,.006])
        self.assertLess(transport_residual(velocity,tracer,times,1.,10),.03)
        self.assertGreater(transport_residual(velocity,tracer,times,float(n),10),.9)

    def test_fhn_complete_initial_data_and_output_subset(self):
        model=BY_TASK['PDEBench_2D_ReactionDiffusion'];seed=17;n=8
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

    def test_darcy_audit_repairs_nonsteady_source_snapshot(self):
        model=BY_TASK['PDEBench_2D_DarcyFlow'];coords=[np.array([.25,.75])]*2
        values={'state':np.zeros((1,2,2,1)),'diffusivity':np.full((1,2,2,1),.1)}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            problem=build_input(model,{'filename':'2D_DarcyFlow_beta1.0_Train.hdf5'},coords,np.array([0.]),values,root)
            evidence=audit_reference(model,problem,values,coords,{},root/'result.npz')
            result=load_result(problem,root/'result.npz')
            # Each 2x2 corner has two zero-exterior faces; uniform 1.25 is
            # independently the solution for f=1, a=.1, h=.5.
            np.testing.assert_allclose(result['state'],1.25,atol=1e-14)
            self.assertEqual(evidence['checks']['official_relative_residual_l2'],1.)
            self.assertLess(evidence['checks']['corrected_relative_residual_l2'],1e-12)
            self.assertFalse(evidence['continuum_error_certified'])

    def test_logistic_reference_constant_ode_and_piecewise_initial_heat(self):
        times=np.array([0.,.125,.5])
        actual=logistic_diffusion(np.full(8,.3),times,.5,10.,4,256)
        exact=.3*np.exp(10*times)/(1+.3*np.expm1(10*times))
        np.testing.assert_allclose(actual[:,:,0],np.repeat(exact[:,None],8,axis=1),atol=2e-14)
        x=(np.arange(8)+.5)/8;initial=.5+.1*np.cos(2*np.pi*x)
        # Exact leading Fourier mode for the piecewise-constant initial data,
        # integrated over the original cells. Higher aliases decay below 1e-40.
        exact=.5+.1*np.sinc(1/8)**2*np.exp(-4*np.pi**2*.5*.1)*np.cos(2*np.pi*x)
        actual=logistic_diffusion(initial,np.array([0.,.1]),.5,0.,128,128)[1,:,0]
        np.testing.assert_allclose(actual,exact,rtol=0,atol=2e-7)

    def test_burgers_integrals_against_independent_quadrature(self):
        from scipy.integrate import quad
        initial=np.array([.3,-.1,.8,.2]);n=len(initial);kappa=.04;t=.19
        mean=initial.mean();dx=1/n
        primitive=np.concatenate(([0.],np.cumsum(initial-mean)*dx))
        def phi0(y):
            i=min(int(y/dx),n-1)
            return np.exp(-(primitive[i]+(initial[i]-mean)*(y-i*dx))/(2*kappa))
        def heat(x):
            x=(x-mean*t)%1
            return sum(quad(lambda y:phi0(y)*np.exp(-(x-y+w)**2/(4*kappa*t)),
                            i*dx,(i+1)*dx,epsabs=1e-13,epsrel=1e-13)[0]
                       for i in range(n) for w in range(-5,6))
        logs=np.log([heat(x) for x in np.arange(n+1)*dx])
        expected=mean-2*kappa/dx*np.diff(logs)
        actual=burgers_average(initial,[0.,t],kappa)[...,0]
        np.testing.assert_array_equal(actual[0],initial)
        np.testing.assert_allclose(actual[1],expected,rtol=0,atol=2e-13)
        np.testing.assert_allclose(burgers_average(np.full(8,2.3),[0.,.1,2.],.001),2.3,atol=1e-12)

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
                        output={'velocity':values['velocity'].reshape(len(times),-1,2).copy()}
                        check_reference_initial(model,problem,output)
                        output['velocity'][0,0,0]+=1.
                        with self.assertRaisesRegex(PreparationError,'Reference t=0'):
                            check_reference_initial(model,problem,output)
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
        if model.model=='reaction_diffusion_1d':labels=[(nu,r) for nu in [.5,1.,2.,5.] for r in [1.,2.,5.,10.]]
        x=(np.arange(1024)+.5)/1024
        for i,label in enumerate(labels):
            name=(f'1D_Advection_Sols_beta{label}.hdf5' if model.model=='advection_1d' else f'1D_Burgers_Sols_Nu{label}.hdf5')
            if model.model=='reaction_diffusion_1d':name=f'ReacDiff_Nu{label[0]}_Rho{label[1]}.hdf5'
            p=local/name
            with h5py.File(p,'w') as h:
                u=np.stack([(k+1)*np.sin(2*np.pi*x)+i/20 for k in range(8)]).astype('float32')
                if model.model=='reaction_diffusion_1d':u=(.5+.04*u).astype('float32')
                h.create_dataset('tensor',data=np.repeat(u[:,None],5,axis=1))
                h.create_dataset('x-coordinate',data=x.astype('float32'))
                h.create_dataset('t-coordinate',data=[0.,.125,.25,.375,.5,.625])
            files.append({'id':i+1,'filename':name,'directory':model.prefix.rstrip('/'),
                          'bytes':p.stat().st_size,'md5':digest(p,'md5'),'url':'https://invalid.test/'+name})
        catalog={'dataset':'offline-fixture','version':'test','files':files}
        cache=root/'runtime/cache';stage=root/'runtime/staging';budget=Budget([root/'runtime',root/'tasks'],100_000_000)
        return model,task,local,catalog,cache,stage,budget

    def test_metadata_only_clone_restores_payloads_and_preserves_definitions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            model,task,local,catalog,cache,stage,budget=self.fixture(root)
            prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1)
            clone=root/'clone';copied=clone/'tasks'/model.task;copied.mkdir(parents=True)
            for path in task.rglob('*'):
                relative=path.relative_to(task)
                if not path.is_file():continue
                if path.name in {'instruction.md','DATA.md','problem.json','certificate.json','selection.json'}:
                    destination=copied/relative;destination.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(path,destination)
            definitions={p:p.read_bytes() for p in copied.rglob('problem.json')}
            self.assertEqual(len(definitions),3)
            self.assertFalse(list(copied.rglob('*.npz')))
            restored=prepare_task(model,catalog,copied,clone/'runtime/cache',clone/'runtime/staging',
                                  Budget([clone],100_000_000),local=local,max_cases=1)
            self.assertEqual(restored['status'],'references_prepared')
            for path,data in definitions.items():self.assertEqual(path.read_bytes(),data)
            p=load_problem(copied/'cases/001/problem.json')
            load_result(p,copied/'reference/001/reference.npz')
            # A versioned definition edited by an author must never be silently
            # replaced with the generator's original mathematical problem.
            edited=copied/'samples/01/input/problem.json'
            manifest=json.loads(edited.read_text())
            manifest['physics']['parameters']['velocity']['value']+=1
            changed=json.dumps(manifest,indent=4)+'\n';edited.write_text(changed)
            reference=copied/'author/sample-certificates/01/reference.npz';before=digest(reference)
            failed=prepare_task(model,catalog,copied,clone/'runtime/cache',clone/'runtime/staging',
                                Budget([clone],100_000_000),local=local,max_cases=1)
            self.assertEqual(failed['status'],'failed')
            self.assertIn('Existing problem definition differs',failed['errors'][0]['error'])
            self.assertEqual(edited.read_text(),changed)
            self.assertEqual(digest(reference),before)

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
            with self.assertRaisesRegex(PreparationError,'Frozen selection'):
                prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=2,refresh_contract=True)

    def test_unreviewed_official_values_never_become_answers(self):
        with tempfile.TemporaryDirectory() as tmp:
            model,task,local,catalog,cache,stage,budget=self.fixture(Path(tmp),'PDEBench_1D_ReactionDiffusion')
            result=prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1)
            self.assertEqual(result['status'],'references_prepared')
            p=load_problem(task/'cases/001/problem.json')
            answer=load_result(p,task/'reference/001/reference.npz')['state']
            candidate=load_result(p,task/'reference/001/official-candidate.npz')['state']
            self.assertGreater(float(np.max(np.abs(answer-candidate))),.01)
            certificate=json.loads((task/'reference/001/certificate.json').read_text())
            self.assertEqual(certificate['official_candidate']['status'],'unreviewed_do_not_grade')
            self.assertFalse(certificate['evidence']['official_trajectory_used'])
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
            model,task,local,catalog,cache,stage,budget=self.fixture(root,'PDEBench_1D_ReactionDiffusion')
            prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1)
            problem=load_problem(task/'cases/001/problem.json')
            original=digest(task/'cases/001/input.npz')
            original_reference=digest(task/'reference/001/reference.npz')
            external=root/'reviewed'/model.task/'case/001';external.mkdir(parents=True)
            values=np.repeat(problem.arrays['initial_state'],len(problem.arrays['times']),axis=0)
            write_result(external/'reference.npz',problem,{'state':values})
            certificate=json.loads((task/'reference/001/certificate.json').read_text())
            audit={'status':'audited','method':'offline interface fixture only',
                   'error_evidence':{'scope':'test of importer, not a scientific reference'},
                   'contract_sha256':certificate['contract_sha256'],
                   'input_files':certificate['input_files'],'reference_sha256':'0'*64}
            (external/'evidence.json').write_text(json.dumps(audit))
            failed=prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1,
                                reference_root=root/'reviewed')
            self.assertEqual(failed['status'],'failed')
            self.assertEqual(len(failed['records']),2)
            self.assertIn('bind',failed['errors'][0]['error'])
            self.assertEqual(original,digest(task/'cases/001/input.npz'))
            self.assertEqual(original_reference,digest(task/'reference/001/reference.npz'))
            audit['reference_sha256']=digest(external/'reference.npz')
            (external/'evidence.json').write_text(json.dumps(audit))
            report=prepare_task(model,catalog,task,cache,stage,budget,local=local,max_cases=1,
                                reference_root=root/'reviewed')
            self.assertEqual(report['pending_references'],0)
            load_result(problem,task/'reference/001/reference.npz')
            self.assertEqual(original,digest(task/'cases/001/input.npz'))


if __name__=='__main__':unittest.main()
