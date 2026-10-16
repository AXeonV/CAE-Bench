"""Declaration boundaries chosen against final DATA; no numerical solver claims."""
from copy import deepcopy
import json
import importlib.util
import sys
import tomllib
from pathlib import Path
import tempfile
import unittest
import h5py
import numpy as np
from multibody_fixture import fixture
from caeoj_ext.multibody import models
from qbank.maintenance.authoring.build_multibody import M as AUTHOR_MODELS
from caeoj.sdk import load_problem,write_result
from caeoj.validation import check_problem,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.grading_policy import author_policy
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class MultibodyTests(unittest.TestCase):
    def mutate(self,slug,change):
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,slug);change(m,path);path.write_text(json.dumps(m));_,report=check_problem(path);return report["errors"]
    def test_all_models_roundtrip_and_real_quantity_policies(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);problem=load_problem(path)
                ref={k:problem.arrays[k].copy() for k in output_support(problem)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((len(problem.arrays[m['time_axes'][s['time_axis']]]),len(problem.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                write_result(Path(tmp)/'result.h5',problem,{s['array']:ref[s['array']] for s in m['outputs'].values()})
                self.assertTrue(validate_output(path,Path(tmp)/'result.h5')['valid'])
                policy=author_policy(task_directory(slug,ROOT),problem);bound=resolve_policy(policy,problem)
                self.assertEqual(grade_arrays(problem,deepcopy(ref),ref,policy=policy)['score'],1)
                for name,s in m['outputs'].items():
                    actual=deepcopy(ref);tol=bound['fields'][name]['atol'];actual[s['array']][:]=tol
                    self.assertEqual(grade_arrays(problem,actual,ref,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(tol,np.inf)
                    self.assertEqual(grade_arrays(problem,actual,ref,policy=policy)['score'],0)
    def test_hand_chosen_invalid_declarations(self):
        def data(op,key,val):
            return lambda m,p:next(c for c in m['conditions'] if c['operator']==op)['data'].__setitem__(key,val)
        mutations=[('normal-contact',data('contact','a',dict(value=0,unit='1'))),('normal-contact',data('contact','stiffness',dict(value=0.,unit='N/m'))),('regularized-friction',data('contact','slip_speed',dict(value=0.,unit='m/s'))),('elastic-connectors',data('spring','rest_length',dict(value=0.,unit='m'))),('planar-kinematics',data('angle_drive','body',dict(value=3.,unit='1'))),('frictional-impact',lambda m,p:m['physics']['parameters']['friction'].update(value=-.1)),('modal-flexible',lambda m,p:m['physics']['parameters']['mode_count'].update(value=True)),('normal-impact',lambda m,p:m['physics']['parameters']['restitution'].update(value=1.1))]
        for slug,mutate in mutations:
            with self.subTest(slug=slug):self.assertTrue(self.mutate(slug,mutate))
    def test_nontrivial_array_boundaries_from_DATA(self):
        def edit(key,value):
            def mutate(m,path):
                with h5py.File(path.parent/'input.h5','r+') as h:h['payload_'+key][:]=value
            return mutate
        variants=[('spatial-free-rigid',edit('body_quaternion0',[0.,0.,0.,0.])),('spatial-free-rigid',edit('body_inertia',np.diag([1.,1.,4.]))),('translating-flexible',edit('modal_system_coupling',[[2.,0.],[0.,2.]])),('modal-flexible',edit('modal_system_stiffness',[[1.,2.],[2.,1.]])),('modal-flexible',edit('modal_system_damping',[[0.,0.],[0.,-1.]])),('normal-impact',edit('body_velocity0',[[0.,0.],[1.,0.]])),('normal-impact',edit('body_position0',[[0.,0.],[3.,0.]]))]
        for slug,mutate in variants:
            with self.subTest(slug=slug):self.assertTrue(self.mutate(slug,mutate))
        # Legitimate dense coupled matrices and negative initial quaternion sign are allowed.
        for slug,mutate in [('modal-flexible',edit('modal_system_mass_matrix',[[2.,.5],[.5,1.]])),('spatial-free-rigid',edit('body_quaternion0',[-1.,0.,0.,0.]))]:
            self.assertFalse(self.mutate(slug,mutate))
    def test_reject_missing_coverage_and_unrelated_objects(self):
        self.assertTrue(self.mutate('planar-inverse-dynamics',lambda m,p:m['outputs'].pop('observation_drive_torque1')))
        self.assertTrue(self.mutate('normal-contact',lambda m,p:m['conditions'].append(deepcopy(m['conditions'][-1]))))
        self.assertTrue(self.mutate('planar-multibody',lambda m,p:m['fields']['loads_force'].update(quantity='velocity')))
        self.assertTrue(self.mutate('planar-multibody',lambda m,p:m['fields']['loads_force']['sampling'].update(time='previous')))
    def test_actual_resource_merge_and_error_classification(self):
        def module(name,path):
            spec=importlib.util.spec_from_file_location(name,ROOT/path);mod=importlib.util.module_from_spec(spec)
            sys.path.insert(0,str(ROOT/'src/utils'))
            try:spec.loader.exec_module(mod)
            finally:sys.path.pop(0)
            return mod
        prepare=module('multibody_prepare','src/utils/prepare_harbor.py')
        judge=module('multibody_judge','src/utils/harbor/tests/judge.py')
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            task=task_directory(slug,ROOT);config=json.loads((task/'judge-config.json').read_text());override=tomllib.loads((task/'harbor/task.toml').read_text())
            merged=tomllib.loads(prepare.task_config(template,override,judge_config=config,case_count=3))
            self.assertEqual((task/'harbor/requirements.txt').read_text().strip(),'scipy==1.18.1')
            self.assertEqual(config['timeout_seconds'],AUTHOR_MODELS[slug]['timeout'])
            self.assertEqual(merged['agent']['timeout_sec'],3600.)
            self.assertEqual(merged['environment']['build_timeout_sec'],1800.)
            self.assertEqual(merged['environment']['cpus'],4)
            self.assertEqual(merged['environment']['memory_mb'],8192)
            self.assertEqual(merged['environment']['gpus'],0)
            self.assertEqual(merged['verifier']['network_mode'],'no-network')
            self.assertEqual(merged['verifier']['environment_mode'],'separate')
            self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(AUTHOR_MODELS[slug]['timeout']+120)))
            self.assertIsNone(judge.output_limit(config))
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,'normal-impact');problem=load_problem(path)
            ref={k:problem.arrays[k].copy() for k in output_support(problem)}
            for s in m['outputs'].values():ref[s['array']]=np.zeros((1,len(problem.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
            policy=author_policy(task_directory('normal-impact',ROOT),problem)
            bad=deepcopy(ref);bad.pop('answer_impulse0')
            self.assertEqual(grade_arrays(problem,bad,ref,policy=policy)['score'],0)
            result=grade_arrays(problem,ref,bad,policy=policy)
            self.assertIsNone(result['score'])

    def test_public_closure(self):
        tasks={slug:task_directory(slug,ROOT) for slug in models()};files,runtime=runtime_materials(tasks,ROOT)
        self.assertEqual(set(runtime['extensions']),{'multibody.mechanics'})
        self.assertEqual(set(runtime['tasks']),set(tasks))
        self.assertIn('src/caeoj_ext/multibody/models.json',files)
        self.assertFalse(any(any(x in p for x in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for p in files))

if __name__=='__main__':unittest.main()
