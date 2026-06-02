# 20260603-06-01 Backend Boundary Smoke Tests

## Task metadata

- Task ID: 20260603-06-01
- Slug: backend-boundary-smoke
- Mode: SILO-DOS Mode A auto-one
- Task type: regression/boundary tests
- Risk level: L0 safe
- Phase reference: Phase 9 native backend
- Design note: `notes/21_native_backend_boundary_design.md`
- Prior report: `tasks/reports/20260603-05-01_phase9-native-backend-design_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260603-06-01_backend-boundary-smoke_report.md`

## Objective

Add backend boundary smoke tests proving that default Python solver paths do not import
optional native backend modules and do not expose native backend selection through the
public CLI.

## Context

Phase 9A created the native backend boundary design note. The note identifies the first
safe implementation-adjacent task as a boundary smoke test that keeps native work optional
and isolated from the default Python solver path.

This is an L0 regression/boundary task. It may add tests that lock the current behavior,
but it must not add backend records, backend selectors, native modules, solver dispatch
behavior, or public contract changes.

## Scope lock

Add exactly one boundary smoke test module and the matching execution report. Do not
modify solver source code or existing solver behavior. If a smoke test exposes a needed
source-code change, stop and report instead of fixing it inside this task.

## Allowed changes

- `tests/unit/test_backend_boundary_smoke.py`
- `tasks/codex/20260603-06-01_backend-boundary-smoke.md`
- `tasks/reports/20260603-06-01_backend-boundary-smoke_report.md`

## Forbidden changes

- Do not modify files under `src/`.
- Do not modify existing tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not create `native/` implementation files.
- Do not add backend capability records.
- Do not add backend selectors or dispatch behavior.
- Do not add optional native dependencies.
- Do not call LP or MIP solvers from native code.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Required test coverage

Add tests that verify:

- importing default LP, MIP, presolve, CLI, and boundary-layer Python modules does not load
  optional native modules into `sys.modules`;
- lower/default solver-layer source files do not import `silo.native` or native-backend
  implementation modules;
- the public CLI command set does not expose a native backend command;
- the public LP solver choices remain the existing Python reference choices.

The tests must avoid broad string bans that would falsely reject existing non-native
terms such as LP backend comparison or optional external-solver interface placeholders.

## Required checks

Run:

```powershell
pytest tests/unit/test_backend_boundary_smoke.py
pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- `tests/unit/test_backend_boundary_smoke.py` is added.
- The tests pass without requiring native modules or optional native dependencies.
- The tests confirm default Python solver paths remain isolated from optional native
  backend modules.
- No source code, existing tests, examples, CLI behavior, JSON schemas, roadmap files, or
  phase files are changed.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- the default solver path already imports native implementation modules;
- passing the tests requires source-code changes;
- passing the tests requires adding native backend records, selectors, or dependencies;
- passing the tests requires CLI or JSON schema changes;
- task ID collision is discovered after issuance.

## Report requirements

Create `tasks/reports/20260603-06-01_backend-boundary-smoke_report.md` with:

- objective;
- risk level;
- task ID scan result;
- files changed;
- checks run and results;
- deviations from scope, if any;
- Git status before and after;
- local commit hash;
- push attempted and result;
- unresolved issues;
- next recommended atomic task.

## Final response requirements

Report:

- task path;
- risk level;
- files changed;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no source code, CLI behavior, JSON schema, native implementation, or
  phase-transition files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
