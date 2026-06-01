# Codex Task: Benders Cut Candidate Records

## Task Metadata

Task ID: 20260601-05-01
Task slug: benders-cut-records
Task type: controlled-implementation
Risk level: L1 controlled implementation
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260601-05-01_benders-cut-records_report.md

## Objective

Add immutable Benders cut candidate records with deterministic canonical-key behavior and
validation tests.

Do not implement a Benders solve loop, cut generation logic, LP/MIP solver calls, cut
materialization into LP relaxations, public CLI behavior, JSON schema changes, examples,
or generated output files.

## Context

Phase 7A created the decomposition boundary design note:

```text
notes/19_decomposition_boundary_design.md
```

The design note states that Benders-style support should begin as an educational
boundary, not a general algorithm, and that cut-candidate representation should be
explicit before any Benders driver or solve loop is implemented.

Completed Phase 7 work already added:

- immutable master/subproblem context and result records;
- immutable decomposition method, termination-reason, iteration-log, and run-summary
  records;
- boundary smoke tests confirming the placeholder Benders and column-generation solvers
  remain no-op `not_solved` boundaries.

This task implements only Benders cut record dataclasses and focused validation tests.

## Scope Lock

This task is atomic.

Primary objective:

- Add immutable Benders cut candidate records and canonical-key tests.

Allowed changes:

- `src/silo/decomposition/benders_cut.py`
- `src/silo/decomposition/__init__.py`
- `tests/unit/test_decomposition_benders_cut.py`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260601-05-01_benders-cut-records_report.md`

Supporting allowed change:

- `tasks/codex/20260601-05-01_benders-cut-records.md` may be committed as the issued
  task contract for this execution.

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
- Do not implement a Benders solve loop.
- Do not implement Benders cut generation logic.
- Do not materialize Benders cuts into LP relaxations.
- Do not call LP or MIP solvers from decomposition code.
- Do not create decomposition examples.
- Do not issue or execute another Phase 7 task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Implementation

Implement immutable records for:

- Benders cut type labels;
- Benders cut candidate data.

The records must:

- be frozen dataclasses or enums at the record boundary;
- support feasibility and optimality cut types;
- validate a nonempty deterministic cut id;
- normalize cut type values from strings or enum values;
- defensively copy and deterministically order coefficient mappings;
- reject empty coefficient mappings;
- reject empty variable names;
- reject nonfinite coefficients;
- reject all-zero coefficient vectors;
- normalize `ConstraintSense` values from strings or enum values;
- validate finite RHS values;
- validate nonempty source subproblem labels;
- validate nonnegative iteration ids;
- validate positive finite tolerances;
- validate message type;
- expose a deterministic `canonical_key()` that is independent of cut id, source
  subproblem, iteration id, tolerance, message, and caller-provided coefficient order;
- support an optional variable-order argument for canonical-key coefficient ordering;
- export the new public record classes from `silo.decomposition`.

## Required Tests

Add deterministic unit tests covering:

- valid feasibility cut construction and normalization;
- valid optimality cut construction and normalization;
- immutability at the dataclass boundary;
- defensive copying and deterministic ordering of coefficients;
- invalid cut ids;
- invalid cut types;
- empty coefficient mappings;
- empty variable names;
- nonfinite coefficients;
- all-zero coefficient vectors;
- invalid constraint senses;
- nonfinite RHS values;
- invalid source subproblem labels;
- invalid iteration ids;
- nonpositive or nonfinite tolerances;
- invalid message values;
- canonical-key independence from cut id, source subproblem, iteration id, tolerance,
  message, and input coefficient order;
- canonical-key ordering with an explicit variable order;
- public exports from `silo.decomposition`;
- confirmation that the placeholder `BendersSolver().solve(model)` behavior remains
  `SolverStatus.NOT_SOLVED`.

## Stop Conditions

Stop and report instead of proceeding if:

- implementing the records requires modifying `benders.py`, `column_generation.py`, LP,
  MIP, presolve, cut, callback, CLI, or JSON schema behavior;
- implementing the records requires adding a Benders solve loop or cut generation logic;
- implementing the records requires calling LP or MIP solvers;
- tests require creating examples or generated output files;
- repository state contains unrelated dirty tracked changes that make the scope
  ambiguous.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_decomposition_benders_cut.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. Immutable Benders cut type and cut candidate records are implemented.
2. Record validation rejects invalid ids, cut types, coefficient maps, senses, RHS values,
   source labels, iteration ids, tolerances, and message values.
3. Coefficient inputs are defensively copied into deterministic immutable storage.
4. Canonical keys are deterministic and ignore metadata fields that should not define
   duplicate mathematical cuts.
5. Public exports from `silo.decomposition` include the new records.
6. Placeholder `BendersSolver` behavior remains `not_solved`.
7. No Benders solve loop or cut generation logic is implemented.
8. No LP/MIP solver calls are introduced.
9. No LP/MIP/presolve/cut/callback behavior is changed.
10. No public CLI behavior is changed.
11. No JSON schemas are changed.
12. No examples or generated output files are created.
13. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7E note.
14. A report is created at the expected report path.
15. Required tests and checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260601-05-01_benders-cut-records_report.md
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
schemas, Benders solve loop, cut generation logic, examples, or generated output files
were modified or created.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260601-05-01_benders-cut-records.md src/silo/decomposition/benders_cut.py src/silo/decomposition/__init__.py tests/unit/test_decomposition_benders_cut.py tasks/phases/phase_07_decomposition.md tasks/reports/20260601-05-01_benders-cut-records_report.md
git commit -m "feat(decomposition): add benders cut records"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether Benders cut candidate records were implemented;
- whether validation and canonical-key tests were added;
- whether no Benders solve loop or cut generation logic was implemented;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
