# MIP Unbounded-Relaxation Status Repair

## Metadata
- ID: 20261010-03-01_mip-unbounded-status
- Risk: L2 correctness maintenance explicitly approved by user on 2026-10-10
- Phase reference: Phase 5 existing bounded-integer B&B scope
- Git mode: local-commit
- Report: tasks/reports/20261010-03-01_mip-unbounded-status_report.md

## Objective / design
Distinguish integer infeasibility from true MIP unboundedness. For an unbounded LP relaxation, solve the identical node feasible region with a zero objective. Validate a complete finite feasible point. Use strict integer coordinates for this proof path; if fractional, branch with existing floor/ceil rule without using the zero objective for incumbent/bound pruning. If integer-feasible, finite bounds on all integer coordinates force every recession direction to have zero integer components, so the original LP improving ray also proves MIP unboundedness. Theory_architect independently reviewed this bounded-domain argument and its failure boundaries.

## Scope lock / allowed changes
src/silo/mip/branch_and_bound.py; tests/unit/test_mip_unbounded_status.py; tests/unit/test_cli_mip_solve.py if CLI coverage needs it; docs/mip_solve_cli.md; docs/development_restart.md; .silo-dos/project_profile.md and technical_route.md only to record repair completion; this new task/report. Preserve deterministic tree order, existing schemas, LP backends, callbacks and bounded-optimum behavior.

## Forbidden changes
No new solver capability line, unbounded integer variables, native implementation, LP algorithms, public statuses/CLI/schema additions, dependency/build changes, phase changes, skill changes, historical task/report edits or push.

## Required checks / acceptance
Red/green deterministic tests for both LP backends: infeasible integer set with unbounded relaxation, true unbounded MIP, fractional feasibility point requiring branching, strict integrality near integer tolerance, node-limit with unknown bound, probe failures/contradictory statuses/missing or nonfinite primal values. Verify no zero-objective incumbent or finite bound. Existing MIP/CLI/callback tests and final full quality script pass. Original audit reproducer exits 0.

## Stop conditions
Proof assumptions do not hold, unrelated solver/CLI changes required, unexpected user edits or external/native dependency needed. Report broader numerical questions without expanding scope.

## Reporting and execution boundary
Before: clean main after a2490ec, local-ahead under explicit recovery authorization. Record files/tests/review, model/tolerance conventions, before/after Git, commit reference, no push and next-step recommendation. This is the last authorized implementation task in the sequence; stop after it and report advice only.
