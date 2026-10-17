"""Electromagnetic public declarations and tooling; no trusted numerical solutions."""
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
from electromagnetic_fixture import fixture
from caeoj_ext.electromagnetic import models
from qbank.maintenance.authoring.build_electromagnetic import M as AUTHOR_MODELS
from caeoj.sdk import load_problem,write_result
from caeoj.validation import validate_input,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.grading_policy import author_policy
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class ElectromagneticTests(unittest.TestCase):
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
    def test_scalar_constants_and_exact_reconstruction(self):
        def constant(m,b):
            c=next(c for c in m['conditions'] if c['operator']=='material');ref=c['data']['permittivity']['field'];key=m['fields'].pop(ref)['array'];c['data']['permittivity']={'value':1.,'unit':'F/m'}
            with h5py.File(b/'input.h5','r+') as h:del h[key]
        self.valid('electrostatic',constant)
        self.invalid('electrostatic',lambda m,b:m['fields']['material_permittivity'].update(quantity='relative_permittivity'))
        self.invalid('dc-conduction',lambda m,b:m['fields']['material_conductivity'].update(unit='S'))
        self.invalid('magnetostatic',lambda m,b:m['fields']['volume_source_value'].update(value_kind='integral'))
        self.invalid('harmonic-eddy',lambda m,b:m['fields']['volume_source_value'].update(components=['imag','real']))
        self.invalid('rlc-transient',lambda m,b:m['fields']['resistor_tail']['sampling'].update(space='piecewise_constant'))
    def test_material_ranges_and_frequency_metadata(self):
        self.invalid('electrostatic',self.edit('material_permittivity',0.))
        self.invalid('dc-conduction',self.edit('material_conductivity',-1.))
        self.invalid('magnetostatic',self.edit('material_reluctivity',0.))
        self.valid('harmonic-eddy',self.edit('material_conductivity',0.));self.invalid('harmonic-eddy',self.edit('material_conductivity',-1.))
        self.invalid('maxwell-cavity',self.edit('material_conductivity',0.))
        self.invalid('harmonic-eddy',lambda m,b:m['physics']['parameters']['frequency'].update(value=0.))
        self.invalid('rlc-harmonic',lambda m,b:m['physics']['parameters']['ground_node'].update(value=True))
        self.invalid('coil-circuit',lambda m,b:m['physics']['parameters']['length'].update(value=0.))
    def test_boundary_closure_floating_charge_and_output_support(self):
        self.invalid('electrostatic',lambda m,b:m['conditions'].remove(next(c for c in m['conditions'] if c['operator']=='dirichlet')))
        self.invalid('floating-electrode',lambda m,b:next(c for c in m['conditions'] if c['operator']=='floating').update(location='fixed'))
        def charge(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['payload_floating_charge'][0,1,0]=1.
        self.invalid('floating-electrode',charge);self.valid('floating-electrode',self.edit('floating_charge',1.))
        self.invalid('floating-electrode',lambda m,b:m['outputs'].pop('observation_electrode_potential'))
        self.invalid('floating-electrode',lambda m,b:m['outputs']['observation_electrode_potential'].update(location='fixed'))
        def flux(m,b):
            m['conditions'].append(dict(role='boundary',variable='displacement_flux',operator='normal_flux',location='flux',data={'value':{'value':0.,'unit':'C/m2'}}))
        self.valid('electrostatic',flux)
        def overlap(m,b):
            flux(m,b)
            c=next(c for c in m['conditions'] if c['operator']=='dirichlet');c['location']='domain';m['fields']['dirichlet_value']['location']='domain'
            with h5py.File(b/'input.h5','r+') as h:del h['payload_dirichlet_value'];h['payload_dirichlet_value']=np.zeros((1,4,1))
        self.invalid('electrostatic',overlap)
    def test_transient_requests_loading_and_static_axes(self):
        self.invalid('dielectric-relaxation',lambda m,b:m['fields']['volume_source_value']['sampling'].update(time='previous'))
        def time(value):
            def change(m,b):
                with h5py.File(b/'input.h5','r+') as h:h['response_times'][0]=value
            return change
        self.invalid('dielectric-relaxation',time(0.));self.invalid('dielectric-relaxation',time(.5));self.valid('dielectric-relaxation',time(.1))
        self.invalid('rlc-transient',self.edit('initial_voltage_value',1.))
        self.invalid('dielectric-relaxation',lambda m,b:m['physics']['parameters']['end_time'].update(value=0.))
    def test_circuit_graphs_directions_id_types_and_partition(self):
        self.invalid('rlc-harmonic',self.edit('resistor_tail',999))
        self.invalid('rlc-harmonic',self.edit('resistor_head',0))
        self.invalid('rlc-harmonic',lambda m,b:m['fields']['resistor_tail'].update(dtype='float64'))
        self.invalid('rlc-harmonic',lambda m,b:m['conditions'].append(deepcopy(m['conditions'][0])))
        self.invalid('rlc-harmonic',lambda m,b:next(c for c in m['conditions'] if c['operator']=='voltage_source').update(role='boundary'))
        self.valid('rlc-harmonic',self.edit('resistor_tail',[[[0],[0]]]))
        def disconnected(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['payload_resistor_tail'][:]=0;h['payload_resistor_head'][:]=7
        self.invalid('rlc-harmonic',disconnected)
        def reverse(m,b):
            with h5py.File(b/'input.h5','r+') as h:
                x=h['payload_resistor_tail'][:];h['payload_resistor_tail'][:]=h['payload_resistor_head'][:];h['payload_resistor_head'][:]=x
        self.valid('rlc-harmonic',reverse)
        def source_cycle(m,b):
            c=next(c for c in m['conditions'] if c['operator']=='current_source');c['operator']='voltage_source';s=m['fields']['current_source_value'];s['unit']='V'
            with h5py.File(b/'input.h5','r+') as h:h['payload_current_source_tail'][:]=0;h['payload_current_source_head'][:]=23
        self.invalid('rlc-harmonic',source_cycle)
    def test_maxwell_and_coil_scope(self):
        self.invalid('maxwell-cavity',lambda m,b:m['conditions'].append(dict(role='boundary',variable='electric_field',operator='dirichlet',location='fixed',data={'value':{'value':0.,'unit':'V/m'}})))
        self.invalid('coil-circuit',self.edit('winding_value',0.))
        self.valid('coil-circuit',self.edit('winding_value',[[[1.],[-1.]]]))
        self.invalid('coil-circuit',lambda m,b:m['outputs']['observation_coil_current'].update(location='cells'))
        self.invalid('maxwell-cavity',lambda m,b:m['outputs']['observation_electric_field'].update(value_kind='point'))
        # Public graph and mesh fields cannot be silently exchanged for coordinate probes.
        self.invalid('rlc-harmonic',lambda m,b:m.update(spatial_dimension=3))
    def test_actual_policies_resource_consumers_and_public_closure(self):
        spec=importlib.util.spec_from_file_location('em_prepare',ROOT/'src/utils/prepare_harbor.py');prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);task=task_directory(slug,ROOT);policy=author_policy(task,p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    q=s['quantity'];expected=({'potential':1e-6,'node_voltage':1e-6,'branch_voltage':1e-6,'electrode_potential':1e-6,'electric_displacement':1e-10,'vector_potential':1e-9,'magnetic_flux_density':1e-8,'coil_current':1e-8,'branch_current':1e-8,'flux_linkage':1e-9,'joule_loss':1e-8}.get(q,1e-7),.005)
                    self.assertEqual((bound['fields'][name]['atol'],bound['fields'][name]['rtol']),expected)
                    actual=deepcopy(ref);tol=bound['fields'][name]['atol'];actual[s['array']][:]=tol
                    self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(tol,np.inf)
                    self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],0)
                    nonzero=deepcopy(ref);nonzero[s['array']][:]=100.;actual=deepcopy(nonzero)
                    edge=100.+expected[0]+100.*expected[1]
                    if edge-100.>expected[0]+100.*expected[1]:edge=np.nextafter(edge,-np.inf)
                    actual[s['array']][:]=edge
                    self.assertEqual(grade_arrays(p,actual,nonzero,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(actual[s['array']].flat[0],np.inf)
                    self.assertEqual(grade_arrays(p,actual,nonzero,policy=policy)['score'],0)
                config=json.loads((task/'judge-config.json').read_text());override=tomllib.loads((task/'harbor/task.toml').read_text());merged=tomllib.loads(prepare.task_config(template,override,judge_config=config,case_count=3))
                self.assertEqual(config['timeout_seconds'],AUTHOR_MODELS[slug]['timeout']);self.assertIsNone(config['max_output_bytes'])
                self.assertEqual(merged['environment']['memory_mb'],8192);self.assertEqual(merged['environment']['cpus'],4);self.assertEqual(merged['environment']['gpus'],0)
                self.assertEqual(merged['agent']['timeout_sec'],3600);self.assertEqual(merged['environment']['build_timeout_sec'],1800)
                self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate');self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(AUTHOR_MODELS[slug]['timeout']+120)))
                self.assertEqual((task/'harbor/requirements.txt').read_text().strip(),'scipy==1.18.1')
                bad=deepcopy(ref);bad.pop(next(iter(m['outputs'].values()))['array'])
                self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0);self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
        files,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'electromagnetic.linear'})
        self.assertFalse(any(any(v in name for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in files))

if __name__=='__main__':unittest.main()
