"""Case-owned evaluation contracts, sparse observations and trusted extensions."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from caeoj.case_grading import direct_config, grade_case, prepare_case
from caeoj.grading_policy import resolve_policy
from caeoj.sdk import load_problem
from caeoj.storage import write_hdf5
from caeoj.validation import output_support, read_mesh
from caeoj_tools.author import load_author_module

ROOT = Path(__file__).resolve().parents[1]
RULE = dict(metric='pointwise', time='per_time', components='per_component', atol=1e-10, rtol=0)

class CaseGradingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        load_author_module('smoke-test', 'examples').make_cases(cls.root/'cases')

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.path = self.root/'cases/09-vector-2d/problem.json'
        self.problem = load_problem(self.path)
        p = self.problem
        self.arrays = {k: p.arrays[k].copy() for k in output_support(p) | {s['array'] for s in p.manifest['outputs'].values()}}
        spec = p.manifest['outputs']['velocity']; loc = p.manifest['locations'][spec['location']]
        mesh = read_mesh(p.path.parent/p.manifest['meshes'][loc['mesh']]['file'], geometry=True); ids = p.arrays[loc['ids']]
        xy = np.array([mesh['node_coordinates'][int(i)][:2] for i in ids])
        self.arrays['velocity'] = np.stack((1+2*xy[:,0]-3*xy[:,1], 4-xy[:,0]+xy[:,1]),axis=-1)[None,:,:]
        cells = np.array(sorted(mesh['elements'][2])[:2],dtype='int64')
        pts = np.array([np.mean([mesh['node_coordinates'][n][:2] for n in mesh['connectivity'][int(c)][1]],axis=0) for c in cells],dtype='float64')
        obsids=np.array([701,13],dtype='int64');times=np.array([0.],dtype='float64')
        write_hdf5(self.work/'observations.h5',dict(points=pts,ids=obsids,times=times,cells=cells))
        write_hdf5(self.work/'reference.h5',dict(values=(1+2*pts[:,0]-3*pts[:,1])[None,:,None],ids=obsids,times=times))
        self.config={'version':1,'checks':[{'id':'u-probes','evaluator':'field.sample_points',
          'source_output':'velocity','components':['x'],
          'observations':dict(file='observations.h5',points='points',ids='ids',times='times',cells='cells'),
          'reference':dict(file='reference.h5',array='values',ids='ids',times='times',unit='m/s'), 'rule':deepcopy(RULE)}]}
        self.save()
        self.output=self.work/'result.h5';write_hdf5(self.output,self.arrays)

    def save(self):
        self.grading=self.work/'grading.json';self.grading.write_text(json.dumps(self.config))

    def grade(self):return grade_case(self.path,self.output,self.grading)

    def test_sparse_linear_field_and_direct_cli(self):
        report=self.grade();self.assertEqual(report['score'],1,report)
        self.assertEqual(report['checks']['u-probes']['observation']['components'],['x'])
        # The unobserved component is still submitted but is not numerically compared.
        self.arrays['velocity'][:,:,1]=1234;write_hdf5(self.output,self.arrays)
        self.assertEqual(self.grade()['score'],1)
        self.assertEqual(set(report['assets']),{'grading.json','observations.h5','reference.h5'})

    def test_full_submission_is_required_before_sparse_comparison(self):
        del self.arrays['velocity'];write_hdf5(self.output,self.arrays)
        self.assertEqual(self.grade()['score'],0)
        self.assertEqual(self.grade()['status'],'invalid_output')

    def test_wrong_answer_does_not_become_infrastructure_error(self):
        self.arrays['velocity'][:,:,0]+=.01;write_hdf5(self.output,self.arrays)
        self.assertEqual(self.grade()['status'],'wrong_answer')

    def test_bad_reference_precedes_bad_candidate(self):
        (self.work/'reference.h5').unlink();self.output.write_bytes(b'bad')
        self.assertIsNone(self.grade()['score'])

    def test_components_units_times_and_unknown_keys_fail_preflight(self):
        for field,value in [('components',['z']),('components',['x','x']),('components',['y','x']),('source_output','absent'),('evaluator','os:system'),('unexpected',1)]:
            with self.subTest(field=field,value=value):
                cfg=deepcopy(self.config);cfg['checks'][0][field]=value
                self.grading.write_text(json.dumps(cfg));self.assertIsNone(self.grade()['score'])
        self.save();self.config['checks'][0]['reference']['unit']='Pa';self.save();self.assertIsNone(self.grade()['score'])

    def test_domain_cell_and_time_mapping_are_checked(self):
        from caeoj.validation import read_hdf5
        original=read_hdf5(self.work/'observations.h5')
        for key,value in [('points',np.full((2,2),100.)),('cells',np.array([-1,-2],dtype='int64')),('times',np.array([1.],dtype='float64'))]:
            data=deepcopy(original);data[key]=value;write_hdf5(self.work/'observations.h5',data)
            self.assertIsNone(self.grade()['score'])
        write_hdf5(self.work/'observations.h5',original)

    def test_no_unbound_arrays_and_reference_axes_match(self):
        from caeoj.validation import read_hdf5
        values=read_hdf5(self.work/'reference.h5');values['ids']=values['ids'][::-1]
        write_hdf5(self.work/'reference.h5',values);self.assertIsNone(self.grade()['score'])
        values['ids']=values['ids'][::-1];values['extra']=np.ones(1)
        write_hdf5(self.work/'reference.h5',values);self.assertIsNone(self.grade()['score'])

    def test_unsafe_asset_and_duplicate_check_are_rejected(self):
        self.config['checks'][0]['reference']['file']='../reference.h5';self.save();self.assertIsNone(self.grade()['score'])
        self.config['checks'][0]['reference']['file']='reference.h5';self.config['checks']*=2;self.save();self.assertIsNone(self.grade()['score'])

    def test_assets_cannot_change_after_preflight(self):
        prepared=prepare_case(self.problem,self.grading)
        self.grading.write_text(self.grading.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'changed after preflight'): prepared.evaluate(self.arrays)

    def test_direct_outputs_accepts_equal_and_rejects_larger_errors(self):
        policy={'version':2,'default':deepcopy(RULE)}
        write_hdf5(self.work/'reference.h5',self.arrays)
        self.config=direct_config(policy);self.save()
        for delta,score in [(0.,1),(1e-8,0)]:
            result=deepcopy(self.arrays);result['velocity']+=delta
            write_hdf5(self.output,result)
            self.assertEqual(self.grade()['score'],score)

    def continuous(self, offset=0., floor=1e-6):
        rule=dict(metric='nrmse',time='per_time',components='per_component',limit=.05,
                  scale_floor=floor,reference_offset=offset)
        self.config=direct_config({'version':2,'default':rule})
        self.config['scoring']=dict(metric='max_nrmse',full_credit=.05,zero_credit=.10)
        write_hdf5(self.work/'reference.h5',self.arrays)
        self.save()

    def test_continuous_boundaries_and_partial_scores(self):
        self.arrays['velocity'][:]=0.
        self.continuous(floor=1.)
        for error,score,status in [(0.,1.,'accepted'),(.04,1.,'accepted'),(.05,1.,'accepted'),
                                   (.07,.6,'partial_credit'),(.075,.5,'partial_credit'),
                                   (.1,0.,'wrong_answer'),(.2,0.,'wrong_answer')]:
            with self.subTest(error=error):
                candidate=deepcopy(self.arrays);candidate['velocity']+=error
                write_hdf5(self.output,candidate);report=self.grade()
                self.assertAlmostEqual(report['score'],score,places=13)
                self.assertEqual(report['status'],status)
                self.assertAlmostEqual(report['total_nrmse'],error,places=13)

    def test_partial_cli_reports_score_and_non_full_exit_code(self):
        import contextlib,io
        from caeoj.cli import main
        self.arrays['velocity'][:]=0.;self.continuous(floor=1.)
        candidate=deepcopy(self.arrays);candidate['velocity']+=.07
        write_hdf5(self.output,candidate)
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            code=main(['grade','--input',str(self.path),'--output',str(self.output),'--grading',str(self.grading)])
        self.assertEqual(code,1)
        report=json.loads(output.getvalue());self.assertEqual(report['status'],'partial_credit')
        self.assertAlmostEqual(report['score'],.6)

    def test_continuous_worst_component_and_scale_floor(self):
        self.arrays['velocity'][:]=0.
        self.continuous(floor=2.)
        candidate=deepcopy(self.arrays);candidate['velocity'][:,:,0]=.04
        candidate['velocity'][:,:,1]=.14
        write_hdf5(self.output,candidate);report=self.grade()
        self.assertAlmostEqual(report['total_nrmse'],.07)
        self.assertAlmostEqual(report['score'],.6)

    def test_continuous_offset_does_not_center_error(self):
        self.arrays['velocity'][:]=100010.
        self.continuous(offset=100000.)
        candidate=deepcopy(self.arrays);candidate['velocity']+=.7
        write_hdf5(self.output,candidate);report=self.grade()
        self.assertAlmostEqual(report['total_nrmse'],.07,places=11)
        self.assertAlmostEqual(report['score'],.6,places=10)

    def test_continuous_invalid_and_extreme_outputs_are_zero(self):
        self.arrays['velocity'][:]=0.
        self.continuous(floor=1e-300)
        for value in (float('nan'),float('inf'),1e308):
            candidate=deepcopy(self.arrays);candidate['velocity'][:]=value
            write_hdf5(self.output,candidate)
            report=self.grade();self.assertEqual(report['score'],0,report)
            self.assertNotEqual(report['status'],'evaluation_error')

    def test_nrmse_weights_each_time_and_component_independently(self):
        from caeoj.grading_metrics import evaluate_observation
        rule=dict(metric='nrmse',time='per_time',components='per_component',
                  scale_floor=1.,limit=.05,weight_field='w')
        expected=np.zeros((2,2,2));actual=np.zeros_like(expected)
        actual[1,0,1]=.14
        record=evaluate_observation(actual,expected,rule,ids=np.array([2,9]),
                 times=np.array([0.,1.]),weights={'w':np.array([1.,3.])})
        self.assertEqual(len(record['groups']),4)
        self.assertEqual([g['value'] for g in record['groups'][:3]],[0.,0.,0.])
        self.assertAlmostEqual(record['groups'][3]['value'],.07)
        self.assertFalse(record['passed'])

    def test_continuous_integer_and_boolean_guards_remain_exact(self):
        problem=load_problem(self.root/'cases/08-scalars-and-dtypes/problem.json')
        keys=output_support(problem)|{s['array'] for s in problem.manifest['outputs'].values()}
        reference={key:problem.arrays[key].copy() for key in keys}
        write_hdf5(self.work/'reference.h5',reference)
        rule=dict(metric='nrmse',time='per_time',components='per_component',limit=.05,scale_floor=1.)
        cfg=direct_config({'version':2,'default':rule})
        cfg['scoring']=dict(metric='max_nrmse',full_credit=.05,zero_credit=.10)
        self.grading.write_text(json.dumps(cfg));plan=prepare_case(problem,self.grading)
        self.assertEqual(plan.evaluate(reference)['score'],1.)
        for key in ('mask','region_label'):
            candidate=deepcopy(reference)
            candidate[key][0,0,0]=not candidate[key][0,0,0] if key=='mask' else candidate[key][0,0,0]+1
            self.assertEqual(plan.evaluate(candidate)['score'],0.)

    def test_continuous_bad_policy_is_infrastructure_error(self):
        self.continuous()
        for mutate in ('threshold','metric','pool','or'):
            cfg=deepcopy(self.config)
            if mutate=='threshold':cfg['scoring']['zero_credit']=.01
            if mutate=='metric':cfg['checks'][0]['policy']['default']=deepcopy(RULE)
            if mutate=='pool':cfg['checks'][0]['policy']['default']['time']='pooled'
            if mutate=='or':cfg['checks'][0]['policy']['default']={'any':[cfg['checks'][0]['policy']['default']]}
            self.grading.write_text(json.dumps(cfg))
            self.assertIsNone(self.grade()['score'])

    def test_unknown_provider_is_not_imported_from_config(self):
        self.config['checks'][0]['evaluator']='arbitrary.module:prepare';self.save()
        with patch('caeoj.runtime.load_symbol') as load:
            self.assertIsNone(self.grade()['score']);load.assert_not_called()

    def test_no_reference_derived_input_and_weight_fallback(self):
        self.config['checks'][0]['rule']['weight_field']='missing';self.save()
        self.assertIsNone(self.grade()['score'])

    def test_input_assets_are_frozen_and_affect_evaluation_identity(self):
        import shutil
        copied=self.work/'input';shutil.copytree(self.path.parent,copied)
        path=copied/'problem.json';problem=load_problem(path)
        prepared=prepare_case(problem,self.grading)
        path.write_text(path.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'input changed'): prepared.evaluate(self.arrays)
        changed=prepare_case(load_problem(path),self.grading)
        self.assertNotEqual(prepared.evidence['evaluation_sha256'],changed.evidence['evaluation_sha256'])

    def test_trusted_provider_can_register_an_evaluator(self):
        from caeoj.case_grading import _direct
        policy={'version':2,'default':deepcopy(RULE)}
        write_hdf5(self.work/'reference.h5',self.arrays)
        self.config=direct_config(policy);self.config['checks'][0]['evaluator']='test.direct';self.save()
        extension={'version':1,'evaluators':{'test.direct':'trusted.module:prepare'},'files':[]}
        with patch('caeoj.runtime.selected',return_value=['trusted']), patch('caeoj.runtime.descriptor',return_value={'extensions':{'trusted':extension}}), patch('caeoj.runtime.load_symbol',return_value=_direct):
            prepared=prepare_case(self.problem,self.grading)
            self.assertEqual(prepared.evaluate(self.arrays)['score'],1)

    def test_sparse_reference_roundtrips_through_pool_and_public_package(self):
        import shutil, importlib.util
        from caeoj_tools import data_pool as pool
        source=self.work/'source'
        shutil.copytree(self.path.parent,source/'cases/a')
        reference=source/'reference/a';reference.mkdir(parents=True)
        for name in ('grading.json','reference.h5','observations.h5'):shutil.copyfile(self.work/name,reference/name)
        shutil.copytree(source/'cases/a',source/'samples/01/input')
        shutil.copytree(reference,source/'samples/01/reference')
        write_hdf5(source/'samples/01/output/result.h5',self.arrays)
        value={'schema_version':4,'task_id':'caeoj-000123','repository':{'repo_id':'test/cases','repo_type':'dataset','path':'qbank/test/sec/smoke-test'}}
        pool.pack(source,self.work/'bundle',value)
        choice=pool.manifest(self.work/'bundle/selection.json')
        target=self.work/'assembled';target.mkdir();pool.write_json(target/'data-manifest.json',choice)
        pool.assemble(target,choice,pool.LocalStore(self.work/'bundle/repository'),cases=[])
        self.assertTrue(pool.verify(target,strict=True,samples_only=True)['valid'])
        self.assertEqual(grade_case(target/'samples/01/input/problem.json',target/'samples/01/output/result.h5',target/'samples/01/reference/grading.json')['score'],1)
        self.assertNotEqual((target/'samples/01/output/result.h5').read_bytes(),(target/'samples/01/reference/reference.h5').read_bytes())
        # Publish and run exactly the assembled public closure, without developer imports.
        from caeoj_tools.assembly import runtime_materials
        canonical=ROOT/'qbank/00-basic-tests/0.1-io/smoke-test'
        files,_=runtime_materials({'smoke-test':canonical},ROOT)
        project=self.work/'project'
        for name,data in files.items():
            path=project/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        for name in ('LICENSE','docs/CONTRACT.md','docs/GRADING.md'):
            path=project/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
        task=project/canonical.relative_to(ROOT);task.mkdir(parents=True,exist_ok=True)
        for name in ('instruction.md','DATA.md'):shutil.copyfile(canonical/name,task/name)
        shutil.copytree(target/'samples',task/'samples')
        spec=importlib.util.spec_from_file_location('sparse_publisher',ROOT/'src/utils/publish_dist.py')
        publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)
        package,_=publisher.collect_materials('smoke-test',project)
        self.assertIn('qbank/00-basic-tests/0.1-io/smoke-test/samples/01/reference/observations.h5',package)
        from caeoj_tools.assembly import validate_public_runtime
        validate_public_runtime(package)
