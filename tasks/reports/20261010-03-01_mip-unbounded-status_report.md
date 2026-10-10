# MIP Unbounded-Relaxation Repair / Recovery Completion Report

## Objective and authorization

L2 maintenance of existing B&B status correctness, explicitly authorized by the user's 2026-10-10 request to organize the project, repair both discovered errors and advise next steps. This is the final task in that approved sequence. Phase 9 remains open/parked, native deferred and Phase 10 not started.

## Task ID scan and Git state

01-01 and 02-01 were used; 03-01 was unused in both contracts/reports before issuance. Before this task: clean main at a2490ec, two commits ahead of origin/main. User-authorized sequential local commits allow this local-ahead state; no push is authorized by the task. Fresh remote ls-remote during recovery failed with Connection was reset; tracked origin/main remains 847bc59. No push was attempted.

## Files changed

- src/silo/mip/branch_and_bound.py
- tests/unit/test_mip_unbounded_status.py
- docs/mip_solve_cli.md
- docs/development_restart.md
- .silo-dos/project_profile.md and technical_route.md: recovery completion only
- Matching new task contract and this report

## Correctness mechanism

An unbounded node relaxation now triggers a zero-objective LP on the identical feasible region, including finite integer-bound rows and ancestor branching rows. Validate all primal coordinates for completeness, finite values, bounds and row feasibility. Strictly fractional integer coordinates trigger existing floor/ceil branching, without incumbent updates or zero-objective bound pruning. Only an integer-feasible point permits MIP UNBOUNDED: finite two-sided integer bounds force every recession direction's integer components to zero, so the original LP improving ray preserves integrality.

The newly introduced unbounded proof path uses strict integrality (0 tolerance); bounded-optimum integer tolerance remains 1e-6. Row/bound feasibility retains DEFAULT_TOLERANCE=1e-9. Probe contradiction/invalid point returns NUMERICAL_ISSUE; other probe failures return ERROR. Unresolved unbounded subtrees keep best_bound=None, preventing a false finite gap at node limits. Node counts describe tree nodes, excluding internal probe LP solves; callbacks/logs retain original-objective relaxation semantics.

## Checks and results

- New MIP regression file before fix: 16 failed, 2 passed, confirming old behavior.
- New final MIP tests: 28 deterministic cases, including tableau/revised, integer-infeasible 0.5 and 1e-7 points, true unboundedness, fractional feasibility branching, node limits, probe failure/contradiction/invalid primal, general bounded integers, pure continuous case and CLI details.
- Targeted MIP/CLI/callback regression set: 106 passed. An earlier targeted invocation omitted .venv/Scripts from PATH and failed only the 13 console-script cases; corrected environment invocation passed.
- Final python scripts/check_quality.py using project .venv and its Scripts on PATH: 1013 passed in 6.71s; all Ruff checks passed.
- Original audit reproducer: six expected/actual matches, exit 0. Both presolve on/off paths return INFEASIBLE for contradictory rows; both B&B backends return INFEASIBLE after 3 nodes for x binary, x=0.5, max y.
- git diff --check passed; CRLF/LF conversion notices are informational.
- No extra solver/build/native commands or dependency declaration changes.

## Independent review

The read-only theory_architect derived the bounded-integer recession argument and required strict integrality, same-region probes, failure propagation and unknown bounds. The implementation incorporated those obligations. An independent read-only red_team_reviewer then inspected the final code and tests and returned ACCEPT_WITH_BOUNDARIES, no fatal/major findings and no additional closure tests. Neither service ran experiments or wrote files; test execution was performed by the main thread.

## Recovery rollup

- Baseline commit: 6bd9543; historical resfs originals preserved, SHA-256 inventory recorded, local archive ignored; project .venv installed; 19 mechanical Ruff findings fixed.
- Presolve repair commit: a2490ec; improving empty column needs a feasible-point check before terminal UNBOUNDED; 10 new tests.
- This MIP repair adds 28 tests, for 38 new tests across both repairs.
- Current Python educational scope unchanged; no native or advanced capability line started.
- Historical task-ID collisions and early record gaps remain preserved historical debt.

## Commit and Remote Sync Proof

This report is included in the local commit with subject `fix(mip): verify integer feasibility before unbounded status`; its hash can be resolved via this report's git history. The commit is created after report generation. After commit, expected status is a clean worktree on main, origin/main...HEAD = 0 3, remote_sync_status=local_ahead_origin. Push not attempted (local-commit). Final response records the actual hashes/state.

## Deviations / unresolved boundaries

No scope expansion. Numeric status confidence remains bounded by the existing floating-point LP backends and tolerance conventions. Strict unbounded-proof integrality can cause extra branching on numerically near-integer points; node-limit or numerical-issue states remain conservative. Fully isolated locked dependencies, cross-platform CI and a general correctness proof are future work; the project environment currently reuses host packages with venv-local SILO and Ruff.

## Next recommended atomic task (advice only)

Establish a small deterministic independent-truth regression set for the existing supported LP/MIP scope. Use analytical LP answers or a test-only independent solver oracle, and exact enumeration for small bounded integer models. Check status, objective and primal feasibility across tableau/revised and presolve on/off, including competing infeasible/unbounded evidence and node-limit semantics. SciPy 1.16.3 is already available in the recovery environment; external solvers must remain restricted to tests/interfaces/examples per AGENTS.md. This is test evidence work, not native acceleration or a phase transition.

Recommended model: GPT-6 Sol / high for status mathematics and oracle mapping; medium for routine documentation/environment maintenance. Do not issue or execute the next task automatically. Stop after the current local commit and deliver advice.
