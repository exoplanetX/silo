# Codex Task: Decomposition Context and Result Records

## Task Metadata

Task ID: 20260601-02-01
Task slug: decomposition-records
Task type: controlled-implementation
Risk level: L1 controlled implementation
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260601-02-01_decomposition-records_report.md

## Objective

Upgrade the existing decomposition placeholder modules with immutable master/subproblem
context and result records plus deterministic validation tests.

Do not implement Benders decomposition, column generation, decomposition drivers, LP/MIP
solver calls, public CLI behavior, or JSON schema changes.

## Context

Phase 7A created the decomposition boundary design note:

```text
notes/19_decomposition_boundary_design.md
```

The design note recommends first upgrading the existing decomposition placeholder modules
into immutable master/subproblem context/result records with validation tests before any
algorithmic loop or solver integration.

Existing tracked decomposition placeholders are:

- `src/silo/decomposition/__init__.py`
- `src/silo/decomposition/master.py`
- `src/silo/decomposition/subproblem.py`
- `src/silo/decomposition/benders.py`
- `src/silo/decomposition/column_generation.py`

The user explicitly approved exactly one Phase 7 L1 implementation task for decomposition
package scaffolding and immutable master/subproblem context/result records with validation
tests.

## Scope Lock

This task is atomic.

Primary objective:

- Add immutable decomposition master/subproblem context and result records with validation
  tests.

Allowed changes:

- `src/silo/decomposition/__init__.py`
- `src/silo/decomposition/master.py`
- `src/silo/decomposition/subproblem.py`
- `tests/unit/test_decomposition_records.py`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260601-02-01_decomposition-records_report.md`

Supporting allowed change:

- `tasks/codex/20260601-02-01_decomposition-records.md` may be committed as the issued
  task contract for this execution.

Forbidden changes:

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

## Required Implementation

Implement immutable record classes for:

- master problem wrapper or context;
- master result;
- subproblem wrapper or context;
- subproblem result.

The records must:

- be frozen dataclasses or otherwise immutable at the record boundary;
- validate nonempty labels/names;
- validate nonnegative iteration ids where present;
- normalize `SolverStatus` values from strings or enum values;
- validate finite objective values and finite numeric mappings;
- defensively copy caller-provided mappings into deterministic immutable storage;
- preserve existing placeholder solver behavior in `benders.py` and
  `column_generation.py`;
- export the new public record classes from `silo.decomposition`.

## Required Tests

Add deterministic unit tests covering:

- valid master problem/context/result construction;
- valid subproblem/context/result construction;
- immutability at the dataclass boundary;
- defensive copying and deterministic ordering of mapping inputs;
- invalid blank labels/names;
- invalid iteration ids;
- invalid statuses;
- nonfinite objective values or mapping values;
- negative generated cut/column counts where applicable;
- public exports from `silo.decomposition`;
- confirmation that existing placeholder Benders and column-generation solvers still
  return `not_solved` without calling LP/MIP solvers.

## Stop Conditions

Stop and report instead of proceeding if:

- implementing the records requires changing LP, MIP, presolve, cut, callback, CLI, or
  JSON schema behavior;
- implementing the records requires adding a Benders or column-generation solve loop;
- implementing the records requires calling LP or MIP solvers;
- tests require creating examples or generated output files;
- repository state contains unrelated dirty tracked changes that make the scope
  ambiguous.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_decomposition_records.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. Immutable master/subproblem context and result records are implemented.
2. Record validation rejects invalid labels, statuses, ids, counts, and nonfinite numeric
   values.
3. Mapping inputs are defensively copied into deterministic immutable storage.
4. Public exports from `silo.decomposition` include the new records.
5. Existing Benders and column-generation placeholder solvers still return `not_solved`.
6. No LP/MIP solver calls are introduced.
7. No LP/MIP/presolve/cut/callback behavior is changed.
8. No public CLI behavior is changed.
9. No JSON schemas are changed.
10. No Benders or column-generation solve loop is implemented.
11. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7B note.
12. A report is created at the expected report path.
13. Required tests and checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260601-02-01_decomposition-records_report.md
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
schemas, Benders solve loop, column-generation solve loop, examples, or generated output
files were modified or created.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260601-02-01_decomposition-records.md src/silo/decomposition/__init__.py src/silo/decomposition/master.py src/silo/decomposition/subproblem.py tests/unit/test_decomposition_records.py tasks/phases/phase_07_decomposition.md tasks/reports/20260601-02-01_decomposition-records_report.md
git commit -m "feat(decomposition): add immutable boundary records"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether the decomposition records were implemented;
- whether validation tests were added;
- whether no Benders or column-generation solve loop was implemented;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
