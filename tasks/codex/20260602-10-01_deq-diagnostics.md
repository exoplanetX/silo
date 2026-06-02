# 20260602-10-01 Deterministic-Equivalent Diagnostics

## Task metadata

- Task ID: 20260602-10-01
- Slug: deq-diagnostics
- Mode: SILO-DOS Mode A auto-one
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 8 stochastic and robust optimization extensions
- Design reference: `notes/20_uncertainty_boundary_design.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260602-10-01_deq-diagnostics_report.md`

## Objective

Add immutable deterministic-equivalent result and diagnostic records without building or
transforming models.

## Context

Phase 8 has finite scenarios, passive stochastic wrapper records, and deterministic
naming helpers. The design note says a future deterministic-equivalent builder should
return both an ordinary `Model` and diagnostics describing generated dimensions,
probability metadata, scenario ids, objective aggregation convention, and naming
convention. Before implementing any builder, add the passive record boundary and
validation tests.

## Scope lock

Implement only passive deterministic-equivalent diagnostics/result records. Do not build,
copy, mutate, or transform optimization models.

## Allowed changes

- `src/silo/uncertainty/deterministic_equivalent.py`
- `tests/unit/test_uncertainty_deterministic_equivalent.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/codex/20260602-10-01_deq-diagnostics.md`
- `tasks/reports/20260602-10-01_deq-diagnostics_report.md`

## Forbidden changes

- Do not modify `src/silo/uncertainty/__init__.py`.
- Do not modify `src/silo/uncertainty/stochastic_model.py`.
- Do not modify `src/silo/uncertainty/scenario.py`.
- Do not build deterministic equivalents.
- Do not change the behavior of the existing `build_deterministic_equivalent` placeholder.
- Do not implement robust wrappers.
- Do not implement uncertainty sets.
- Do not modify LP, MIP, presolve, cuts, decomposition, or core solver behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not create or modify examples.
- Do not issue or execute another task.
- Do not start Phase 9.

## Implementation requirements

- Add immutable diagnostics and result records to
  `src/silo/uncertainty/deterministic_equivalent.py`.
- Include a diagnostics record with validated fields for:
  - scenario ids;
  - generated variable count;
  - generated constraint count;
  - nonanticipativity constraint count;
  - objective aggregation convention;
  - probability total;
  - probability tolerance;
  - naming convention;
  - scalar metadata;
  - message.
- Include a result record that pairs a validated `Model` with diagnostics and optional
  scalar metadata/message.
- Normalize scenario ids deterministically and reject duplicates, empty ids, and
  non-string ids.
- Reject negative counts and boolean count values.
- Reject non-finite probability totals/tolerances and nonpositive tolerances.
- Preserve records as passive dataclasses with no solver calls and no transformation
  logic.
- Keep package-level `silo.uncertainty` exports unchanged.
- Keep the existing `build_deterministic_equivalent` placeholder return behavior
  unchanged.

## Required tests

Add focused tests covering:

- diagnostics construction and deterministic normalization;
- diagnostics immutability;
- duplicate, empty, and non-string scenario id rejection;
- invalid count rejection;
- invalid probability total/tolerance rejection;
- invalid metadata/message rejection;
- result construction with a valid `Model` and diagnostics;
- result immutability;
- invalid result model/diagnostics rejection;
- existing placeholder `build_deterministic_equivalent` behavior remains unchanged;
- package public export boundary remains unchanged;
- static guard that the module does not import solver layers or implement
  transformation logic.

## Required checks

Run:

```powershell
pytest tests/unit/test_uncertainty_deterministic_equivalent.py tests/unit/test_uncertainty_boundary_smoke.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- Diagnostics/result records are immutable and deterministic.
- Invalid diagnostic values are rejected with clear exceptions.
- The placeholder deterministic-equivalent function still returns the wrapper base model
  exactly as before.
- Existing public exports, CLI behavior, JSON schemas, and solver behavior remain
  unchanged.
- Required checks pass.
- The required report is created.

## Stop conditions

Stop and report instead of proceeding if the task appears to require:

- deterministic-equivalent model construction;
- model replication, nonanticipativity generation, or objective aggregation
  implementation;
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
