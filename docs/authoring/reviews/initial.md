# Independent initial review

needs_revision; structural/provenance review only, not numerical acceptance

Coverage: Poisson 3 cases + 1 sample + 1 pending; CalculiX 2 cases + 1 sample + 2 pending. Every actual JSON variant read, both inventory scripts run, all 10 input structures independently validated.

Source semantics: Poisson four holes and conditions=[] are explicitly represented by physics parameters. COMSOL header supplies m and dimensionless u. CalculiX SI is an OJ addition; original inp nodes are used, not FRD visualization nodes. The adapter projects full integration-point tensor onto original member tangent and checks all eight projections before using the first; no solver or numerical evaluator was run.

Public ZIP separation and manifest hashes independently passed. Formal release remains blocked by unverified source data rights, numerical accuracy and resources.

## R1 open
File/location: src/utils/authoring/fetch.py / fetch download read loop and sha256 deadline
Evidence: Original cache fetch --max-seconds 0.000001 returned ok:true elapsed .0012368. Latest cache reproduction correctly exits 1. Network loop still calls response.read(1MiB), which may internally perform repeated socket reads under the same timeout.
Impact: Slow trickle can delay returning beyond global deadline.
Revision required: Use response.read1 per iteration or an independent wallclock-bounded worker; retain cache deadline checks and verify slow-trickle fixture.

## R2 resolved_during_initial
File/location: tasks/calculix-truss/DATA.md / conditions nodal_force data.force
Evidence: All 3 official/sample and 2 pending inputs use data.force.field. Initial document named data.field; latest document now data.force.
Impact: Wrong JSON path prevents force reading.
Revision required: Keep data.force matching every input.

## R3 resolved_during_initial
File/location: tasks/pinnacle-poisson-cg/instruction.md; tasks/calculix-truss/instruction.md / sample links
Evidence: Initial samples/01 did not exist; latest samples/source-001 links match both existing public samples.
Impact: Broken advertised complete sample.
Revision required: Keep actual sample paths.

## R4 open
File/location: docs/authoring/source-registry.json / public_reference_field.scope
Evidence: Scope says new sampling locations can reuse the source field; adapter only selects original published coordinate rows and performs no interpolation.
Impact: Could incorrectly grant reference validity to unseen coordinates.
Revision required: Specify only subsets of published source rows at their original coordinates may reuse corresponding values; new coordinates require independent reference.

## R5 resolved_during_initial
File/location: tasks/pinnacle-poisson-cg/README.md; tasks/calculix-truss/README.md / preparation commands
Evidence: Initial nonexistent src/utils/authoring/prepare.py --profile minimum; latest uses workflow.py and task author/prepare.py --mode sample|selected|all.
Impact: Reproducibility command previously failed.
Revision required: Retain real CLI and bounded explicit all.

## R6 resolved_during_initial
File/location: src/utils/publish_dist.py; src/utils/prepare_harbor.py / release_ready gate
Evidence: Initial truthiness accepted string false. Latest code requires is True; both actual authoring-status.json are false; release gate unit test passes.
Impact: Malformed config could enable uncalibrated evaluation.
Revision required: Retain strict bool gate and false statuses until independent numerical acceptance.

## L1 deferred_release_blocker
File/location: tasks/calculix-truss/DESIGN.md; tasks/pinnacle-poisson-cg/DESIGN.md / license/numerical acceptance
Evidence: Source-specific data rights unresolved, added physics cases lack references, source numerical error and resource calibration not independently verified.
Impact: Cannot conclude formal release or numerical correctness.
Revision required: Keep release_ready false and evidence queue open; independently resolve before release.

