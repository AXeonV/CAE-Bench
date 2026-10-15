"""Independent 0/1 grading against a supplied reference, after structural checks."""
import math

import numpy as np

from .grading_policy import UNSET, validate_policy, policy_hash, resolve_policy
from .grading_metrics import evaluate_field
from .sdk import load_problem
from .validation import ContractError, check_result, read_hdf5

DEFAULT_ATOL = 1e-6
DEFAULT_RTOL = 1e-5


def _tolerance(atol, rtol):
    try:
        valid = math.isfinite(atol) and math.isfinite(rtol) and atol >= 0 and rtol >= 0
    except (TypeError, OverflowError):
        valid = False
    if not valid:
        raise ValueError("atol and rtol must be finite nonnegative numbers.")
    return {"atol": float(atol), "rtol": float(rtol)}


def grade_arrays(problem, result, reference, *, atol=UNSET, rtol=UNSET, policy=None):
    """Reference and result both use the output contract, regardless of task physics.

    Float fields: abs(result-reference) <= atol + rtol*abs(reference).
    Integer and boolean fields: exact equality. IDs/times remain structural checks.
    Invalid reference data is an infrastructure error, not a wrong answer.
    """
    if policy is not None:
        if atol is not UNSET or rtol is not UNSET:
            raise ValueError('Cannot combine a grading policy with atol/rtol')
        source_policy = policy
        policy = resolve_policy(policy, problem)
        tolerance = None
    else:
        tolerance = _tolerance(DEFAULT_ATOL if atol is UNSET else atol,
                               DEFAULT_RTOL if rtol is UNSET else rtol)
    diagnostics = check_result(problem, reference)
    if not diagnostics["valid"]:
        return {"status": "reference_error", "score": None, "contract": diagnostics}
    diagnostics = check_result(problem, result)
    if not diagnostics["valid"]:
        return {"status": "invalid_output", "score": 0, "contract": diagnostics}
    fields = {}
    for name, spec in problem.manifest["outputs"].items():
        actual, expected = result[spec["array"]], reference[spec["array"]]
        if spec["dtype"] == "float64" and policy is not None:
            fields[name] = evaluate_field(problem, name, actual, expected, policy['fields'][name])
            continue
        if spec["dtype"] == "float64":
            with np.errstate(over="ignore", invalid="ignore"):
                matches = np.isclose(actual, expected, **tolerance)
                difference = np.abs(actual - expected)
            maximum = float(np.max(difference))
            metrics = {"max_abs_error": maximum if math.isfinite(maximum) else "overflow"}
        else:
            matches = actual == expected
            metrics = {}
        fields[name] = {**metrics, "failed_values": int(np.count_nonzero(~matches)),
                        "total_values": int(actual.size)}
    if policy is not None:
        accepted = all(f.get('passed', f.get('failed_values') == 0) for f in fields.values())
        return {'status': 'accepted' if accepted else 'wrong_answer', 'score': int(accepted),
                'policy_version': source_policy['version'], 'policy_sha256': policy_hash(source_policy),
                'bound_policy_sha256': policy_hash(policy), 'fields': fields}
    accepted = all(f["failed_values"] == 0 for f in fields.values())
    return {"status": "accepted" if accepted else "wrong_answer", "score": int(accepted),
            "tolerance": tolerance, "fields": fields}


def grade_files(input_path, output_path, reference_path, *, atol=UNSET, rtol=UNSET, policy=None):
    """Grade three files without invoking any solver or Agent."""
    if policy is not None:
        if atol is not UNSET or rtol is not UNSET:
            raise ValueError('Cannot combine a grading policy with atol/rtol')
        validate_policy(policy)
    else:
        _tolerance(DEFAULT_ATOL if atol is UNSET else atol, DEFAULT_RTOL if rtol is UNSET else rtol)
    try:
        problem = load_problem(input_path)
    except ContractError as exc:
        return {"status": "input_error", "score": None, "contract": exc.report}
    if policy is not None:
        validate_policy(policy, problem)
    try:
        reference = read_hdf5(reference_path)
    except ContractError as exc:
        return {"status": "reference_error", "score": None, "contract": exc.report}
    # Check the reference before inspecting a possibly invalid candidate file.
    diagnostics = check_result(problem, reference)
    if not diagnostics["valid"]:
        return {"status": "reference_error", "score": None, "contract": diagnostics}
    try:
        result = read_hdf5(output_path)
    except ContractError as exc:
        return {"status": "invalid_output", "score": 0, "contract": exc.report}
    return grade_arrays(problem, result, reference, atol=atol, rtol=rtol, policy=policy)
