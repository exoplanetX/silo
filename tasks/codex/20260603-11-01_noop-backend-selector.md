# 20260603-11-01 No-Op Backend Selector Boundary

## Task metadata

- Task ID: 20260603-11-01
- Slug: noop-backend-selector
- Mode: SILO-DOS Mode A auto-one / review-gated L1 execution
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 9 native backend
- Design note: `notes/21_native_backend_boundary_design.md`
- Prior report: `tasks/reports/20260603-10-01_unavailable-native-diagnostics_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260603-11-01_noop-backend-selector_report.md`

## Objective

Add a no-op backend selector boundary that always returns the Python reference backend by
default, without changing solver behavior, solver dispatch, public backend behavior, CLI
behavior, JSON schemas, native implementation, or native dependency requirements.

## Review gate

This task is L1 because it adds a Phase 9 backend-selection boundary record. Mode A may
execute it only after the user explicitly approves this specific L1 task.

If explicit approval is absent, stop after issuing this task and do not execute it.

Reclassify and stop before execution as L2 if implementation would change solver dispatch,
public backend behavior, CLI behavior, JSON schemas, fallback behavior, or any default
solve path.

## Context

Phase 9 planning established that backend selection should eventually be explicit,
optional, and reversible, while the default solver path remains the Python implementation.
The prior tasks added passive backend capability records, Python-reference adapter records,
conformance fixture records, and unavailable-native diagnostics tests. The next
conservative step is a no-op selector boundary that records the default selection decision
without integrating with solvers.

## Scope lock

Add only passive/no-op selector records and tests. Do not wire the selector into LP/MIP
solvers, CLI commands, JSON schemas, environment-variable behavior, fallback behavior,
parity execution paths, or native implementation code.

## Allowed changes

- `src/silo/interfaces/selector.py`
- `tests/unit/test_backend_selector.py`
- `tasks/codex/20260603-11-01_noop-backend-selector.md`
- `tasks/reports/20260603-11-01_noop-backend-selector_report.md`

## Forbidden changes

- Do not modify LP solvers.
- Do not modify MIP solvers or branch-and-bound behavior.
- Do not modify presolve behavior.
- Do not modify cut/callback behavior.
- Do not modify decomposition behavior.
- Do not modify uncertainty behavior.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify existing backend capability, Python-reference adapter, conformance, or
  diagnostics source records unless completing this task is impossible without it; if so,
  stop and report instead.
- Do not modify `src/silo/interfaces/__init__.py`.
- Do not create `native/` implementation files.
- Do not add solver discovery, solver dispatch, fallback behavior, or parity execution
  behavior.
- Do not add optional native dependencies.
- Do not add build-system or packaging changes.
- Do not call LP or MIP solvers.
- Do not call external solvers.
- Do not read model fixture JSON files.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Implementation requirements

Add `src/silo/interfaces/selector.py` with passive/no-op selector records only:

- define an immutable selector request record with an optional requested backend id and a
  fallback policy label;
- define an immutable selector decision record containing selected backend id, selected
  kind, availability status, fallback policy, reason, and message;
- expose a no-op selection function that returns the existing Python-reference backend
  records by default;
- when a requested backend id is the Python-reference backend id, return the same
  Python-reference decision;
- for any non-Python-reference requested backend id, return a passive unavailable or
  unsupported decision without fallback execution;
- keep returned records deterministic and immutable;
- do not import solver layers, CLI modules, native modules, dynamic import helpers,
  environment variables, or optional dependencies.

The selector must not include:

- `solve` methods;
- solver factories;
- calls to LP or MIP solvers;
- hidden fallback execution;
- environment-variable reads;
- dynamic imports;
- native availability probing;
- CLI or JSON schema integration.

## Required tests

Add `tests/unit/test_backend_selector.py` covering:

- default no-op selection returns the Python-reference backend id, kind, and available
  status;
- explicit Python-reference request returns the same deterministic decision;
- non-Python-reference requested backend ids produce a passive unavailable or unsupported
  decision without invoking fallback execution;
- selector request and decision records are immutable;
- selector records normalize and validate nonempty backend ids and fallback policy labels;
- importing the selector does not load optional native modules into `sys.modules`;
- selector source does not import solver layers, CLI modules, native modules, dynamic
  import helpers, or environment variables;
- existing public CLI solver choices remain unchanged;
- existing backend capability, adapter, conformance, and unavailable-native diagnostics
  tests still pass.

## Required checks

Run:

```powershell
pytest tests/unit/test_backend_selector.py
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

- A no-op backend selector boundary is added under `src/silo/interfaces/selector.py`.
- Default selection is deterministic and returns the Python-reference backend records.
- Non-Python-reference requests do not dispatch, fallback-execute, or probe native code.
- Tests cover default selection, explicit Python-reference selection, unsupported or
  unavailable non-Python-reference requests, immutability, validation, and import
  boundaries.
- Existing Phase 9 interface boundary tests still pass.
- CLI behavior and solver choices remain unchanged.
- No solver behavior, solver dispatch, public CLI behavior, JSON schemas, examples,
  roadmap files, or phase files are changed.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- implementing the selector requires changing solver dispatch or any default solve path;
- implementing the selector requires CLI or JSON schema changes;
- implementing the selector requires fallback execution behavior;
- implementing the selector requires native implementation modules or dependencies;
- existing Phase 9 records need a source change to support this task;
- tests can pass only by modifying forbidden files;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260603-11-01_noop-backend-selector_report.md` with:

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
- confirmation that no solver behavior, solver dispatch, CLI behavior, JSON schema,
  native implementation, dependency, roadmap, or phase-transition files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
