"""Author-only numerical templates and explicit case configuration generation."""
from pathlib import Path
import json
from caeoj.grading_policy import parse_policy, validate_policy
from caeoj.case_grading import direct_config


def author_policy(task_dir, problem=None, *, read_bytes=None):
    task = Path(task_dir)
    read = read_bytes or (lambda path: path.read_bytes())
    config_path = task/'judge-config.json'
    config = json.loads(read(config_path)) if config_path.is_file() else {}
    if 'atol' in config or 'rtol' in config:
        raise ValueError('Scoring belongs in case grading.json, not judge-config atol/rtol')
    policy = parse_policy(read(task/'author/grading-template.json'))
    validate_policy(policy, problem)
    return policy


def write_direct_grading(directory, policy):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    (directory/'grading.json').write_text(json.dumps(direct_config(policy), indent=2, allow_nan=False)+'\n', encoding='utf-8')


def materialize_references(destination, policy, *, echo=False):
    """Author operation: persist complete direct plans beside actual references."""
    import shutil
    from caeoj.sdk import load_problem
    from caeoj.validation import output_support
    from caeoj.storage import write_hdf5
    destination = Path(destination)
    for problem_path in sorted((destination/'cases').glob('*/problem.json')):
        reference = destination/'reference'/problem_path.parent.name
        if echo:
            problem = load_problem(problem_path)
            keys = output_support(problem) | {s['array'] for s in problem.manifest['outputs'].values()}
            write_hdf5(reference/'reference.h5', {k: problem.arrays[k] for k in keys})
        if (reference/'reference.h5').is_file(): write_direct_grading(reference, policy)
    for result in sorted((destination/'samples').glob('*/output/result.h5')):
        reference = result.parent.parent/'reference'
        reference.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(result, reference/'reference.h5')
        write_direct_grading(reference, policy)
