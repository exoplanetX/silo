# 20260602-16-01 Robust RHS Toy Counterpart

## Task metadata

- Task ID: 20260602-16-01
- Slug: robust-rhs-toy-counterpart
- Mode: SILO-DOS Mode A auto-one, review-gated before execution
- Task type: controlled implementation
- Risk level: L2 high-risk
- Phase reference: Phase 8 stochastic and robust optimization extensions
- Design reference: `notes/20_uncertainty_boundary_design.md`
- Prior audit: `tasks/reports/20260602-15-01_phase8-completion-audit_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260602-16-01_robust-rhs-toy-counterpart_report.md`

## Objective

Add one conservative toy robust counterpart transformation for interval RHS uncertainty
on documented continuous LP fixtures, returning an ordinary SILO `Model` plus deterministic
diagnostics without solver calls.

## Review gate

This task is L2 because it introduces robust transformation behavior and records a
mathematical convention. Do not execute this task unless the current user instruction
explicitly approves executing:

```text
tasks/codex/20260602-16-01_robust-rhs-toy-counterpart.md
```

If explicit approval is absent, stop with a Decision Packet and do not modify source,
tests, reports, or phase files.

## Context

Phase 8 has finite-scenario records, stochastic wrappers, deterministic naming helpers,
deterministic-equivalent diagnostics/result records, a tiny stochastic deterministic-
equivalent builder, uncertainty-set records, and robust wrapper records. The Phase 8
completion audit recommended `not_ready_for_closure_review` because robust transformation
support is still records-only while `ROADMAP.md` and
`tasks/phases/phase_08_stochastic_robust.md` require small stochastic and robust examples
to be transformed into ordinary model objects.

This task adds only the first robust counterpart toy boundary. It must not claim broad
robust optimization support.

## Mathematical convention

Support only independent interval uncertainty on the RHS of existing linear constraints.
For an interval `b in [lower, upper]` attached to a base constraint:

- If the base constraint sense is `<=`, the robust counterpart uses `rhs = lower`.
- If the base constraint sense is `>=`, the robust counterpart uses `rhs = upper`.
- If the base constraint sense is `=`, reject non-degenerate intervals where
  `lower != upper`; for a degenerate interval, use the fixed RHS value.

Require every supported interval to:

- have `target == RHS_TARGET`;
- have a nonempty `constraint_name` that exists in the base model;
- have an empty `variable_name`;
- have finite lower and upper bounds, already enforced by `IntervalUncertainty`;
- use a nominal value equal to the base constraint RHS when `nominal` is provided.

Reject duplicate RHS intervals for the same base constraint. Copy untargeted constraints
unchanged.

## Scope lock

Implement exactly one toy robust counterpart path for interval RHS uncertainty. Keep the
implementation readable, deterministic, and fixture-oriented. Do not implement coefficient
uncertainty, objective uncertainty, budgeted uncertainty, automatic dualization, robust
solvers, stochastic transformations, examples, CLI behavior, or JSON schema behavior.

## Allowed changes

- `src/silo/uncertainty/robust_counterpart.py`
- `tests/unit/test_uncertainty_robust_counterpart.py`
- `tests/unit/test_uncertainty_boundary_smoke.py`
- `tasks/phases/phase_08_stochastic_robust.md`
- `tasks/codex/20260602-16-01_robust-rhs-toy-counterpart.md`
- `tasks/reports/20260602-16-01_robust-rhs-toy-counterpart_report.md`

## Forbidden changes

- Do not modify LP solvers.
- Do not modify MIP solvers or branch-and-bound behavior.
- Do not modify presolve behavior.
- Do not modify cut/callback behavior.
- Do not modify decomposition behavior.
- Do not modify stochastic deterministic-equivalent behavior except through regression
  checks.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not modify examples.
- Do not add external dependencies.
- Do not start Phase 9.
- Do not close Phase 8.
- Do not issue or execute another task.

## Required implementation details

- Add a small robust counterpart result/diagnostics boundary. Keep diagnostics separate
  from public `Solution` schemas.
- The builder should accept a `RobustModel` and return the original base model unchanged
  only when no RHS intervals request a transformation.
- When transformation is requested, return a new `Model` object and diagnostics.
- The transformed model name should be deterministic, for example
  `{base_model.name}_robust_counterpart`.
- Copy variables, objective, and untargeted constraints without mutating the base model.
- Apply only the RHS worst-case convention described above.
- Keep all implementation inside `src/silo/uncertainty/robust_counterpart.py`; do not
  export it from `silo.uncertainty.__init__` in this task.
- Add/update boundary smoke tests to confirm public uncertainty package exports remain
  unchanged and lower layers do not import uncertainty modules.

## Stop conditions

Stop and report instead of proceeding if:

- the implementation appears to require changing `Model`, `Constraint`, `Objective`,
  canonicalization, LP/MIP/presolve behavior, CLI behavior, or JSON schemas;
- the robust counterpart convention needs coefficient uncertainty, objective uncertainty,
  automatic dualization, or non-linear reformulation;
- public package exports must change to complete the task;
- deterministic tests require solving the transformed model rather than inspecting it;
- completing the task would require adding examples or starting Phase 9.

## Required checks

Run:

```powershell
pytest tests/unit/test_uncertainty_robust_counterpart.py tests/unit/test_uncertainty_robust_model.py tests/unit/test_uncertainty_set.py tests/unit/test_uncertainty_boundary_smoke.py tests/unit/test_uncertainty_deterministic_equivalent_builder.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- A tiny interval-RHS robust counterpart builder is implemented behind a direct module
  import, not a public package export.
- Tests cover `<=`, `>=`, and supported degenerate `=` RHS conventions.
- Tests reject non-degenerate equality intervals.
- Tests reject unsupported target kinds, unknown constraints, duplicate RHS intervals,
  nonempty variable names, and nominal/base-RHS mismatches.
- Tests confirm the base model and uncertainty records are not mutated.
- Tests inspect transformed `Model` objects and deterministic diagnostics without solver
  calls.
- Existing stochastic deterministic-equivalent behavior remains unchanged.
- Public CLI behavior and JSON schemas remain unchanged.
- The Phase 8 phase record is updated only to add the completed robust RHS toy
  counterpart item; it must not mark Phase 8 complete.
- The required report is created.

## Report requirements

Create `tasks/reports/20260602-16-01_robust-rhs-toy-counterpart_report.md` with:

- objective;
- risk level and approval boundary;
- files changed;
- implementation summary;
- mathematical convention recorded;
- tests added or updated;
- checks run and results;
- Git status before and after;
- local commit hash;
- push attempted and result;
- confirmation that no CLI, JSON schema, solver, presolve, stochastic builder, examples,
  roadmap, Phase 8 closure, or Phase 9 work changed;
- next recommended atomic task.

## Final response requirements

Report:

- task path;
- risk level and approval confirmation;
- files changed;
- checks run and results;
- commit hash;
- whether push succeeded;
- robust counterpart convention implemented;
- confirmation that Phase 8 was not closed and Phase 9 was not started;
- confirmation that no second task was issued or executed.
