# 20260602-09-01 Uncertainty Naming Helpers

## Task metadata

- Task ID: 20260602-09-01
- Slug: uncertainty-naming
- Mode: SILO-DOS Mode A auto-one
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 8 stochastic and robust optimization extensions
- Design reference: `notes/20_uncertainty_boundary_design.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260602-09-01_uncertainty-naming_report.md`

## Objective

Add deterministic uncertainty naming-convention helpers and tests for scenario variables,
scenario constraints, and nonanticipativity constraints.

## Context

Phase 8 already has finite-scenario records, uncertainty boundary smoke tests, and passive
stochastic model wrapper records. The next smallest design-backed step is to make the
documented deterministic naming convention executable and tested before any
deterministic-equivalent builder is attempted.

The design note recommends:

- scenario variable: `{base_name}__s::{scenario_id}`
- scenario constraint: `{base_name}__s::{scenario_id}`
- nonanticipativity constraint: `na::{base_variable}::{scenario_id}`

## Scope lock

Implement only pure naming helpers. The helpers must be deterministic, validation-only,
and free of solver/model transformation behavior.

## Allowed changes

- `src/silo/uncertainty/naming.py`
- `tests/unit/test_uncertainty_naming.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/codex/20260602-09-01_uncertainty-naming.md`
- `tasks/reports/20260602-09-01_uncertainty-naming_report.md`

## Forbidden changes

- Do not modify `src/silo/uncertainty/__init__.py`.
- Do not modify `src/silo/uncertainty/deterministic_equivalent.py`.
- Do not build deterministic equivalents.
- Do not implement robust wrappers.
- Do not implement uncertainty sets.
- Do not modify stochastic wrapper semantics.
- Do not modify LP, MIP, presolve, cuts, decomposition, or core solver behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not create or modify examples.
- Do not issue or execute another task.
- Do not start Phase 9.

## Implementation requirements

- Add a new `src/silo/uncertainty/naming.py` module.
- Define explicit constants for the scenario component delimiter and
  nonanticipativity prefix/delimiter.
- Implement pure helper functions for:
  - scenario variable names;
  - scenario constraint names;
  - nonanticipativity constraint names.
- Normalize labels by requiring strings, trimming surrounding whitespace, and rejecting
  empty results.
- Reject names that would make the generated convention ambiguous:
  - scenario component helpers must reject labels containing the scenario component
    delimiter;
  - nonanticipativity helpers must reject labels containing the nonanticipativity
    delimiter.
- Do not import solver layers, call solvers, create models, or transform models.
- Keep package-level `silo.uncertainty` exports unchanged.

## Required tests

Add focused tests covering:

- exact scenario variable naming;
- exact scenario constraint naming;
- exact nonanticipativity constraint naming;
- deterministic whitespace trimming;
- rejection of non-string labels;
- rejection of empty labels;
- rejection of ambiguous delimiter-containing labels;
- static guard that the naming module does not import solver layers or deterministic
  equivalent construction;
- package public export boundary remains unchanged.

## Required checks

Run:

```powershell
pytest tests/unit/test_uncertainty_naming.py tests/unit/test_uncertainty_boundary_smoke.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- Naming helper outputs match the documented Phase 8 convention exactly.
- Invalid or ambiguous labels are rejected with clear exceptions.
- The helpers remain pure and do not create or mutate models.
- Existing public exports, CLI behavior, JSON schemas, and solver behavior remain
  unchanged.
- Required checks pass.
- The required report is created.

## Stop conditions

Stop and report instead of proceeding if the task appears to require:

- deterministic-equivalent construction;
- public package export changes;
- CLI or JSON schema changes;
- changes to LP/MIP/presolve/cuts/decomposition behavior;
- modifying any file outside the allowed list.

## Final response requirements

Report:

- generated task path;
- risk level and execution decision;
- files changed;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no second task was issued or executed.
