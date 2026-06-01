# Codex Task: Toy Benders Driver

## Task Metadata

Task ID: 20260601-08-01
Task slug: toy-benders-driver
Task type: review-gated-implementation
Risk level: L2 high-risk
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260601-08-01_toy-benders-driver_report.md

## Objective

Add one toy Benders-style driver for a documented fixture, with explicit validity
assumptions, deterministic iteration logs, duplicate/no-cut stopping, and no performance
claims.

This task must not be executed without explicit user approval because it introduces
fixture-level decomposition algorithm behavior.

## Context

Phase 7A created the decomposition boundary design note:

```text
notes/19_decomposition_boundary_design.md
```

The design note states that early Benders-style support should remain educational and
fixture-level, not a general algorithm. It also states that feasibility and optimality
cuts should begin as placeholders with documented assumptions and that no Phase 7 Benders
task should claim industrial performance, broad model support, or automatic decomposition
detection.

Completed Phase 7 work already added:

- immutable master/subproblem context and result records;
- immutable decomposition method, termination-reason, iteration-log, and run-summary
  records;
- boundary smoke tests confirming placeholder decomposition solvers remain no-op
  `not_solved` boundaries;
- immutable Benders cut candidate records;
- immutable column candidate records and reduced-cost convention tests;
- a no-op decomposition driver boundary that records one deterministic iteration and
  does not accept models or call LP/MIP solvers.

This task is the first fixture-level Benders behavior task. It must remain toy-only and
must not modify existing LP/MIP behavior or the placeholder `BendersSolver` API.

## Scope Lock

This task is atomic.

Primary objective:

- Add a toy Benders-style driver for a documented fixture and deterministic tests.

Allowed changes:

- `src/silo/decomposition/toy_benders.py`
- `src/silo/decomposition/__init__.py`
- `tests/unit/test_decomposition_toy_benders.py`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260601-08-01_toy-benders-driver_report.md`

Supporting allowed change:

- `tasks/codex/20260601-08-01_toy-benders-driver.md` may be committed as the issued task
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
- Do not implement general Benders decomposition.
- Do not implement column generation.
- Do not implement pricing logic.
- Do not add restricted-master solve behavior.
- Do not call LP or MIP solvers from decomposition code.
- Do not materialize cuts into LP relaxations.
- Do not mutate user-authored models.
- Do not create decomposition examples.
- Do not issue or execute another Phase 7 task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Implementation

Implement a toy-only Benders-style driver boundary that:

- is represented by immutable dataclasses or small explicit records where appropriate;
- documents its fixture-level validity assumptions in class/module docstrings or test
  names;
- accepts only pre-built toy fixture data, not arbitrary `Model` objects;
- generates deterministic `BendersCutCandidate` placeholders from fixture-provided cut
  data;
- records deterministic `DecompositionIterationLog` entries;
- returns a `DecompositionRunSummary`;
- stops when a fixture iteration provides no cut candidates;
- stops when a duplicate Benders cut canonical key is detected;
- stops when the configured iteration limit is reached;
- uses existing `BendersCutCandidate`, `DecompositionIterationLog`,
  `DecompositionRunSummary`, `DecompositionMethod`, and
  `DecompositionTerminationReason` records;
- does not call LP or MIP solvers;
- does not modify public `Solution` schemas;
- exports the toy driver only from `silo.decomposition` if the implementation keeps the
  public surface clearly marked as toy/educational.

## Required Tests

Add deterministic unit tests covering:

- one toy run that accepts one or more fixture-provided Benders cut candidates and then
  stops with `no_cut_generated`;
- one toy run that stops on duplicate cut canonical key detection;
- one toy run that stops on iteration limit;
- deterministic iteration ids and run summary ordering;
- generated and accepted cut counts in iteration logs;
- duplicate counts in iteration logs;
- no generated column counts;
- no LP/MIP solver calls or `Model` inputs are required;
- no mutation of caller-provided fixture cut data;
- public exports from `silo.decomposition`, if exported;
- placeholder `BendersSolver().solve(model)` behavior remains `SolverStatus.NOT_SOLVED`;
- lower-layer packages still do not import decomposition.

## Stop Conditions

Stop and report instead of proceeding if:

- implementing the toy driver requires modifying `benders.py`, `column_generation.py`,
  LP, MIP, presolve, cut, callback, CLI, or JSON schema behavior;
- implementing the toy driver requires calling LP or MIP solvers;
- implementing the toy driver requires materializing cuts into LP relaxations;
- implementing the toy driver requires mutating user-authored models;
- the implementation would become a general Benders solver rather than a toy fixture
  driver;
- tests require creating examples or generated output files;
- repository state contains unrelated dirty tracked changes that make the scope
  ambiguous.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_decomposition_toy_benders.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. A toy-only Benders-style driver is implemented in a separate module.
2. The fixture-level validity assumptions are explicit.
3. The driver returns deterministic `DecompositionRunSummary` records.
4. Tests cover no-cut stopping, duplicate-cut stopping, and iteration-limit stopping.
5. Tests verify generated/accepted/duplicate cut counts and zero column counts.
6. Tests verify no `Model` inputs or LP/MIP solver calls are required.
7. Placeholder `BendersSolver` behavior remains `not_solved`.
8. No general Benders solver is implemented.
9. No column-generation behavior is implemented.
10. No LP/MIP solver calls are introduced.
11. No LP/MIP/presolve/cut/callback behavior is changed.
12. No public CLI behavior is changed.
13. No JSON schemas are changed.
14. No examples or generated output files are created.
15. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7H note.
16. A report is created at the expected report path.
17. Required tests and checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260601-08-01_toy-benders-driver_report.md
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
schemas, general Benders solve loop, column-generation behavior, examples, or generated
output files were modified or created.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260601-08-01_toy-benders-driver.md src/silo/decomposition/toy_benders.py src/silo/decomposition/__init__.py tests/unit/test_decomposition_toy_benders.py tasks/phases/phase_07_decomposition.md tasks/reports/20260601-08-01_toy-benders-driver_report.md
git commit -m "feat(decomposition): add toy benders driver"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether the toy Benders driver was implemented;
- whether deterministic fixture tests were added;
- whether no general Benders solver or LP/MIP solver calls were implemented;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
