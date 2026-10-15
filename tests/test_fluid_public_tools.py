"""Isolate the actual public runtime file list with temporary protocol payloads.

No qbank case is created, no production release is published, and the roundtrip
values below carry no numerical/physical correctness claim.
"""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class FluidPublicToolsTests(unittest.TestCase):
    def test_public_runtime_isolated_for_all_three_domains(self):
        publisher = module('fluid_tool_publisher', ROOT/'src/utils/publish_dist.py')
        energy = module('fluid_tool_energy_fixture', ROOT/'tests/test_fluid_energy.py')
        multiphase = module('fluid_tool_multiphase_fixture', ROOT/'tests/test_fluid_multiphase.py')
        reduced = module('fluid_tool_reduced_fixture', ROOT/'tests/test_fluid_reduced.py')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            # This is the publisher's real allow-list, not a directory-wide copy.
            for name in publisher.TOOL_FILES:
                destination = root/'src/caeoj'/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT/'src/caeoj'/name, destination)
            for name in ('CONTRACT.md','GRADING.md','CFD-2.1.md',
                         'FLUID-ENERGY.md','FLUID-MULTIPHASE.md','FLUID-REDUCED.md'):
                destination = root/'docs'/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT/'docs'/name, destination)
            fixtures = root/'fixtures'
            fixtures.mkdir()
            energy.fixture(fixtures/'energy', 'fluid-energy-lowmach-laminar-transient-v1')
            multiphase.make_fixture(fixtures/'multiphase')
            (fixtures/'reduced').mkdir()
            reduced.make_fixture(fixtures/'reduced','fluid-reduced-viscoelastic-transient-v1')
            code = '''
from pathlib import Path
import numpy as np
import caeoj
from caeoj.sdk import load_problem, write_result, load_result
from caeoj.validation import validate_input, validate_output
import caeoj.fluid_energy, caeoj.fluid_multiphase, caeoj.fluid_reduced
expected = Path('src/caeoj').resolve()
for mod in (caeoj, caeoj.fluid_energy, caeoj.fluid_multiphase, caeoj.fluid_reduced):
    assert Path(mod.__file__).resolve().parent == expected, mod.__file__
for path in sorted(Path('fixtures').glob('*/problem.json')):
    assert validate_input(path)['valid'], validate_input(path)
    p = load_problem(path)
    values = {s['array']: np.zeros((len(p.arrays[p.manifest['time_axes'][s['time_axis']]]),
              len(p.arrays[p.manifest['locations'][s['location']]['ids']]), *s['component_shape']),
              dtype=np.float64) for s in p.manifest['outputs'].values()}
    result = path.parent/'roundtrip.h5'
    write_result(result, p, values)
    assert validate_output(path, result)['valid']
    arrays = load_result(p, result)
    for key, value in values.items():
        np.testing.assert_array_equal(arrays[key], value)
print('isolated runtime: 3 domains, input/output roundtrip passed')
'''
            environment = {**os.environ, 'PYTHONPATH':str(root/'src')}
            execution = subprocess.run([sys.executable,'-c',code], cwd=root, env=environment,
                                       capture_output=True, text=True, timeout=60)
            self.assertEqual(execution.returncode,0,execution.stdout+execution.stderr)
            self.assertIn('3 domains',execution.stdout)


if __name__ == '__main__':
    unittest.main()
