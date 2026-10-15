"""Acoustic public declarations and tooling; no trusted numerical solutions."""
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
from acoustic_fixture import fixture
from caeoj_ext.acoustic import models,helmholtz_hessian
from caeoj.sdk import load_problem,write_result
from caeoj.validation import validate_input,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class AcousticTests(unittest.TestCase):
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
    def test_kernel_hand_values_and_helmholtz_identity(self):
        np.testing.assert_allclose(helmholtz_hessian([2.,0.,0.],0.),np.diag([2.,-1.,-1.])/(32*np.pi))
        x=np.array([[1.,2.,3.],[2.,-.1,.4]]);r=np.linalg.norm(x,axis=1);k=1.7;h=helmholtz_hessian(x,k)
        np.testing.assert_allclose(h,np.swapaxes(h,-1,-2));np.testing.assert_allclose(np.trace(h,axis1=-2,axis2=-1),-k*k*np.exp(-1j*k*r)/(4*np.pi*r))
        for x,k in [([0.,0.,0.],1.),([1.,2.],1.),([1.,0.,0.],-1.),([np.nan,1.,0.],1.)]:
            with self.assertRaises(ValueError):helmholtz_hessian(x,k)
    def test_metadata_reconstruction_units_and_scalar_constants(self):
        for mutate in [lambda m,b:m['physics']['parameters']['frequency'].update(value=0.),lambda m,b:m.update(task='acoustic-transient'),lambda m,b:m['fields']['material_density'].update(unit='kg'),lambda m,b:m['fields']['material_density'].update(quantity='pressure'),lambda m,b:m['fields']['volume_source_value']['sampling'].update(time='linear'),lambda m,b:m['fields']['volume_source_value'].update(components=['imag','real']),lambda m,b:m['fields']['material_density'].update(value_kind='integral')]:self.invalid('acoustic-harmonic',mutate)
        self.invalid('thermoviscous-acoustics',lambda m,b:m['physics']['parameters']['gamma'].update(value=1.))
        self.invalid('thermoviscous-acoustics',lambda m,b:m['physics']['parameters']['viscosity'].update(value=0.))
        self.invalid('rigid-scattering',lambda m,b:m['physics']['parameters']['direction_x'].update(value=2.))
        self.invalid('modal-vibroacoustics',lambda m,b:m['physics']['parameters']['mode_count'].update(value=True))
        def constant(m,b):
            c=next(c for c in m['conditions'] if c['operator']=='material');ref=c['data']['density']['field'];key=m['fields'].pop(ref)['array'];c['data']['density']={'value':1.,'unit':'kg/m3'}
            with h5py.File(b/'input.h5','r+') as h:del h[key]
        self.valid('acoustic-harmonic',constant)
        def marker(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['harmonic_times'][:]=1.
        self.invalid('surface-radiation',marker)
    def test_passivity_and_full_tensor_symmetry(self):
        for key in ('density','compressibility'):
            self.invalid('equivalent-fluid',self.edit('material_'+key,[1.,.1]));self.invalid('equivalent-fluid',self.edit('material_'+key,[0.,-.1]))
        def impedance(z):
            def change(m,b):
                s=deepcopy(m['fields']['volume_source_value']);s.update(array='z',quantity='impedance',unit='Pa.s/m',location='wall');m['fields']['z']=s
                drive=deepcopy(s);drive.update(array='drive',quantity='drive',unit='Pa');m['fields']['drive']=drive
                m['conditions'].append(dict(role='boundary',variable='normal_velocity',operator='impedance',location='wall',data=dict(impedance={'field':'z'},drive={'field':'drive'})))
                with h5py.File(b/'input.h5','r+') as h:h['z']=np.array([[z]],dtype=float);h['drive']=np.zeros((1,1,2))
            return change
        self.valid('acoustic-harmonic',impedance([0.,1.]));self.invalid('acoustic-harmonic',impedance([-1.,0.]));self.invalid('acoustic-harmonic',impedance([0.,0.]))
        def tensor(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['payload_lighthill_tensor_value'][0,0,0,1,1]=1.
        self.invalid('lighthill-radiation',tensor)
        self.valid('lighthill-radiation',self.edit('lighthill_tensor_value',np.stack([np.eye(3),np.eye(3)],axis=-1)))
    def test_receivers_closed_surface_and_orientation(self):
        def receiver(x):
            def change(m,b):
                with h5py.File(b/'input.h5','r+') as h:h['receiver_coordinates'][0]=x
            return change
        for slug in ('surface-radiation','rigid-scattering','lighthill-radiation'):
            self.invalid(slug,receiver([.1,.1,.1]));self.invalid(slug,receiver([0.,0.,0.]));self.valid(slug,receiver([2.,2.,2.]))
        def reverse(m,b):
            # ASCII MSH4.1: reverse every surface triangle connectivity.
            p=b/'mesh.msh';lines=p.read_text().splitlines();start=lines.index('$Elements');end=lines.index('$EndElements');i=start+2
            while i<end:
                dim,tag,typ,count=map(int,lines[i].split());i+=1
                for j in range(count):
                    row=lines[i+j].split();lines[i+j]=' '.join(row[:1]+list(reversed(row[1:])))
                i+=count
            p.write_text('\n'.join(lines)+'\n')
        self.invalid('surface-radiation',reverse)
    def test_periodic_pair_coverage_geometry_and_initial_state(self):
        self.invalid('uniform-flow-acoustics',lambda m,b:m['physics']['parameters']['mean_x'].update(value=1.))
        self.invalid('uniform-flow-acoustics',lambda m,b:next(c for c in m['conditions'] if c['operator']=='periodic')['data'].update(partner={'location':'x_minus'}))
        self.invalid('uniform-flow-acoustics',lambda m,b:next(c for c in m['conditions'] if c['operator']=='periodic')['data'].update(partner={'location':'y_plus'}))
        self.invalid('uniform-flow-acoustics',lambda m,b:m['conditions'].pop())
        def nonperiodic(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['payload_initial_pressure_value'][0,0,0]=1.
        self.invalid('uniform-flow-acoustics',nonperiodic)
        self.invalid('acoustic-transient',lambda m,b:m['fields']['volume_source_value']['sampling'].update(time='previous'))
    def test_modal_positivity_independence_and_wall_outputs(self):
        for key in ('mass','stiffness'):self.invalid('modal-vibroacoustics',self.edit('structure_'+key,-1.))
        self.invalid('modal-vibroacoustics',self.edit('structure_damping',-1.));self.invalid('modal-vibroacoustics',self.edit('modal_wall_shape',0.))
        self.invalid('modal-vibroacoustics',lambda m,b:m['outputs'].pop('observation_modal_displacement'))
        self.invalid('resonator-wall',lambda m,b:m['outputs'].pop('observation_wall_velocity'))
        self.invalid('resonator-wall',self.edit('resonator_damping',-1.))
        def overlap(m,b):
            m['conditions'].append(dict(role='boundary',variable='normal_velocity',operator='normal_velocity',location='wall',data={'value':{'value':0.,'unit':'m/s'}}))
        self.invalid('resonator-wall',overlap)
        self.invalid('thermoviscous-acoustics',lambda m,b:next(c for c in m['conditions'] if c['operator']=='wall_velocity').update(location='wall'))
    def test_actual_policies_resource_consumers_and_public_closure(self):
        spec=importlib.util.spec_from_file_location('acoustic_prepare',ROOT/'src/utils/prepare_harbor.py');prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);task=task_directory(slug,ROOT);policy=task_policy(task,p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    q=s['quantity'];expected=(1e-5,.01) if q in ('pressure','scattered_pressure') else (1e-7,.01)
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
                self.assertEqual(config['timeout_seconds'],cfg['timeout']);self.assertIsNone(config['max_output_bytes'])
                self.assertEqual(merged['environment']['memory_mb'],6144);self.assertEqual(merged['environment']['cpus'],4);self.assertEqual(merged['environment']['gpus'],0)
                self.assertEqual(merged['agent']['timeout_sec'],3600);self.assertEqual(merged['environment']['build_timeout_sec'],1800)
                self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate');self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(cfg['timeout']+60)))
                self.assertEqual((task/'harbor/requirements.txt').read_text().strip(),'scipy==1.18.1')
                bad=deepcopy(ref);bad.pop(next(iter(m['outputs'].values()))['array'])
                self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0);self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
        files,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'acoustic.linear'})
        self.assertFalse(any(any(v in name for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in files))

if __name__=='__main__':unittest.main()
