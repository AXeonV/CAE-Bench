"""Independent 0/1 grading against a supplied reference, after structural checks."""
import math

import numpy as np

from .sdk import load_problem
from .validation import ContractError, check_result, read_npz

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


def grade_arrays(problem, result, reference, *, atol=DEFAULT_ATOL, rtol=DEFAULT_RTOL):
    """Reference and result both use the output contract, regardless of task physics.

    Float fields: abs(result-reference) <= atol + rtol*abs(reference).
    Integer and boolean fields: exact equality. IDs/times remain structural checks.
    Invalid reference data is an infrastructure error, not a wrong answer.
    """
    tolerance = _tolerance(atol, rtol)
    diagnostics = check_result(problem, reference)
    if not diagnostics["valid"]:
        return {"status": "reference_error", "score": None, "contract": diagnostics}
    diagnostics = check_result(problem, result)
    if not diagnostics["valid"]:
        return {"status": "invalid_output", "score": 0, "contract": diagnostics}
    fields = {}
    for name, spec in problem.manifest["outputs"].items():
        actual, expected = result[spec["array"]], reference[spec["array"]]
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
    accepted = all(f["failed_values"] == 0 for f in fields.values())
    return {"status": "accepted" if accepted else "wrong_answer", "score": int(accepted),
            "tolerance": tolerance, "fields": fields}


def grade_files(input_path, output_path, reference_path, *, atol=DEFAULT_ATOL, rtol=DEFAULT_RTOL):
    """Grade three files without invoking any solver or Agent."""
    _tolerance(atol, rtol)
    try:
        problem = load_problem(input_path)
    except ContractError as exc:
        return {"status": "input_error", "score": None, "contract": exc.report}
    try:
        reference = read_npz(reference_path)
    except ContractError as exc:
        return {"status": "reference_error", "score": None, "contract": exc.report}
    # Check the reference before inspecting a possibly invalid candidate file.
    diagnostics = check_result(problem, reference)
    if not diagnostics["valid"]:
        return {"status": "reference_error", "score": None, "contract": diagnostics}
    try:
        result = read_npz(output_path)
    except ContractError as exc:
        return {"status": "invalid_output", "score": 0, "contract": exc.report}
    return grade_arrays(problem, result, reference, atol=atol, rtol=rtol)
