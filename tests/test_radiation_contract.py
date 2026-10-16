"""Radiation contract/tool regression, not numerical-physics validation."""
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
from radiation_fixture import fixture
from caeoj_ext.radiation import models
from caeoj.sdk import load_problem, write_result
from caeoj.validation import validate_input, validate_output, output_support
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.task_paths import task_directory
from caeoj_tools.assembly import runtime_materials

ROOT = Path(__file__).resolve().parents[1]


class RadiationTests(unittest.TestCase):
    def changed(self, slug, mutate):
        with tempfile.TemporaryDirectory() as tmp:
            path, manifest = fixture(tmp, slug)
            mutate(manifest, path.parent)
            path.write_text(json.dumps(manifest), encoding='utf-8')
            return validate_input(path)

    def valid(self, slug, mutate):
        r = self.changed(slug, mutate)
        self.assertTrue(r['valid'], r)

    def invalid(self, slug, mutate):
        r = self.changed(slug, mutate)
        self.assertFalse(r['valid'], r)
        self.assertTrue(r['errors'], r)

    @staticmethod
    def edit(key, values):
        def mutate(m, b):
            with h5py.File(b/'input.h5', 'r+') as h:
                h['payload_'+key][:] = values
        return mutate

    def test_all_models_sdk_roundtrip_and_optional_task(self):
        for slug in models():
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as tmp:
                path, m = fixture(tmp, slug)
                p = load_problem(path)
                outputs = {s['array']: np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),
                    len(p.arrays[m['locations'][s['location']]['ids']]), *s['component_shape']))
                    for s in m['outputs'].values()}
                write_result(Path(tmp)/'result.h5', p, outputs)
                self.assertTrue(validate_output(path, Path(tmp)/'result.h5')['valid'])
            self.valid(slug, lambda m,b: m.pop('task'))

    def test_public_typed_contract_and_diagnostics(self):
        self.invalid('photon-absorption', lambda m,b: m['physics']['parameters']['group_count'].update(value=True))
        self.invalid('photon-absorption', lambda m,b: m['physics']['parameters']['group_count'].update(value=2.0))
        self.invalid('photon-absorption', lambda m,b: m['physics']['parameters'].pop('group_count'))
        self.invalid('photon-absorption', lambda m,b: m['physics'].update(model='radiation-unknown-v1'))
        self.invalid('photon-absorption', lambda m,b: m['fields']['beam_energy'].update(unit='eV'))
        self.invalid('photon-absorption', lambda m,b: m['fields']['beam_energy'].update(components=['c2','c1']))
        self.invalid('photon-absorption', lambda m,b: m['conditions'][0]['data'].update(width={'value':1,'unit':'m'}))
        self.invalid('point-kinetics', lambda m,b: m['conditions'][-1]['data'].update(source={'field':'missing'}))
        self.invalid('point-kinetics', lambda m,b: m['fields']['history_source']['sampling'].update(time='previous'))
        self.invalid('decay-network', lambda m,b: m['outputs']['observation_activity'].update(unit='1/s'))
        self.invalid('decay-network', lambda m,b: m['outputs']['observation_activity'].update(location='nuclides'))
        self.invalid('decay-network', lambda m,b: m['conditions'].append(deepcopy(m['conditions'][0])))
        self.invalid('decay-network', lambda m,b: m['conditions'].pop())

    def test_slab_identity_interfaces_and_physical_values(self):
        self.valid('photon-absorption', self.edit('absorption_sigma', 0.))
        self.invalid('photon-absorption', self.edit('absorption_sigma', -1.))
        self.invalid('photon-absorption', self.edit('beam_energy', 0.))
        self.invalid('slab-transport-steady', self.edit('incoming_left', -1.))
        self.invalid('slab-transport-steady', self.edit('medium_absorption', 0.))
        self.invalid('slab-transport-steady', self.edit('medium_scatter', -1.))
        # Up-scattering, self-scattering and nonsymmetric transfer are all supported.
        self.valid('slab-transport-steady', self.edit('medium_scatter', [[.3,.8],[.1,.2]]))
        self.invalid('slab-transport-transient', self.edit('speed_value', 0.))
        self.valid('slab-transport-transient', self.edit('initial_value', 3.))
        self.invalid('neutron-diffusion-source', self.edit('medium_diffusion', 0.))
        self.invalid('neutron-diffusion-critical', self.edit('medium_production', 0.))
        self.invalid('neutron-diffusion-critical', self.edit('medium_spectrum', .4))
        def probes(x):
            def mutate(m,b):
                with h5py.File(b/'input.h5','r+') as h:
                    h['probes_coordinates'][:] = [[x],[1.7]]
            return mutate
        self.invalid('neutron-diffusion-source', probes(1.))
        self.invalid('neutron-diffusion-source', probes(0.))
        self.invalid('neutron-diffusion-source', probes(2.))
        self.invalid('neutron-diffusion-source', probes(1e-11))
        self.valid('neutron-diffusion-source', probes(1e-8))
        self.valid('neutron-diffusion-source', probes(1.9))  # order follows IDs, not x

    def test_independent_times_initial_state_and_kinetics(self):
        self.invalid('point-kinetics', self.edit('precursors_fraction', .6))
        self.invalid('point-kinetics', self.edit('precursors_decay', 0.))
        self.invalid('point-kinetics', self.edit('history_reactivity', .51))
        self.valid('point-kinetics', self.edit('history_reactivity', -.5))
        self.valid('point-kinetics', self.edit('initial_precursor_state', 0.))
        def change_times(name, v):
            def mutate(m,b):
                with h5py.File(b/'input.h5','r+') as h:
                    h[name][:] = v
            return mutate
        self.valid('point-kinetics', change_times('requested_times', [.1,.4,1.]))
        self.invalid('point-kinetics', change_times('requested_times', [-.1,.4,1.]))
        self.invalid('point-kinetics', change_times('control_times', [.01,.25,1.]))
        self.invalid('point-kinetics', change_times('control_times', [0.,.25,1.1]))
        self.invalid('slab-transport-steady', change_times('marker', [1.]))

    def test_inventory_branch_direction_cycles_stable_and_leakage(self):
        # Independently selected matrix: source column 0 splits .3+.4; last stable column zero.
        self.valid('decay-network', self.edit('branches_value', [[0,0,0],[.3,0,0],[.4,.2,0]]))
        self.invalid('decay-network', self.edit('branches_value', [[0,0,0],[.6,0,0],[.6,0,0]]))
        self.invalid('decay-network', self.edit('branches_value', [[.1,0,0],[0,0,0],[0,0,0]]))
        self.invalid('decay-network', self.edit('branches_value', [[0,.5,0],[.5,0,0],[0,0,0]]))
        self.invalid('decay-network', self.edit('branches_value', [[0,0,.2],[0,0,0],[0,0,0]]))
        self.valid('decay-network', self.edit('nuclides_decay', [.1]))  # repeated rates allowed
        self.valid('irradiated-network', self.edit('products_value', [[0,.5,0],[.5,0,0],[0,0,0]]))
        self.invalid('irradiated-network', self.edit('products_value', [[0,.5,0],[.5,0,0],[.6,0,0]]))
        self.invalid('irradiated-network', self.edit('reaction_cross_section', -1.))
        self.invalid('irradiated-network', self.edit('history_value', -1.))

    def test_grading_boundaries_configuration_consumption_and_closure(self):
        spec = importlib.util.spec_from_file_location('prepare_radiation', ROOT/'src/utils/prepare_harbor.py')
        prepare = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT/'src/utils'))
        try:
            spec.loader.exec_module(prepare)
        finally:
            sys.path.pop(0)
        template = (ROOT/'src/utils/harbor/task.toml').read_text()
        expected_times = {'photon-absorption':600, 'slab-transport-steady':1200,
            'slab-transport-transient':1200, 'neutron-diffusion-source':600,
            'neutron-diffusion-critical':600, 'point-kinetics':300,
            'decay-network':300, 'irradiated-network':300}
        expected_tolerances = {'transmitted_flux':(1e-8,.005), 'deposited_power':(1e-8,.005),
            'scalar_flux':(1e-8,.005), 'current':(1e-8,.005), 'multiplication_factor':(1e-7,.001),
            'population':(1e-8,.002), 'precursor_state':(1e-8,.002), 'inventory':(1e-6,.002),
            'activity':(1e-8,.002), 'decay_power':(1e-12,.002)}
        for slug in models():
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as tmp:
                path, m = fixture(tmp, slug); p = load_problem(path)
                task = task_directory(slug, ROOT); policy = task_policy(task, p)
                bound = resolve_policy(policy, p)
                ref = {s['array']:np.zeros((len(p.arrays[m['time_axes'][s['time_axis']]]),
                    len(p.arrays[m['locations'][s['location']]['ids']]), *s['component_shape'])) for s in m['outputs'].values()}
                ref.update({key:p.arrays[key].copy() for key in output_support(p)})
                self.assertEqual(grade_arrays(p, ref, ref, policy=policy)['score'], 1)
                for name, s in m['outputs'].items():
                    atol, rtol = expected_tolerances[s['quantity']]
                    self.assertEqual((bound['fields'][name]['atol'], bound['fields'][name]['rtol']), (atol, rtol))
                    actual = deepcopy(ref); actual[s['array']][:] = atol
                    self.assertEqual(grade_arrays(p, actual, ref, policy=policy)['score'], 1)
                    actual[s['array']].flat[0] = np.nextafter(atol, np.inf)
                    self.assertEqual(grade_arrays(p, actual, ref, policy=policy)['score'], 0)
                    nonzero = deepcopy(ref); nonzero[s['array']][:] = 100.
                    actual = deepcopy(nonzero); edge = 100.+atol+100.*rtol
                    if edge-100. > atol+100.*rtol:
                        edge = np.nextafter(edge, -np.inf)
                    actual[s['array']][:] = edge
                    self.assertEqual(grade_arrays(p, actual, nonzero, policy=policy)['score'], 1)
                    actual[s['array']].flat[0] = np.nextafter(edge, np.inf)
                    self.assertEqual(grade_arrays(p, actual, nonzero, policy=policy)['score'], 0)
                bad = deepcopy(ref); bad.pop(next(iter(m['outputs'].values()))['array'])
                self.assertEqual(grade_arrays(p,bad,ref,policy=policy)['score'],0)
                self.assertIsNone(grade_arrays(p,ref,bad,policy=policy)['score'])
                config = json.loads((task/'judge-config.json').read_text())
                override = tomllib.loads((task/'harbor/task.toml').read_text())
                merged = tomllib.loads(prepare.task_config(template, override, judge_config=config, case_count=3))
                self.assertEqual(config['timeout_seconds'], expected_times[slug])
                self.assertIsNone(config['max_output_bytes'])
                self.assertEqual(merged['environment']['cpus'],2)
                self.assertEqual(merged['environment']['memory_mb'],4096)
                self.assertEqual(merged['environment']['gpus'],0)
                self.assertEqual(merged['agent']['timeout_sec'],3600)
                self.assertEqual(merged['environment']['build_timeout_sec'],1800)
                self.assertEqual(merged['verifier']['network_mode'],'no-network')
                self.assertEqual(merged['verifier']['environment_mode'],'separate')
                self.assertEqual(merged['verifier']['timeout_sec'],max(1200,300+3*(expected_times[slug]+60)))
        files, runtime = runtime_materials({s:task_directory(s,ROOT) for s in models()},ROOT)
        self.assertEqual(set(runtime['extensions']), {'radiation.nuclear'})
        self.assertFalse(any(any(p in name for p in ('caeoj_tools','/author/','maintenance','/cases/','/reference/')) for name in files))


if __name__ == '__main__':
    unittest.main()
