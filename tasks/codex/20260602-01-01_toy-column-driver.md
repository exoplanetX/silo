# Codex Task: Toy Column-Generation Driver

## Task Metadata

Task ID: 20260602-01-01
Task slug: toy-column-driver
Task type: review-gated-implementation
Risk level: L2 high-risk
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260602-01-01_toy-column-driver_report.md

## Objective

Add one toy column-generation-style driver for a documented fixture, with explicit
reduced-cost conventions, deterministic iteration logs, duplicate/no-improving-column
stopping, and no branch-and-price claims.

This task must not be executed without explicit user approval because it introduces
fixture-level decomposition algorithm behavior.

## Context

Phase 7A created the decomposition boundary design note:

```text
notes/19_decomposition_boundary_design.md
```

The design note states that column-generation support should begin as a boundary and toy
workflow, not as a production framework. It also states that reduced-cost sign
conventions must be documented before implementation:

- for minimization pricing, an improving column has reduced cost below `-tolerance`;
- for maximization pricing, an improving column has reduced cost above `tolerance`.

Completed Phase 7 work already added:

- immutable master/subproblem context and result records;
- immutable decomposition method, termination-reason, iteration-log, and run-summary
  records;
- immutable Benders cut candidate records;
- immutable column candidate records and reduced-cost convention tests;
- a no-op decomposition driver boundary;
- a toy fixture-only Benders-style driver with deterministic stopping tests.

This task is the first fixture-level column-generation behavior task. It must remain
toy-only and must not modify existing LP/MIP behavior or the placeholder
`ColumnGenerationSolver` API.

## Scope Lock

This task is atomic.

Primary objective:

- Add a toy column-generation-style driver for a documented fixture and deterministic
  tests.

Allowed changes:

- `src/silo/decomposition/toy_column_generation.py`
- `src/silo/decomposition/__init__.py`
- `tests/unit/test_decomposition_toy_column_generation.py`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260602-01-01_toy-column-driver_report.md`

Supporting allowed change:

- `tasks/codex/20260602-01-01_toy-column-driver.md` may be committed as the issued task
  contract for this execution.

Forbidden changes:

- Do not modify `src/silo/decomposition/benders.py`.
- Do not modify `src/silo/decomposition/column_generation.py`.
- Do not modify LP solver behavior.
- Do not modify MIP solver behavior.
- Do not modify presolve behavior.
- Do not modify Phase 6 cut or callback behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify examples.
- Do not implement general column generation.
- Do not implement branch-and-price.
- Do not implement Benders decomposition.
- Do not add restricted-master solve behavior.
- Do not call LP or MIP solvers from decomposition code.
- Do not add columns to model objects or mutate user-authored models.
- Do not create decomposition examples.
- Do not issue or execute another Phase 7 task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Implementation

Implement a toy-only column-generation-style driver boundary that:

- is represented by immutable dataclasses or small explicit records where appropriate;
- documents its fixture-level validity assumptions in class/module docstrings or test
  names;
- accepts only pre-built toy fixture data, not arbitrary `Model` objects;
- uses existing `ColumnCandidate` records for fixture-provided column candidates;
- records deterministic `DecompositionIterationLog` entries;
- returns a `DecompositionRunSummary`;
- stops when a fixture iteration provides no improving columns under the configured
  objective sense;
- stops when a duplicate column canonical key is detected;
- stops when the configured iteration limit is reached;
- uses existing `ColumnCandidate`, `DecompositionIterationLog`,
  `DecompositionRunSummary`, `DecompositionMethod`, and
  `DecompositionTerminationReason` records;
- does not call LP or MIP solvers;
- does not modify public `Solution` schemas;
- exports the toy driver only from `silo.decomposition` if the implementation keeps the
  public surface clearly marked as toy/educational.

## Required Tests

Add deterministic unit tests covering:

- one toy minimization run that accepts one or more improving fixture-provided column
  candidates and then stops with `no_improving_column`;
- one toy maximization run that applies the documented reduced-cost convention;
- one toy run that stops on duplicate column canonical key detection;
- one toy run that stops on iteration limit;
- deterministic iteration ids and run summary ordering;
- generated and accepted column counts in iteration logs;
- duplicate counts in iteration logs;
- zero generated cut counts;
- no LP/MIP solver calls or `Model` inputs are required;
- no mutation of caller-provided fixture column data;
- public exports from `silo.decomposition`, if exported;
- placeholder `ColumnGenerationSolver().solve(model)` behavior remains
  `SolverStatus.NOT_SOLVED`;
- lower-layer packages still do not import decomposition.

## Stop Conditions

Stop and report instead of proceeding if:

- implementing the toy driver requires modifying `benders.py`, `column_generation.py`,
  LP, MIP, presolve, cut, callback, CLI, or JSON schema behavior;
- implementing the toy driver requires calling LP or MIP solvers;
- implementing the toy driver requires mutating model objects or adding columns to a
  restricted master;
- implementing the toy driver becomes a general column-generation solver rather than a
  toy fixture driver;
- tests require creating examples or generated output files;
- repository state contains unrelated dirty tracked changes that make the scope
  ambiguous.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_decomposition_toy_column_generation.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. A toy-only column-generation-style driver is implemented in a separate module.
2. The fixture-level validity assumptions and reduced-cost conventions are explicit.
3. The driver returns deterministic `DecompositionRunSummary` records.
4. Tests cover no-improving-column stopping, duplicate-column stopping, and
   iteration-limit stopping.
5. Tests cover minimization and maximization reduced-cost conventions.
6. Tests verify generated/accepted/duplicate column counts and zero cut counts.
7. Tests verify no `Model` inputs or LP/MIP solver calls are required.
8. Placeholder `ColumnGenerationSolver` behavior remains `not_solved`.
9. No general column-generation solver is implemented.
10. No branch-and-price behavior is implemented.
11. No LP/MIP solver calls are introduced.
12. No LP/MIP/presolve/cut/callback behavior is changed.
13. No public CLI behavior is changed.
14. No JSON schemas are changed.
15. No examples or generated output files are created.
16. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7I note.
17. A report is created at the expected report path.
18. Required tests and checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260602-01-01_toy-column-driver_report.md
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

The report must explicitly state that no LP/MIP solver behavior, public CLI behavior, JSON
schemas, general column-generation solver, branch-and-price behavior, examples, or
generated output files were modified or created.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260602-01-01_toy-column-driver.md src/silo/decomposition/toy_column_generation.py src/silo/decomposition/__init__.py tests/unit/test_decomposition_toy_column_generation.py tasks/phases/phase_07_decomposition.md tasks/reports/20260602-01-01_toy-column-driver_report.md
git commit -m "feat(decomposition): add toy column-generation driver"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether the toy column-generation driver was implemented;
- whether deterministic fixture tests were added;
- whether no general column-generation solver or LP/MIP solver calls were implemented;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
