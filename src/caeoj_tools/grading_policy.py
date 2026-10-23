"""Author-only numerical templates and explicit case configuration generation."""
from pathlib import Path
import json
from caeoj.grading_policy import parse_policy, validate_policy
from caeoj.case_grading import direct_config, parse_config


def author_case_grading(task_dir, problem=None, *, read_bytes=None):
    """Read the explicit complete author plan, or wrap an old numerical policy.

    Shape, rather than metric or task identity, determines this conversion.
    There is no runtime fallback: the returned plan must be written per case.
    """
    task = Path(task_dir)
    read = read_bytes or (lambda path: path.read_bytes())
    config_path = task/'judge-config.json'
    config = json.loads(read(config_path)) if config_path.is_file() else {}
    if 'atol' in config or 'rtol' in config:
        raise ValueError('Scoring belongs in case grading.json, not judge-config atol/rtol')
    raw = read(task/'author/grading-template.json')
    candidate = json.loads(raw)
    if 'checks' in candidate:
        result = parse_config(raw)
        for check in result['checks']:
            if 'policy' in check:
                validate_policy(check['policy'], problem)
        return result
    policy = parse_policy(raw)
    validate_policy(policy, problem)
    return direct_config(policy)


def author_policy(task_dir, problem=None, *, read_bytes=None):
    """Extract the single policy for legacy author callers; not a case plan."""
    result = author_case_grading(task_dir, problem, read_bytes=read_bytes)
    if len(result['checks']) != 1 or 'policy' not in result['checks'][0]:
        raise ValueError('Author template does not contain one numerical policy')
    return result['checks'][0]['policy']


def write_case_grading(directory, config):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(config, indent=2, allow_nan=False)+'\n'
    parse_config(encoded)
    (directory/'grading.json').write_text(encoded, encoding='utf-8')


def write_direct_grading(directory, policy):
    write_case_grading(directory, direct_config(policy))


def materialize_references(destination, policy=None, *, case_config=None, echo=False):
    """Author operation: persist complete direct plans beside actual references."""
    import shutil
    from caeoj.sdk import load_problem
    from caeoj.validation import output_support
    from caeoj.storage import write_hdf5
    destination = Path(destination)
    if (policy is None) == (case_config is None):
        raise ValueError('Supply exactly one policy or complete case_config')
    config = case_config if case_config is not None else direct_config(policy)
    for problem_path in sorted((destination/'cases').glob('*/problem.json')):
        reference = destination/'reference'/problem_path.parent.name
        if echo:
            problem = load_problem(problem_path)
            keys = output_support(problem) | {s['array'] for s in problem.manifest['outputs'].values()}
            write_hdf5(reference/'reference.h5', {k: problem.arrays[k] for k in keys})
        if (reference/'reference.h5').is_file(): write_case_grading(reference, config)
    for result in sorted((destination/'samples').glob('*/output/result.h5')):
        reference = result.parent.parent/'reference'
        reference.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(result, reference/'reference.h5')
        write_case_grading(reference, config)
