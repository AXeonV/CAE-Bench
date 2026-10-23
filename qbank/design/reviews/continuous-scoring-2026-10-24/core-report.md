# Continuous scoring core implementation

Implemented optional case-level `scoring={metric:max_nrmse,full_credit:0.05,zero_credit:0.10}`. Without scoring, binary case behavior remains unchanged. Continuous preflight requires every numerical rule to use per-time/per-component NRMSE with limit equal to full credit; OR/pooled scopes are rejected. All numerical diagnostic groups across checks/fields/time/components contribute to the maximum error. Exact integer/bool mismatch and candidate normalization overflow force zero; bad references/configuration remain infrastructure errors (score null). Normalized fields keep their existing trusted transform and report semantics.

NRMSE accepts the existing explicit reference_offset binding (finite fixed scalar or version-2 input parameter). Only its reference RMS denominator is centered; the error is always direct actual-reference. The denominator RMS is computed with bounded scales, including centered magnitudes above DBL_MAX. No fitted normalization or hidden output gauge is introduced.

Reports distinguish accepted (1), partial_credit (strictly between 0 and 1), wrong_answer (0), and invalid_output (0). total_nrmse is the maximum numerical error; unrepresentable metrics use the JSON-safe overflow marker. CLI continues to return 0 for full credit, 1 for partial/zero credit, and 2 for infrastructure failure; consumers must use JSON score. Existing data-pool and assembly checks requiring score=1 validate correct references/examples and intentionally remain strict.

Harbor aggregates the actual scores with math.fsum, divides by all formal cases, and separately records full-credit and partial-credit counts. The real managed grading worker test produces case scores [1,0.6] and reward 0.8, rather than converting partial credit into failure.

## Verification

- core-tests.log: **91 passed, 154 subtests passed** (147.05s). Case/metric/configuration, 67 released chapter-2 quantity templates, all 24 trusted CFDCodeBench evaluators, and complete Harbor adapter suite.
- endpoint-tests.log: **30 passed, 28 subtests passed** (10.84s). Includes the final added extreme centered NRMSE check and actual CLI partial-score JSON/exit-code test. This overlaps core tests; counts are not additive.
- compatibility-tests.log: **23 passed, 17 subtests passed** (23.72s). Prior numerical engines, equation policy, and actual chapter-0 case evaluation witnesses. Chapter-0 formal rules unchanged; stale sample tests now enforce random-format-only samples with no reference.
- git diff --check for owned files: passed.

Earlier exploratory runs exposed stale assumptions in test fixtures (65 chapter-2 templates, obsolete separate CFD case templates, .02 K always failing, adding atol/rtol onto an NRMSE leaf, and random samples carrying correct references). These assertions were updated to current explicit author plans/release scope and policy, without changing formal references or weakening numerical comparisons. harbor-tests.log preserves the earlier failed fixture run; core-tests.log is the corrected complete Harbor result.

No paid model calls or numerical solver runs. Tests use disposable synthetic engine fixtures and current author templates; they verify scoring, not physical reference qualification. The root release task owns real selected-case checks, packaging, independent install verification, and publication evidence.
