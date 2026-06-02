# 20260602-13-01 Uncertainty Sets

## Task metadata

- Task ID: 20260602-13-01
- Slug: uncertainty-sets
- Mode: SILO-DOS Mode A auto-one
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 8 stochastic and robust optimization extensions
- Design reference: `notes/20_uncertainty_boundary_design.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260602-13-01_uncertainty-sets_report.md`

## Objective

Add immutable uncertainty-set records for simple interval and box uncertainty with
validation tests.

## Context

The Phase 8 progress audit recommended filling the missing robust/uncertainty-set side
before considering closure. This task adds passive records only; it must not implement
robust counterparts or solver behavior.

## Scope lock

Implement only immutable interval and box uncertainty records. Do not transform models,
solve models, expose public CLI/schema contracts, or implement robust counterparts.

## Allowed changes

- `src/silo/uncertainty/uncertainty_set.py`
- `tests/unit/test_uncertainty_set.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/codex/20260602-13-01_uncertainty-sets.md`
- `tasks/reports/20260602-13-01_uncertainty-sets_report.md`

## Forbidden changes

- Do not modify `src/silo/uncertainty/__init__.py`.
- Do not modify `src/silo/uncertainty/robust_model.py`.
- Do not modify stochastic wrapper or deterministic-equivalent behavior.
- Do not implement robust counterpart construction.
- Do not implement deterministic equivalents.
- Do not modify LP, MIP, presolve, cuts, decomposition, or core solver behavior.
- Do not call LP or MIP solvers.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not create or modify examples.
- Do not issue or execute another task.
- Do not mark Phase 8 complete.
- Do not start Phase 9.

## Implementation requirements

- Replace the placeholder uncertainty-set record with immutable dataclasses for:
  - scalar interval uncertainty;
  - independent box uncertainty as a deterministic collection of intervals.
- Validate names, target labels, and optional constraint/variable context labels.
- Support documented target labels for objective, RHS, constraint coefficient, and
  parameter uncertainty.
- Validate finite lower and upper bounds with `lower <= upper`.
- Validate optional nominal values as finite and within interval bounds.
- Normalize intervals deterministically and reject duplicate interval names in a box.
- Normalize scalar metadata into immutable deterministic tuples.
- Keep the records passive: no model construction, no solver calls, no robust
  counterpart logic.
- Keep package-level `silo.uncertainty` exports unchanged.

## Required tests

Add focused tests covering:

- interval construction and normalization;
- interval immutability;
- invalid names, target labels, bounds, nominal values, metadata, and messages;
- box construction and deterministic ordering;
- duplicate/empty/invalid interval collection rejection;
- box immutability;
- package public export boundary remains unchanged;
- uncertainty-set module does not import solver layers or implement transformation logic.

## Required checks

Run:

```powershell
pytest tests/unit/test_uncertainty_set.py tests/unit/test_uncertainty_boundary_smoke.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- Interval and box uncertainty records are immutable, deterministic, and validated.
- The records describe uncertainty only and do not transform or solve models.
- Existing public exports, CLI behavior, JSON schemas, and solver behavior remain
  unchanged.
- Required checks pass.
- The required report is created.

## Stop conditions

Stop and report instead of proceeding if the task appears to require:

- robust counterpart construction;
- deterministic-equivalent construction;
- public package export changes;
- CLI or JSON schema changes;
- solver or presolve changes;
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
