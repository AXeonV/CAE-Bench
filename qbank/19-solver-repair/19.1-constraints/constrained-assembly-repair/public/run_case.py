"""Neutral data adapter for the installed Chrono assembly driver."""
import argparse
import json
from pathlib import Path
import subprocess
import numpy as np
from caeoj.sdk import load_problem, write_result


def serialize(problem):
    meta, arrays = problem.manifest, problem.arrays
    ids = arrays['body_ids']
    rows = {int(tag): index for index, tag in enumerate(ids)}
    links = arrays.get('link_ids', [])
    params = meta['physics']['parameters']
    tokens = [len(ids), len(links), int(params['action']['value'])]
    tokens += [params['gravity_' + axis]['value'] for axis in 'xyz']
    for i in range(len(ids)):
        tokens += [arrays['mass'][0, i, 0], int(arrays['fixed'][0, i, 0])]
        for name in ['position', 'velocity', 'force']:
            tokens += list(arrays[name][0, i])
    for i in range(len(links)):
        a, b = arrays['endpoints'][0, i]
        tokens += [rows[int(a)], rows[int(b)], arrays['length'][0, i, 0]]
    return ' '.join(str(t) for t in tokens) + '\n'


def run(problem_path, output_path, driver='/opt/driver-build/assembly-driver'):
    problem = load_problem(problem_path)
    execution = subprocess.run([str(driver)], input=serialize(problem),
                               text=True, capture_output=True, check=True)
    values = json.loads(execution.stdout)
    fields = {name: np.asarray(values[name], dtype='float64')[None, :, :]
              for name in problem.manifest['outputs']}
    write_result(output_path, problem, fields)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--driver', default='/opt/driver-build/assembly-driver')
    args = parser.parse_args()
    run(args.input, args.output, args.driver)
