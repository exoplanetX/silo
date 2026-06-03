# 20260604-01-01 Backend Parity Result Records

## Task metadata

- Task ID: 20260604-01-01
- Slug: parity-result-records
- Mode: SILO-DOS Mode A auto-one / review-gated L1 execution
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 9 native backend
- Design note: `notes/21_native_backend_boundary_design.md`
- Prior report: `tasks/reports/20260603-11-01_noop-backend-selector_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260604-01-01_parity-result-records_report.md`

## Objective

Add passive backend parity result records for comparing Python-reference expectations
with future backend outputs, without adding a comparison execution path, solver calls,
solver dispatch, CLI behavior, JSON schema changes, native implementation, or native
dependencies.

## Review gate

This task is L1 because it adds passive immutable Phase 9 interface records and validation
tests backed by `notes/21_native_backend_boundary_design.md`.

Mode A may execute this task only after the user explicitly approves this specific L1
task. If explicit approval is absent, stop after issuing this task and do not execute it.

Reclassify and stop before execution as L2 if implementation would add parity comparison
execution, call LP or MIP solvers, alter backend selector behavior, alter solver dispatch,
modify public backend behavior, change CLI behavior, change JSON schemas, or introduce
native availability probing.

## Context

Phase 9 planning established that Python reference behavior is the source of truth for
future optional native backend work. Completed Phase 9 tasks added backend boundary smoke
tests, immutable capability and availability records, passive Python-reference adapter
records, conformance fixture records, unavailable-native diagnostics tests, and a no-op
backend selector boundary. The next conservative step is to add passive parity result
records that can describe future comparison outcomes without executing comparisons or
connecting to solver dispatch.

## Scope lock

Add only passive parity result records and validation tests. The records may represent
expected and observed backend result summaries and a precomputed parity decision, but they
must not compute solver results, read model fixtures, execute parity comparisons, dispatch
to selected backends, probe native code, or expose any new public CLI or JSON schema
surface.

## Allowed changes

- `src/silo/interfaces/parity.py`
- `tests/unit/test_backend_parity_records.py`
- `tasks/codex/20260604-01-01_parity-result-records.md`
- `tasks/reports/20260604-01-01_parity-result-records_report.md`

## Forbidden changes

- Do not modify LP solvers.
- Do not modify MIP solvers or branch-and-bound behavior.
- Do not modify presolve behavior.
- Do not modify cut/callback behavior.
- Do not modify decomposition behavior.
- Do not modify uncertainty behavior.
- Do not modify backend selector behavior.
- Do not modify existing backend capability, Python-reference adapter, conformance,
  diagnostics, or selector source records unless completing this task is impossible
  without it; if so, stop and report instead.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `src/silo/interfaces/__init__.py`.
- Do not create `native/` implementation files.
- Do not add solver discovery, solver dispatch, fallback behavior, or parity comparison
  execution behavior.
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

Add `src/silo/interfaces/parity.py` with passive records only:

- define immutable backend result summary records suitable for parity diagnostics;
- include fields for backend id, status, optional objective value, primal values,
  tolerance label, and message;
- normalize primal values into deterministic sorted immutable tuples;
- validate nonempty labels and reject duplicate primal variable names;
- reject nonfinite objective values and nonfinite primal values;
- define an immutable parity decision or parity outcome record with fixture id,
  reference backend id, candidate backend id, match status, tolerance label, reason, and
  message;
- normalize and validate match status or reason labels deterministically;
- keep all records passive: they may store already-known comparison outcomes but must not
  perform comparisons against tolerances;
- do not import solver layers, CLI modules, native modules, selector modules, dynamic
  import helpers, environment variables, or optional dependencies.

The parity module must not include:

- `solve` methods;
- solver factories;
- parity comparison runners;
- fixture readers;
- calls to LP or MIP solvers;
- hidden fallback execution;
- environment-variable reads;
- dynamic imports;
- native availability probing;
- CLI or JSON schema integration.

## Required tests

Add `tests/unit/test_backend_parity_records.py` covering:

- backend result records normalize mapping or pair-sequence primal values into sorted
  immutable tuples;
- parity records can represent a matching Python-reference/candidate result pair
  passively without executing a comparison;
- parity records can represent a mismatch or unsupported comparison reason passively;
- records are immutable;
- blank labels are rejected;
- duplicate primal variable names are rejected;
- nonfinite objective values and primal values are rejected;
- importing the parity module does not load optional native modules into `sys.modules`;
- parity source does not import solver layers, CLI modules, native modules, selector
  modules, dynamic import helpers, environment variables, fixture readers, or solver
  factories;
- existing public CLI solver choices remain unchanged;
- existing Phase 9 backend boundary, capability, adapter, conformance, diagnostics, and
  selector tests still pass.

## Required checks

Run:

```powershell
pytest tests/unit/test_backend_parity_records.py
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

- Passive backend parity result records are added under
  `src/silo/interfaces/parity.py`.
- Records are immutable and deterministic.
- Records validate nonempty labels, duplicate primal names, and finite numeric values.
- Records can represent precomputed match, mismatch, and unsupported parity outcomes
  without executing comparisons.
- Tests cover validation, immutability, deterministic normalization, import boundaries,
  and unchanged CLI solver choices.
- Existing Phase 9 interface boundary tests still pass.
- No solver behavior, solver dispatch, public CLI behavior, JSON schemas, examples,
  roadmap files, or phase files are changed.
- No native backend implementation, native dependency, or native probing is added.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- implementing parity records requires changing backend selector behavior or any default
  solve path;
- implementing parity records requires a comparison execution path;
- implementing parity records requires LP or MIP solver calls;
- implementing parity records requires CLI or JSON schema changes;
- implementing parity records requires native implementation modules, native probing, or
  optional dependencies;
- existing Phase 9 source records need a source change to support this task;
- tests can pass only by modifying forbidden files;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260604-01-01_parity-result-records_report.md` with:

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
- confirmation that no solver behavior, solver dispatch, backend selector behavior, CLI
  behavior, JSON schema, native implementation, dependency, roadmap, or phase-transition
  files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
