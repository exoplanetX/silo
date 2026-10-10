# Independent Small-Instance Correctness Baseline

## Metadata
- ID: 20261010-04-01_correctness-oracles
- Type/risk: L1 test-evidence maintenance; user approved continuation on 2026-10-10
- Phase reference: existing Phase 2-5 LP/MIP capabilities; no phase transition
- Git mode: local-commit
- Report: tasks/reports/20261010-04-01_correctness-oracles_report.md

## Objective
Establish independent expected statuses and objective values for small supported LP/MIP models, and validate returned optimal primal points against the original input. The prior three recovery commits were pushed before this task; main starts clean and synchronized at a4814f4.

## Scope lock / allowed changes
New tests under tests/verification/ using analytical LP fixtures, exact bounded-integer enumeration, and optional SciPy HiGHS comparison with a test-only conversion. Supporting docs/correctness_baseline.md, dated evidence entries in docs/development_restart.md and .silo-dos/project_profile.md and technical_route.md, and this new task/report only. Main thread is sole writer; experiment_auditor may provide read-only independent evidence review.

## Forbidden changes
No src/ algorithm or interface edits, new dependencies, CI/build changes, generated/binary datasets, historical task/report edits, phase transition, native work, performance claims or push of the new commit. External solvers remain confined to tests. Do not hide a discovered mismatch with xfail, weakened expectations or silent fixture removal.

## Required checks / acceptance
Both LP backends, with and without presolve, agree with analytically established statuses/objectives. Exact enumeration independently checks finite pure-integer cases using rational arithmetic. Optimal solutions have complete finite primal values satisfying original bounds, rows, integrality and objective reconstruction. Optional SciPy tests use a separately implemented input conversion; missing SciPy skips only those tests. Deterministic targeted tests, full quality script, Ruff and git diff checks pass. Document finite coverage, tolerance, optional dependency and proof limits.

## Stop conditions
A genuine solver/oracle disagreement, unsupported-domain requirement, unexpected user edits or need for source/dependency changes. Preserve evidence and report a separate repair task if blocked; do not expand this task.

## Reporting / boundary
Record checks, case counts and independence, files, before/after Git, commit reference, initial push success, new-work push skipped and next atomic recommendation. Stop after this one task; discuss project direction with the user.
