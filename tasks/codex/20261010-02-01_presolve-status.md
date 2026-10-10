# Presolve Unbounded-Status Repair

## Metadata
- ID: 20261010-02-01_presolve-status
- Risk: L2 solver correctness maintenance, explicitly approved by user on 2026-10-10
- Phase reference: Phase 4 existing conservative presolve scope
- Type: bug fix
- Git mode: local-commit
- Report: tasks/reports/20261010-02-01_presolve-status_report.md

## Objective
Prevent an improving empty column from masking an infeasible remaining system. Presolve may return UNBOUNDED only with a cheap sufficient feasible-point check; otherwise retain the model and defer final status to the LP solver. Preserve presolve's independence from LP modules.

## Scope lock and allowed changes
src/silo/presolve/presolver.py, column_diagnostics.py; tests/unit/test_presolve_status_correctness.py; docs/lp_solver.md; this new contract/report only. Use existing tolerances and statuses; do not change public schema or add LP dependencies.

## Forbidden changes
MIP algorithms, LP algorithms, CLI/schema, dependency/build configuration, historical task files/reports, phase/native decisions, skill files, push.

## Required checks and acceptance
First reproduce the contradictory nonempty rows plus improving empty column; test tableau/revised with presolve on/off, a genuinely unbounded feasible background, fixed-variable-induced contradiction and deferred feasibility. Targeted presolve/CLI regression tests, Ruff and diff checks pass. Existing simple empty-column unbounded diagnostics remain supported when a feasible point is certified.

## Stop conditions
Unrelated implementation required, unexpected edits, schema/dependency/phase changes. Record wider issues instead.

## Execution context and report
Baseline commit 6bd9543 is local-only. User authorized this recovery sequence, including proceeding local-ahead without push. Record before/after Git state, test evidence, changed files, commit reference, no-push result and next authorized MIP repair. Stop this task at its commit before issuing the next one.
