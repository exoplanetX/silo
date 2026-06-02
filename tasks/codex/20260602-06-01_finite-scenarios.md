# Codex Task: Finite Scenario Records

## Task Metadata

Task ID: 20260602-06-01
Task slug: finite-scenarios
Task type: controlled-implementation
Risk level: L1 controlled implementation
Related phase: Phase 8 / Stochastic and Robust Optimization Extensions
Git mode: push-on-success
Expected report path: tasks/reports/20260602-06-01_finite-scenarios_report.md

## Objective

Add immutable finite-scenario records and validation tests for scenario ids,
probabilities, metadata, coefficient overrides, and deterministic scenario ordering.

## User Approval

The user explicitly approved starting Phase 8 implementation with exactly one L1 task:
add immutable finite-scenario records and validation tests.

## Context

Phase 8A created the uncertainty boundary design note:

```text
notes/20_uncertainty_boundary_design.md
```

The design note states that Phase 8 should begin with finite scenario records and
validation tests before stochastic model wrappers, robust wrappers, uncertainty sets, or
deterministic-equivalent builders.

Existing `src/silo/uncertainty/` files are placeholders. This task may upgrade only the
scenario record boundary and package exports.

## Scope Lock

This task is atomic.

Primary objective:

- Add immutable finite-scenario records and validation tests.

Allowed changes:

- `src/silo/uncertainty/scenario.py`
- `src/silo/uncertainty/__init__.py`
- `tests/unit/test_uncertainty_scenario.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/reports/20260602-06-01_finite-scenarios_report.md`

Supporting allowed change:

- `tasks/codex/20260602-06-01_finite-scenarios.md` may be committed as the issued task
  contract for this execution.

Forbidden changes:

- Do not modify stochastic model wrappers.
- Do not modify robust model wrappers.
- Do not modify uncertainty-set placeholders.
- Do not modify deterministic-equivalent placeholders.
- Do not implement stochastic model wrappers.
- Do not implement robust model wrappers.
- Do not implement uncertainty sets.
- Do not implement deterministic equivalents.
- Do not modify examples.
- Do not modify public CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify LP solver behavior.
- Do not modify MIP solver behavior.
- Do not modify presolve behavior.
- Do not modify cut, callback, or decomposition behavior.
- Do not issue or execute another Phase 8 task.
- Do not start Phase 9.

## Required Implementation

Implement finite-scenario records in `src/silo/uncertainty/scenario.py`:

- immutable `Scenario` record with a deterministic scenario id, probability, optional
  scenario-specific data, scalar metadata, and message;
- immutable `ScenarioSet` or similarly named finite collection record that validates
  duplicate ids, positive total probability mass, probability sum tolerance, and
  deterministic ordering;
- validation for nonempty ids, finite nonnegative probabilities, finite numeric override
  values, finite scalar metadata, and immutable defensive copies;
- no `Model` inputs;
- no solver calls;
- no transformation logic.

Acceptable scenario-specific data for this first task:

- objective coefficient overrides keyed by variable name;
- RHS overrides keyed by constraint name;
- constraint coefficient overrides keyed by constraint and variable name;
- scalar parameter values.

Update `src/silo/uncertainty/__init__.py` to export only the new scenario records and
constants needed by tests. Do not export stochastic/robust transformation behavior.

Update `tasks/phases/phase_08_stochastic_robust.md` with only a brief Phase 8B note.

## Required Tests

Add deterministic unit tests covering:

- scenario construction normalizes ids and defensively copies all mapping inputs;
- scenario records are immutable;
- invalid scenario ids are rejected;
- nonfinite or negative probabilities are rejected;
- finite zero probabilities are accepted on individual scenarios but collection-level
  zero total probability is rejected;
- objective, RHS, constraint-coefficient, and parameter overrides validate finite numeric
  values and nonempty labels;
- metadata validates scalar values and rejects nonfinite floats;
- message values must be strings;
- scenario collection rejects duplicate ids;
- scenario collection rejects probability sums outside tolerance;
- scenario collection accepts probability sums within tolerance;
- scenario collection ordering is deterministic;
- invalid collection tolerances are rejected;
- public exports are available from `silo.uncertainty`;
- lower layers still do not import uncertainty.

## Required Checks

Run at least:

```bash
git status --short
pytest tests/unit/test_uncertainty_scenario.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. Immutable finite-scenario records are implemented.
2. Scenario and collection validation behavior is covered by tests.
3. Scenario collection ordering is deterministic.
4. Scenario-specific data is copied immutably.
5. No stochastic model wrapper is implemented or modified.
6. No robust model wrapper is implemented or modified.
7. No uncertainty-set or deterministic-equivalent behavior is implemented or modified.
8. No examples are modified.
9. No public CLI behavior or JSON schemas are changed.
10. No lower-layer dependency direction is violated.
11. A report is created at the expected report path.
12. Required checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260602-06-01_finite-scenarios_report.md
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

The report must explicitly state that no stochastic wrapper, robust wrapper,
uncertainty-set, deterministic-equivalent, examples, CLI behavior, or JSON schema work was
implemented.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add src/silo/uncertainty/scenario.py src/silo/uncertainty/__init__.py tests/unit/test_uncertainty_scenario.py tasks/phases/phase_08_stochastic_robust.md tasks/codex/20260602-06-01_finite-scenarios.md tasks/reports/20260602-06-01_finite-scenarios_report.md
git commit -m "feat(uncertainty): add finite scenario records"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether finite-scenario records were added;
- whether validation tests were added;
- whether no wrappers, deterministic equivalents, examples, CLI behavior, or JSON schemas
  were changed;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
