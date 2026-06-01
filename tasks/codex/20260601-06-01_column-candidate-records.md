# Codex Task: Column Candidate Records

## Task Metadata

Task ID: 20260601-06-01
Task slug: column-candidate-records
Task type: controlled-implementation
Risk level: L1 controlled implementation
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260601-06-01_column-candidate-records_report.md

## Objective

Add immutable column-generation candidate records with deterministic canonical-key
behavior and reduced-cost convention tests.

Do not implement a column-generation solve loop, pricing logic, LP/MIP solver calls,
public CLI behavior, JSON schema changes, examples, or generated output files.

## Context

Phase 7A created the decomposition boundary design note:

```text
notes/19_decomposition_boundary_design.md
```

The design note states that column-generation support should begin as a boundary and toy
workflow, and that column candidate representation and reduced-cost sign conventions
should be documented before implementing any driver or solve loop.

Completed Phase 7 work already added:

- immutable master/subproblem context and result records;
- immutable decomposition method, termination-reason, iteration-log, and run-summary
  records;
- boundary smoke tests confirming placeholder decomposition solvers remain no-op
  `not_solved` boundaries;
- immutable Benders cut candidate records and canonical-key tests.

This task implements only column candidate record dataclasses and focused validation
tests.

## Scope Lock

This task is atomic.

Primary objective:

- Add immutable column candidate records, canonical-key behavior, and reduced-cost
  convention tests.

Allowed changes:

- `src/silo/decomposition/column_candidate.py`
- `src/silo/decomposition/__init__.py`
- `tests/unit/test_decomposition_column_candidate.py`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260601-06-01_column-candidate-records_report.md`

Supporting allowed change:

- `tasks/codex/20260601-06-01_column-candidate-records.md` may be committed as the
  issued task contract for this execution.

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
- Do not implement a column-generation solve loop.
- Do not implement pricing logic.
- Do not add restricted-master solve behavior.
- Do not call LP or MIP solvers from decomposition code.
- Do not create decomposition examples.
- Do not issue or execute another Phase 7 task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Implementation

Implement immutable records for column-generation candidate data.

The records must:

- be frozen dataclasses at the record boundary;
- validate a nonempty deterministic column id;
- validate a nonempty generated variable name or column key;
- validate finite objective coefficients;
- defensively copy and deterministically order restricted-master row coefficient
  mappings;
- reject empty row coefficient mappings;
- reject empty row names;
- reject nonfinite row coefficients;
- reject all-zero row coefficient vectors;
- validate finite reduced costs;
- validate nonempty source pricing subproblem labels;
- validate nonnegative iteration ids;
- validate positive finite tolerances;
- validate message type;
- expose `is_improving_for(objective_sense)` with the documented convention:
  - minimization pricing improves when reduced cost is below `-tolerance`;
  - maximization pricing improves when reduced cost is above `tolerance`;
- normalize `OptimizationSense` values from strings or enum values in
  `is_improving_for`;
- expose a deterministic `canonical_key()` that is independent of column id, source
  pricing subproblem, iteration id, reduced cost, tolerance, message, and
  caller-provided row coefficient order;
- support an optional row-order argument for canonical-key row coefficient ordering;
- export the new public record class from `silo.decomposition`.

## Required Tests

Add deterministic unit tests covering:

- valid column candidate construction and normalization;
- immutability at the dataclass boundary;
- defensive copying and deterministic ordering of row coefficients;
- invalid column ids;
- invalid variable names;
- empty row coefficient mappings;
- empty row names;
- nonfinite row coefficients;
- all-zero row coefficient vectors;
- nonfinite objective coefficients;
- nonfinite reduced costs;
- invalid source pricing subproblem labels;
- invalid iteration ids;
- nonpositive or nonfinite tolerances;
- invalid message values;
- reduced-cost convention for minimization, maximization, and tolerance boundaries;
- invalid objective sense values in reduced-cost convention checks;
- canonical-key independence from column id, source pricing subproblem, iteration id,
  reduced cost, tolerance, message, and input row order;
- canonical-key ordering with an explicit row order;
- public exports from `silo.decomposition`;
- confirmation that placeholder `ColumnGenerationSolver().solve(model)` behavior remains
  `SolverStatus.NOT_SOLVED`.

## Stop Conditions

Stop and report instead of proceeding if:

- implementing the records requires modifying `benders.py`, `column_generation.py`, LP,
  MIP, presolve, cut, callback, CLI, or JSON schema behavior;
- implementing the records requires adding a column-generation solve loop or pricing
  logic;
- implementing the records requires calling LP or MIP solvers;
- tests require creating examples or generated output files;
- repository state contains unrelated dirty tracked changes that make the scope
  ambiguous.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_decomposition_column_candidate.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. Immutable column candidate records are implemented.
2. Record validation rejects invalid ids, variable names, row coefficient maps,
   objective coefficients, reduced costs, source labels, iteration ids, tolerances, and
   message values.
3. Row coefficient inputs are defensively copied into deterministic immutable storage.
4. Reduced-cost convention tests cover minimization, maximization, and tolerance
   boundaries.
5. Canonical keys are deterministic and ignore metadata fields that should not define
   duplicate mathematical columns.
6. Public exports from `silo.decomposition` include the new record.
7. Placeholder `ColumnGenerationSolver` behavior remains `not_solved`.
8. No column-generation solve loop or pricing logic is implemented.
9. No LP/MIP solver calls are introduced.
10. No LP/MIP/presolve/cut/callback behavior is changed.
11. No public CLI behavior is changed.
12. No JSON schemas are changed.
13. No examples or generated output files are created.
14. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7F note.
15. A report is created at the expected report path.
16. Required tests and checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260601-06-01_column-candidate-records_report.md
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
schemas, column-generation solve loop, pricing logic, examples, or generated output files
were modified or created.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260601-06-01_column-candidate-records.md src/silo/decomposition/column_candidate.py src/silo/decomposition/__init__.py tests/unit/test_decomposition_column_candidate.py tasks/phases/phase_07_decomposition.md tasks/reports/20260601-06-01_column-candidate-records_report.md
git commit -m "feat(decomposition): add column candidate records"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether column candidate records were implemented;
- whether validation, canonical-key, and reduced-cost convention tests were added;
- whether no column-generation solve loop or pricing logic was implemented;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
