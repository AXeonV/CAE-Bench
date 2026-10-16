"""Plasma contract, policy, isolation and regression checks; no trusted solutions."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

import h5py
import numpy as np

from plasma_fixture import fixture
from caeoj_ext.plasma import models
from caeoj.grading import grade_arrays
from caeoj.grading_policy import resolve_policy
from caeoj.sdk import load_problem, write_result
from caeoj.validation import output_support, validate_input, validate_output
from caeoj_tools.assembly import runtime_materials
from caeoj_tools.grading_policy import task_policy
from caeoj_tools.task_paths import task_directory

ROOT = Path(__file__).resolve().parents[1]


class PlasmaContractTests(unittest.TestCase):
    def mutate(self, slug, edit, *, valid=False):
        with tempfile.TemporaryDirectory() as tmp:
            path, manifest = fixture(tmp, slug)
            edit(manifest, path.parent)
            path.write_text(json.dumps(manifest))
            result = validate_input(path)
            self.assertEqual(result['valid'], valid, result)
            return result

    @staticmethod
    def payload(logical, values):
        def edit(m, base):
            with h5py.File(base / 'input.h5', 'r+') as h5:
                h5[m['fields'][logical]['array']][:] = values
        return edit

    def test_all_models_roundtrip_not_numerical_correctness(self):
        for slug in models():
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as tmp:
                path, m = fixture(tmp, slug)
                problem = load_problem(path)
                fields = {s['array']: np.zeros((len(problem.arrays[m['time_axes'][s['time_axis']]]),
                         len(problem.arrays[m['locations'][s['location']]['ids']]), *s['component_shape'])) for s in m['outputs'].values()}
                output = Path(tmp) / 'result.h5'
                write_result(output, problem, fields)
                self.assertTrue(validate_output(path, output)['valid'])

    def test_constants_references_and_distinct_names(self):
        def scalar(m, base):
            rec = next(c for c in m['conditions'] if c['operator'] == 'particles')
            logical = rec['data']['mass']['field']
            key = m['fields'].pop(logical)['array']
            rec['data']['mass'] = {'value': 1., 'unit': 'kg'}
            with h5py.File(base / 'input.h5', 'r+') as h5:
                del h5[key]
        self.mutate('charged-orbits', scalar, valid=True)
        self.mutate('charged-orbits', lambda m, b: m['fields']['launch_velocity'].update(unit='kg.m/s'))
        self.mutate('relativistic-orbits', lambda m, b: m['fields']['launch_momentum'].update(quantity='velocity'))
        self.mutate('charged-orbits', lambda m, b: m['conditions'].pop())
        self.mutate('charged-orbits', lambda m, b: m['conditions'].append(deepcopy(m['conditions'][0])))
        self.mutate('charged-orbits', lambda m, b: m['conditions'][0]['data'].update(extra={'value': 1., 'unit': '1'}))

    def test_initial_drive_axes_and_sampling(self):
        self.mutate('charged-orbits', lambda m, b: m['fields']['electric_offset']['sampling'].update(time='previous'))
        self.mutate('charged-orbits', lambda m, b: m['fields']['electric_offset'].update(time_axis='initial'))
        self.mutate('plasma-chemistry', lambda m, b: m['physics']['parameters']['end_time'].update(value=True))
        def drive(m, base):
            with h5py.File(base / 'input.h5', 'r+') as h5:
                h5['drive_time'][-1] = .09
        self.mutate('plasma-chemistry', drive)
        self.mutate('magnetized-plasma-slab', lambda m, b: m['outputs']['request_reflectance'].update(time_axis='initial'))

    def test_orbits_signed_charge_mass_and_symmetric_gradient(self):
        self.mutate('charged-orbits', self.payload('particles_mass', 0.))
        self.mutate('relativistic-orbits', self.payload('particles_charge', 0.))
        self.mutate('charged-orbits', self.payload('electric_gradient', [[0., 1., 0.], [0., 0., 0.], [0., 0., 0.]]))
        self.mutate('charged-orbits', self.payload('electric_gradient', [[0., 1., 0.], [1., 0., 0.], [0., 0., 0.]]), valid=True)

    def test_collision_kernel_orientation_and_population(self):
        self.mutate('collisional-states', self.payload('transitions_value', np.eye(3)))
        self.mutate('collisional-states', self.payload('transitions_value', [[0., -1., 0.], [0., 0., 0.], [0., 0., 0.]]))
        self.mutate('collisional-states', self.payload('population_value', 0.))
        self.mutate('collisional-states', lambda m, b: m['physics']['parameters']['state_count'].update(value=3.0))
        self.mutate('collisional-states', lambda m, b: m['fields']['transitions_value'].update(components=list(reversed(m['fields']['transitions_value']['components']))))
        # No detailed-balance or symmetric-kernel restriction: directed cycle is valid.
        self.mutate('collisional-states', self.payload('transitions_value', [[0., 4., 0.], [0., 0., 3.], [2., 0., 0.]]), valid=True)

    def test_chemistry_zero_channels_and_species_order(self):
        self.mutate('plasma-chemistry', self.payload('rates_attachment', -1.))
        self.mutate('plasma-chemistry', self.payload('initial_value', [-1., 1., 0.]))
        self.mutate('plasma-chemistry', self.payload('initial_value', 0.))
        self.mutate('plasma-chemistry', lambda m, b: m['fields']['initial_value'].update(components=['positive_ion', 'electron', 'negative_ion']))
        self.mutate('plasma-chemistry', self.payload('rates_recombination', 0.), valid=True)

    def test_vlasov_phase_bins_and_mesh_tag_identity(self):
        self.mutate('vlasov-poisson', self.payload('initial_value', -1.))
        self.mutate('vlasov-poisson', self.payload('initial_value', 0.))
        self.mutate('vlasov-poisson', lambda m, b: m['fields']['initial_value'].update(value_kind='point'))
        self.mutate('vlasov-poisson', lambda m, b: m['physics']['parameters']['velocity_min'].update(value=0.))
        self.mutate('vlasov-poisson', lambda m, b: m['physics']['parameters'].update(background_density={'value': 1., 'unit': '1/m3'}))

    def test_beam_branch_and_discharge_boundary_compatibility(self):
        self.mutate('space-charge-beam', self.payload('right_potential_value', -.5))
        self.mutate('space-charge-beam', lambda m, b: m['physics']['parameters']['particle_flux'].update(value=10.))
        self.mutate('isothermal-discharge', self.payload('left_reservoir_electron_density', 2.))
        self.mutate('energy-discharge', self.payload('initial_electron_energy', 0.))
        self.mutate('energy-discharge', self.payload('heating_value', -1.))
        self.mutate('isothermal-discharge', lambda m, b: m['fields']['transport_ion_diffusion'].update(location='domain'))
        self.mutate('energy-discharge', lambda m, b: m['fields']['initial_electron_energy'].update(unit='V/m3'))

    def test_cold_current_and_slab_phasors(self):
        self.mutate('cold-plasma-relaxation', self.payload('species_collision_frequency', -1.))
        self.mutate('cold-plasma-relaxation', lambda m, b: m['outputs']['request_current_density'].update(location='system'))
        self.mutate('magnetized-plasma-slab', self.payload('incident_value', 0.))
        self.mutate('magnetized-plasma-slab', self.payload('layers_collision_frequency', 0.))
        self.mutate('magnetized-plasma-slab', lambda m, b: m['outputs']['request_magnetic_amplitude'].update(unit='T'))
        self.mutate('magnetized-plasma-slab', lambda m, b: m['fields']['incident_value'].update(components=['y_real', 'z_real', 'y_imag', 'z_imag']))
        def interface(m, base):
            with h5py.File(base / 'input.h5', 'r+') as h5:
                h5['receivers_coordinates'][0] = 1.
        self.mutate('magnetized-plasma-slab', interface)

    def test_declared_dynamical_scale_limits(self):
        self.mutate('charged-orbits', self.payload('magnetic_value', [1e8, 0., 0.]))
        self.mutate('collisional-states', self.payload('transitions_value', [[0., 1e9, 0.], [0., 0., 0.], [0., 0., 0.]]))
        self.mutate('plasma-chemistry', self.payload('rates_ionization', 1e9))
        self.mutate('cold-plasma-relaxation', self.payload('species_density', 1e20))
        self.mutate('magnetized-plasma-slab', lambda m, b: m['physics']['parameters']['permeability'].update(value=1e-300))
        self.mutate('magnetized-plasma-slab', self.payload('incident_value', 1e200))

    def test_duplicate_requests_and_reserved_model_errors(self):
        def duplicate(m, base):
            field = deepcopy(next(iter(m['outputs'].values())))
            field['array'] = 'second_payload'
            m['outputs']['second_request'] = field
        self.mutate('cold-plasma-relaxation', duplicate, valid=True)
        report = self.mutate('charged-orbits', lambda m, b: m['physics'].update(model='plasma-unregistered-v1'))
        self.assertTrue(any(error['code'] == 'E_PLASMA' for error in report['errors']))

    def test_policies_resources_and_public_boundaries(self):
        sys.path.insert(0, str(ROOT / 'src/utils'))
        try:
            spec = importlib.util.spec_from_file_location('plasma_prepare', ROOT / 'src/utils/prepare_harbor.py')
            prepare = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(prepare)
        finally:
            sys.path.pop(0)
        budgets = {'charged-orbits': (30, 1, 1024), 'relativistic-orbits': (60, 1, 1024),
                   'collisional-states': (60, 1, 1024), 'plasma-chemistry': (60, 1, 1024),
                   'vlasov-poisson': (600, 4, 4096), 'space-charge-beam': (60, 1, 1024),
                   'isothermal-discharge': (300, 2, 2048), 'energy-discharge': (600, 2, 4096),
                   'cold-plasma-relaxation': (60, 1, 1024), 'magnetized-plasma-slab': (180, 2, 2048)}
        for slug in models():
            with self.subTest(slug=slug), tempfile.TemporaryDirectory() as tmp:
                path, m = fixture(tmp, slug)
                problem = load_problem(path)
                task = task_directory(slug, ROOT)
                policy = task_policy(task, problem)
                bound = resolve_policy(policy, problem)
                reference = {k: problem.arrays[k].copy() for k in output_support(problem)}
                for field in m['outputs'].values():
                    reference[field['array']] = np.zeros((len(problem.arrays[m['time_axes']['output']]), len(problem.arrays[m['locations'][field['location']]['ids']]), *field['component_shape']))
                self.assertEqual(grade_arrays(problem, reference, reference, policy=policy)['score'], 1)
                for name, field in m['outputs'].items():
                    actual = deepcopy(reference)
                    tolerance = bound['fields'][name]['atol']
                    actual[field['array']].flat[0] = tolerance
                    self.assertEqual(grade_arrays(problem, actual, reference, policy=policy)['score'], 1)
                    actual[field['array']].flat[0] = np.nextafter(tolerance, np.inf)
                    self.assertEqual(grade_arrays(problem, actual, reference, policy=policy)['score'], 0)
                config = json.loads((task / 'judge-config.json').read_text())
                overrides = tomllib.loads((task / 'harbor/task.toml').read_text())
                merged = tomllib.loads(prepare.task_config((ROOT / 'src/utils/harbor/task.toml').read_text(), overrides, judge_config=config, case_count=3))
                self.assertEqual((config['timeout_seconds'], merged['environment']['cpus'], merged['environment']['memory_mb']), budgets[slug])
                self.assertIsNone(config['max_output_bytes'])
                self.assertGreaterEqual(merged['verifier']['timeout_sec'], 120 + 3 * (config['timeout_seconds'] + 15))
                self.assertFalse(any((task / folder).exists() for folder in ('cases', 'reference', 'samples')))
                public, runtime = runtime_materials({slug: task}, ROOT)
                self.assertEqual(set(runtime['extensions']), {'plasma'})
                self.assertIn('src/caeoj/runtime.py', public)
                self.assertFalse(any('caeoj_tools' in k or 'maintenance' in k or '/author/' in k for k in public))

    def test_standalone_normal_install_and_multitask_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            public, _ = runtime_materials({slug: task_directory(slug, ROOT) for slug in models()}, ROOT)
            source, installed, away = base / 'package', base / 'installed', base / 'away'
            for relative, content in public.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            cases = []
            for slug in models():
                path, _ = fixture(base / slug, slug)
                cases.append(str(path))
            env = os.environ.copy()
            env.pop('PYTHONPATH', None)
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-deps', '--no-build-isolation',
                '--no-index', '--disable-pip-version-check', '--target', str(installed), str(source)],
                env=env, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            source.rename(base / 'source-removed')
            away.mkdir()
            env['PYTHONPATH'] = str(installed)
            code = '''
import json, sys
from pathlib import Path
import caeoj, caeoj_bundle, caeoj_ext.plasma
from caeoj.sdk import load_problem
from caeoj.runtime import bundle_info
base=Path(sys.argv[1]).resolve()
for module in (caeoj,caeoj_bundle,caeoj_ext.plasma):
    assert Path(module.__file__).resolve().is_relative_to(base), (module.__name__, module.__file__, str(base))
for path in sys.argv[2:]:
    p=load_problem(path)
    assert p.manifest['physics']['model'].startswith('plasma-')
assert len(bundle_info()['tasks'])==10
print(json.dumps({'normal_install':True,'loaded_inputs':len(sys.argv)-2}))
'''
            result = subprocess.run([sys.executable, '-c', code, str(installed), *cases], cwd=away,
                                    env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)['loaded_inputs'], 10)


if __name__ == '__main__':
    unittest.main()
