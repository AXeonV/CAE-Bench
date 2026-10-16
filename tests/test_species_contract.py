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
from species_fixture import fixture
from caeoj_ext.species import models
from caeoj.sdk import load_problem,write_result
from caeoj.validation import validate_input,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class SpeciesTests(unittest.TestCase):
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
                v={s['array']:np.zeros((3,len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                out=Path(tmp)/'protocol-output.h5';write_result(out,p,v)
                self.assertTrue(validate_output(path,out)['valid'])
    def test_transport_reconstruction_corners_and_time(self):
        for slug in ('fick-diffusion','imposed-field-migration','pore-adsorption','reactive-transport'):
            self.invalid(slug,self.edit('diffusivity_value',0.))
            self.invalid(slug,self.edit('initial_value',-1.))
            self.invalid(slug,self.edit('left_value',2.))
            self.invalid(slug,lambda m,b:m['fields']['initial_value']['sampling'].update(space='uniform'))
        def interior_history(m,b):
            with h5py.File(b/'input.h5','r+') as h:
                h['payload_left_value'][1:]=3.;h['knots_coordinates'][:]=[[0.],[.1],[1.]]
        self.valid('fick-diffusion',interior_history)
        def time_gap(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['boundary_times'][-1]=.9
        self.invalid('fick-diffusion',time_gap)
        def order(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['knots_coordinates'][:]=[[0.],[1.],[.5]]
        self.invalid('fick-diffusion',order)
        def endpoint(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['probes_coordinates'][0]=0.
        self.invalid('pore-adsorption',endpoint)
        self.invalid('fick-diffusion',lambda m,b:m['outputs']['observe_concentration'].update(time_axis='initial'))
    def test_charge_and_adsorption_capacity(self):
        self.valid('imposed-field-migration',self.edit('charge_value',[0.,-4.]))
        self.invalid('imposed-field-migration',self.edit('charge_value',[.5,1.]))
        self.valid('imposed-field-migration',lambda m,b:m['physics']['parameters']['electric_field'].update(value=-10.))
        for slug in ('pore-adsorption','competitive-adsorption'):
            self.valid(slug,self.edit('initial_loading_value',[.5,.5]))
            self.invalid(slug,self.edit('initial_loading_value',[.6,.6]))
            self.valid(slug,self.edit('sites_adsorption',0.))
            self.invalid(slug,self.edit('sites_desorption',-1.))
        self.invalid('pore-adsorption',lambda m,b:m['physics']['parameters']['porosity'].update(value=1.))
        self.invalid('competitive-adsorption',lambda m,b:m['physics']['parameters']['capacity'].update(value=True))
    def test_stoichiometry_units_mass_and_no_implicit_reverse(self):
        for slug in ('mass-action-network','reactive-transport','adiabatic-combustion'):
            self.invalid(slug,self.edit('kinetics_reactants',0.))
            self.invalid(slug,self.edit('kinetics_products',[1.,0.]))
            self.invalid(slug,self.edit('kinetics_reactants',[.5,0.]))
            self.invalid(slug,self.edit('species_molar_mass',[1.,2.]))
            self.valid(slug,self.edit('species_molar_mass',[1e200,1e200]))
            self.invalid(slug,lambda m,b:m['fields']['kinetics_prefactor'].update(unit='1/s'))
        # Independent balanced second-order reaction 2 A -> B, M_B=2 M_A.
        def balanced(m,b):
            for k,v in [('kinetics_reactants',[2.,0.]),('species_molar_mass',[1.,2.])]:self.edit(k,v)(m,b)
        self.valid('mass-action-network',balanced)
        self.invalid('mass-action-network',lambda m,b:m['physics']['parameters']['reaction_count'].update(value=1))
        self.invalid('mass-action-network',lambda m,b:m['physics']['parameters']['species_count'].update(value=2.0))
    def test_thermal_and_transfer_declarations(self):
        self.valid('adiabatic-combustion',self.edit('species_reference_energy',[-1e6,2e6]))
        self.invalid('adiabatic-combustion',self.edit('thermal_initial_value',249.))
        self.invalid('adiabatic-combustion',self.edit('species_heat_capacity',0.))
        self.invalid('adiabatic-combustion',self.edit('initial_value',0.))
        self.invalid('adiabatic-combustion',self.edit('kinetics_activation',-1.))
        self.valid('partition-transfer',self.edit('links_partition',[.2,3.]))
        self.valid('partition-transfer',self.edit('links_conductance',0.))
        self.invalid('partition-transfer',self.edit('links_partition',0.))
        self.invalid('partition-transfer',self.edit('links_destination',17.))
        self.invalid('partition-transfer',self.edit('links_origin',0.))
        self.invalid('partition-transfer',self.edit('links_origin',17.5))
        self.invalid('partition-transfer',self.edit('volumes_value',0.))
    def test_errors_are_diagnostics_and_unknowns_rejected(self):
        self.invalid('fick-diffusion',lambda m,b:m['physics']['parameters'].pop('length'))
        self.invalid('fick-diffusion',lambda m,b:m['conditions'][0]['data'].update(extra={'value':1.,'unit':'1'}))
        self.invalid('fick-diffusion',lambda m,b:m['conditions'][0]['data'].update(value={'value':1.,'unit':'m2/s'}))
        self.invalid('fick-diffusion',lambda m,b:m['conditions'][0]['data'].update(value={'field':'nonexistent'}))
        self.invalid('fick-diffusion',lambda m,b:m['conditions'].pop())
        self.invalid('fick-diffusion',lambda m,b:m['outputs']['observe_concentration'].update(quantity='flux'))
        self.invalid('fick-diffusion',lambda m,b:m['physics'].update(model='species-unknown-v1'))
    def test_independent_rows_aliases_duplicates_and_explicit_time_sampling(self):
        # Different vessel rows are legal despite the storage label space=uniform.
        self.valid('competitive-adsorption',self.edit('initial_value',[[[1.,2.],[3.,4.]]]))
        def duplicate_points(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['probes_coordinates'][:]=.25
        self.valid('fick-diffusion',duplicate_points)
        def duplicate_output(m,b):
            v=deepcopy(m['outputs']['observe_concentration']);v['array']='second_concentration';m['outputs']['another_observation']=v
        self.valid('fick-diffusion',duplicate_output)
        def wrong_identity_location(m,b):
            m['fields']['kinetics_reactants']['location']='vessels'
        self.invalid('mass-action-network',wrong_identity_location)
        def too_large_id(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['vessels_identity'][:]=[17,2**53]
        self.invalid('partition-transfer',too_large_id)
        from caeoj.sdk import sample_field
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,'fick-diffusion')
            with h5py.File(path.parent/'input.h5','r+') as h:h['payload_left_value'][1:]=3.
            p=load_problem(path)
            np.testing.assert_array_equal(sample_field(p,'left_value',.15),[[2.,2.]])
            with self.assertRaises(ValueError):sample_field(p,'left_value',1.1)
    def test_actual_policies_resources_and_closure(self):
        spec=importlib.util.spec_from_file_location('species_prepare',ROOT/'src/utils/prepare_harbor.py');prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);task=task_directory(slug,ROOT);policy=task_policy(task,p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((3,len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    # Independent values from public instruction, not generated metadata.
                    tol,rtol={'concentration':(1e-6,.002),'loading':(1e-8,.002),'temperature':(.02,.001),'pressure':(.1,.002),'molar_flow':(1e-9,.002)}[s['quantity']]
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
                expected=1200 if slug=='adiabatic-combustion' else 900 if slug in ('pore-adsorption','reactive-transport') else 300
                self.assertEqual(config['timeout_seconds'],expected);self.assertIsNone(config['max_output_bytes'])
                for k,v in dict(cpus=2,memory_mb=4096,gpus=0,os='linux',build_timeout_sec=1800.).items():self.assertEqual(merged['environment'][k],v)
                self.assertEqual(merged['agent']['timeout_sec'],3600.)
                self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate')
                self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(expected+60)))
        files,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'species.transport_kinetics'})
        self.assertFalse(any(any(v in name for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in files))

if __name__=='__main__':unittest.main()
