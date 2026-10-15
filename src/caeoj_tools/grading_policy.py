"""Resolve grading policy from trusted task-maintenance files."""
import json
from pathlib import Path

from caeoj.grading_policy import (parse_policy, legacy_policy, validate_policy,
                                  _tolerance, DEFAULT_ATOL, DEFAULT_RTOL)


def task_policy(task_dir, problem, *, read_bytes=None):
    """Resolve public policy or legacy tolerances; prohibit ambiguous sources."""
    task_dir = Path(task_dir)
    read = read_bytes or (lambda path: path.read_bytes())
    config_path = task_dir / 'judge-config.json'
    config = json.loads(read(config_path)) if config_path.is_file() else {}
    path = task_dir / 'grading.json'
    if path.is_file():
        if 'atol' in config or 'rtol' in config:
            raise ValueError('grading.json and legacy judge-config atol/rtol cannot coexist')
        policy = parse_policy(read(path))
    else:
        tolerance = _tolerance(config.get('atol', DEFAULT_ATOL), config.get('rtol', DEFAULT_RTOL))
        policy = legacy_policy(problem, **tolerance)
    validate_policy(policy, problem)
    return policy
