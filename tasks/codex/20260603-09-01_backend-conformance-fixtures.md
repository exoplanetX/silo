# 20260603-09-01 Backend Conformance Fixtures

## Task metadata

- Task ID: 20260603-09-01
- Slug: backend-conformance-fixtures
- Mode: SILO-DOS Mode A auto-one
- Task type: regression/boundary fixture records
- Risk level: L0 safe
- Phase reference: Phase 9 native backend
- Design note: `notes/21_native_backend_boundary_design.md`
- Prior report: `tasks/reports/20260603-08-01_python-backend-adapter_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260603-09-01_backend-conformance-fixtures_report.md`

## Objective

Add passive backend conformance fixture records for small LP fixtures without native code,
solver calls, backend selection, solver dispatch, CLI behavior changes, or JSON schema
changes.

## Context

Phase 9 planning requires Python/native parity tests eventually, but early conformance
records must not require native code to exist. The prior task added passive
Python-reference backend metadata. The next safe step is to define small deterministic
fixture records that future parity checks can use.

This task is L0 because it adds passive conformance fixture records and regression tests
only. It must not execute solvers or route models through backend-selection behavior.

## Scope lock

Add only passive fixture metadata plus tests. Do not wire the fixtures into LP/MIP
solvers, CLI commands, JSON schemas, environment-variable behavior, backend selection,
fallback behavior, parity execution paths, or native implementation code.

## Allowed changes

- `src/silo/interfaces/conformance.py`
- `tests/unit/test_backend_conformance.py`
- `tasks/codex/20260603-09-01_backend-conformance-fixtures.md`
- `tasks/reports/20260603-09-01_backend-conformance-fixtures_report.md`

## Forbidden changes

- Do not modify LP solvers.
- Do not modify MIP solvers or branch-and-bound behavior.
- Do not modify presolve behavior.
- Do not modify cut/callback behavior.
- Do not modify decomposition behavior.
- Do not modify uncertainty behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `src/silo/interfaces/backend.py`.
- Do not modify `src/silo/interfaces/python_reference.py`.
- Do not modify `src/silo/interfaces/__init__.py`.
- Do not create `native/` implementation files.
- Do not add backend selectors, fallback behavior, solver discovery, solver dispatch, or
  parity execution behavior.
- Do not add optional native dependencies.
- Do not add build-system or packaging changes.
- Do not call LP or MIP solvers.
- Do not call external solvers.
- Do not modify fixture JSON files.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Implementation requirements

Add `src/silo/interfaces/conformance.py` with passive immutable records for:

- a conformance fixture id;
- a model path or fixture path string;
- expected backend id, defaulting to the Python reference backend id;
- expected solver status as a string;
- expected objective value when applicable;
- expected primal values as immutable sorted items;
- expected tolerance label;
- optional message.

The module must also expose a deterministic tuple of small LP conformance fixtures based
on existing checked-in LP fixture files. The fixture records must not read model files,
solve models, import solver layers, dynamically import native modules, probe backend
availability, or depend on native code.

Validation requirements:

- ids, paths, status labels, backend ids, and tolerance labels must be nonempty trimmed
  strings;
- expected primal values must be immutable sorted tuples;
- duplicate primal variable names must be rejected;
- objective values and primal values must be finite when provided.

## Required tests

Add `tests/unit/test_backend_conformance.py` covering:

- valid deterministic fixture records for existing small LP fixture paths;
- immutable dataclass behavior;
- validation failures for blank ids/paths/status/tolerance labels;
- duplicate primal variable names;
- nonfinite objective or primal values;
- deterministic fixture ordering and paths;
- source/import boundary checks proving the conformance fixture module does not import
  solver layers, native implementation modules, dynamic import helpers, or CLI modules;
- importing the conformance fixture module does not load optional native modules into
  `sys.modules`;
- public CLI solver choices remain unchanged.

## Required checks

Run:

```powershell
pytest tests/unit/test_backend_conformance.py
pytest tests/unit/test_python_backend_adapter.py
pytest tests/unit/test_backend_capability_records.py
pytest tests/unit/test_backend_boundary_smoke.py
pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- Passive backend conformance fixture records are added under
  `src/silo/interfaces/conformance.py`.
- The records reference existing small LP fixture paths without reading or solving them.
- Tests cover validation, immutability, deterministic fixture content, and import
  boundaries.
- Existing Python-reference adapter, capability-record, and boundary-smoke tests still
  pass.
- CLI behavior and solver choices remain unchanged.
- No solver behavior, CLI behavior, JSON schemas, examples, fixture JSON files, roadmap
  files, or phase files are changed.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- implementing fixtures requires solver calls or solver dispatch changes;
- implementing fixtures requires backend selector behavior;
- implementing fixtures requires native implementation modules or dependencies;
- existing backend records need a change to support this task;
- tests can pass only by changing public CLI behavior or JSON schemas;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260603-09-01_backend-conformance-fixtures_report.md` with:

- objective;
- risk level;
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
- risk level;
- files changed;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no solver behavior, CLI behavior, JSON schema, native implementation,
  dependency, roadmap, or phase-transition files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
