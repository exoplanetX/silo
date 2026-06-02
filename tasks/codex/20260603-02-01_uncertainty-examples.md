# 20260603-02-01 Uncertainty Examples

## Task metadata

- Task ID: 20260603-02-01
- Slug: uncertainty-examples
- Mode: SILO-DOS Mode A auto-one
- Task type: examples
- Risk level: L0 safe
- Phase reference: Phase 8 stochastic and robust optimization extensions
- Design reference: `notes/20_uncertainty_boundary_design.md`
- Prior report: `tasks/reports/20260603-01-01_phase8-closure-readiness-audit_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260603-02-01_uncertainty-examples_report.md`

## Objective

Add checked-in toy uncertainty transformation examples covering one stochastic
deterministic-equivalent fixture and one robust interval-RHS counterpart fixture.

## Context

The Phase 8 closure-readiness audit found that the core conservative stochastic and robust
toy transformation boundary is implemented and tested, but the `examples/` tree has no
checked-in uncertainty examples. The audit recommended an examples-only L0 task before
asking the user to close Phase 8.

## Scope lock

Add exactly two small example scripts under `examples/uncertainty/`. The examples may
construct models and call the already implemented direct-module transformation builders,
but they must not add new behavior, tests, public exports, CLI commands, JSON schemas, or
solver calls.

## Allowed changes

- `examples/uncertainty/toy_stochastic_de.py`
- `examples/uncertainty/toy_robust_rhs.py`
- `tasks/codex/20260603-02-01_uncertainty-examples.md`
- `tasks/reports/20260603-02-01_uncertainty-examples_report.md`

## Forbidden changes

- Do not modify files under `src/`.
- Do not modify tests.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not add generated output files.
- Do not add external dependencies.
- Do not close Phase 8.
- Do not start Phase 9.
- Do not issue or execute another task.

## Required example behavior

- `toy_stochastic_de.py` should build a tiny continuous LP, wrap it in finite scenarios,
  call `build_deterministic_equivalent()` by direct module import, and print a compact
  deterministic summary of generated constraint names, objective coefficients, and
  diagnostics.
- `toy_robust_rhs.py` should build a tiny continuous LP, wrap it in a robust model with
  interval RHS uncertainty, call `build_robust_counterpart()` by direct module import, and
  print a compact deterministic summary of transformed RHS values and diagnostics.
- Both examples must be small, deterministic, and runnable with `python`.
- The examples must not solve the transformed models.
- The examples must not mutate base models or uncertainty records.
- The examples must not rely on public package exports that are intentionally hidden from
  `silo.uncertainty.__init__`.

## Stop conditions

Stop and report instead of proceeding if:

- an example requires modifying solver source code or tests;
- an example requires public package exports, CLI commands, or JSON schema changes;
- an example requires solving transformed models;
- the existing transformation APIs are insufficient for a small checked-in example;
- completing the task would require Phase 8 closure or Phase 9 work.

## Required checks

Run:

```powershell
python examples/uncertainty/toy_stochastic_de.py
python examples/uncertainty/toy_robust_rhs.py
pytest tests/unit/test_uncertainty_boundary_smoke.py tests/unit/test_uncertainty_deterministic_equivalent_builder.py tests/unit/test_uncertainty_robust_counterpart.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- Both example scripts are created under `examples/uncertainty/`.
- Both examples run successfully and print deterministic summaries.
- No source, test, roadmap, phase, CLI, or JSON schema files are modified.
- No generated output files are added.
- Required checks pass.
- The required report is created.
- No follow-on task is issued or executed.

## Report requirements

Create `tasks/reports/20260603-02-01_uncertainty-examples_report.md` with:

- objective;
- risk level and execution decision;
- files changed;
- example summaries;
- checks run and results;
- Git status before and after;
- local commit hash;
- push attempted and result;
- confirmation that no source, test, phase, roadmap, CLI, JSON schema, generated output,
  Phase 8 closure, or Phase 9 work changed;
- next recommended atomic task.

## Final response requirements

Report:

- generated task path;
- risk level and execution decision;
- files changed;
- checks run and results;
- commit hash;
- whether push succeeded;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
