# 20260603-10-01 Unavailable Native Diagnostics Tests

## Task metadata

- Task ID: 20260603-10-01
- Slug: unavailable-native-diagnostics
- Mode: SILO-DOS Mode A auto-one
- Task type: regression/boundary diagnostics tests
- Risk level: L0 safe
- Phase reference: Phase 9 native backend
- Design note: `notes/21_native_backend_boundary_design.md`
- Prior report: `tasks/reports/20260603-09-01_backend-conformance-fixtures_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260603-10-01_unavailable-native-diagnostics_report.md`

## Objective

Add unavailable-native-backend diagnostics tests using existing passive availability
records, without source-code changes, native dependencies, backend selection, solver
dispatch, CLI behavior changes, or JSON schema changes.

## Context

Phase 9 planning requires future diagnostics to distinguish unavailable or unsupported
native backends. Existing passive records already support backend kind, availability
status, reason, and message. This task locks that behavior with tests only.

This task is L0 because it adds regression tests and the matching report only.

## Scope lock

Add tests that exercise existing passive `BackendAvailability` behavior for unavailable
and unsupported native-experimental records. Do not add diagnostic source modules, selector
behavior, fallback behavior, native discovery, native probing, or solver execution paths.

## Allowed changes

- `tests/unit/test_unavailable_native_backend_diagnostics.py`
- `tasks/codex/20260603-10-01_unavailable-native-diagnostics.md`
- `tasks/reports/20260603-10-01_unavailable-native-diagnostics_report.md`

## Forbidden changes

- Do not modify files under `src/`.
- Do not modify existing tests.
- Do not modify LP solvers.
- Do not modify MIP solvers or branch-and-bound behavior.
- Do not modify presolve behavior.
- Do not modify cut/callback behavior.
- Do not modify decomposition behavior.
- Do not modify uncertainty behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify backend capability, adapter, or conformance source records.
- Do not modify `src/silo/interfaces/__init__.py`.
- Do not create `native/` implementation files.
- Do not add backend selectors, fallback behavior, solver discovery, solver dispatch, or
  parity execution behavior.
- Do not add optional native dependencies.
- Do not add build-system or packaging changes.
- Do not call LP or MIP solvers.
- Do not call external solvers.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Required tests

Add `tests/unit/test_unavailable_native_backend_diagnostics.py` covering:

- unavailable native-experimental availability records preserve backend id, kind, status,
  reason, and message;
- unsupported native-experimental availability records preserve a stable unsupported
  feature reason;
- unavailable and unsupported records reject missing reasons;
- available native-experimental records are permitted without an unavailability reason
  but remain passive;
- importing passive backend availability records does not load optional native modules
  into `sys.modules`;
- public CLI commands do not expose native/backend selection commands;
- public `Solution` schema does not gain backend availability, backend id, fallback, or
  native diagnostic fields.

## Required checks

Run:

```powershell
pytest tests/unit/test_unavailable_native_backend_diagnostics.py
pytest tests/unit/test_backend_conformance.py
pytest tests/unit/test_python_backend_adapter.py
pytest tests/unit/test_backend_capability_records.py
pytest tests/unit/test_backend_boundary_smoke.py
pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- Unavailable and unsupported native-experimental diagnostics are covered by tests using
  existing passive records.
- Tests confirm missing reasons are rejected for unavailable or unsupported records.
- Tests confirm passive record imports do not load optional native modules.
- Tests confirm public CLI and public `Solution` schema remain unchanged.
- No source code, existing tests, examples, CLI behavior, JSON schemas, roadmap files, or
  phase files are changed.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- tests require changing source code;
- tests require adding diagnostic records or behavior;
- tests require backend selector behavior;
- tests require native implementation modules or dependencies;
- tests can pass only by changing public CLI behavior or JSON schemas;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260603-10-01_unavailable-native-diagnostics_report.md` with:

- objective;
- risk level;
- task ID scan result;
- files changed;
- test summary;
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
- confirmation that no source code, solver behavior, CLI behavior, JSON schema, native
  implementation, dependency, roadmap, or phase-transition files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
