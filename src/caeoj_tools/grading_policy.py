"""Resolve grading policy from trusted task-maintenance files."""
import json
from pathlib import Path

from caeoj.grading_policy import parse_policy, validate_policy


def task_policy(task_dir, problem, *, read_bytes=None):
    """Read the task's explicit policy; execution settings cannot define scoring."""
    task_dir = Path(task_dir)
    read = read_bytes or (lambda path: path.read_bytes())
    config_path = task_dir / 'judge-config.json'
    config = json.loads(read(config_path)) if config_path.is_file() else {}
    if 'atol' in config or 'rtol' in config:
        raise ValueError('Scoring belongs in grading.json, not judge-config atol/rtol')
    policy = parse_policy(read(task_dir / 'grading.json'))
    validate_policy(policy, problem)
    return policy
