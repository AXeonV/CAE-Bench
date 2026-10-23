# Uniform format sample generator report

## Scope and changes

- `src/caeoj_tools/format_examples.py` now draws float64 uniformly in [-1, 1), int64 uniformly from the integers [-1000, 1000], and bool as Bernoulli(0.5). Integer and boolean outputs no longer arise by casting floats. Output dimensions come from the declared time axis, location IDs, and complete component shape; SDK `write_result` preserves all shared support arrays verbatim. The helper reads public inputs only and writes `example.json` with `kind=format`.
- The case-grading, steady heat, and transient heat author generators call this helper for public output examples. They no longer write or copy sample `reference.h5`, `grading.json`, observation references, or sample numerical verification records. Formal case input/reference generation is unchanged.
- The steady mixed-boundary input builder accepts `reference_dir=None` to skip computing/writing its reference values for the public example. The transient public publisher copies input assets only. Smoke's generator only creates formal cases and therefore required no sample-generation change.
- Existing author evidence was preserved. This subtask did not modify current data manifests, dataset pools, release archives, or task prose. Actual installed sample conversion is handled by the coordinating task.

## Regression coverage

- Dtypes, rank-1/rank-2/rank-3 component shapes, irregular output times, shared ID/time support arrays, same-seed equality, different-seed changes, format validation, and lack of reference reads.
- All three public sample generators: no sample references; steady sample generation cannot call polynomial reference evaluation; transient sample generation cannot call its reference oracle; case-grading reference generation receives formal case paths only.
- Default public fixtures now exercise format-only samples. Explicit internal numerical-role fixtures preserve legacy grading/publishing regression coverage using arbitrary expected arrays, without claiming physical correctness.
- Heat sample assertions validate public input semantics and output format. The standalone transient solver regression was retained with a private formal reference; it was not run for this task.

## Validation

- `generator-tests.log`: 5 passed, 23 deselected, 2 subtests passed. This includes the dedicated generators and three heat sample assertions. No solver/model was run.
- `format-publish-harbor-tests.log`: 44 passed, 12 subtests passed; two remaining failures were explicit legacy numerical-role fixture assumptions. After correcting those fixtures, `format-publish-harbor-fixed-tests.log` confirms both pass (2 passed). All 46 collected format/publish/Harbor tests are covered by passing runs.
- An initial integration run found 6 failures (40 passed) from old numerical fixture assumptions and the loss of format identity when republishing an extracted archive. Explicit legacy fixtures were corrected; the coordinating task fixed recovery from public MANIFEST metadata.

No Hugging Face upload, model benchmark, or numerical solver was executed.

- `git diff --check` on all subtask-owned source and test files: passed.


## PDEBench pipeline follow-up

Only `src/utils/PDEBench/pipeline.py`, its README, and `tests/test_pdebench_prepare.py` were changed for this follow-up. The frozen randomizer and original generators were not changed.

- Public `prepare_entry` output uses `randomize_example(sample, seed=int(build_key[:16],16))`; `format_example` provenance is saved in the private certificate and preparation record. The public marker is `kind=format`.
- Private `reference/sample-certificates/` still retains reference/candidate/certificate materials. Formal case input/reference production is unchanged. The existing helper source is included in the pipeline tool hash to invalidate stale preparation records if the randomization implementation changes.
- A second leakage path was found by the prepare_task regression: its final generic materialization call copied sample outputs into sample/reference. The pipeline now writes the same direct grading plan only beside existing formal case references, leaving public samples free of grading/reference material.
- `pdebench-offline-tests.log`: **4 passed in 3.10s**. Exact tests: `PipelineTests::test_prepare_entry_public_output_is_random_with_reference`, `PipelineTests::test_prepare_entry_pending_reference_still_has_format_output`, `PipelineTests::test_metadata_only_clone_restores_payloads_and_preserves_definitions`, and `PipelineTests::test_real_pipeline_disjoint_resume_and_tamper_repair`.
- These checks cover public marker, private provenance and seed binding, output distinct from reference values, independent `validate_output`, actual reference_pending behavior with a mocked offline selected payload, metadata-only hydration, reuse, source selection disjointness, and formal input tamper repair. Local synthetic advection uses the existing analytic integral; the pending sorption fixture does not compute a reference. No real source download, solver, model, HF upload, or release rebuild was run.
