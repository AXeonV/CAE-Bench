"""Thin helpers; array values, shapes and numbering are never repaired."""
from pathlib import Path

import numpy as np

from .validation import ContractError, check_problem, check_result, output_support, read_npz


def load_problem(path):
    problem, diagnostics = check_problem(path)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    return problem


def load_result(problem, path):
    arrays = read_npz(path)
    diagnostics = check_result(problem, arrays)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    return arrays


def write_result(path, problem, fields):
    """fields maps required NPZ array keys to actual ndarrays; no dtype conversion."""
    if any(not isinstance(a, np.ndarray) for a in fields.values()):
        raise TypeError("Pass ndarrays with the declared dtype and shape.")
    support = output_support(problem)
    if set(fields) & support:
        raise ValueError("Field keys cannot overwrite support arrays.")
    arrays = {key: problem.arrays[key] for key in support} | fields
    diagnostics = check_result(problem, arrays)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    path = Path(path)
    if path.suffix != ".npz":
        raise ValueError("Output path must end in .npz.")
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **arrays)
    return arrays


def target_ids(problem, location):
    return problem.arrays[problem.manifest["locations"][location]["ids"]].copy()


def id_to_row(ids):
    if len(set(map(int, ids))) != len(ids):
        raise ValueError("Entity IDs must be unique.")
    return {int(tag): row for row, tag in enumerate(ids)}
