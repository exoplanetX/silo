# 20260603-08-01 Python Backend Adapter Record

## Task metadata

- Task ID: 20260603-08-01
- Slug: python-backend-adapter
- Mode: SILO-DOS Mode A auto-one / review-gated L1 execution
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 9 native backend
- Design note: `notes/21_native_backend_boundary_design.md`
- Prior report: `tasks/reports/20260603-07-01_backend-capability-records_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260603-08-01_python-backend-adapter_report.md`

## Objective

Add a passive Python-reference backend adapter record that describes existing Python
solver capabilities without changing solver behavior, backend selection, solver dispatch,
CLI behavior, JSON schemas, or native dependency requirements.

## Review gate

This task is L1 because it adds Phase 9 implementation records under the backend
interface boundary. Mode A may execute it only after the user explicitly approves this
specific L1 task.

If explicit approval is absent, stop after issuing this task and do not execute it.

## Context

Phase 9 planning established that Python reference behavior remains the source of truth
and that native-backend work must be optional and isolated. The prior task added passive
backend capability and availability records in `src/silo/interfaces/backend.py`.

The next conservative step is to add a passive Python-reference adapter record that uses
those records to describe the already-existing Python reference solver family. This
adapter must not call solvers, select solvers, or become part of CLI or JSON contracts.

## Scope lock

Add only passive Python-reference adapter metadata plus validation tests. Do not wire the
adapter into LP/MIP solvers, CLI commands, JSON schemas, environment-variable behavior,
backend selection, fallback behavior, or native implementation code.

## Allowed changes

- `src/silo/interfaces/python_reference.py`
- `tests/unit/test_python_backend_adapter.py`
- `tasks/codex/20260603-08-01_python-backend-adapter.md`
- `tasks/reports/20260603-08-01_python-backend-adapter_report.md`

## Forbidden changes

- Do not modify LP solvers.
- Do not modify MIP solvers or branch-and-bound behavior.
- Do not modify presolve behavior.
- Do not modify cut/callback behavior.
- Do not modify decomposition behavior.
- Do not modify uncertainty behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `src/silo/interfaces/backend.py` unless a validation bug in the existing
  records makes this task impossible; if that happens, stop and report instead.
- Do not modify `src/silo/interfaces/__init__.py`.
- Do not create `native/` implementation files.
- Do not add backend selectors, fallback behavior, solver discovery, or solver dispatch.
- Do not add optional native dependencies.
- Do not add build-system or packaging changes.
- Do not call LP or MIP solvers from the adapter.
- Do not call external solvers.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Implementation requirements

Add `src/silo/interfaces/python_reference.py` with passive metadata only:

- define a deterministic Python-reference backend id;
- define a `BackendCapability` record describing the current Python reference scope;
- define a `BackendAvailability` record marking the Python reference backend available;
- expose a small function or constant that returns those records without solving,
  selecting, discovering, dynamically importing, or probing any backend;
- keep all tuple-like metadata deterministic and covered by tests.

The adapter must not include:

- `solve` methods;
- solver factories;
- backend selector logic;
- fallback policy;
- environment-variable reads;
- dynamic imports;
- native availability probing;
- imports from LP, MIP, presolve, cuts, decomposition, uncertainty, or CLI modules.

## Required tests

Add `tests/unit/test_python_backend_adapter.py` covering:

- the Python-reference capability record uses `BackendKind.PYTHON_REFERENCE`;
- the Python-reference availability record is `available` and has no required
  unavailability reason;
- returned records are immutable and deterministic;
- the adapter module imports only the passive backend record module, not solver layers;
- importing the adapter does not load optional native modules into `sys.modules`;
- public CLI solver choices remain unchanged.

## Required checks

Run:

```powershell
pytest tests/unit/test_python_backend_adapter.py
pytest tests/unit/test_backend_capability_records.py
pytest tests/unit/test_backend_boundary_smoke.py
pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- A passive Python-reference adapter record is added under
  `src/silo/interfaces/python_reference.py`.
- The adapter uses existing backend capability and availability records.
- The adapter is deterministic, immutable through its records, and covered by tests.
- The adapter does not import or call solver layers.
- The adapter does not load optional native modules.
- Existing capability-record and boundary-smoke tests still pass.
- CLI behavior and solver choices remain unchanged.
- No solver behavior, CLI behavior, JSON schemas, examples, roadmap files, or phase files
  are changed.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- implementing the adapter requires solver calls or solver dispatch changes;
- implementing the adapter requires backend selector behavior;
- implementing the adapter requires native implementation modules or dependencies;
- existing backend records need a change to support this task;
- tests can pass only by changing public CLI behavior or JSON schemas;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260603-08-01_python-backend-adapter_report.md` with:

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
