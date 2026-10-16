"""Public semiconductor declaration, scoring, resource and assembly evidence."""
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
from semiconductor_fixture import fixture
from caeoj_ext.semiconductor import models
from caeoj.sdk import load_problem, write_result
from caeoj.validation import validate_input, validate_output, output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.assembly import runtime_materials

ROOT=Path(__file__).resolve().parents[1]


class SemiconductorTests(unittest.TestCase):
    def changed(self, slug, mutate):
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,slug)
            mutate(m,path.parent)
            path.write_text(json.dumps(m),encoding='utf-8')
            return validate_input(path)

    def invalid(self, slug, mutate):
        result=self.changed(slug,mutate)
        self.assertFalse(result['valid'],result)

    def valid(self, slug, mutate):
        result=self.changed(slug,mutate)
        self.assertTrue(result['valid'],result)

    @staticmethod
    def edit(key,value):
        def change(m,base):
            with h5py.File(base/'input.h5','r+') as h:h[key][:]=value
        return change

    def test_every_task_real_io_sdk_and_binding(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug)
                p=load_problem(path)
                fields={s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                result=Path(tmp)/'output.h5'
                write_result(result,p,fields)
                self.assertTrue(validate_output(path,result)['valid'])
                # Tooling fixtures verify array contracts, not physical solutions.
                self.assertEqual(p.manifest['task'],slug)
                self.invalid(slug,lambda m,b:m['physics'].update(model='semiconductor-unknown-v1'))
                self.invalid(slug,lambda m,b:m.update(spatial_dimension=2))
                self.invalid(slug,lambda m,b:m['conditions'][0].update(operator='implicit_model'))
                self.invalid(slug,lambda m,b:m['fields'][next(iter(m['fields']))].update(unit='wrong'))

    def test_profile_and_contacts_identity_and_receiver_sampling(self):
        slug='semiconductor-equilibrium'
        self.valid(slug,lambda m,b:None) # unsorted/repeated receiver coordinates and sparse IDs.
        self.invalid(slug,self.edit('profile_x',[[0.],[.5e-6],[.4e-6]]))
        self.invalid(slug,self.edit('contacts_x',[[1e-6],[0.]]))
        self.invalid(slug,self.edit('receivers_x',[[0.],[.2e-6],[.3e-6]]))
        self.invalid(slug,lambda m,b:m['fields']['input_doping']['sampling'].update(space='uniform'))
        self.invalid(slug,lambda m,b:m['physics']['parameters']['temperature'].update(value=True))
        self.invalid(slug,lambda m,b:m['time_axes'].update(initial='marker'))

    def test_transient_zero_time_counterexample_and_compatibility(self):
        slug='semiconductor-drift-transient'
        self.invalid(slug,self.edit('observation_times',[0.,1e-6]))
        self.invalid(slug,self.edit('drive_times',[1e-9,1e-7,1e-6]))
        self.invalid(slug,self.edit('drive_times',[0.,1e-7,2e-6]))
        self.invalid(slug,self.edit('payload_initial_electron',[[[2e16],[1e16],[1e16]]]))
        self.invalid(slug,lambda m,b:m['fields']['input_contact_potential']['sampling'].update(time='previous'))
        self.valid(slug,self.edit('payload_doping',[[[-1e18],[0.],[1e18]]]))

    def test_kinetics_and_minority_bounds(self):
        trap='semiconductor-trap-kinetics'
        self.valid(trap,self.edit('payload_initial_occupation',0.))
        self.valid(trap,self.edit('payload_initial_occupation',1.))
        self.invalid(trap,self.edit('payload_initial_occupation',1.01))
        self.invalid(trap,self.edit('payload_initial_hole',-1.))
        self.valid(trap,self.edit('observation_times',[0.,1e-6]))
        bulk='semiconductor-bulk-recombination'
        self.valid(bulk,lambda m,b:m['physics']['parameters']['radiative'].update(value=0.))
        self.invalid(bulk,lambda m,b:m['physics']['parameters']['auger_n'].update(value=-1.))
        minor='semiconductor-minority-diffusion'
        self.valid(minor,self.edit('payload_surface_velocity',0.))
        self.invalid(minor,self.edit('payload_surface_velocity',-1.))
        self.invalid(minor,self.edit('payload_initial_excess',1.01e19))
        self.invalid(minor,self.edit('payload_generation',1.01e25))
        self.invalid(minor,self.edit('observation_times',[0.,1e-6]))

    def test_ballistic_and_quantum_nondefault_branches(self):
        slug='semiconductor-landauer'
        self.valid(slug,self.edit('payload_transmission',0.))
        self.valid(slug,lambda m,b:m['physics']['parameters']['degeneracy'].update(value=1))
        self.invalid(slug,lambda m,b:m['physics']['parameters']['degeneracy'].update(value=2.0))
        self.invalid(slug,self.edit('payload_energy',[[[-2e-20],[2e-20],[0.]]]))
        self.invalid(slug,self.edit('payload_transmission',-1.))
        quantum='semiconductor-effective-mass'
        self.valid(quantum,self.edit('receivers_x',[[2e-9],[1e-9],[2e-9]])) # interface and repeated points.
        self.invalid(quantum,self.edit('payload_mass',0.))
        self.invalid(quantum,self.edit('receivers_x',[[0.],[1e-9],[2e-9]]))
        self.invalid(quantum,self.edit('modes_ids',[7,18]))
        self.invalid(quantum,lambda m,b:m['outputs']['observation_wavefunction'].update(components=['real','imag']))
        def single(m,b):
            m['physics']['parameters']['mode_count']['value']=1
            m['outputs']['observation_wavefunction'].update(component_shape=[1],components=['c1'])
            with h5py.File(b/'input.h5','r+') as h:
                del h['modes_ids'];h['modes_ids']=np.array([0],dtype='int64')
        self.valid(quantum,single) # m=1 remains components, never scalar.

    def test_policy_boundaries_errors_renamed_and_duplicate_outputs(self):
        # Independent expectations taken from final instructions, not config data.
        expected={'potential':(2e-5,.002),'electron_density':(1e10,.005),'hole_density':(1e10,.005),
                  'electric_field':(1.,.005),'electron_current':(.01,.005),'hole_current':(.01,.005),
                  'occupation':(1e-6,.002),'excess_density':(1e9,.005),'particle_flux':(1e10,.005),
                  'net_recombination':(1e14,.005),'electric_current':(1e-12,.002),'heat_left':(1e-14,.002),
                  'eigenenergy':(1e-25,.0001),'wavefunction':(.01,.003)}
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug)
                if slug=='semiconductor-bulk-recombination':
                    expected['electron_density']=(1e10,.003);expected['hole_density']=(1e10,.003)
                elif slug=='semiconductor-trap-kinetics':
                    expected['electron_density']=(1e10,.003);expected['hole_density']=(1e10,.003)
                p=load_problem(path);policy=task_policy(task_directory(slug,ROOT),p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for name,s in m['outputs'].items():
                    rule=bound['fields'][name]
                    self.assertEqual((rule['atol'],rule['rtol']),expected[s['quantity']])
                    ref[s['array']]=np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    tol=bound['fields'][name]['atol'];actual=deepcopy(ref);actual[s['array']][:]=tol
                    self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(tol,np.inf)
                    self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],0)
                    # Exercise the relative term independently of zero-reference tests.
                    rtol=bound['fields'][name]['rtol'];baseline=10*tol/rtol
                    nonzero=deepcopy(ref);nonzero[s['array']][:]=baseline
                    actual=deepcopy(nonzero);tau=tol+rtol*baseline;edge=baseline+tau
                    if edge-baseline>tau:edge=np.nextafter(edge,-np.inf)
                    actual[s['array']][:]=edge
                    self.assertEqual(grade_arrays(p,actual,nonzero,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(edge,np.inf)
                    self.assertEqual(grade_arrays(p,actual,nonzero,policy=policy)['score'],0)
                bad=deepcopy(ref);del bad[next(iter(m['outputs'].values()))['array']]
                self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0)
                self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
                # Repeated quantity with distinct logical/array names is public and must bind.
                s=deepcopy(next(iter(m['outputs'].values())));s['array']='another_answer'
                m['outputs']['another_logical_name']=s;path.write_text(json.dumps(m))
                p=load_problem(path);self.assertIn('another_logical_name',resolve_policy(policy,p)['fields'])

    def test_resource_consumers_and_public_assembly(self):
        spec=importlib.util.spec_from_file_location('semiconductor_prepare',ROOT/'src/utils/prepare_harbor.py')
        prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            task=task_directory(slug,ROOT);config=json.loads((task/'judge-config.json').read_text())
            merged=tomllib.loads(prepare.task_config(template,tomllib.loads((task/'harbor/task.toml').read_text()),judge_config=config,case_count=4))
            self.assertEqual(config['timeout_seconds'],cfg['timeout']);self.assertIsNone(config['max_output_bytes'])
            self.assertEqual(merged['environment']['cpus'],2);self.assertEqual(merged['environment']['memory_mb'],2048)
            self.assertEqual(merged['environment']['gpus'],0);self.assertEqual(merged['environment']['os'],'linux')
            self.assertEqual(merged['agent']['timeout_sec'],3600);self.assertEqual(merged['environment']['build_timeout_sec'],1200)
            self.assertEqual(merged['verifier']['timeout_sec'],max(1200,180+4*(cfg['timeout']+60)))
            self.assertEqual(merged['verifier']['environment_mode'],'separate');self.assertEqual(merged['verifier']['network_mode'],'no-network')
        public,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'semiconductor.transport'})
        self.assertFalse(any(any(v in name for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in public))


if __name__=='__main__':unittest.main()
