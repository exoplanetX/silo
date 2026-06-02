# 20260602-14-01 Robust Wrapper Records

## Task metadata

- Task ID: 20260602-14-01
- Slug: robust-wrapper-records
- Mode: SILO-DOS Mode A auto-one
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 8 stochastic and robust optimization extensions
- Design reference: `notes/20_uncertainty_boundary_design.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260602-14-01_robust-wrapper-records_report.md`

## Objective

Add immutable robust model wrapper records that pair a validated base `Model` with an
uncertainty set and assumption metadata.

## Context

The previous Phase 8 task added passive interval and box uncertainty-set records. The next
smallest step is to replace the robust wrapper placeholder with a passive record boundary
before any robust counterpart construction is considered.

## Scope lock

Implement only passive robust wrapper records. Do not build robust counterparts, transform
models, solve models, expose public CLI/schema contracts, or change deterministic
equivalent behavior.

## Allowed changes

- `src/silo/uncertainty/robust_model.py`
- `tests/unit/test_uncertainty_robust_model.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/codex/20260602-14-01_robust-wrapper-records.md`
- `tasks/reports/20260602-14-01_robust-wrapper-records_report.md`

## Forbidden changes

- Do not modify `src/silo/uncertainty/__init__.py`.
- Do not modify `src/silo/uncertainty/uncertainty_set.py`.
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

- Replace the placeholder `RobustModel` with an immutable dataclass.
- Require `base_model` to be a `silo.core.model.Model` and validate it via
  `base_model.validate()`.
- Require `uncertainty_set` to be an `UncertaintySet`.
- Store assumptions as an immutable deterministic tuple of nonempty strings.
- Normalize scalar metadata into immutable deterministic tuples.
- Validate `message` is a string.
- Provide convenience properties for `uncertainty_set_name` and `assumption_count`.
- Keep the record passive: no model construction, no solver calls, no robust counterpart
  logic.
- Keep package-level `silo.uncertainty` exports unchanged.

## Required tests

Add focused tests covering:

- construction and normalization;
- wrapper immutability;
- base-model validation;
- uncertainty-set type validation;
- invalid assumption sequences;
- invalid metadata and message values;
- package public export boundary remains unchanged;
- robust wrapper module does not import solver layers or implement transformation logic.

## Required checks

Run:

```powershell
pytest tests/unit/test_uncertainty_robust_model.py tests/unit/test_uncertainty_boundary_smoke.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- `RobustModel` is immutable, deterministic, and validated.
- The wrapper describes robust model metadata only and does not transform or solve models.
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
