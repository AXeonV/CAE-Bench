"""Public microstructure declaration/tool validation, not physical reference tests."""
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
from microstructure_fixture import fixture
from caeoj_ext.microstructure import models
from caeoj.sdk import load_problem,write_result
from caeoj.validation import validate_input,validate_output,output_support
from grading_fixtures import evaluate_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.grading_policy import author_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.assembly import runtime_materials

ROOT=Path(__file__).resolve().parents[1]


class MicrostructureTests(unittest.TestCase):
    def changed(self,slug,mutate):
        with tempfile.TemporaryDirectory() as tmp:
            path,m=fixture(tmp,slug);mutate(m,path.parent)
            path.write_text(json.dumps(m),encoding='utf-8');return validate_input(path)

    def valid(self,slug,mutate):
        r=self.changed(slug,mutate);self.assertTrue(r['valid'],r)

    def invalid(self,slug,mutate):
        r=self.changed(slug,mutate);self.assertFalse(r['valid'],r);self.assertTrue(r['errors'])

    @staticmethod
    def edit(key,value):
        def mutate(m,b):
            with h5py.File(b/'input.h5','r+') as h:h['payload_'+key][:]=value
        return mutate

    @staticmethod
    def param(key,value):
        return lambda m,b:m['physics']['parameters'][key].update(value=value)

    def test_models_sdk_identity_aliases_and_grain_counts(self):
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path)
                values={s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),
                    len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                result=Path(tmp)/'result.h5';write_result(result,p,values)
                self.assertTrue(validate_output(path,result)['valid'])
            self.valid(slug,lambda m,b:m.pop('task'))
            self.valid(slug,lambda m,b:m['conditions'].reverse())
        for count in (2,6):
            with tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,'grain-coarsening',grain_count=count)
                self.assertTrue(validate_input(path)['valid'])
        def duplicate(m,b):
            name=next(iter(m['outputs']));s=deepcopy(m['outputs'][name]);s['array']='another_answer'
            m['outputs']['another_observation']=s
        self.valid('binary-separation',duplicate)

    def test_exact_fields_shapes_units_references_and_parameters(self):
        self.invalid('grain-coarsening',self.param('grain_count',True))
        self.invalid('grain-coarsening',self.param('grain_count',2.0))
        self.invalid('grain-coarsening',self.param('competition',1.))
        self.invalid('binary-separation',lambda m,b:m['physics']['parameters'].pop('gradient'))
        self.invalid('binary-separation',lambda m,b:m['physics'].update(model='microstructure-unknown-v1'))
        self.invalid('binary-separation',lambda m,b:m['fields']['series_wave'].update(unit='1/m'))
        self.invalid('binary-separation',lambda m,b:m['fields']['series_wave'].update(components=['c2','c1']))
        self.invalid('binary-separation',lambda m,b:m['fields']['series_amplitude']['sampling'].update(space='piecewise_linear'))
        self.invalid('binary-separation',lambda m,b:m['conditions'][0]['data'].update(value={'value':0,'unit':'1'}))
        self.invalid('binary-separation',lambda m,b:m['conditions'][0]['data'].update(value={'field':'absent'}))
        self.invalid('binary-separation',lambda m,b:m['conditions'].pop())
        self.invalid('binary-separation',lambda m,b:m['conditions'].append(deepcopy(m['conditions'][0])))
        self.invalid('grain-coarsening',lambda m,b:m['outputs']['observation_order_parameters'].update(unit='J'))
        self.invalid('crystal-density',lambda m,b:m['outputs']['observation_chemical_potential'].update(location='system'))

    def test_mode_normalization_initial_bounds_and_signed_coefficients(self):
        self.invalid('binary-separation',self.edit('series_wave',[[0,0],[0,2]]))
        self.invalid('binary-separation',self.edit('series_wave',[[-1,1],[0,2]]))
        self.invalid('binary-separation',self.edit('series_wave',[[1,.5],[0,2]]))
        self.invalid('binary-separation',self.edit('series_wave',[[1,-1],[1,-1]]))
        self.invalid('binary-separation',self.edit('series_wave',[[9,1],[0,2]]))
        self.valid('binary-separation',self.edit('series_wave',[[8,-8],[0,1]]))
        self.valid('binary-separation',self.edit('series_amplitude',[[[-.1,.1]],[[.1,-.1]]]))
        self.valid('binary-separation',self.edit('series_amplitude',0.))
        self.invalid('binary-separation',self.edit('series_amplitude',.6))
        self.invalid('ternary-separation',self.edit('offset_value',[.5,.5]))
        self.invalid('ternary-separation',self.edit('offset_value',[-.1,.3]))
        self.invalid('grain-coarsening',self.edit('offset_value',0.))
        self.valid('grain-coarsening',self.edit('offset_value',.5))  # no sum-eta constraint
        self.valid('crystal-density',self.edit('offset_value',-.5))

    def test_periodic_coordinates_and_independent_time_axes(self):
        def coordinates(v):
            def mutate(m,b):
                with h5py.File(b/'input.h5','r+') as h:h['probe_coordinates'][:]=v
            return mutate
        self.valid('order-relaxation',coordinates([[0,0],[.8e-6,1.8e-6],[0,0]]))
        self.invalid('order-relaxation',coordinates([[1e-6,0],[.8e-6,1.8e-6],[0,0]]))
        self.invalid('order-relaxation',coordinates([[-1e-12,0],[.8e-6,1.8e-6],[0,0]]))
        def times(key,v):
            def mutate(m,b):
                with h5py.File(b/'input.h5','r+') as h:h[key][:]=v
            return mutate
        self.valid('driven-ordering',times('request_times',[.1,.8,1.]))
        self.invalid('driven-ordering',times('control_times',[.01,.25,1.]))
        self.invalid('driven-ordering',times('control_times',[0.,.25,1.1]))
        self.invalid('binary-separation',times('static_times',[1.]))
        self.invalid('binary-separation',times('request_times',[-.1,.5,1.]))

    def test_material_spd_and_public_dimensionless_limits(self):
        self.valid('ternary-separation',self.edit('mobility_value',[[1e-13,-5e-14],[-5e-14,1e-13]]))
        self.invalid('ternary-separation',self.edit('mobility_value',[[1e-13,2e-14],[0,1e-13]]))
        self.invalid('ternary-separation',self.edit('mobility_value',[[1e-13,2e-13],[2e-13,1e-13]]))
        self.invalid('ternary-separation',self.edit('mobility_value',[[1e-13,1e-13],[1e-13,1e-13]]))
        self.invalid('ternary-separation',self.edit('mobility_value',[[1e-13,0],[0,1e-16]]))
        self.valid('ternary-separation',self.edit('mobility_value',[[1e-12,0],[0,1e-12]]))
        self.invalid('ternary-separation',self.edit('mobility_value',[[1.1e-12,0],[0,1.1e-12]]))
        self.invalid('order-relaxation',self.param('length_x',1e-200))  # review overflow counterexample
        self.invalid('order-relaxation',self.param('length_y',5e-6))
        self.valid('order-relaxation',self.param('gradient',2.5e-15))
        self.valid('order-relaxation',self.param('gradient',1e-13))
        self.invalid('order-relaxation',self.param('gradient',2.4e-15))
        self.invalid('order-relaxation',self.param('relaxation',11.))
        self.invalid('binary-separation',self.param('mobility',1.1e-12))
        self.valid('binary-separation',self.param('mobility_contrast',0.))
        self.invalid('binary-separation',self.param('mobility_contrast',4.1))
        self.invalid('driven-ordering',self.edit('history_value',2.1))
        self.valid('driven-ordering',self.edit('history_value',-2.))
        self.invalid('coupled-precipitation',self.param('coupling_energy',11.))
        self.invalid('crystal-density',self.param('length_scale',.3e-6))
        self.invalid('crystal-density',self.param('mobility',.3e-12))

    def test_actual_grading_resources_templates_and_public_closure(self):
        spec=importlib.util.spec_from_file_location('microstructure_prepare',ROOT/'src/utils/prepare_harbor.py')
        prepare=importlib.util.module_from_spec(spec);sys.path.insert(0,str(ROOT/'src/utils'))
        try:spec.loader.exec_module(prepare)
        finally:sys.path.pop(0)
        template=(ROOT/'src/utils/harbor/task.toml').read_text(encoding='utf-8')
        timeouts={'binary-separation':900,'ternary-separation':1200,'order-relaxation':300,
            'driven-ordering':450,'grain-coarsening':1200,'coupled-precipitation':1200,'crystal-density':1800}
        for slug in models():
            with self.subTest(slug=slug),tempfile.TemporaryDirectory() as tmp:
                path,m=fixture(tmp,slug);p=load_problem(path);task=task_directory(slug,ROOT)
                policy=author_policy(task,p);bound=resolve_policy(policy,p)
                ref={s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),
                    len(p.arrays[m['locations'][s['location']]['ids']]),*s['component_shape'])) for s in m['outputs'].values()}
                ref.update({k:p.arrays[k].copy() for k in output_support(p)})
                self.assertEqual(evaluate_arrays(p,ref,ref,policy=policy)['score'],1)
                for name,s in m['outputs'].items():
                    atol=1e-5 if s['unit']=='1' else 1e-7;rtol=.005
                    self.assertEqual((bound['fields'][name]['atol'],bound['fields'][name]['rtol']),(atol,rtol))
                    actual=deepcopy(ref);actual[s['array']][:]=atol
                    self.assertEqual(evaluate_arrays(p,actual,ref,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(atol,np.inf)
                    self.assertEqual(evaluate_arrays(p,actual,ref,policy=policy)['score'],0)
                    nonzero=deepcopy(ref);nonzero[s['array']][:]=100.
                    actual=deepcopy(nonzero);edge=100.+atol+100.*rtol
                    if edge-100.>atol+100.*rtol:edge=np.nextafter(edge,-np.inf)
                    actual[s['array']][:]=edge
                    self.assertEqual(evaluate_arrays(p,actual,nonzero,policy=policy)['score'],1)
                    actual[s['array']].flat[0]=np.nextafter(edge,np.inf)
                    self.assertEqual(evaluate_arrays(p,actual,nonzero,policy=policy)['score'],0)
                bad=deepcopy(ref);bad.pop(next(iter(m['outputs'].values()))['array'])
                self.assertEqual(evaluate_arrays(p,bad,ref,policy=policy)['score'],0)
                self.assertIsNone(evaluate_arrays(p,ref,bad,policy=policy)['score'])
                config=json.loads((task/'judge-config.json').read_text(encoding='utf-8'));override=tomllib.loads((task/'harbor/task.toml').read_text(encoding='utf-8'))
                merged=tomllib.loads(prepare.task_config(template,override,judge_config=config,case_count=3))
                self.assertEqual(config['timeout_seconds'],timeouts[slug]);self.assertIsNone(config['max_output_bytes'])
                self.assertEqual(merged['environment']['cpus'],2);self.assertEqual(merged['environment']['memory_mb'],4096)
                self.assertEqual(merged['environment']['gpus'],0);self.assertEqual(merged['agent']['timeout_sec'],3600)
                self.assertEqual(merged['environment']['build_timeout_sec'],1800)
                self.assertEqual(merged['verifier']['network_mode'],'no-network');self.assertEqual(merged['verifier']['environment_mode'],'separate')
                self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(timeouts[slug]+120)))
                instruction=(task/'instruction.md').read_text(encoding='utf-8')
                self.assertNotIn('{c[',instruction);self.assertNotIn('{tolerances}',instruction)
                self.assertIn(str(timeouts[slug])+'秒墙钟',instruction)
                self.assertEqual((task/'harbor/requirements.txt').read_text(encoding='utf-8').strip(),'scipy==1.18.1')
        files,runtime=runtime_materials({slug:task_directory(slug,ROOT) for slug in models()},ROOT)
        self.assertEqual(set(runtime['extensions']),{'microstructure.phase_field'})
        self.assertFalse(any(any(k in name for k in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in files))


if __name__=='__main__':unittest.main()
