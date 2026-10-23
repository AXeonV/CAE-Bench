"""Neutral JSON/HDF5 adapter for a fixed installed PyBaMM driver."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from caeoj.sdk import load_problem, write_result


def serialize(problem):
    params = problem.manifest['physics']['parameters']
    arrays = problem.arrays
    states = []
    for i in range(len(arrays['state_ids'])):
        state = {}
        for name in ('current', 'average_soc', 'diffusion_enabled', 'reversible_heat'):
            state[name] = arrays[name][0, i, 0].item()
        for name in ('soc_profile', 'ocv_coefficients', 'element_heat'):
            state[name] = arrays[name][0, i].tolist()
        states.append(state)
    return json.dumps({'grid_count': params['grid_count']['value'],
                       'rc_count': params['rc_count']['value'], 'states': states})


def run(input_path, output_path):
    problem = load_problem(input_path)
    process = subprocess.run([sys.executable, '/opt/repair-driver/driver.py'],
                             input=serialize(problem), text=True, capture_output=True)
    if process.returncode:
        sys.stderr.write(process.stderr)
        raise RuntimeError(f'Trusted library driver exited {process.returncode}')
    fields = {name: np.asarray(value, dtype='float64')[None, :, :]
              for name, value in json.loads(process.stdout).items()}
    write_result(output_path, problem, fields)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.input, args.output)
