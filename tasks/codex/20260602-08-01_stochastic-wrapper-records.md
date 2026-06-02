# 20260602-08-01 Stochastic Wrapper Records

## Task type

Controlled implementation.

## Risk level

L1 controlled implementation.

This task adds narrow immutable Phase 8 records backed by `notes/20_uncertainty_boundary_design.md`, the existing finite-scenario records, and explicit validation tests. It does not alter solver behavior, public CLI behavior, JSON schemas, deterministic equivalents, robust wrappers, or uncertainty sets.

## User approval

The user explicitly approved the next Phase 8 L1 implementation task: stochastic model wrapper records with validation tests.

## Objective

Add immutable stochastic model wrapper records that bind a validated base `Model` to a finite scenario collection and declaration metadata for first-stage and scenario-dependent model components.

## Scope lock

Implement only the stochastic wrapper record boundary. The wrapper must remain a passive data record and must not solve, transform, mutate, or materialize any optimization model.

## Allowed changes

- `src/silo/uncertainty/stochastic_model.py`
- `tests/unit/test_uncertainty_stochastic_model.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/reports/20260602-08-01_stochastic-wrapper-records_report.md`
- `tasks/codex/20260602-08-01_stochastic-wrapper-records.md`

## Forbidden changes

- Do not build deterministic equivalents.
- Do not modify `src/silo/uncertainty/deterministic_equivalent.py`.
- Do not implement robust wrappers.
- Do not implement uncertainty sets.
- Do not modify LP, MIP, presolve, cuts, decomposition, or core solver behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not create or modify examples.
- Do not issue or execute another task.
- Do not start Phase 9.

## Implementation requirements

- Replace the placeholder `StochasticModel` with an immutable dataclass.
- Require a `base_model` that is an instance of `silo.core.model.Model`.
- Validate the base model by calling `base_model.validate()`.
- Accept either a `ScenarioSet` or a sequence of `Scenario` objects and normalize it to a `ScenarioSet`.
- Store declaration fields as immutable tuples:
  - `first_stage_variables`
  - `scenario_dependent_variables`
  - `scenario_dependent_constraints`
- Validate that declared variable names exist in the base model.
- Validate that declared constraint names exist in the base model.
- Reject overlap between first-stage and scenario-dependent variable declarations.
- Normalize metadata into an immutable deterministic mapping.
- Preserve the wrapper as a passive record with no solver calls, no deterministic-equivalent construction, and no model mutation.
- Keep package-level uncertainty exports unchanged unless required by tests.

## Required tests

Add focused validation tests covering:

- construction from a sequence of scenarios;
- construction from an existing `ScenarioSet`;
- immutable wrapper fields;
- base-model validation;
- unknown declared variables;
- unknown declared constraints;
- overlapping first-stage and scenario-dependent variables;
- duplicate or invalid declaration names;
- metadata and message validation;
- no solver or deterministic-equivalent integration inside the wrapper module.

## Required checks

Run:

```powershell
pytest tests/unit/test_uncertainty_stochastic_model.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- `StochasticModel` is immutable and deterministic.
- Invalid scenario collections are rejected through `ScenarioSet` validation.
- Invalid base models or declarations are rejected with clear exceptions.
- Existing LP, MIP, presolve, CLI, JSON schema, examples, robust, and deterministic-equivalent behavior remains unchanged.
- Required checks pass.
- The required report is created.

## Expected report

Create `tasks/reports/20260602-08-01_stochastic-wrapper-records_report.md`.

## Git mode

push-on-success.
