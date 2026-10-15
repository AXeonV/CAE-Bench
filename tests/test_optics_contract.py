"""Optical public declarations and tooling; no trusted numerical solutions."""
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
from optics_fixture import fixture
from caeoj_ext.optics import models
from caeoj.sdk import load_problem,write_result
from caeoj.validation import validate_input,validate_output,output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.assembly import runtime_materials
ROOT=Path(__file__).resolve().parents[1]


class OpticsTests(unittest.TestCase):
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
    def test_scalar_constants_units_shapes_and_sampling(self):
        def constant(m,b):
            c=next(c for c in m['conditions'] if c['operator']=='layers');ref=c['data']['thickness']['field'];key=m['fields'].pop(ref)['array'];c['data']['thickness']={'value':1.,'unit':'m'}
            with h5py.File(b/'input.h5','r+') as h:del h[key]
        self.valid('thin-film',constant)
        self.invalid('thin-film',lambda m,b:m['fields']['layers_index'].update(unit='m'))
        self.invalid('fresnel-aperture',lambda m,b:m['fields']['aperture_field_value'].update(value_kind='integral'))
        self.invalid('partial-coherence',lambda m,b:m['fields']['coherence_value'].update(quantity='centered_covariance'))
        self.invalid('jones-chain',lambda m,b:m['fields']['elements_value']['sampling'].update(space='piecewise_linear'))
        self.invalid('coherent-interference',lambda m,b:m['fields']['waves_amplitude'].update(components=['imag','real']))
    def test_directions_critical_incidence_and_launch_plane(self):
        self.invalid('layered-rays',self.edit('launch_origin',[0.,0.,1.]))
        self.invalid('layered-rays',self.edit('launch_direction',[0.,0.,-1.]))
        self.invalid('coherent-interference',self.edit('waves_direction',[1.,0.,1.]))
        self.invalid('farfield-aperture',self.edit('directions_value',[0.,0.,-1.]))
        def critical(m,b):
            m['physics']['parameters']['input_index']['value']=1.5
            self.edit('launch_direction',[2/3,0.,np.sqrt(5)/3])(m,b)
        self.invalid('layered-rays',critical)
        def tir(m,b):
            m['physics']['parameters']['input_index']['value']=2.
            self.edit('launch_direction',[.9,0.,np.sqrt(.19)])(m,b)
        self.valid('layered-rays',tir)
    def test_coherence_hermitian_and_psd_hand_matrices(self):
        # Hand eigenvalues of [[1,i],[-i,1]] are 0,2; [[1,2],[2,1]] gives -1,3.
        good=np.array([[[1.,0.],[0.,1.]],[[0.,-1.],[1.,0.]]])
        self.valid('partial-coherence',self.edit('coherence_value',good))
        self.valid('partial-coherence',self.edit('coherence_value',good*1e200))
        bad=np.array([[[1.,0.],[2.,0.]],[[2.,0.],[1.,0.]]]);self.invalid('partial-coherence',self.edit('coherence_value',bad))
        self.invalid('partial-coherence',self.edit('coherence_value',bad*1e200))
        bad=good.copy();bad[1,0,1]=1.;self.invalid('partial-coherence',self.edit('coherence_value',bad))
        self.valid('partial-coherence',self.edit('coherence_value',0.))
        self.invalid('partial-coherence',lambda m,b:m['physics']['parameters']['wave_count'].update(value=True))
    def test_jones_passivity_includes_singular_and_zero_states(self):
        self.valid('jones-chain',self.edit('elements_value',0.))
        self.valid('jones-chain',self.edit('states_value',0.))
        unitary=np.zeros((2,2,2));unitary[0,1,1]=1.;unitary[1,0,1]=1.
        self.valid('jones-chain',self.edit('elements_value',unitary))
        gain=unitary*1.01;self.invalid('jones-chain',self.edit('elements_value',gain))
    def test_optical_layer_ranges_modes_and_reference_axes(self):
        self.invalid('thin-film',self.edit('layers_thickness',0.))
        self.invalid('thin-film',self.edit('layers_index',.1))
        self.invalid('thin-film',lambda m,b:m['physics']['parameters']['incidence_sine'].update(value=1.))
        self.invalid('thin-film',lambda m,b:m['physics']['parameters']['polarization'].update(value=2))
        self.invalid('slab-modes',self.edit('layers_index',1.))
        self.invalid('slab-modes',lambda m,b:m['physics']['parameters']['mode_count'].update(value=2.0))
        self.invalid('slab-modes',lambda m,b:m['outputs']['observation_mode_profile'].update(unit='V/m'))
        self.invalid('slab-modes',lambda m,b:m['outputs']['observation_effective_index'].update(location='receivers'))
        def marker(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['marker'][:]=1.
        self.invalid('thin-film',marker)
    def test_aperture_points_identity_and_disconnected_support(self):
        def receiver(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['receivers_coordinates'][0,2]=0.
        self.invalid('fresnel-aperture',receiver)
        self.invalid('farfield-aperture',lambda m,b:m['outputs']['observation_radiant_intensity'].update(unit='W/m2'))
        self.invalid('fresnel-aperture',lambda m,b:m['outputs']['observation_amplitude'].update(location='aperture'))
        def disconnected(m,b):
            import gmsh
            tags=[13,31,59,83,107,131];xyz=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[3.,0.,0.],[4.,0.,0.],[3.,1.,0.]])
            gmsh.initialize([],readConfigFiles=False)
            try:
                gmsh.option.setNumber('General.Terminal',0);gmsh.model.add('disconnected_aperture');e=gmsh.model.addDiscreteEntity(2);gmsh.model.mesh.addNodes(2,e,tags,xyz.ravel());gmsh.model.mesh.addElementsByType(e,2,[101,149],tags);gmsh.option.setNumber('Mesh.MshFileVersion',4.1);gmsh.option.setNumber('Mesh.Binary',0);gmsh.write(str(b/'mesh.msh'))
            finally:gmsh.finalize()
            with h5py.File(b/'input.h5','r+') as h:del h['domain_ids'];h['domain_ids']=np.array(tags,dtype='int64')
        self.valid('fresnel-aperture',disconnected)
    def test_actual_policies_resource_consumers_and_public_closure(self):
        spec=importlib.util.spec_from_file_location('optics_prepare',ROOT/'src/utils/prepare_harbor.py');prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text()
        for slug,cfg in models().items():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);task=task_directory(slug,ROOT);policy=task_policy(task,p);bound=resolve_policy(policy,p)
                ref={k:p.arrays[k].copy() for k in output_support(p)}
                for s in m['outputs'].values():ref[s['array']]=np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape']))
                for name,s in m['outputs'].items():
                    q=s['quantity'];expected=({'terminal_position':(1e-8,0.),'terminal_direction':(1e-8,0.),'optical_path':(1e-8,1e-6),'termination':(0.,0.),'amplitude':(1e-6,.005),'intensity':(1e-8,.005),'far_amplitude':(1e-8,.005),'radiant_intensity':(1e-9,.005),'jones':(1e-6,.005),'stokes':(1e-7,.005),'reflection':(1e-7,.002),'transmission':(1e-7,.002),'reflectance':(1e-8,.002),'transmittance':(1e-8,.002),'effective_index':(1e-7,0.),'mode_profile':(1e-5,.005)}[q])
                    self.assertEqual((bound['fields'][name]['atol'],bound['fields'][name]['rtol']),expected)
                    actual=deepcopy(ref);tol=bound['fields'][name]['atol'];actual[s['array']][:]=tol
                    self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(tol,np.inf)
                    self.assertEqual(grade_arrays(p,actual,ref,policy=policy)['score'],0)
                    nonzero=deepcopy(ref);baseline=1. if q=='termination' else 100.;nonzero[s['array']][:]=baseline;actual=deepcopy(nonzero)
                    edge=baseline+expected[0]+baseline*expected[1]
                    if edge-baseline>expected[0]+baseline*expected[1]:edge=np.nextafter(edge,-np.inf)
                    actual[s['array']][:]=edge
                    self.assertEqual(grade_arrays(p,actual,nonzero,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(actual[s['array']].flat[0],np.inf)
                    self.assertEqual(grade_arrays(p,actual,nonzero,policy=policy)['score'],0)
                config=json.loads((task/'judge-config.json').read_text());override=tomllib.loads((task/'harbor/task.toml').read_text());merged=tomllib.loads(prepare.task_config(template,override,judge_config=config,case_count=3))
                self.assertEqual(config['timeout_seconds'],cfg['timeout']);self.assertIsNone(config['max_output_bytes'])
                self.assertEqual(merged['environment']['memory_mb'],4096);self.assertEqual(merged['environment']['cpus'],2);self.assertEqual(merged['environment']['gpus'],0)
                self.assertEqual(merged['agent']['timeout_sec'],3600);self.assertEqual(merged['environment']['build_timeout_sec'],1800)
                self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate');self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(cfg['timeout']+60)))
                self.assertEqual((task/'harbor/requirements.txt').read_text().strip(),'scipy==1.18.1')
                bad=deepcopy(ref);bad.pop(next(iter(m['outputs'].values()))['array'])
                self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0);self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
        files,runtime=runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'optics.linear'})
        self.assertFalse(any(any(v in name for v in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in files))

if __name__=='__main__':unittest.main()
