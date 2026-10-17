"""System topology, declaration, public scoring and resource consumers."""
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
from systems_fixture import fixture
from caeoj_ext.systems import models,incidence
from caeoj.sdk import load_problem,write_result,load_result
from caeoj.validation import validate_input,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.grading_policy import author_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class SystemTests(unittest.TestCase):
    def changed(self,slug,mutate):
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,slug);mutate(m,path.parent);path.write_text(json.dumps(m));return validate_input(path)
    def invalid(self,slug,mutate):
        r=self.changed(slug,mutate);self.assertFalse(r['valid'],r);return r
    def valid(self,slug,mutate):
        r=self.changed(slug,mutate);self.assertTrue(r['valid'],r)
    @staticmethod
    def edit(key,v):
        def change(m,b):
            with h5py.File(b/'input.h5','r+') as h:h[key][:]=v
        return change
    def test_all_models_sdk_roundtrip(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path)
                values={s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                out=Path(tmp)/'result.h5';write_result(out,p,values);self.assertTrue(validate_output(path,out)['valid']);load_result(p,out)
    def test_hand_incidence_noncontinuous_ids_parallel_and_reverse_edges(self):
        ids=np.array([11,41,103],dtype='int64');ends=np.array([[103,11],[11,41],[41,103],[103,11]],dtype='int64')
        expected=np.array([[-1.,1.,0.,-1.],[0.,-1.,1.,0.],[1.,0.,-1.,1.]])
        np.testing.assert_array_equal(incidence(ids,ends),expected)
        # Independently selected outgoing flows give node balances [-7,1,6].
        np.testing.assert_array_equal(expected@np.array([2.,3.,4.,8.]),[-7.,1.,6.])
        np.testing.assert_array_equal(incidence(ids.astype('>i8'),ends.astype('>i8')),expected)
        for bad in (np.array([[0,1]],dtype='int64'),np.array([[11,11]],dtype='int64'),np.array([[11.,41.]])):
            with self.assertRaises(ValueError):incidence(ids,bad)
    def test_actual_topology_references_no_selfloops_connected_parallel_allowed(self):
        slug='geared-torsional-network'
        self.invalid(slug,self.edit('payload_edge_properties_endpoints',[[[0,1],[11,41],[41,103]]]))
        self.invalid(slug,self.edit('payload_edge_properties_endpoints',[[[11,11],[11,41],[41,103]]]))
        self.invalid(slug,self.edit('payload_edge_properties_endpoints',[[[11,41],[11,41],[41,11]]]))
        self.valid(slug,self.edit('payload_edge_properties_endpoints',[[[103,11],[103,11],[41,103]]]))
        self.invalid(slug,lambda m,b:m['fields']['edge_properties_endpoints'].update(components=['head','tail']))
    def test_big_endian_integer_hdf5_remains_legal(self):
        def big_endian(m,b):
            with h5py.File(b/'input.h5','r+') as h:
                for key in ('node_ids','edge_ids','payload_edge_properties_endpoints'):
                    values=h[key][()].astype('>i8');del h[key];h[key]=values
        self.valid('geared-torsional-network',big_endian)
    def test_model_specific_physical_declarations(self):
        self.invalid('deadzone-transmission-network',self.edit('payload_edge_properties_ratio',0.))
        self.valid('deadzone-transmission-network',self.edit('payload_edge_properties_ratio',-.1))
        self.valid('geared-torsional-network',self.edit('payload_edge_properties_ratio',10.))
        self.invalid('geared-torsional-network',self.edit('payload_edge_properties_ratio',10.01))
        self.invalid('deadzone-transmission-network',self.edit('payload_edge_properties_gap',0.))
        self.invalid('nonlinear-hydraulic-network',self.edit('payload_node_properties_compliance',0.))
        self.valid('nonlinear-hydraulic-network',self.edit('payload_initial_nodes_pressure',-1.))
        self.invalid('distributed-pipe-network',self.edit('payload_driving_injection',1.))
        self.invalid('isothermal-pneumatic-network',self.edit('payload_initial_nodes_pressure',0.))
        self.invalid('isothermal-pneumatic-network',lambda m,b:m['physics']['parameters']['gas_temperature'].update(value=True))
        self.invalid('radiative-thermal-network',self.edit('payload_driving_ambient_temperature',0.))
        self.valid('radiative-thermal-network',self.edit('payload_driving_heat_source',-1.))
        self.invalid('nonlinear-diode-rlc-network',self.edit('payload_edge_properties_saturation_current',0.))
        self.invalid('motor-thermal-feedback-system',self.edit('payload_properties_reference_temperature',0.))
        self.invalid('electrohydraulic-actuator-system',self.edit('payload_properties_volume_a',0.))
    def test_units_conditions_and_output_observation_shapes(self):
        for slug in models():
            with self.subTest(slug=slug):
                self.invalid(slug,lambda m,b:m['conditions'].pop())
                self.invalid(slug,lambda m,b:m['conditions'].append(deepcopy(m['conditions'][0])))
                self.invalid(slug,lambda m,b:next(iter(m['fields'].values())).update(unit='wrong'))
                self.invalid(slug,lambda m,b:m['outputs'].pop(next(iter(m['outputs']))))
                self.invalid(slug,lambda m,b:m.update(task='unknown-system-task'))
        self.invalid('geared-torsional-network',lambda m,b:m['conditions'][0]['data'].update(inertia={'value':1.,'unit':'kg.m2'}))
        self.invalid('distributed-pipe-network',lambda m,b:m['outputs']['observation_endpoint_volume_flow'].update(components=['head','tail']))
        self.invalid('electrohydraulic-actuator-system',lambda m,b:m['outputs']['observation_chamber_pressure'].update(components=['B','A']))
        self.invalid('nonlinear-hydraulic-network',lambda m,b:m['fields']['edge_properties_resistance'].update(location='nodes'))
        self.invalid('geared-torsional-network',lambda m,b:m['physics'].update(model='systems-unknown-v1'))
    def test_time_reconstruction_and_control_clock(self):
        slug='sampled-position-servo'
        self.valid(slug,self.edit('response_times',[.1,.6,1.]))
        self.invalid(slug,self.edit('response_times',[0.,.2,1.01]))
        self.invalid(slug,self.edit('static_times',[.01]))
        self.invalid(slug,self.edit('control_times',[0.,.1,.6,1.01]))
        self.invalid(slug,lambda m,b:m['fields']['reference_position_reference']['sampling'].update(time='linear'))
        self.invalid(slug,lambda m,b:m['fields']['driving_load_torque']['sampling'].update(time='previous'))
        self.invalid(slug,lambda m,b:m['fields']['properties_resistance'].update(time_axis='response'))
        self.valid(slug,self.edit('payload_reference_position_reference',-1.))
    def test_repeated_quantities_and_arbitrary_names(self):
        def repeated(m,b):
            name,s=next(iter(m['outputs'].items()));m['outputs']['same_quantity_again']=dict(s,array='another_result_array')
        self.valid('geared-torsional-network',repeated)
        self.valid('electrohydraulic-actuator-system',repeated)
    def test_public_quantity_policy_boundaries_and_failure_classification(self):
        # Literal expectations from instruction tables, independent of metadata generator.
        defaults={'angle':(1e-7,.002),'angular_velocity':(1e-7,.002),'transmitted_torque':(1e-6,.002),'pressure':(1e-3,.002),'volume_flow':(1e-9,.002),'endpoint_volume_flow':(1e-9,.003),'absolute_pressure':(1e-3,.002),'mass_flow':(1e-9,.002),'temperature':(1e-5,.002),'heat_rate':(1e-5,.002),'voltage':(1e-7,.002),'current':(1e-8,.002),'displacement':(1e-8,.003),'velocity':(1e-7,.003),'chamber_pressure':(1e-2,.003),'control_voltage':(1e-6,.002)}
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);policy=author_policy(task_directory(slug,ROOT),p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    want=defaults[s['quantity']]
                    if slug=='distributed-pipe-network' and s['quantity']=='pressure':want=(1e-3,.003)
                    if slug=='electrohydraulic-actuator-system':want=(want[0],.003)
                    rule=bound['fields'][name];self.assertEqual((rule['atol'],rule['rtol']),want)
                    for base in (0.,100.):
                        reference=deepcopy(ref);reference[s['array']][:]=base;actual=deepcopy(reference);tol=want[0]+want[1]*base;edge=base+tol
                        if edge-base>tol:edge=np.nextafter(edge,-np.inf)
                        actual[s['array']][:]=edge;self.assertEqual(grade_arrays(p,actual,reference,policy=policy)['score'],1)
                        actual[s['array']].flat[0]=np.nextafter(edge,np.inf);self.assertEqual(grade_arrays(p,actual,reference,policy=policy)['score'],0)
                bad=deepcopy(ref);bad.pop(next(iter(m['outputs'].values()))['array']);self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0);self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
    def test_resource_consumers_and_public_closure(self):
        spec=importlib.util.spec_from_file_location('system_prepare',ROOT/'src/utils/prepare_harbor.py');prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        expected={'geared-torsional-network':180,'deadzone-transmission-network':300,'nonlinear-hydraulic-network':240,'distributed-pipe-network':600,'isothermal-pneumatic-network':240,'radiative-thermal-network':240,'nonlinear-diode-rlc-network':300,'motor-thermal-feedback-system':240,'electrohydraulic-actuator-system':480,'sampled-position-servo':300}
        for slug in models():
            task=task_directory(slug,ROOT);config=json.loads((task/'judge-config.json').read_text());override=tomllib.loads((task/'harbor/task.toml').read_text());merged=tomllib.loads(prepare.task_config((ROOT/'src/utils/harbor/task.toml').read_text(),override,judge_config=config,case_count=3))
            self.assertEqual(config['timeout_seconds'],expected[slug]);self.assertIsNone(config['max_output_bytes'])
            self.assertEqual(merged['environment']['cpus'],2);self.assertEqual(merged['environment']['memory_mb'],4096);self.assertEqual(merged['environment']['gpus'],0)
            self.assertEqual(merged['agent']['timeout_sec'],3600);self.assertEqual(merged['environment']['build_timeout_sec'],1800)
            self.assertEqual(merged['verifier']['environment_mode'],'separate');self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(expected[slug]+120)))
        files,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'systems.networks'})
        self.assertFalse(any(any(v in n for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for n in files))

if __name__=='__main__':unittest.main()
