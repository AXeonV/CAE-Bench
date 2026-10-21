# Native Thetis staging for remaining shallow-water cases

The installed Firedrake image imports successfully but does not include Thetis. Official Thetis release source is pinned to commit 162c605079611dfce69b4d1182181a421116b141. Its shallowwater_eq.LinearDragTerm supplies the native -C*u velocity residual, a prospective match for the frozen linear momentum drag in smooth fully wet cases. This is a source/module finding, not completed physical equivalence or a reference result.

The first proposed adapter is 2.9.2 case08: exact frozen P1 initial depth and velocity, flat bed, drag_rate=.1, all impermeable slip walls, no rotation or viscosity, end time=.5. Native nonlinear transport, boundary treatment and output sampling still require case configuration. No custom PDE or friction law may be written, and no quadratic/Manning law may substitute for linear drag.

stage_native_thetis.py runs one isolated, one-core, 2 GiB dependency/download/import stage with a 30-minute cap. It preserves downloaded distributions and SHA256 evidence in Titan maintenance; it changes neither shared host Python nor the base image. A successful import is native_solver_imported_pending_case_adapter and does not count as case computation, reference, or validation. A failed stage is retained and never automatically retried. Next inspect its exact status and implement the finite native case adapter only after import succeeds.

Sources: https://github.com/thetisproject/thetis/blob/162c605079611dfce69b4d1182181a421116b141/thetis/shallowwater_eq.py and https://thetisproject.org/download.html . Live resource decision and exact follow-up are stored in Titan maintenance/native-thetis-adapter-handoff.json.
