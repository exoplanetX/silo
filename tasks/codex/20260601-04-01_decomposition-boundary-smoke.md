# Codex Task: Decomposition Boundary Smoke Tests

## Task Metadata

Task ID: 20260601-04-01
Task slug: decomposition-boundary-smoke
Task type: regression-test-addition
Risk level: L0 safe
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260601-04-01_decomposition-boundary-smoke_report.md

## Objective

Add deterministic decomposition boundary smoke tests showing that the placeholder
Benders and column-generation solvers remain no-op `not_solved` boundaries while the new
decomposition logging records can wrap their statuses without implementing solve loops.

Do not modify solver source code, CLI behavior, JSON schemas, LP/MIP behavior, examples,
or existing decomposition implementation files.

## Context

Phase 7A created the decomposition boundary design note:

```text
notes/19_decomposition_boundary_design.md
```

Phase 7B added immutable master/subproblem context and result records.

Phase 7C added immutable decomposition method, termination-reason, iteration-log, and
run-summary records. Its report recommends a small boundary smoke-test task before
moving to richer candidate-record or driver work.

This task implements only regression tests. It must not implement Benders decomposition,
column generation, decomposition drivers, LP/MIP solver calls, public CLI behavior, or
JSON schema changes.

## Scope Lock

This task is atomic.

Primary objective:

- Add focused smoke tests for the current decomposition boundary and dependency
  direction.

Allowed changes:

- `tests/unit/test_decomposition_boundary_smoke.py`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260601-04-01_decomposition-boundary-smoke_report.md`

Supporting allowed change:

- `tasks/codex/20260601-04-01_decomposition-boundary-smoke.md` may be committed as the
  issued task contract for this execution.

Forbidden changes:

- Do not modify solver source code under `src/silo/`.
- Do not modify existing tests.
- Do not modify LP solver behavior.
- Do not modify MIP solver behavior.
- Do not modify presolve behavior.
- Do not modify cut or callback behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify examples.
- Do not implement a Benders solve loop.
- Do not implement a column-generation solve loop.
- Do not call LP or MIP solvers from decomposition code.
- Do not create decomposition examples.
- Do not issue or execute another Phase 7 task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Tests

Add deterministic unit tests covering:

- `BendersSolver().solve(model)` still returns `SolverStatus.NOT_SOLVED` with the
  placeholder message.
- `ColumnGenerationSolver().solve(model)` still returns `SolverStatus.NOT_SOLVED` with
  the placeholder message.
- The returned placeholder statuses can be represented in `DecompositionIterationLog`
  and `DecompositionRunSummary` records without invoking LP/MIP solvers or solve loops.
- Decomposition logging records remain separate from public `Solution` schemas.
- Lower layers `core`, `modeling`, `presolve`, `lp`, and `mip` do not import
  `silo.decomposition`.

## Stop Conditions

Stop and report instead of proceeding if:

- the smoke tests require modifying any source file under `src/silo/`;
- the smoke tests require changing existing tests;
- the smoke tests require implementing Benders or column-generation solve loops;
- the smoke tests require calling LP or MIP solvers;
- the smoke tests require CLI or JSON schema changes;
- repository state contains unrelated dirty tracked changes that make the scope
  ambiguous.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_decomposition_boundary_smoke.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. A new focused smoke-test file is added.
2. Placeholder Benders and column-generation solvers are verified to remain `not_solved`.
3. The new decomposition log records are verified to wrap placeholder statuses without
   requiring solver loops.
4. Lower-layer packages are verified not to import decomposition.
5. No source code under `src/silo/` is modified.
6. No existing tests are modified.
7. No LP/MIP/presolve/cut/callback behavior is changed.
8. No public CLI behavior is changed.
9. No JSON schemas are changed.
10. No examples or generated output files are created.
11. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7D smoke-test
    note.
12. A report is created at the expected report path.
13. Required tests and checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260601-04-01_decomposition-boundary-smoke_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk and approval:
Files changed:
Implementation summary:
Tests added:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

The report must explicitly state that no solver source code, LP/MIP solver behavior,
public CLI behavior, JSON schemas, Benders solve loop, column-generation solve loop,
examples, or generated output files were modified or created.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260601-04-01_decomposition-boundary-smoke.md tests/unit/test_decomposition_boundary_smoke.py tasks/phases/phase_07_decomposition.md tasks/reports/20260601-04-01_decomposition-boundary-smoke_report.md
git commit -m "test(decomposition): add boundary smoke coverage"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether boundary smoke tests were added;
- whether no source code was modified;
- whether no Benders or column-generation solve loop was implemented;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
