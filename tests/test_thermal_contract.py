"""Thermal declarations and material maps, not reference solver validation."""
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
from thermal_fixture import fixture
from qbank.maintenance.authoring.build_thermal import M as AUTHOR_MODELS
from caeoj_ext.thermal import models,phase_state
from caeoj.sdk import load_problem,write_result
from caeoj.validation import validate_input,validate_output,output_support
from grading_fixtures import evaluate_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.grading_policy import author_policy
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class ThermalTests(unittest.TestCase):
    def changed(self,slug,mutate):
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,slug);mutate(m,path.parent);path.write_text(json.dumps(m));return validate_input(path)
    def invalid(self,slug,mutate):
        r=self.changed(slug,mutate);self.assertFalse(r['valid'],r);return r
    def valid(self,slug,mutate):
        r=self.changed(slug,mutate);self.assertTrue(r['valid'],r)
    @staticmethod
    def edit(key,values):
        def change(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['payload_'+key][:]=values
        return change
    def test_all_models_real_files_and_sdk_roundtrip(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path)
                values={s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                output=Path(tmp)/'protocol-output.h5';write_result(output,p,values)
                self.assertTrue(validate_output(path,output)['valid'])
                # Pure protocol payloads do not claim to be physical references.
    def test_local_phase_maps_independent_hand_values(self):
        # C=2,L=6,Ts=10,Tl=12 => middle H=5 gives T=11,f=.5.
        t,f=phase_state(np.array([-2.,0.,5.,10.,12.]),2.,6.,10.,12.)
        np.testing.assert_allclose(t,[9.,10.,11.,12.,13.]);np.testing.assert_allclose(f,[0.,0.,.5,1.,1.])
        t,f=phase_state(np.array([-2.,0.,3.,6.,8.]),2.,6.,10.)
        np.testing.assert_allclose(t,[9.,10.,10.,10.,11.]);np.testing.assert_allclose(f,[0.,0.,.5,1.,1.])
        for args in [(0.,0.,1.,10.),(0.,1.,0.,10.),(0.,1.,1.,10.,9.)]:
            with self.assertRaises(ValueError):phase_state(*args)
    def test_units_fields_sampling_and_operating_ranges(self):
        mutations=[lambda m,b:m['physics']['parameters']['temperature_max'].update(value=100.),lambda m,b:m['conditions'][0]['data'].update(extra={'value':1.,'unit':'1'}),lambda m,b:m['fields']['material_capacity'].update(unit='J/K'),lambda m,b:m['fields']['material_capacity'].update(quantity='density'),lambda m,b:m['fields']['heat_source_value']['sampling'].update(time='previous'),lambda m,b:m['fields']['initial_temperature_value'].update(value_kind='integral')]
        for mutate in mutations:self.invalid('thermal-transient',mutate)
        self.invalid('thermal-transient',self.edit('material_capacity',0.))
        self.invalid('thermal-transient',self.edit('initial_temperature_value',0.))
        self.invalid('nonlinear-conductivity',self.edit('material_beta',1.))
        self.invalid('nonlinear-capacity',self.edit('material_gamma',.01))
        self.valid('nonlinear-capacity',self.edit('material_gamma',.001))
        self.invalid('anisotropic-conduction',self.edit('material_conductivity',[[1.,2.,0.],[2.,1.,0.],[0.,0.,1.]]))
        self.valid('anisotropic-conduction',self.edit('material_conductivity',[[2.,.3,0.],[.3,1.,0.],[0.,0.,1.]]))
    def test_constants_steady_anchor_and_boundary_face_closure(self):
        def constant(m,b):
            c=next(c for c in m['conditions'] if c['operator']=='material');ref=c['data']['conductivity']['field'];key=m['fields'].pop(ref)['array'];c['data']['conductivity']={'value':2.,'unit':'W/(m.K)'}
            with h5py.File(b/'input.h5','r+') as h:del h[key]
        self.valid('thermal-transient',constant)
        def remove_temperature(m,b):
            c=next(c for c in m['conditions'] if c['operator']=='temperature');m['conditions'].remove(c);ref=c['data']['value']['field'];key=m['fields'].pop(ref)['array']
            with h5py.File(b/'input.h5','r+') as h:del h[key]
        self.invalid('thermal-steady',remove_temperature)
        def robin_only(m,b):
            remove_temperature(m,b);m['conditions'].append(dict(role='boundary',variable='heat_flux',operator='convection',location='exchange',data=dict(coefficient={'value':2.,'unit':'W/(m2.K)'},ambient={'value':300.,'unit':'K'})))
        self.valid('thermal-steady',robin_only)
        def closure_overlap(m,b):
            c=next(c for c in m['conditions'] if c['operator']=='temperature');c['location']='domain';m['fields'][c['data']['value']['field']]['location']='domain'
            with h5py.File(b/'input.h5','r+') as h:
                key=m['fields'][c['data']['value']['field']]['array'];del h[key];h[key]=np.full((3,len(h['domain_ids']),1),300.)
            m['conditions'].append(dict(role='boundary',variable='heat_flux',operator='heat_flux',location='exchange',data=dict(value={'value':0.,'unit':'W/m2'})))
        self.invalid('thermal-transient',closure_overlap)
        self.invalid('thin-sheet-heat',lambda m,b:m['fields']['face_exchange_h_plus'].update(unit='W/(m.K)'))
    def test_interface_geometry_both_sides_and_surface_averages(self):
        self.invalid('thermal-contact',lambda m,b:next(c for c in m['conditions'] if c['operator']=='thermal_pair')['data'].update(partner={'location':'minus'}))
        self.invalid('thermal-contact',lambda m,b:next(c for c in m['conditions'] if c['operator']=='thermal_pair')['data'].update(partner={'location':'exchange'}))
        self.invalid('thermal-contact',lambda m,b:m['outputs']['observation_interface_heat_flux'].update(location='plus'))
        def extra_flux(side):
            return lambda m,b:m['conditions'].append(dict(role='boundary',variable='heat_flux',operator='heat_flux',location=side,data=dict(value={'value':0.,'unit':'W/m2'})))
        self.invalid('thermal-contact',extra_flux('minus'));self.invalid('thermal-contact',extra_flux('plus'))
        def swap(m,b):
            c=next(c for c in m['conditions'] if c['operator']=='thermal_pair');c['location']='plus';c['data']['partner']['location']='minus';m['fields']['thermal_pair_conductance']['location']='plus';m['outputs']['observation_interface_heat_flux']['location']='plus'
        self.valid('thermal-contact',swap)
        # Hand geometry: shared z=0 interface has area .5, outward normals +z/-z.
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,'thermal-contact');p=load_problem(path)
            from caeoj.mesh_geometry import boundary_geometry
            _,nm,am=boundary_geometry(p,'minus');_,np_,ap=boundary_geometry(p,'plus')
            np.testing.assert_allclose(nm,[[0,0,1]]);np.testing.assert_allclose(np_,[[0,0,-1]]);np.testing.assert_allclose(am,[.5]);np.testing.assert_allclose(ap,[.5])
    def test_given_velocity_inflow_and_solid_compatibility(self):
        def flow(m,b):
            # Literal divergence-free v=(1,0,0); all exterior faces given T.
            tc=next(c for c in m['conditions'] if c['operator']=='temperature');tc['location']='domain';m['fields']['temperature_value']['location']='domain'
            with h5py.File(b/'input.h5','r+') as h:
                n=len(h['domain_ids']);del h['payload_temperature_value'];h['payload_temperature_value']=np.full((3,n,1),300.);h['payload_prescribed_velocity_value'][:]=[1.,0.,0.]
        self.valid('prescribed-advection-heat',flow)
        self.invalid('prescribed-advection-heat',self.edit('prescribed_velocity_value',[1.,0.,0.]))
        self.invalid('prescribed-advection-heat',self.edit('material_capacity',[[[1.],[2.]]]))
        self.invalid('conjugate-prescribed-flow',self.edit('prescribed_velocity_value',[1.,0.,0.]))
        self.invalid('conjugate-prescribed-flow',self.edit('material_medium',2))
        def divergence(m,b):
            flow(m,b)
            with h5py.File(b/'input.h5','r+') as h:h['payload_prescribed_velocity_value'][0,:,0]=[0.,1.,0.,0.,0.]
        self.invalid('prescribed-advection-heat',divergence)
    def test_radiation_view_factors_and_phase_input_edges(self):
        self.invalid('gray-enclosure',self.edit('enclosure_view_factors',[[0.,.5],[1.,0.]]))
        self.invalid('gray-enclosure',self.edit('enclosure_area',[1.,2.]))
        self.invalid('gray-enclosure',self.edit('enclosure_emissivity',0.))
        self.valid('gray-enclosure',self.edit('enclosure_view_factors',[[.25,.75],[.75,.25]]))
        self.invalid('gray-enclosure',lambda m,b:m['physics']['parameters']['patch_count'].update(value=2.0))
        self.invalid('mushy-enthalpy',lambda m,b:m['physics']['parameters']['liquidus'].update(value=300.))
        self.invalid('isothermal-stefan',self.edit('initial_enthalpy_value',-10000.))
        def early(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['response_times'][0]=0.
        self.invalid('mushy-enthalpy',early)
    def test_actual_policies_resource_consumers_and_public_closure(self):
        spec=importlib.util.spec_from_file_location('thermal_prepare',ROOT/'src/utils/prepare_harbor.py');prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);task=task_directory(slug,ROOT);policy=author_policy(task,p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    q=s['quantity'];expected=(.1,0.) if q=='temperature' else (.005,0.) if q=='liquid_fraction' else (100.,.005) if q=='enthalpy' else (.1,.005)
                    self.assertEqual((bound['fields'][name]['atol'],bound['fields'][name]['rtol']),expected)
                    actual=deepcopy(ref);tol=bound['fields'][name]['atol'];actual[s['array']][:]=tol
                    self.assertEqual(evaluate_arrays(p,actual,ref,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(tol,np.inf)
                    self.assertEqual(evaluate_arrays(p,actual,ref,policy=policy)['score'],0)
                    nonzero=deepcopy(ref);nonzero[s['array']][:]=100.;actual=deepcopy(nonzero)
                    actual[s['array']][:]=100.+expected[0]+100.*expected[1]
                    self.assertEqual(evaluate_arrays(p,actual,nonzero,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(actual[s['array']].flat[0],np.inf)
                    self.assertEqual(evaluate_arrays(p,actual,nonzero,policy=policy)['score'],0)
                config=json.loads((task/'judge-config.json').read_text());override=tomllib.loads((task/'harbor/task.toml').read_text());merged=tomllib.loads(prepare.task_config(template,override,judge_config=config,case_count=3))
                self.assertEqual(config['timeout_seconds'],AUTHOR_MODELS[slug]['timeout']);self.assertIsNone(config['max_output_bytes'])
                self.assertEqual(merged['environment']['memory_mb'],6144);self.assertEqual(merged['environment']['cpus'],4);self.assertEqual(merged['environment']['gpus'],0)
                self.assertEqual(merged['agent']['timeout_sec'],3600);self.assertEqual(merged['environment']['build_timeout_sec'],1800)
                self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate');self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(AUTHOR_MODELS[slug]['timeout']+120)))
                self.assertEqual((task/'harbor/requirements.txt').read_text().strip(),'scipy==1.18.1')
                bad=deepcopy(ref);bad.pop(next(iter(m['outputs'].values()))['array'])
                self.assertEqual(evaluate_arrays(p,bad,ref,policy=policy)['score'],0);self.assertIsNone(evaluate_arrays(p,ref,bad,policy=policy)['score'])
        files,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'thermal.transport'})
        self.assertFalse(any(any(v in name for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in files))

if __name__=='__main__':unittest.main()
