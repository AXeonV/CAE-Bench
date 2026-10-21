# Code_Saturne boundary configuration repair

The native 6.0 preprocessor retained Gmsh physical tags 2, 3 and 4, rather than PhysicalNames. The failed attempt stopped before the time loop with all boundary types unset. The relaxation setup now selects those numeric groups while preserving descriptive labels, geometry and frozen physical values.

The failed native run, container identity, mount evidence and script hashes are retained on Titan in the adapter-attempts archive and maintenance/codesaturne-numeric-boundary-repair.json. One finite approved queue entered the native time loop on 2026-10-21.

At step 181, the native output still showed uniform 300 K and zero velocity despite the 305/295 K wall inputs. This is an unresolved thermal boundary activation concern, not a candidate reference or validation result. The next bounded task is to inspect native thermal boundary parser semantics against the actual XML. Keep this attempt and its raw output; do not automatically retry it or admit raw completion as a reference. Detailed live evidence and next action are in maintenance/codesaturne-boundary-group-handoff.json on Titan.
