# Independent final recheck (round 2 of 2)

static review passed with deferred release blockers and public-network availability limitation; not numerical acceptance

Initial R1-R6 fixes remain resolved. R7 is resolved with an availability limitation: actual successful source-body download records are supported by fresh files whose exact byte counts and SHA256 this reviewer independently checked. The full seven transport tests independently passed (curl and urllib cache/resume, bad Range rejection, safe full restart, selected/all guards, byte budgets, unsafe paths, checksum rejection and deadlines).

The new curl implementation uses argument arrays without a shell, limits initial and redirected protocols to HTTP(S), bounds subprocess/curl wall time, checks resumed final Content-Range, and verifies pinned file size and SHA256 before cache promotion.

An additional reviewer empty-cache real Poisson GET timed out at the 45-second global deadline; the exception correctly rejected the attempt, and this run did not reach CalculiX. Therefore the data-agent successful cold downloads demonstrate availability at their recorded times, while public-network retrieval is intermittently unavailable. This failure is retained instead of claiming stable one-command retrieval.

Formal release remains blocked by L1: unresolved source-specific asset rights, absent independent references for expanded physics, unverified numerical reference accuracy and uncalibrated tolerances/resources. No equation solve, numerical grader, participant benchmark or numerical acceptance was performed.

Full first-round report is preserved in recheck.json history.
