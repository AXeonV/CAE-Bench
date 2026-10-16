"""Coupling declaration, scoring and assembly checks; no physical reference claims."""
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
from multiphysics_fixture import fixture
from caeoj_ext.multiphysics import models
from caeoj.sdk import load_problem,write_result,load_result
from caeoj.validation import validate_input,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class CoupledTests(unittest.TestCase):
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
            with h5py.File(b/'input.h5','r+') as h:h[key][:]=values
        return change
    def test_all_models_sdk_and_noncontinuous_identity(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path)
                values={s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                out=Path(tmp)/'result.h5';write_result(out,p,values);self.assertTrue(validate_output(path,out)['valid']);load_result(p,out)
    def test_points_and_endpoint_objects_are_not_interchangeable(self):
        slug='compliant-tube-wave'
        self.invalid(slug,self.edit('domain_coordinates',[[1.01],[0.],[.37]]))
        self.invalid(slug,self.edit('domain_coordinates',[[.37],[0.],[.37]]))
        self.invalid(slug,lambda m,b:m['fields']['left_pressure'].update(location='right'))
        self.invalid(slug,lambda m,b:m['outputs']['observation_pressure'].update(location='left'))
        self.valid(slug,self.edit('domain_coordinates',[[.2],[.9],[.1]]))
    def test_transient_zero_initial_time_coverage_and_sampling(self):
        slug='reciprocal-thermoelastic-wave'
        self.invalid(slug,self.edit('payload_left_displacement',1.))
        self.invalid(slug,self.edit('response_times',[0.,.1,1.01]))
        self.invalid(slug,self.edit('load_times',[.01,.2,1.]))
        self.invalid(slug,lambda m,b:m['fields']['right_traction']['sampling'].update(time='previous'))
        self.invalid(slug,lambda m,b:m['conditions'][0]['data'].update(displacement={'value':0.,'unit':'m'}))
        self.valid(slug,self.edit('response_times',[.01,.07,.8]))
    def test_steady_constants_harmonic_layout_and_units(self):
        def constant(m,b):
            c=m['conditions'][0];key=next(iter(c['data']));ref=c['data'][key]['field'];fs=m['fields'].pop(ref);c['data'][key]={'value':.01,'unit':fs['unit']}
            with h5py.File(b/'input.h5','r+') as h:del h[fs['array']]
        self.valid('static-piezoelectric-rod',constant)
        self.invalid('shunted-piezoelectric-rod',constant)
        self.invalid('shunted-piezoelectric-rod',lambda m,b:m['fields']['right_current'].update(components=['imag','real']))
        self.invalid('magnetic-diffusion-elasticity',lambda m,b:m['fields']['left_magnetic_field'].update(unit='T'))
        self.invalid('thermoelectric-leg',lambda m,b:m['outputs']['observation_total_heat_flux'].update(unit='W'))
        self.invalid('static-piezoelectric-rod',lambda m,b:m['physics']['parameters']['permittivity'].update(value=True))
    def test_coupling_parameter_and_boundary_acceptance_limits(self):
        self.invalid('compliant-tube-wave',lambda m,b:m['physics']['parameters']['wall_thickness'].update(value=.10001))
        self.valid('compliant-tube-wave',lambda m,b:m['physics']['parameters']['wall_thickness'].update(value=.1))
        self.invalid('biot-consolidation',lambda m,b:m['physics']['parameters']['biot_alpha'].update(value=1.01))
        self.invalid('thermo-poroelastic-transient',lambda m,b:m['physics']['parameters']['fluid_thermal'].update(value=4.))
        self.valid('thermo-poroelastic-transient',lambda m,b:m['physics']['parameters']['fluid_thermal'].update(value=0.))
        self.invalid('steady-joule-feedback',self.edit('payload_right_voltage',4.))
        self.invalid('transient-joule-feedback',self.edit('payload_left_temperature_rise',[[[0.]],[[-.01]],[[0.]]]))
        self.valid('steady-joule-feedback',self.edit('payload_right_voltage',-1.))
        self.invalid('thermoelectric-leg',self.edit('payload_left_temperature',0.))
        self.invalid('constrained-thermal-expansion',lambda m,b:m['physics']['parameters']['alpha'].update(value=-1.))
    def test_missing_extra_and_wrong_model_declarations(self):
        for slug in models():
            with self.subTest(slug=slug):
                self.invalid(slug,lambda m,b:m['conditions'].pop())
                self.invalid(slug,lambda m,b:m['conditions'].append(deepcopy(m['conditions'][0])))
                self.invalid(slug,lambda m,b:m['physics']['parameters'].update(unlisted={'value':1.,'unit':'1'}))
                self.invalid(slug,lambda m,b:m['outputs'].pop(next(iter(m['outputs']))))
                self.invalid(slug,lambda m,b:m.update(task='completely-wrong-task'))
        self.invalid('compliant-tube-wave',lambda m,b:m['physics'].update(model='multiphysics-unknown-v1'))
    def test_quantity_policies_rounding_boundary_and_bad_reference(self):
        # Expected tolerances independently selected from final DATA/instruction tables.
        expected={'pressure':(1e-3,.003),'velocity':(1e-7,.003),'wall_displacement':(1e-10,.003),'piston_displacement':(1e-9,.003),'temperature_rise':(1e-5,.003),'displacement':(1e-9,.003),'electric_potential':(1e-7,.003),'axial_stress':(1e-2,.002),'electric_displacement':(1e-10,.002),'magnetic_field':(1e-6,.003),'pore_pressure':(1e-3,.003),'temperature':(1e-5,.002),'total_heat_flux':(1e-4,.003)}
        for slug,cfg in models().items():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);policy=task_policy(task_directory(slug,ROOT),p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    want=expected[s['quantity']]
                    if slug=='constrained-thermal-expansion':want={'temperature_rise':(1e-5,.002),'displacement':(1e-9,.002),'axial_stress':(1e-2,.002)}[s['quantity']]
                    if slug=='static-piezoelectric-rod':want={'displacement':(1e-10,.002),'electric_potential':(1e-8,.002),'electric_displacement':(1e-10,.002)}[s['quantity']]
                    if slug=='thermoelectric-leg' and s['quantity']=='electric_potential':want=(1e-8,.002)
                    rule=bound['fields'][name];self.assertEqual((rule['atol'],rule['rtol']),want)
                    for base in (0.,100.):
                        reference=deepcopy(ref);reference[s['array']][:]=base;actual=deepcopy(reference);edge=base+want[0]+want[1]*base
                        if edge-base>want[0]+want[1]*base:edge=np.nextafter(edge,-np.inf)
                        actual[s['array']][:]=edge;self.assertEqual(grade_arrays(p,actual,reference,policy=policy)['score'],1)
                        actual[s['array']].flat[0]=np.nextafter(edge,np.inf);self.assertEqual(grade_arrays(p,actual,reference,policy=policy)['score'],0)
                bad=deepcopy(ref);bad.pop(next(iter(m['outputs'].values()))['array']);self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0);self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
    def test_actual_backend_resource_merge_and_public_closure(self):
        spec=importlib.util.spec_from_file_location('coupled_prepare',ROOT/'src/utils/prepare_harbor.py');prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            task=task_directory(slug,ROOT);config=json.loads((task/'judge-config.json').read_text());override=tomllib.loads((task/'harbor/task.toml').read_text());merged=tomllib.loads(prepare.task_config(template,override,judge_config=config,case_count=3))
            timeout=480 if slug in ('steady-joule-feedback','transient-joule-feedback','thermo-poroelastic-transient') else 360
            self.assertEqual(config['timeout_seconds'],timeout);self.assertIsNone(config['max_output_bytes'])
            self.assertEqual(merged['environment']['cpus'],2);self.assertEqual(merged['environment']['memory_mb'],4096);self.assertEqual(merged['environment']['gpus'],0)
            self.assertEqual(merged['agent']['timeout_sec'],3600);self.assertEqual(merged['environment']['build_timeout_sec'],1800)
            self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate');self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(timeout+60)))
        files,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'multiphysics.continuum'})
        self.assertFalse(any(any(v in n for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for n in files))

if __name__=='__main__':unittest.main()
