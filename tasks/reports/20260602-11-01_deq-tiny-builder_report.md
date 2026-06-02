# Task Report: 20260602-11-01 Deterministic-Equivalent Tiny Builder

Task ID: 20260602-11-01

Objective: Add a tiny deterministic-equivalent builder for objective and RHS overrides
on continuous LP fixtures, returning an ordinary SILO `Model` plus diagnostics.

Risk and execution: L2 high-risk. Mode A stopped at the review gate when the task was
issued. The user explicitly approved executing this exact task with additional
boundaries:

- no base-model mutation;
- no general deterministic-equivalent builder;
- no scenario-dependent variables yet;
- no nonanticipativity constraints;
- no stochastic CLI or JSON schema support;
- no LP/MIP solver calls.

Scope note: The user's additional approval narrowed the issued task. This implementation
rejects nonempty `scenario_dependent_variables` and rejects constraint coefficient
overrides. The tiny supported path covers continuous LP fixtures with objective
coefficient overrides and RHS overrides on declared scenario-dependent constraints.

Files changed:

- `src/silo/uncertainty/deterministic_equivalent.py`
- `tests/unit/test_uncertainty_deterministic_equivalent_builder.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/codex/20260602-11-01_deq-tiny-builder.md`
- `tasks/reports/20260602-11-01_deq-tiny-builder_report.md`

Implementation summary:

- Added a tiny transformation path in `build_deterministic_equivalent`.
- Preserved the legacy no-op behavior for stochastic wrappers with no transformation
  request so earlier diagnostics tests remain stable.
- Returned `DeterministicEquivalentResult` for wrappers with objective/RHS transformation
  requests.
- Built a new ordinary `Model` without mutating the input `StochasticModel`, scenarios,
  or base `Model`.
- Copied shared variables and shared constraints through constructors rather than
  mutating a model in place.
- Generated scenario constraint names deterministically through the naming helper.
- Applied expected-value objective coefficients using scenario probabilities and
  objective overrides.
- Applied RHS overrides only to declared scenario-dependent constraints.
- Rejected scenario-dependent variables, non-continuous variables, unknown overrides,
  constraint coefficient overrides, and generated-name collisions.
- Added diagnostics for scenario ids, generated variable/constraint counts,
  nonanticipativity count, probability metadata, naming convention, and builder metadata.

Tests added:

- Tiny two-scenario continuous LP transformation.
- Generated scenario constraint names.
- RHS override application.
- Expected-value objective aggregation.
- Diagnostic counts and scenario ids.
- No mutation of base model or scenario records.
- Non-continuous variable rejection.
- Scenario-dependent variable rejection.
- Unknown objective/RHS override rejection.
- Undeclared RHS override rejection.
- Constraint coefficient override rejection.
- Generated-name collision rejection.
- No-op placeholder compatibility for empty wrappers.
- Static guard that the module does not integrate solver, CLI, or schema behavior.

Checks run:

- `pytest tests/unit/test_uncertainty_deterministic_equivalent_builder.py tests/unit/test_uncertainty_deterministic_equivalent.py tests/unit/test_uncertainty_boundary_smoke.py`
- `python scripts/check_quality.py`
- `git diff --check`

Results:

- Initial targeted test run found two in-scope issues: a binary-variable fixture needed
  valid binary bounds, and an internal helper alias still matched an older static guard.
  Both were fixed inside the allowed files.
- Final targeted test run: 49 passed.
- `python scripts/check_quality.py`: 795 passed, all checks passed.
- `git diff --check`: passed.

Git status before:

```text
## main...origin/main
?? tasks/codex/20260602-11-01_deq-tiny-builder.md
```

Git status after implementation before commit:

```text
 M src/silo/uncertainty/deterministic_equivalent.py
 M tasks/phases/phase_08_stochastic_robust.md
?? tasks/codex/20260602-11-01_deq-tiny-builder.md
?? tasks/reports/20260602-11-01_deq-tiny-builder_report.md
?? tests/unit/test_uncertainty_deterministic_equivalent_builder.py
```

Local commit hash: Created locally after this report was staged; the final response
records the commit hash.

Push attempted: Yes; the final response records whether push succeeded. If push fails,
the failure is recorded by amending this report.

Issues or conflicts:

- None remaining.
- No nonanticipativity constraints, scenario-dependent variables, robust wrappers,
  uncertainty sets, examples, public exports, CLI behavior, JSON schemas, LP/MIP/presolve
  behavior, or lower solver-layer behavior were modified.
- No Phase 9 work was issued or started.

Next recommended atomic task: Add a Phase 8 audit or a separate L2 review-gated task for
nonanticipativity generation, depending on whether the user wants to continue the tiny
stochastic transformation line.
