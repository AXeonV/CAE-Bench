"""Budget and source-selection checks; no network or paid jobs."""
import importlib.util
from pathlib import Path
import unittest
from fractions import Fraction
import io
import base64
import zipfile


def module(filename):
    path = Path(__file__).resolve().parents[1]/'src/utils/PDEBench'/filename
    spec = importlib.util.spec_from_file_location(filename.removesuffix('.py'), path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class CloudTrialTests(unittest.TestCase):
    def test_runtime_identity_tracks_content_without_zip_timestamps(self):
        worker=module('hf_migrate.py')
        def payload(text,year):
            output=io.BytesIO()
            with zipfile.ZipFile(output,'w') as archive:
                info=zipfile.ZipInfo('docs/CONTRACT.md',(year,1,1,0,0,0));archive.writestr(info,text)
            return base64.b64encode(output.getvalue())
        self.assertEqual(worker.runtime_identity(payload('a',2020)),worker.runtime_identity(payload('a',2026)))
        self.assertNotEqual(worker.runtime_identity(payload('a',2026)),worker.runtime_identity(payload('b',2026)))

    def test_checkpoint_never_regresses_or_changes_bound_identity(self):
        worker=module('hf_migrate.py')
        state={'version':1,'status':'planned','batch_key':'a','recipe':{'x':1}}
        worker.transition(None,state)
        prepared={**state,'status':'prepared','selection':{'cases':1},'transport_sha256':'b'}
        worker.transition(state,prepared)
        verified={**prepared,'status':'verified'};worker.transition(prepared,verified)
        for before,after in ((verified,prepared),(prepared,{**prepared,'selection':{}}),
                             (prepared,{**prepared,'transport_sha256':'c'}),(state,{**state,'status':'unknown'})):
            with self.assertRaises(RuntimeError):worker.transition(before,after)

    def test_active_unknown_budget_holds_are_not_released(self):
        launcher=module('hf_trial_launch.py')
        for status in ('submitted','submission_pending'):
            self.assertEqual(launcher.effective_reservation({'status':status,'maximum_reserved_compute_usd':.02,
                'api_lifecycle_cost_upper_bound_usd':.001}),.02)
        self.assertEqual(launcher.effective_reservation({'status':'completed','maximum_reserved_compute_usd':.02,
            'api_lifecycle_cost_upper_bound_usd':.001}),.001)

    def test_settlement_distinguishes_hub_endpoint_from_exposed_job(self):
        from types import SimpleNamespace
        from datetime import datetime,timedelta,timezone
        launcher=module('hf_trial_launch.py');start=datetime.now(timezone.utc)
        info=SimpleNamespace(status=SimpleNamespace(stage='COMPLETED'),flavor='cpu-upgrade',
            endpoint='https://huggingface.co',expose_urls=None,ssh_url=None,
            created_at=start,finished_at=start+timedelta(seconds=61))
        api=SimpleNamespace(inspect_job=lambda **_:info)
        ledger={'attempts':[{'job_id':'a','status':'submitted','maximum_reserved_compute_usd':.02}]}
        launcher.settle_completed(api,ledger)
        self.assertEqual(launcher.effective_reservation(ledger['attempts'][0]),.0015)
        info.expose_urls=['https://example.hf.jobs']
        ledger={'attempts':[{'job_id':'b','status':'submitted','maximum_reserved_compute_usd':.02}]}
        launcher.settle_completed(api,ledger)
        self.assertEqual(launcher.effective_reservation(ledger['attempts'][0]),.02)

    def test_launch_dispatch_preserves_source_case_and_calibration_workers(self):
        launcher=module('hf_trial_launch.py')
        self.assertEqual(launcher.worker_path('source').name,'hf_source_probe.py')
        self.assertEqual(launcher.worker_path('calibration').name,'hf_cost_calibration.py')
        self.assertEqual(launcher.worker_path('archive-pilot').name,'hf_archive_migrate.py')
        for phase in ('transport','readiness','migration-prep','migration','preflight'):
            self.assertEqual(launcher.worker_path(phase).name,'hf_transport_trial.py')
        self.assertEqual(launcher.worker_path('preflight',True).name,'hf_burgers_preflight.py')

    def test_archive_submission_embeds_only_the_payload_assignment(self):
        from unittest.mock import patch,Mock
        from types import SimpleNamespace
        import tempfile,json
        launcher=module('hf_trial_launch.py')
        api=Mock()
        api.whoami.return_value={'name':'fixture'}
        api.list_jobs_hardware.return_value=[SimpleNamespace(name='cpu-basic',unit_label='minute',unit_cost_micro_usd=167)]
        captured={}
        def submit(path,**kwargs):
            captured.update(text=Path(path).read_text(),args=kwargs)
            return SimpleNamespace(id='fixture-job',url='https://example.test/job')
        api.run_uv_job.side_effect=submit
        api.inspect_job.return_value=SimpleNamespace(flavor='cpu-basic')
        hub=SimpleNamespace(HfApi=lambda:api,get_token=lambda:'fixture-not-a-secret')
        with tempfile.TemporaryDirectory() as tmp:
            worker=Path(tmp)/'worker.py'
            worker.write_text('RUNTIME_ZIP = \'\'\nliteral = "RUNTIME_ZIP = \'\'"\n')
            with patch.dict('sys.modules',{'huggingface_hub':hub}),patch.object(launcher,'worker_path',return_value=worker),patch.object(launcher,'runtime_payload',return_value='cGF5bG9hZA=='),patch('sys.stdout',new_callable=io.StringIO):
                launcher.main(['--phase','archive-pilot','--hardware','cpu-basic','--per-file','16',
                    '--batch-start','32','--source-revision','f'*40,'--repo-id','fixture/data',
                    '--revision','fixture','--prefix','fixture','--ledger',str(Path(tmp)/'budget.json'),'--submit'])
            namespace={};exec(captured['text'],namespace)
            self.assertEqual(namespace['RUNTIME_ZIP'],'cGF5bG9hZA==')
            self.assertEqual(namespace['literal'],"RUNTIME_ZIP = ''")
            self.assertEqual(captured['args']['flavor'],'cpu-basic')
            self.assertIn('--per-file',captured['args']['script_args'])
            attempt=json.loads((Path(tmp)/'budget.json').read_text())['attempts'][0]
            self.assertEqual(attempt['batch_start'],32)

    def test_archive_invalid_span_is_rejected_before_any_api_call(self):
        from unittest.mock import patch
        launcher=module('hf_trial_launch.py')
        with patch('sys.stderr',new_callable=io.StringIO),self.assertRaises(SystemExit):
            launcher.main(['--phase','archive-pilot','--hardware','cpu-basic',
                '--per-file','16','--batch-start','9999','--submit'])

    def test_full_launch_reserves_whole_timeout_and_inherits_fixed_baseline(self):
        from unittest.mock import patch,Mock
        from types import SimpleNamespace
        import tempfile,json
        launcher=module('hf_trial_launch.py')
        for previous,allowed in ((.107185,True),(.4,False)):
            api=Mock()
            api.whoami.return_value={'name':'fixture'}
            api.list_jobs_hardware.return_value=[SimpleNamespace(name='cpu-basic',unit_label='minute',unit_cost_micro_usd=167)]
            api.run_uv_job.return_value=SimpleNamespace(id='fixture-job',url='https://example.test/job')
            api.inspect_job.return_value=SimpleNamespace(flavor='cpu-basic')
            hub=SimpleNamespace(HfApi=lambda:api,get_token=lambda:'fixture-not-a-secret')
            with tempfile.TemporaryDirectory() as tmp,patch.dict('sys.modules',{'huggingface_hub':hub}),patch.object(launcher,'runtime_payload',return_value='cGF5bG9hZA=='),patch('sys.stdout',new_callable=io.StringIO):
                ledger=Path(tmp)/'budget.json'
                ledger.write_text(json.dumps({'budget_usd':1.0,'attempts':[{'status':'completed',
                    'api_lifecycle_cost_upper_bound_usd':previous,'maximum_reserved_compute_usd':previous}]}))
                argv=['--phase','archive-full','--hardware','cpu-basic','--source-revision','f'*40,
                    '--baseline-revision','b'*40,'--repo-id','fixture/data','--revision','full',
                    '--prefix','full','--ledger',str(ledger),'--submit']
                if not allowed:
                    with self.assertRaisesRegex(ValueError,'exceed USD 1'):launcher.main(argv)
                    api.run_uv_job.assert_not_called();api.create_branch.assert_not_called()
                    continue
                launcher.main(argv)
                self.assertEqual(api.run_uv_job.call_args.kwargs['timeout'],72*3600)
                self.assertEqual(api.create_branch.call_args.kwargs['revision'],'b'*40)
                self.assertIn('--full',api.run_uv_job.call_args.kwargs['script_args'])
                attempt=json.loads(ledger.read_text())['attempts'][-1]
                self.assertAlmostEqual(attempt['maximum_reserved_compute_usd'],.72311)

    def test_calibration_worker_refuses_local_numeric_access(self):
        from unittest.mock import patch
        worker=module('hf_cost_calibration.py')
        with patch.dict('os.environ',{},clear=True),self.assertRaises(SystemExit):worker.main([])

    def test_requested_basic_hardware_reaches_actual_job_submission(self):
        from unittest.mock import patch,Mock
        from types import SimpleNamespace
        import tempfile,json
        launcher=module('hf_trial_launch.py')
        api=Mock()
        api.whoami.return_value={'name':'fixture'}
        api.list_jobs_hardware.return_value=[SimpleNamespace(name='cpu-basic',unit_label='minute',unit_cost_micro_usd=167)]
        api.run_uv_job.return_value=SimpleNamespace(id='fixture-job',url='https://example.test/job',flavor='cpu-basic')
        api.inspect_job.return_value=SimpleNamespace(flavor='cpu-basic')
        hub=SimpleNamespace(HfApi=lambda:api,get_token=lambda:'fixture-not-a-secret')
        with tempfile.TemporaryDirectory() as tmp,patch.dict('sys.modules',{'huggingface_hub':hub}),patch.object(launcher,'runtime_payload',return_value=base64.b64encode(b'fixture').decode()),patch('sys.stdout',new_callable=io.StringIO):
            ledger=Path(tmp)/'budget.json'
            launcher.main(['--phase','migration-prep','--hardware','cpu-basic','--source-file','fixture.hdf5',
                '--source-revision','f'*40,'--repo-id','fixture/data','--revision','fixture','--prefix','fixture',
                '--batch-count','1','--ledger',str(ledger),'--submit'])
            self.assertEqual(api.run_uv_job.call_args.kwargs['flavor'],'cpu-basic')
            self.assertEqual(api.run_uv_job.call_args.kwargs['timeout'],1800)
            attempt=json.loads(ledger.read_text())['attempts'][0]
            self.assertEqual(attempt['hardware_unit_cost_micro_usd'],167)
            self.assertEqual(attempt['maximum_reserved_compute_usd'],.00668)
            self.assertEqual(attempt['observed_hardware'],'cpu-basic')
            api.cancel_job.assert_not_called()
            api.inspect_job.return_value=SimpleNamespace(flavor='cpu-upgrade')
            with self.assertRaisesRegex(RuntimeError,'Actual Job hardware differs'):
                launcher.main(['--phase','migration-prep','--hardware','cpu-basic','--source-file','fixture.hdf5',
                    '--source-revision','f'*40,'--repo-id','fixture/data','--revision','fixture','--prefix','fixture',
                    '--batch-count','1','--ledger',str(Path(tmp)/'mismatch.json'),'--submit'])
            api.cancel_job.assert_called_once_with(job_id='fixture-job')
            failed=json.loads((Path(tmp)/'mismatch.json').read_text())['attempts'][0]
            self.assertEqual(launcher.effective_reservation(failed),.00668)

    def test_basic_cpu_uses_captured_rate_and_rejects_price_increase(self):
        from types import SimpleNamespace
        from datetime import datetime,timedelta,timezone
        launcher=module('hf_trial_launch.py')
        hardware={'name':'cpu-basic','unit_label':'minute','unit_cost_micro_usd':167}
        self.assertEqual(launcher.reservation_usd(hardware,1800),.005177)
        hardware['unit_cost_micro_usd']=168
        with self.assertRaises(ValueError):launcher.reservation_usd(hardware,1800)
        start=datetime.now(timezone.utc)
        info=SimpleNamespace(status=SimpleNamespace(stage='COMPLETED'),flavor='cpu-basic',
            expose_urls=None,ssh_url=None,created_at=start,finished_at=start+timedelta(seconds=61))
        ledger={'attempts':[{'job_id':'fixture','hardware':'cpu-basic','hardware_unit_cost_micro_usd':167,
            'status':'submitted','maximum_reserved_compute_usd':.00668}]}
        launcher.settle_completed(SimpleNamespace(inspect_job=lambda **_:info),ledger)
        self.assertEqual(launcher.effective_reservation(ledger['attempts'][0]),.000501)

    def test_source_batch_bounds_fail_before_network_or_array_import(self):
        from unittest.mock import patch
        worker=module('hf_migrate.py')
        with patch.dict('os.environ',{'JOB_ID':'fixture'}):
            for start,count in ((-1,1),(9999,2),(0,1001),(0,0)):
                with self.assertRaises(ValueError):worker.extract_span({},start,count,Path('/unused'))

    def test_cole_hopf_constant_and_independent_heat_mode_limit(self):
        import numpy as np
        worker=module('hf_burgers_preflight.py')
        values,_=worker.cole_hopf_averages(np.full(1024,2.),.1,[.01,.1,1.])
        np.testing.assert_allclose(values,2.,rtol=0,atol=1e-10)
        errors=[]
        for n in (256,512,1024):
            edges=np.arange(n+1)/n;mu=.1;time=.1;amplitude=.2
            initial=-2*mu*n*np.diff(np.log(1+amplitude*np.cos(2*np.pi*edges)))
            actual,_=worker.cole_hopf_averages(initial,mu,[time])
            exact=-2*mu*n*np.diff(np.log(1+amplitude*np.exp(-mu*(2*np.pi)**2*time)*np.cos(2*np.pi*edges)))
            errors.append(float(abs(actual[0]-exact).max()))
        # Piecewise-constant initial interpretation converges toward the smooth
        # closed-form mode; it must not be declared identical at finite n.
        self.assertLess(errors[-1],1e-5)
        self.assertLess(errors[-1],errors[0]/10)

    def test_selection_is_unique_bounded_and_spans_file(self):
        worker = module('hf_source_probe.py')
        result = worker.sample_indices(10000, 10)
        self.assertEqual(len(result), 10)
        self.assertEqual((result[0], result[-1]), (0, 9999))
        self.assertEqual(worker.sample_indices(1, 1), [0])
        with self.assertRaises(ValueError):
            worker.sample_indices(4, 5)

    def test_only_known_time_mismatch_is_recorded(self):
        worker = module('hf_source_probe.py')
        self.assertEqual(worker.valid_time_count(202, 201)['unused_trailing_coordinates'], 1)
        with self.assertRaises(ValueError):
            worker.valid_time_count(200, 201)

    def test_reservation_includes_rounding_and_rejects_price_increase(self):
        launcher = module('hf_trial_launch.py')
        hardware = {'name': 'cpu-upgrade', 'unit_label': 'minute', 'unit_cost_micro_usd': 500}
        self.assertEqual(launcher.reservation_usd(hardware, 3600), .0305)
        hardware['unit_cost_micro_usd'] = 501
        with self.assertRaises(ValueError):
            launcher.reservation_usd(hardware, 3600)

    def test_worker_refuses_local_array_access(self):
        from unittest.mock import patch
        worker = module('hf_source_probe.py')
        with patch.dict('os.environ', {}, clear=True), self.assertRaises(SystemExit):
            worker.main(['--repo-id', 'a/b', '--revision', 'trial', '--prefix', 'trial'])

    def test_translation_against_rational_interval_intersections(self):
        import numpy as np
        worker = module('hf_transport_trial.py')
        initial = [Fraction(-2), Fraction(1, 3), Fraction(7, 2), Fraction(-1, 4), Fraction(3)]
        times = [Fraction(0), Fraction(1, 5), Fraction(17, 9)]
        speed = Fraction(7, 3)
        expected = []
        n = len(initial)
        for time in times:
            row = []
            for cell in range(n):
                left = Fraction(cell, n) - speed*time
                right = left + Fraction(1,n)
                integral = Fraction(0)
                for k in range((left*n).__floor__(), (right*n).__ceil__()):
                    overlap = min(right,Fraction(k+1,n))-max(left,Fraction(k,n))
                    if overlap>0:
                        integral += initial[k % n]*overlap
                row.append(float(n*integral))
            expected.append(row)
        actual = worker.translated_averages([float(x) for x in initial], [float(t) for t in times], float(speed))
        np.testing.assert_allclose(actual[...,0], expected, rtol=0, atol=1e-12)

    def test_runtime_payload_only_contains_inventoried_code_and_contract(self):
        launcher = module('hf_trial_launch.py')
        root = Path(__file__).resolve().parents[1]
        payload = launcher.runtime_payload(root)
        with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload))) as archive:
            names = archive.namelist()
            import json
            libraries = json.loads(archive.read('support/gmsh-system-packages.json'))
        self.assertIn('libxcursor1', libraries)
        self.assertIn('libglu1-mesa', libraries)
        self.assertTrue(any(n.endswith('/instruction.md') for n in names))
        self.assertTrue(any(n.endswith('/public-runtime.json') for n in names))
        self.assertFalse(any(n.endswith(('.h5','.hdf5','.msh','.env')) for n in names))
        self.assertFalse(any('__pycache__' in n or '/cases/' in n or '/samples/' in n for n in names))


if __name__ == '__main__':
    unittest.main()
