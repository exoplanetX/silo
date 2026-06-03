# 20260603-07-01 Backend Capability Records

## Task metadata

- Task ID: 20260603-07-01
- Slug: backend-capability-records
- Mode: SILO-DOS Mode A auto-one / review-gated L1 execution
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 9 native backend
- Design note: `notes/21_native_backend_boundary_design.md`
- Prior report: `tasks/reports/20260603-06-01_backend-boundary-smoke_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260603-07-01_backend-capability-records_report.md`

## Objective

Add immutable backend capability and backend availability records with validation tests,
without adding backend selection, solver dispatch, native dependencies, CLI behavior, or
JSON schema changes.

## Review gate

This task is L1 because it adds passive Phase 9 implementation records under the backend
interface boundary. Mode A may execute it only after the user explicitly approves this
specific L1 task.

If explicit approval is absent, stop after issuing this task and do not execute it.

## Context

Phase 9 planning established that Python reference behavior remains the source of truth
and that early native-backend work must be optional, isolated, and reversible. The prior
L0 task added backend boundary smoke tests proving the default Python solver path does
not import optional native implementation modules or expose native backend CLI commands.

The next conservative step is to add passive records that describe backend capabilities
and availability. These records should support future diagnostics and conformance tests,
but they must not select, dispatch to, or call any backend.

## Scope lock

Add only passive immutable records plus validation tests. Do not wire these records into
LP/MIP solvers, CLI commands, JSON schemas, environment-variable behavior, or native
implementation code.

## Allowed changes

- `src/silo/interfaces/backend.py`
- `tests/unit/test_backend_capability_records.py`
- `tasks/codex/20260603-07-01_backend-capability-records.md`
- `tasks/reports/20260603-07-01_backend-capability-records_report.md`

## Forbidden changes

- Do not modify LP solvers.
- Do not modify MIP solvers or branch-and-bound behavior.
- Do not modify presolve behavior.
- Do not modify cut/callback behavior.
- Do not modify decomposition behavior.
- Do not modify uncertainty behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not create `native/` implementation files.
- Do not add backend selectors, fallback behavior, or solver dispatch behavior.
- Do not add optional native dependencies.
- Do not add build-system or packaging changes.
- Do not call external solvers.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Implementation requirements

Add `src/silo/interfaces/backend.py` with small immutable records for:

- backend kind, including at least Python reference and native experimental labels;
- backend availability status, including available, unavailable, and unsupported labels;
- backend capability metadata such as backend id, kind, supported problem families,
  variable types, constraint senses, diagnostics, and tolerance label;
- backend availability metadata such as backend id, status, reason, and optional message.

Validation requirements:

- backend ids must be nonempty trimmed strings;
- tuple-like metadata fields must be immutable tuples of nonempty strings;
- duplicate entries in tuple-like fields must be rejected;
- unavailable or unsupported availability records must include a reason;
- available records must not require a reason;
- records must not reference or import native implementation modules.

Keep the records passive. They must not include solver calls, backend discovery, backend
selection, fallback logic, environment-variable reads, dynamic imports, or import-time
availability probing.

## Required tests

Add `tests/unit/test_backend_capability_records.py` covering:

- immutable dataclass behavior;
- valid Python-reference capability records;
- valid unavailable native-experimental availability records;
- validation failures for blank ids, blank tuple values, duplicate tuple values, and
  missing unavailability reasons;
- source/import boundary checks proving the records do not import native implementation
  modules and do not load `silo.native` into `sys.modules`.

## Required checks

Run:

```powershell
pytest tests/unit/test_backend_capability_records.py
pytest tests/unit/test_backend_boundary_smoke.py
pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- Backend capability and availability records are immutable and validated.
- The records are isolated under `src/silo/interfaces/backend.py`.
- Tests cover validation and immutability.
- Tests confirm no optional native implementation modules are imported.
- Existing backend boundary smoke tests still pass.
- CLI behavior and solver choices remain unchanged.
- No solver behavior, CLI behavior, JSON schemas, examples, roadmap files, or phase files
  are changed.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- implementing the records requires backend selector behavior;
- implementing the records requires solver dispatch changes;
- implementing the records requires native implementation modules or dependencies;
- tests can pass only by changing public CLI behavior or JSON schemas;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260603-07-01_backend-capability-records_report.md` with:

- objective;
- risk level and approval confirmation;
- task ID scan result;
- files changed;
- implementation summary;
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
- risk level and approval confirmation;
- files changed;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no solver behavior, CLI behavior, JSON schema, native implementation,
  dependency, roadmap, or phase-transition files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
