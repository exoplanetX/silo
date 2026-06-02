# 20260603-05-01 Phase 9 Native Backend Design

## Task metadata

- Task ID: 20260603-05-01
- Slug: phase9-native-backend-design
- Mode: SILO-DOS Mode C principal mode / review-gated planning
- Task type: planning/design note
- Risk level: L3 strategic
- Phase reference: Phase 9 native backend
- Prior report: `tasks/reports/20260603-04-01_phase8-closure-bookkeeping_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260603-05-01_phase9-native-backend-design_report.md`

## Objective

Create a Phase 9 planning/design note for the native backend boundary, preserving Python
reference behavior as the source of truth and forbidding implementation work.

## Review gate

This task is L3 because it starts Phase 9 planning. It may be executed only when the
current user instruction explicitly approves Phase 9 planning and explicitly does not
approve Phase 9 implementation.

If explicit approval is absent, stop with a Decision Packet and do not modify any file.

## Context

Phase 8 is closed for the current conservative stochastic/robust transformation boundary
scope. The latest Phase 8 closure report says the next atomic task is Phase 9 planning
only if the user explicitly approves starting Phase 9 planning. The user has approved
Phase 9 planning but has not approved Phase 9 implementation.

Phase 9 should prepare selected solver kernels for a future native backend while
preserving Python reference behavior. It must keep native work optional and isolated from
the default educational solver path.

## Scope lock

Planning only. Create the design note and update the Phase 9 phase record. Do not create
native implementation files, backend interfaces, conformance tests, CLI behavior, JSON
schemas, examples, or source-code changes.

## Allowed changes

- `notes/21_native_backend_boundary_design.md`
- `tasks/phases/phase_09_native_backend.md`
- `tasks/codex/20260603-05-01_phase9-native-backend-design.md`
- `tasks/reports/20260603-05-01_phase9-native-backend-design_report.md`

## Forbidden changes

- Do not modify files under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not create `native/` implementation files.
- Do not create backend conformance tests.
- Do not add dependencies.
- Do not call external solvers.
- Do not implement native kernels.
- Do not issue or execute a Phase 9 implementation task.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Design note requirements

The design note must cover:

- Phase 9 purpose and conservative scope;
- dependency direction and package boundaries;
- Python-reference source-of-truth policy;
- optional backend interface boundary;
- candidate native kernel selection criteria;
- parity and conformance testing strategy;
- failure-mode and diagnostics expectations;
- dependency and build policy;
- public CLI and JSON schema non-goals;
- explicit non-goals;
- candidate atomic implementation task sequence;
- review gates and risk levels for future tasks.

## Phase record requirements

Update `tasks/phases/phase_09_native_backend.md` only to record that Phase 9A is a
planning/design-note step. Do not mark implementation started, active, approved, or
complete.

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

- `notes/21_native_backend_boundary_design.md` is created and is planning-only.
- `tasks/phases/phase_09_native_backend.md` records Phase 9A planning without starting
  implementation.
- No source, test, example, CLI, JSON schema, native implementation, or dependency files
  are modified.
- The design note defines future task boundaries and approval gates.
- Required checks pass.
- The required report is created.
- No follow-on implementation task is issued or executed.

## Report requirements

Create `tasks/reports/20260603-05-01_phase9-native-backend-design_report.md` with:

- objective;
- risk level and approval boundary;
- files changed;
- design summary;
- implementation non-start confirmation;
- checks run and results;
- Git status before and after;
- local commit hash;
- push attempted and result;
- next recommended atomic task.

## Final response requirements

Report:

- task path;
- risk level and approval confirmation;
- files changed;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that Phase 9 implementation was not started;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
