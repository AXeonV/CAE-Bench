"""Thin helpers; array values, shapes and numbering are never repaired."""
import numpy as np

from .storage import write_hdf5
from .validation import ContractError, check_problem, check_result, output_support, read_hdf5


def load_problem(path):
    problem, diagnostics = check_problem(path)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    return problem


def load_result(problem, path):
    arrays = read_hdf5(path)
    diagnostics = check_result(problem, arrays)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    return arrays


def read_constant(data):
    """Read a validated {value, unit} constant; never convert its unit."""
    if not isinstance(data, dict) or set(data) != {"value", "unit"}:
        raise TypeError('Expected a {"value": number, "unit": string} constant; '
                        'use read_field(problem, reference) for a field reference.')
    return data["value"]


def read_field(problem, reference):
    """Resolve {field: name} to its HDF5 array; preserve dtype, shape and order."""
    if not isinstance(reference, dict) or set(reference) != {"field"}:
        raise TypeError('Expected a {"field": name} reference; '
                        'use read_constant(data) for a constant.')
    name = reference["field"]
    if name not in problem.manifest["fields"]:
        raise KeyError(f'Unknown input field: {name!r}; use the field name, not the HDF5 key.')
    return problem.arrays[problem.manifest["fields"][name]["array"]]


def write_result(path, problem, fields):
    """fields maps required HDF5 array keys to actual ndarrays; no dtype conversion."""
    if any(not isinstance(a, np.ndarray) for a in fields.values()):
        raise TypeError("Pass ndarrays with the declared dtype and shape.")
    support = output_support(problem)
    if set(fields) & support:
        raise ValueError("Field keys cannot overwrite support arrays.")
    arrays = {key: problem.arrays[key] for key in support} | fields
    diagnostics = check_result(problem, arrays)
    if not diagnostics["valid"]:
        raise ContractError(diagnostics)
    write_hdf5(path, arrays)
    return arrays


def target_ids(problem, location):
    return problem.arrays[problem.manifest["locations"][location]["ids"]].copy()


def id_to_row(ids):
    if len(set(map(int, ids))) != len(ids):
        raise ValueError("Entity IDs must be unique.")
    return {int(tag): row for row, tag in enumerate(ids)}
