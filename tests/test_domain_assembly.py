"""Exercise actual single-capability runtime closures away from the repository.

Fixtures are temporary protocol payloads, not benchmark cases or references.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from caeoj_tools.assembly import runtime_materials
from caeoj_tools.task_paths import task_directory

ROOT = Path(__file__).resolve().parents[1]


def fixture_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'tests'/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DomainAssemblyTests(unittest.TestCase):
    def test_six_physical_capability_closures(self):
        energy = fixture_module('assembly_energy_fixture', 'test_fluid_energy.py')
        reduced = fixture_module('assembly_reduced_fixture', 'test_fluid_reduced.py')
        scenarios = [
            ('newtonian-lowmach-steady-3d', 'fluid-energy-lowmach-laminar-steady-v1',
             'thermal_flow', 6),
            ('resolved-statistics-3d', 'fluid-energy-incompressible-resolved-statistics-v1',
             'turbulence', 14),
            ('nonnewtonian-film', 'fluid-reduced-nonnewtonian-film-v1', 'thin_film', 4),
            ('fully-wet-steady', 'fluid-reduced-fully-wet-steady-v1', 'depth_averaged', 4),
            ('isothermal-slip', 'fluid-reduced-isothermal-slip-v1', 'rarefied', 4),
            ('thixotropic-transient', 'fluid-reduced-thixotropic-transient-v1', 'complex_fluid', 5),
        ]
        for task, model, capability, model_count in scenarios:
            with self.subTest(capability=capability), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                files, runtime = runtime_materials({task: task_directory(task, ROOT)}, ROOT)
                expected = {'fluid.common', 'fluid.'+capability}
                if capability == 'turbulence':
                    expected.add('fluid.thermal_flow')
                self.assertEqual(set(runtime['extensions']), expected)
                for name, data in files.items():
                    target = directory/name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                case = directory/'fixture'
                if capability in ('thermal_flow', 'turbulence'):
                    energy.fixture(case, model)
                    path = case/'problem.json'
                    manifest = json.loads(path.read_text())
                else:
                    case.mkdir()
                    path, manifest = reduced.make_fixture(case, model)
                manifest['task'] = task
                path.write_text(json.dumps(manifest))
                away = directory/'away'
                away.mkdir()
                code = r'''
import importlib.util
import json
import math
from pathlib import Path
import sys
import numpy as np
import caeoj
from caeoj.sdk import load_problem, load_result, write_result
from caeoj.validation import validate_input

path = Path(sys.argv[1])
capability = sys.argv[2]
assert Path(caeoj.__file__).is_relative_to(path.parent.parent/'src')
problem = load_problem(path)
assert validate_input(path)['valid']
fields = {}
for spec in problem.manifest['outputs'].values():
    times = problem.arrays[problem.manifest['time_axes'][spec['time_axis']]]
    ids = problem.arrays[problem.manifest['locations'][spec['location']]['ids']]
    fields[spec['array']] = np.zeros((len(times), len(ids), *spec['component_shape']), dtype='float64')
write_result(path.parent/'result.h5', problem, fields)
load_result(problem, path.parent/'result.h5')

if capability in ('thermal_flow', 'turbulence'):
    from caeoj.fluid_energy import MODELS
    from caeoj.sdk import fluid_energy_properties, fluid_energy_statistics
    response = fluid_energy_properties(problem, [300.])
    np.testing.assert_allclose(response['density'], [1000.])
    np.testing.assert_allclose(response['dynamic_viscosity'], [.01])
    if capability == 'turbulence':
        stats = fluid_energy_statistics([0., 1.], [[[1., 0.]], [[3., 0.]]])
        np.testing.assert_array_equal(stats['velocity'], [[2., 0.]])
        np.testing.assert_array_equal(stats['velocity_covariance'], [[[1., 0.], [0., 0.]]])
    else:
        assert importlib.util.find_spec('caeoj_ext.fluid.turbulence') is None
        try:
            fluid_energy_statistics([0., 1.], [[[1., 0.]], [[3., 0.]]])
        except RuntimeError:
            pass
        else:
            raise AssertionError('Unassembled turbulence capability was accepted')
else:
    from caeoj.fluid_reduced import MODELS, maxwellian, reduced_time_derivative
    from caeoj.sdk import reduced_parameters, reduced_viscosity
    assert reduced_parameters(problem) == {k: v['value'] for k, v in problem.manifest['physics']['parameters'].items()}
    if capability == 'thin_film':
        # n=1 makes the declared Carreau response exactly mu_0 for every rate.
        params = dict(zero_viscosity=10., infinite_viscosity=2., time_constant=3., power_index=1.)
        np.testing.assert_allclose(reduced_viscosity(model='fluid-reduced-nonnewtonian-film-v1', params=params, shear_rate=[0., 5.]), [10., 10.])
    elif capability == 'depth_averaged':
        np.testing.assert_array_equal(reduced_time_derivative([0., 2.], np.array([[1.], [7.]]), 1.), [3.])
    elif capability == 'rarefied':
        mass, temperature = 6.6e-26, 300.
        speed = math.sqrt(2*1.380649e-23*temperature/mass)
        distribution = maxwellian(1., [0.,0.,0.], temperature, mass, [[0.,0.,0.],[speed,0.,0.]])
        from caeoj.sdk import maxwellian as sdk_maxwellian
        np.testing.assert_array_equal(distribution, sdk_maxwellian(number_density=1.,
            velocity=[0.,0.,0.], temperature=temperature, mass=mass,
            molecular_velocity=[[0.,0.,0.],[speed,0.,0.]]))
        np.testing.assert_allclose(distribution[1]/distribution[0], math.exp(-1))
    elif capability == 'complex_fluid':
        assert float(reduced_viscosity('fluid-reduced-thixotropic-transient-v1',
            {'base_viscosity':2., 'structure_viscosity':8.}, 0., structure=.25)) == 4.
    if capability != 'rarefied':
        assert importlib.util.find_spec('caeoj_ext.fluid.rarefied') is None
        try:
            maxwellian(1., [0.,0.,0.], 300., 6.6e-26, [0.,0.,0.])
        except RuntimeError:
            pass
        else:
            raise AssertionError('Unassembled rarefied capability was accepted')
assert len(MODELS) == int(sys.argv[3])
# The installed checker must remain active, beyond structural/schema validity.
manifest = json.loads(path.read_text())
next(iter(manifest['physics']['parameters'].values()))['unit'] = 'wrong-unit'
path.write_text(json.dumps(manifest))
invalid = validate_input(path)
assert not invalid['valid'] and 'E_FLUID' in {error['code'] for error in invalid['errors']}, invalid
'''
                result = subprocess.run(
                    [sys.executable, '-c', code, str(path), capability, str(model_count)],
                    cwd=away, env={**os.environ, 'PYTHONPATH': str(directory/'src')},
                    capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)


if __name__ == '__main__':
    unittest.main()
