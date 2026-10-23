# Continuous scoring public and author policy migration

Scope: the 80 numerical tasks selected by the 82-task RC4 plan. Chapter 0's two infrastructure fixtures remain binary. No solver output, formal reference array, input, grading pool descriptor, or release archive was changed by this subtask.

## Public definition

Each requested physical quantity/output, scalar component and requested time has its own spatial weighted NRMSE. Case E is the maximum over these groups. E <= 0.05 yields 1; 0.05 < E < 0.10 yields (0.10-E)/0.05; E >= 0.10 yields 0. Task reward is the arithmetic mean of formal case scores. Invalid output or solver failure remains zero, and evaluation/infrastructure errors are not candidate errors.

All 80 instruction.md files include the formula, max aggregation, weights and an explicit per-field/quantity scale_floor table. All locations/times, including initial frame and boundary/zero values, participate. Equal observation weights are explicitly stated where no former weight_field exists; existing explicit weights remain bound. This is an observation error metric and does not invent cell/volume weights.

The six existing CFDCodeBench normalized transforms retain pressure weighted-mean removal and temperature fixed-background subtraction. The two selected interface tasks' reference_offset pressure parameter only affects the denominator RMS: numerator remains raw absolute-pressure difference. DATA already states these same physical and transformation semantics. The parent corrected the single-entity EVP DATA weight sentence to explicitly say equal weighting and no score effect from the supplied weights; the CFD renderer mirrors this exception. No other DATA changes were needed. The Chapter 0 statements are untouched.

## Scale choice and limitation

Existing NRMSE floors retain their numerical values. Former pointwise/violation_fraction atol values become scale_floor with the original physical units. The spectral EVP former max_abs limit 1e-4 becomes its floor. These are explicit inherited scales, not a numerical calibration or equivalence to the old acceptance regions. Old atol/rtol/outlier limits and old binary scores have no implied equivalence to the new grades. In particular, absolute-temperature RMS, raw pressure RMS and any pre-existing pressure qualification concerns remain matters for scientific calibration.

## Author configuration and generation

All 80 author/grading-template.json files now contain the complete outer case plan, including explicit scoring, checks, weights and domain transformations. CFDCodeBench's 24 duplicate author/case-grading-template.json files were removed; the renderer writes the sole complete grading-template.json.

caeoj_tools.continuous_scoring.convert_grading is an explicit, copy-preserving migration helper. It never changes arrays and refuses missing/nonpositive/nonfinite scales or unsupported rules. It has no task-name heuristic. scoring_text renders public statements from the bound migrated policy.

caeoj_tools.grading_policy.author_case_grading reads a complete outer template with schema validation, or explicitly wraps an old inner policy for unrelated legacy tasks without adding scoring. author_policy only extracts a single check policy for legacy callers and rejects multi-check extraction. write_case_grading/materialize_references accept the complete explicit plan. The two thermal generators, PDEBench shared pipeline, CFDCodeBench renderer/build_local grading function and verify_install fixture path now preserve the outer plan. The maintained ten-case-candidates/build_designs.py uses author_policy explicitly for observation-request design, rather than treating the complete outer template as a quantity dictionary. Historical frozen source-design snapshots were not rewritten and must not be mistaken for current generation templates.

## Verification

- helper-tests.log: 4 tests and 3 subtests passed. Explicit migration preserves transforms, weights and offset binding; zero/unknown/nonfinite inherited scales are rejected; complete plan materialization retains scoring; legacy policy remains binary; multi-check extraction rejects.
- author-bindings.json: all 80 current templates parse through the shared author reader and schema, bind exact scoring constants, contain the public max/linear formula, and have no duplicate full template.
- authoring-tests.log: initial combined offline run had 31 passed / 40 subtests passed and 11 historical-selection subtest failures. The failure was an obsolete requirement that preserved source-freeze contract hashes equal the newly changed public scoring statements; no historical selection/certificate was re-signed.
- pdebench-tests-fixed.log: 23 passed / 24 subtests passed after replacing that obsolete assertion with a real pipeline contract-mutation test. The pipeline rejects changed contracts without rewriting the old frozen selection.
- pdebench-historical-tests.log: 1 passed / 11 subtests passed for the 11 actual preserved historical source selections, checking task/status, hash identities, source references, entry indexes and unique roles.
- equation-policy-tests.log: 2 passed / 11 subtests passed. Current 11 equation templates bind explicit continuous grading with inherited scales; the separate legacy outlier-policy test remains to prevent unrequested changes to old rules.
- runtime-author-tests.log: 2 passed / 291 subtests passed. All task templates (including untouched non-release chapters) parse from their single explicit author source; execution settings cannot supply scoring tolerances.
- cfd-render-check.log: all 24 generated CFD grading configurations equal the sole checked-in complete author templates.

The heat/transient physics regression helpers now use explicit historical absolute-error test policies rather than loading live release templates, preserving those old numerical solver/error tests as separate tests. Their normal fixture generation and direct per-case evaluation use the new complete templates. No expensive full thermal solver suite was rerun for these test-only reader changes; the release scoring boundaries are covered independently by core tests.

The independent core scoring tests, real formal grading migration, package/release checks and candidate review are coordinated by the parent task. This report does not claim new reference correctness, physical solver validation, resource calibration or benchmark execution.
