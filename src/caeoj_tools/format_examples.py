"""Create format-only answers from public output declarations, never references."""
from pathlib import Path
import numpy as np
from caeoj.sdk import load_problem, write_result
from caeoj.validation import validate_output
from caeoj_tools import data_pool as pool


def randomize_example(sample: Path, *, seed: int):
    sample = Path(sample)
    problem = load_problem(sample / 'input/problem.json')
    rng = np.random.default_rng(seed)
    fields = {}
    for spec in problem.manifest['outputs'].values():
        nt = len(problem.arrays[problem.manifest['time_axes'][spec['time_axis']]])
        ne = len(problem.arrays[problem.manifest['locations'][spec['location']]['ids']])
        shape = (nt, ne, *spec['component_shape'])
        dtype = np.dtype(spec['dtype'])
        if dtype == np.dtype('float64'):
            values = rng.uniform(-1., 1., shape)
        elif dtype == np.dtype('int64'):
            values = rng.integers(-1000, 1001, shape, dtype=dtype)
        elif dtype == np.dtype('bool'):
            values = rng.integers(0, 2, shape, dtype=np.int64).astype(dtype)
        else:
            raise ValueError(f'Unsupported output dtype: {dtype}')
        fields[spec['array']] = values
    target = sample / 'output/result.h5'
    write_result(target, problem, fields)
    if not validate_output(sample / 'input/problem.json', target)['valid']:
        raise ValueError('Random example failed its output format')
    pool.write_json(sample / 'example.json', {'kind': 'format'})
    return {'seed': seed, 'generator': 'numpy.PCG64: float64 uniform[-1,1), int64 uniform[-1000,1000], bool Bernoulli(0.5)',
            'reference_values_read': False, 'output_sha256': pool.digest(target),
            'shapes': {k: list(v.shape) for k, v in fields.items()}}
