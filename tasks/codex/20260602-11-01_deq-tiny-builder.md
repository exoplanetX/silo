# 20260602-11-01 Deterministic-Equivalent Tiny Builder

## Task metadata

- Task ID: 20260602-11-01
- Slug: deq-tiny-builder
- Mode: SILO-DOS Mode A review gate
- Task type: controlled implementation with review gate
- Risk level: L2 high-risk
- Phase reference: Phase 8 stochastic and robust optimization extensions
- Design reference: `notes/20_uncertainty_boundary_design.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260602-11-01_deq-tiny-builder_report.md`

## Objective

Add a tiny deterministic-equivalent builder for objective and RHS overrides on
continuous LP fixtures, returning an ordinary SILO `Model` plus diagnostics.

## Context

Phase 8 currently has:

- finite-scenario records;
- uncertainty boundary smoke tests;
- passive stochastic wrapper records;
- deterministic naming helpers;
- deterministic-equivalent diagnostics/result records.

The design note next recommends a tiny deterministic-equivalent builder. This task is
classified as L2 because it begins model transformation logic and must preserve SILO's
modeling conventions carefully.

## Scope lock

Implement only a tiny finite-scenario deterministic-equivalent transformation for
continuous LP fixtures with explicit objective and RHS overrides. Do not implement a
general stochastic solver or broad deterministic-equivalent coverage.

## Allowed changes

- `src/silo/uncertainty/deterministic_equivalent.py`
- `tests/unit/test_uncertainty_deterministic_equivalent_builder.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/codex/20260602-11-01_deq-tiny-builder.md`
- `tasks/reports/20260602-11-01_deq-tiny-builder_report.md`

## Forbidden changes

- Do not modify `src/silo/uncertainty/__init__.py`.
- Do not modify `src/silo/uncertainty/scenario.py`.
- Do not modify `src/silo/uncertainty/stochastic_model.py`.
- Do not modify `src/silo/uncertainty/naming.py`.
- Do not implement robust wrappers.
- Do not implement uncertainty sets.
- Do not modify LP, MIP, presolve, cuts, decomposition, or core solver behavior.
- Do not call LP or MIP solvers.
- Do not call external solvers.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not create or modify examples.
- Do not issue or execute another task.
- Do not start Phase 9.

## Implementation requirements

- Preserve the existing public function name `build_deterministic_equivalent`.
- Change `build_deterministic_equivalent` to return `DeterministicEquivalentResult`
  instead of returning the base model directly.
- Build a new ordinary `Model` without mutating the input `StochasticModel`,
  `ScenarioSet`, `Scenario`, or base `Model`.
- Support only continuous LP fixture models:
  - all variables must be continuous;
  - no integer or binary variable transformation is allowed;
  - unsupported variable types must raise a clear exception.
- Keep the first implementation limited to:
  - explicit `scenario_dependent_constraints`;
  - explicit `scenario_dependent_variables` only when needed by copied scenario
    constraints;
  - objective coefficient overrides from `Scenario.objective_coefficients`;
  - RHS overrides from `Scenario.rhs_values`;
  - coefficient overrides from `Scenario.constraint_coefficients` only for copied
    scenario constraints.
- Preserve first-stage variables as shared base-name variables.
- Replicate only declared scenario-dependent variables with
  `scenario_variable_name(base_name, scenario_id)`.
- Replicate only declared scenario-dependent constraints with
  `scenario_constraint_name(base_name, scenario_id)`.
- Do not generate nonanticipativity constraints in this task.
- Aggregate the objective using the expected-value convention:

```text
objective = first_stage_terms + sum_s probability_s * scenario_objective_terms_s
```

- Count generated variables and constraints in `DeterministicEquivalentDiagnostics`.
- Record scenario ids, probability total/tolerance, objective aggregation convention,
  and naming convention in diagnostics.
- Reject ambiguous generated names before adding variables or constraints.
- Keep the transformation deterministic.

## Required tests

Add focused tests covering:

- a tiny continuous LP fixture with two scenarios, objective overrides, and RHS
  overrides;
- generated variable names for scenario-dependent variables;
- generated constraint names for scenario-dependent constraints;
- expected-value objective aggregation;
- diagnostic counts and scenario ids;
- no mutation of the base model or scenario records;
- unsupported integer/binary variables are rejected;
- unknown scenario override names are rejected;
- generated-name collisions are rejected;
- no solver calls or CLI/schema changes;
- existing boundary smoke tests remain passing.

## Required checks

Run:

```powershell
pytest tests/unit/test_uncertainty_deterministic_equivalent_builder.py tests/unit/test_uncertainty_deterministic_equivalent.py tests/unit/test_uncertainty_boundary_smoke.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- The tiny builder returns a `DeterministicEquivalentResult`.
- The returned `Model` is an ordinary SILO `Model`.
- The builder is deterministic and does not mutate inputs.
- Objective/RHS/coefficient override conventions are explicit and tested.
- No solvers are called.
- Existing public exports, CLI behavior, JSON schemas, and lower solver behavior remain
  unchanged.
- Required checks pass.
- The required report is created.

## Stop conditions

Stop and report instead of proceeding if the implementation appears to require:

- LP/MIP solver calls;
- presolve changes;
- core model API changes;
- public CLI or JSON schema changes;
- robust wrappers or uncertainty sets;
- nonanticipativity generation;
- general stochastic-programming coverage beyond tiny continuous LP fixtures;
- modifying any file outside the allowed list.

## Approval requirement

This task is L2 and must not be executed until the user explicitly approves this exact
task and its boundaries.

## Final response requirements

Report:

- task path;
- risk level and approval status;
- files changed;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no second task was issued or executed.
