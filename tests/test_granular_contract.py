"""Granular DATA declarations, configurations and public assembly regressions."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import tomllib
import unittest
import h5py
import numpy as np
from granular_fixture import fixture
from caeoj_ext.granular import models
from caeoj.sdk import load_problem,write_result
from caeoj.validation import validate_input,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.assembly import runtime_materials

ROOT=Path(__file__).resolve().parents[1]


class GranularTests(unittest.TestCase):
    def changed(self,slug,mutate):
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,slug);mutate(m,path.parent);path.write_text(json.dumps(m),encoding='utf-8')
            return validate_input(path)

    def invalid(self,slug,mutate):
        r=self.changed(slug,mutate);self.assertFalse(r['valid'],r)

    def valid(self,slug,mutate):
        r=self.changed(slug,mutate);self.assertTrue(r['valid'],r)

    @staticmethod
    def edit(key,values):
        def change(m,b):
            with h5py.File(b/'input.h5','r+') as h:h[key][:]=values
        return change

    def test_all_models_real_files_sdk_and_public_bindings(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path)
                values={s['array']:np.zeros((2,len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                out=Path(tmp)/'result.h5';write_result(out,p,values)
                self.assertTrue(validate_output(path,out)['valid'])
                self.invalid(slug,lambda m,b:m['physics'].update(model='granular-unknown-v1'))
                self.invalid(slug,lambda m,b:m['conditions'][0].update(operator='guess'))
                self.invalid(slug,lambda m,b:m['fields'][next(iter(m['fields']))].update(unit='wrong'))
                self.invalid(slug,lambda m,b:m['locations'][next(iter(m['locations']))].update(kind='points'))

    def test_force_motion_scale_identity_and_drives(self):
        slug='granular-forced-motion'
        self.valid(slug,self.edit('payload_radius',.1)) # overlapping particles may pass in noninteracting motion.
        self.valid(slug,self.edit('payload_drag',0.))
        self.invalid(slug,self.edit('payload_mass',0.))
        self.invalid(slug,self.edit('payload_drag',-1.))
        self.invalid(slug,self.edit('drive_times',[0.,.004,.02]))
        self.invalid(slug,lambda m,b:m['fields']['given_external_force']['sampling'].update(time='previous'))
        # Reviewer counterexample: representable position increments must not require identical rounding at 5e17 m.
        def huge(m,b):
            with h5py.File(b/'input.h5','r+') as h:
                h['payload_mass'][:]=1e-12;h['payload_external_force'][:]=[1e4,0.,0.]
        self.invalid(slug,huge)
        def fast_drag(m,b):
            with h5py.File(b/'input.h5','r+') as h:
                h['payload_mass'][:]=1e-4;h['payload_drag'][:]=1e4
        self.invalid(slug,fast_drag) # dimensionless relaxation limit.

    def test_contact_overlap_and_distinct_centers(self):
        slug='granular-normal-contact'
        def position(xs):return self.edit('payload_initial_position',[[[x,.1,.1] for x in xs]])
        self.valid(slug,position([.1,.1198,.6]))
        self.valid(slug,position([.1,.12,.6])) # exact touching is allowed for trajectory-only observations.
        self.invalid(slug,position([.1,.119,.6]))
        self.invalid(slug,position([.1,.1,.6]))
        self.invalid(slug,lambda m,b:m['physics']['parameters']['normal_damping'].update(value=-1.))
        self.valid(slug,lambda m,b:m['physics']['parameters']['normal_damping'].update(value=0.))

    def test_regularized_friction_and_cohesion_difficulty_counterexamples(self):
        friction='granular-sliding-friction';cohesion='granular-cohesive-contact'
        self.valid(friction,lambda m,b:m['physics']['parameters']['friction'].update(value=0.))
        self.invalid(friction,lambda m,b:m['physics']['parameters']['slip_speed'].update(value=0.))
        self.invalid(friction,self.edit('payload_spin_drag',1e4))
        def stiff(m,b):
            p=m['physics']['parameters'];p['friction']['value']=2.;p['slip_speed']['value']=1e-8;p['stiffness']['value']=1e7
            with h5py.File(b/'input.h5','r+') as h:h['payload_mass'][:]=1.;h['payload_radius'][:]=.1
        self.invalid(friction,stiff)
        self.valid(cohesion,lambda m,b:m['physics']['parameters']['cohesive_force'].update(value=0.))
        def rapid(m,b):
            p=m['physics']['parameters'];p['cohesive_force']['value']=1000.;p['interaction_range']['value']=1e-8;p['stiffness']['value']=1e-4
            with h5py.File(b/'input.h5','r+') as h:h['payload_mass'][:]=1e-12
        self.invalid(cohesion,rapid)

    def test_periodic_nearest_image_margin_and_stress_tensor(self):
        slug='granular-periodic-assembly'
        self.valid(slug,self.edit('payload_initial_position',[[[.0099,.1,.1],[.9901,.1,.1],[.5,.5,.5]]]))
        self.invalid(slug,self.edit('payload_initial_position',[[[.005,.1,.1],[.995,.1,.1],[.5,.5,.5]]])) # overlap only across periodic boundary.
        self.invalid(slug,self.edit('payload_initial_position',[[[0.,.1,.1],[1.,.1,.1],[.5,.5,.5]]]))
        self.invalid(slug,self.edit('payload_initial_position',[[[.01,.1,.1],[.99,.1,.1],[.5,.5,.5]]])) # touching at observed t=0.
        self.invalid(slug,self.edit('payload_radius',.25))
        self.invalid(slug,lambda m,b:m['outputs']['observed_stress'].update(kind='components'))
        self.invalid(slug,lambda m,b:m['outputs']['observed_stress'].update(value_kind='average'))

    def test_population_bin_identity_and_aggregation_kernel(self):
        slug='granular-coagulation'
        self.valid(slug,self.edit('payload_collision_kernel',0.))
        self.valid(slug,self.edit('payload_initial_density',0.))
        self.invalid(slug,self.edit('bins_ids',[0,1,2]))
        self.invalid(slug,lambda m,b:m['physics']['parameters']['bin_count'].update(value=3.0))
        self.invalid(slug,self.edit('payload_collision_kernel',[[[[0.,1.,0.],[0.,0.,0.],[0.,0.,0.]]]]))
        self.invalid(slug,self.edit('payload_initial_density',1e9)) # initial volume fraction.
        self.invalid(slug,lambda m,b:m['fields']['given_collision_kernel'].update(components=['wrong']*9))

    def test_fragmentation_daughter_order_topology_and_mass_conservation(self):
        slug='granular-fragmentation'
        # Fractional expected counts are valid; this is not an integer event sampler.
        self.valid(slug,self.edit('payload_daughter_count',[[[[0.,2.,.5],[0.,0.,1.25],[0.,0.,0.]]]]))
        self.valid(slug,self.edit('payload_breakage_rate',0.))
        self.invalid(slug,self.edit('payload_daughter_count',[[[[0.,0.,0.],[2.,0.,0.],[1.,1.,0.]]]])) # transposed matrix.
        self.invalid(slug,self.edit('payload_daughter_count',[[[[0.,2.,0.],[0.,0.,1.],[0.,0.,0.]]]])) # volume loss.
        self.invalid(slug,self.edit('payload_breakage_rate',1.)) # nonzero monomer breakup.

    def test_actual_policies_thresholds_relative_terms_and_error_categories(self):
        expected={'position':(1e-9,0),'velocity':(1e-7,1e-4),'angular_velocity':(1e-6,1e-4),
                  'stress':(1e-5,.003),'kinetic_energy':(1e-12,.003),'coordination':(1e-9,0),
                  'size_density':(1e-3,.002),'number_density':(1e-3,.002)}
        for slug,cfg in models().items():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);policy=task_policy(task_directory(slug,ROOT),p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for name,s in m['outputs'].items():
                    want=(1e-10,.002 if cfg['population'] else 1e-6) if s['quantity']=='solid_fraction' else expected[s['quantity']]
                    self.assertEqual((bound['fields'][name]['atol'],bound['fields'][name]['rtol']),want)
                    ref[s['array']]=np.zeros((2,len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    rule=bound['fields'][name];tol=rule['atol'];actual=deepcopy(ref);actual[s['array']][:]=tol
                    self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(tol,np.inf)
                    self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],0)
                    if rule['rtol']:
                        baseline=10*tol/rule['rtol'];nonzero=deepcopy(ref);nonzero[s['array']][:]=baseline
                        tau=tol+rule['rtol']*baseline;edge=baseline+tau
                        if edge-baseline>tau:edge=np.nextafter(edge,-np.inf)
                        actual=deepcopy(nonzero);actual[s['array']][:]=edge
                        self.assertEqual(grade_arrays(p,actual,nonzero,policy=policy)['score'],1)
                        actual[s['array']].flat[0]=np.nextafter(edge,np.inf)
                        self.assertEqual(grade_arrays(p,actual,nonzero,policy=policy)['score'],0)
                bad=deepcopy(ref);del bad[next(iter(m['outputs'].values()))['array']]
                self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0)
                self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
                s=deepcopy(next(iter(m['outputs'].values())));s['array']='duplicate_quantity_answer';m['outputs']['another_name']=s
                path.write_text(json.dumps(m));p=load_problem(path)
                self.assertIn('another_name',resolve_policy(policy,p)['fields'])

    def test_resource_consumers_and_minimal_combined_closure(self):
        spec=importlib.util.spec_from_file_location('granular_prepare',ROOT/'src/utils/prepare_harbor.py')
        prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            task=task_directory(slug,ROOT);config=json.loads((task/'judge-config.json').read_text())
            merged=tomllib.loads(prepare.task_config(template,tomllib.loads((task/'harbor/task.toml').read_text()),judge_config=config,case_count=5))
            self.assertEqual(config['timeout_seconds'],cfg['timeout']);self.assertIsNone(config['max_output_bytes'])
            self.assertEqual(merged['environment']['cpus'],2);self.assertEqual(merged['environment']['memory_mb'],2048)
            self.assertEqual(merged['environment']['gpus'],0);self.assertEqual(merged['agent']['timeout_sec'],3600)
            self.assertEqual(merged['environment']['build_timeout_sec'],1200)
            self.assertEqual(merged['verifier']['timeout_sec'],max(1200,180+5*(cfg['timeout']+60)))
            self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate')
        public,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'granular.dynamics'})
        self.assertFalse(any(any(v in name for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in public))


if __name__=='__main__':unittest.main()
