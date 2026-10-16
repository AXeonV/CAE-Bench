"""Declaration, grading and assembly checks, not numerical physics validation."""
from copy import deepcopy
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import tomllib
import unittest
import h5py
import numpy as np
from electrochemistry_fixture import fixture
from caeoj_ext.electrochemistry import models
from caeoj.sdk import load_problem,write_result
from caeoj.validation import validate_input,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.grading_policy import author_policy
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class ElectrochemistryTests(unittest.TestCase):
    def changed(self,slug,mutate):
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,slug);mutate(m,path.parent);path.write_text(json.dumps(m));return validate_input(path)
    def valid(self,slug,mutate):
        report=self.changed(slug,mutate);self.assertTrue(report['valid'],report)
    def invalid(self,slug,mutate):
        report=self.changed(slug,mutate);self.assertFalse(report['valid'],report);return report
    @staticmethod
    def edit(key,value):
        def change(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['payload_'+key][:]=value
        return change
    def test_all_models_sdk_roundtrip(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path)
                nt=3 if models()[slug]['dynamic'] else 1
                v={s['array']:np.zeros((nt,len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                out=Path(tmp)/'protocol-output.h5';write_result(out,p,v)
                self.assertTrue(validate_output(path,out)['valid'])
    def test_ionic_exact_neutrality_and_drive_compatibility(self):
        for slug in ('ionic-equilibrium','blocking-pnp'):
            key='ions_reservoir' if slug=='ionic-equilibrium' else 'initial_value'
            self.invalid(slug,self.edit('ions_charge',[1.,1.]))
            self.invalid(slug,self.edit('ions_charge',[1.,-1.5]))
            self.invalid(slug,self.edit(key,[1.,1.+2**-40]))
            def exact_multivalent(m,b):
                self.edit('ions_charge',[2.,-1.])(m,b);self.edit(key,[1.,2.])(m,b)
            self.valid(slug,exact_multivalent)
            self.invalid(slug,self.edit('left_value',1e6))
        self.invalid('blocking-pnp',self.edit('left_value',.01))
        def ramp(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['payload_left_value'][1:]=.01
        self.valid('blocking-pnp',ramp)
        self.invalid('blocking-pnp',self.edit('ions_diffusivity',0.))
        def endpoint(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['probes_coordinates'][:]=[[0.],[1.]]
        self.valid('blocking-pnp',endpoint)
        self.invalid('electrode-diffusion',endpoint)
    def test_interface_inventory_area_units_and_frequency(self):
        self.valid('capacitive-redox',self.edit('initial_value',[0.,1.]))
        self.invalid('capacitive-redox',self.edit('initial_value',0.))
        self.invalid('redox-impedance',self.edit('initial_value',[0.,1.]))
        for slug in ('capacitive-redox','redox-impedance'):
            self.invalid(slug,self.edit('material_capacitance',0.))
            self.invalid(slug,self.edit('material_alpha',1.))
            self.invalid(slug,self.edit('material_electrons',1.5))
            self.invalid(slug,lambda m,b:m['fields']['material_capacitance'].update(unit='F'))
        self.invalid('redox-impedance',self.edit('frequency_value',0.))
        self.invalid('redox-impedance',lambda m,b:m['fields']['frequency_value'].update(unit='Hz'))
        self.valid('mixed-potential',lambda m,b:m['physics']['parameters']['applied_current'].update(value=-1.))
        self.invalid('mixed-potential',self.edit('channels_area',0.))
        self.invalid('mixed-potential',self.edit('channels_reduced_activity',0.))
        self.valid('electrode-diffusion',self.edit('potential_value',.1))
    def test_battery_radial_identity_and_fuel_cell_branches(self):
        self.invalid('particle-battery',self.edit('initial_value',0.))
        self.valid('particle-battery',self.edit('initial_value',1e-6))
        self.invalid('particle-battery',self.edit('current_value',1.))
        self.invalid('particle-battery',self.edit('particles_solid_fraction',1.01))
        def ids(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['electrodes_ids'][:]=[2,3]
        self.invalid('particle-battery',ids)
        def radius(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['positive_probes_coordinates'][-1]=2e-5
        self.invalid('particle-battery',radius)
        self.invalid('particle-battery',lambda m,b:m['fields']['particles_ocp'].update(components=['b0','b1','b2','b3']))
        self.invalid('fuel-cell-energy',self.edit('operating_water_activity',0.))
        self.invalid('fuel-cell-energy',self.edit('operating_effective_electrons_anode',1.5))
        self.valid('fuel-cell-energy',self.edit('operating_current_density',1e4))
        self.valid('fuel-cell-energy',self.edit('operating_effective_electrons_cathode',3.))
    def test_time_sampling_reference_and_malformed_declarations(self):
        from caeoj.sdk import sample_field
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,'capacitive-redox');p=load_problem(path)
            np.testing.assert_array_equal(sample_field(p,'current_value',.15),[[.05],[.05]])
            with self.assertRaises(ValueError):sample_field(p,'current_value',1.1)
        def gap(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['drive_times'][-1]=.9
        self.invalid('capacitive-redox',gap)
        self.invalid('capacitive-redox',lambda m,b:m['fields']['current_value']['sampling'].update(time='previous'))
        self.invalid('capacitive-redox',lambda m,b:m['fields']['initial_value'].update(location='system'))
        self.invalid('electrode-diffusion',lambda m,b:m['physics']['parameters'].pop('length'))
        self.invalid('mixed-potential',lambda m,b:m['conditions'][0]['data'].update(area={'value':1.,'unit':'m2'}))
        self.invalid('mixed-potential',lambda m,b:m['conditions'][0]['data'].update(area={'field':'missing'}))
        self.invalid('mixed-potential',lambda m,b:m['conditions'][0].update(time_axis='state'))
        self.invalid('mixed-potential',lambda m,b:m['conditions'].pop())
        self.invalid('mixed-potential',lambda m,b:m['physics'].update(model='electrochemistry-unknown-v1'))
    def test_distinct_rows_duplicate_points_and_observations(self):
        self.valid('capacitive-redox',self.edit('initial_value',[[[1.,2.],[3.,4.]]]))
        def duplicate(m,b):
            v=deepcopy(m['outputs']['observe_potential']);v['array']='second_potential';m['outputs']['second_observation']=v
            with h5py.File(b/'input.h5','r+') as h:h['probes_coordinates'][:]=.25
        self.valid('blocking-pnp',duplicate)
    def test_actual_policies_resources_and_closure(self):
        spec=importlib.util.spec_from_file_location('species_prepare',ROOT/'src/utils/prepare_harbor.py');prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);task=task_directory(slug,ROOT);policy=author_policy(task,p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((3 if cfg['dynamic'] else 1,len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    # Independent values from public instruction, not generated metadata.
                    tol,rtol=({**{q:(v,.002) for q,v in dict(surface_charge_left=1e-8,surface_charge_right=1e-8,potential=2e-6,metal_potential=2e-6,concentration=1e-6,surface_concentration=1e-6,faradaic_current=1e-5,capacitive_current=1e-5,area_impedance=1e-7,solid_concentration_negative=.01,solid_concentration_positive=.01,surface_stoichiometry=1e-5,cell_voltage=1e-4,reversible_voltage=2e-6,electric_power=.001,heat_release=.001).items()}})[s['quantity']]
                    self.assertEqual((bound['fields'][name]['atol'],bound['fields'][name]['rtol']),(tol,rtol))
                    candidate=deepcopy(ref);candidate[s['array']][:]=tol
                    self.assertEqual(grade_arrays(p,candidate,ref,policy=policy)['score'],1)
                    candidate[s['array']].flat[0]=np.nextafter(tol,np.inf)
                    self.assertEqual(grade_arrays(p,candidate,ref,policy=policy)['score'],0)
                    nonzero=deepcopy(ref);nonzero[s['array']][:]=100.;candidate=deepcopy(nonzero);edge=100.+tol+100.*rtol
                    if edge-100.>tol+100.*rtol:edge=np.nextafter(edge,-np.inf)
                    candidate[s['array']][:]=edge;self.assertEqual(grade_arrays(p,candidate,nonzero,policy=policy)['score'],1)
                    candidate[s['array']].flat[0]=np.nextafter(edge,np.inf);self.assertEqual(grade_arrays(p,candidate,nonzero,policy=policy)['score'],0)
                bad=deepcopy(ref);bad.pop(next(iter(m['outputs'].values()))['array'])
                self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0)
                self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
                config=json.loads((task/'judge-config.json').read_text());override=tomllib.loads((task/'harbor/task.toml').read_text());merged=tomllib.loads(prepare.task_config(template,override,judge_config=config,case_count=3))
                expected=1200 if slug in ('blocking-pnp','particle-battery') else 900 if slug=='electrode-diffusion' else 600 if slug=='ionic-equilibrium' else 240
                self.assertEqual(config['timeout_seconds'],expected);self.assertIsNone(config['max_output_bytes'])
                for k,v in dict(cpus=2,memory_mb=4096,gpus=0,os='linux',build_timeout_sec=1800.).items():self.assertEqual(merged['environment'][k],v)
                self.assertEqual(merged['agent']['timeout_sec'],3600.)
                self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate')
                self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(expected+120)))
        files,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'electrochemistry.interfaces_transport'})
        self.assertFalse(any(any(v in name for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in files))

if __name__=='__main__':unittest.main()
