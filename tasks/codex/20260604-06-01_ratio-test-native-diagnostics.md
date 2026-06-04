# 20260604-06-01 Ratio-Test Native Diagnostics

## Task metadata

- Task ID: 20260604-06-01
- Slug: ratio-test-native-diagnostics
- Mode: SILO-DOS Mode A auto-one / review-gated L1 execution
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 9 native backend
- Design notes:
  - `notes/21_native_backend_boundary_design.md`
  - `notes/22_native_kernel_candidate_selection.md`
- Prior report:
  `tasks/reports/20260604-05-01_phase9-implementation-readiness-audit_report.md`
- Git mode: push-on-success
- Expected report:
  `tasks/reports/20260604-06-01_ratio-test-native-diagnostics_report.md`

## Objective

Add passive unavailable-native diagnostic records for the selected
`tableau_leaving_row_ratio_test` native-kernel candidate, without native implementation,
solver calls, solver dispatch, public CLI changes, JSON schema changes, native
dependencies, build changes, packaging changes, roadmap changes, or phase changes.

## Review gate

This task is L1 because it adds passive candidate-specific diagnostic records and
validation tests backed by Phase 9 design notes and the latest implementation-readiness
audit.

Mode A may execute this task only after the user explicitly approves this specific L1
task. If explicit approval is absent, stop after issuing this task and do not execute it.

Reclassify and stop before execution as L2 or L3 if implementation would probe native
runtime availability, import native modules, call LP/MIP solvers, execute parity
comparisons, change backend selector behavior, add solver dispatch, alter public CLI
behavior, modify JSON schemas, add native dependencies, modify build or packaging files,
create native implementation files, or approve native implementation.

## Context

The Phase 9 native-kernel candidate selection note selected
`tableau_leaving_row_ratio_test` as the first future native-kernel candidate and stated
that unavailable-native diagnostics must exist before native implementation can be
considered.

The latest Phase 9 implementation-readiness audit classified the project as
`not_ready_for_native_kernel` because candidate-specific unavailable-native diagnostics,
native build/dependency policy, platform/artifact policy, and a native strategy decision
packet are still missing. This task addresses only the first blocker: passive
candidate-specific diagnostics.

## Scope lock

Add only passive diagnostic records and validation tests for unavailable or unsupported
native status of the selected ratio-test candidate. The records may identify the
candidate, backend id, availability status, reason, tolerance label, and message, but
they must not probe native code, execute ratio tests, call solvers, run parity
comparisons, read model files, dispatch to backends, or expose public CLI/JSON behavior.

## Allowed changes

- `src/silo/interfaces/tableau_ratio_native_diagnostics.py`
- `tests/unit/test_tableau_ratio_native_diagnostics.py`
- `tasks/codex/20260604-06-01_ratio-test-native-diagnostics.md`
- `tasks/reports/20260604-06-01_ratio-test-native-diagnostics_report.md`

## Forbidden changes

- Do not modify `src/silo/lp/simplex/ratio_test.py`.
- Do not modify `src/silo/interfaces/tableau_ratio_parity.py`.
- Do not modify existing backend interface records.
- Do not modify `src/silo/interfaces/__init__.py`.
- Do not modify tests other than the new diagnostic tests.
- Do not modify solver source outside the new passive interface diagnostic module.
- Do not modify examples.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify notes.
- Do not create or modify native implementation files.
- Do not add native dependencies.
- Do not add build-system or packaging changes.
- Do not add generated build artifacts.
- Do not implement a native kernel.
- Do not implement solver dispatch.
- Do not add backend fallback behavior.
- Do not call LP or MIP solvers.
- Do not call external solvers.
- Do not call `choose_leaving_row`.
- Do not execute parity comparisons.
- Do not probe native availability through imports, filesystem checks, subprocesses,
  dynamic imports, environment variables, or platform checks.
- Do not read model fixture JSON files.
- Do not close Phase 9.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Implementation requirements

Add `src/silo/interfaces/tableau_ratio_native_diagnostics.py` with passive records only:

- define immutable diagnostic records for the `tableau_leaving_row_ratio_test` candidate;
- include fields for candidate id, backend id, availability status, reason, tolerance
  label, and message;
- normalize string labels by trimming whitespace and rejecting empty values;
- normalize availability status through the existing `BackendAvailabilityStatus`
  conventions;
- reject unsupported status values;
- require a nonempty reason for `UNAVAILABLE` and `UNSUPPORTED` statuses;
- allow `AVAILABLE` status only as a passive record and do not probe runtime availability;
- provide deterministic candidate-specific records for:
  - unavailable native ratio-test kernel because the optional native runtime is not
    installed;
  - unsupported ratio-test native kernel candidate because implementation is not
    approved yet;
- expose a function returning the deterministic diagnostic tuple;
- keep messages deterministic and separate from public `Solution` schemas;
- keep the module passive: it must not import solver layers, CLI modules, native modules,
  dynamic import helpers, environment variables, subprocesses, pathlib/file readers,
  platform checks, backend selector code, or parity runner code.

The diagnostic module must not include:

- `solve` methods;
- solver factories;
- native implementation helpers;
- native availability probing;
- parity comparison runners;
- fixture file readers;
- calls to LP or MIP solvers;
- calls to external solvers;
- hidden fallback execution;
- CLI or JSON schema integration.

## Required tests

Add `tests/unit/test_tableau_ratio_native_diagnostics.py` covering:

- the diagnostic tuple is deterministic and includes the required diagnostic ids in fixed
  order;
- records normalize labels and availability statuses deterministically;
- records are immutable;
- blank candidate ids, backend ids, reasons, tolerance labels, and messages are rejected
  where applicable;
- unavailable or unsupported statuses require a nonempty reason;
- unknown status values are rejected;
- boolean or non-string labels are rejected where labels are expected;
- importing the diagnostic module does not load optional native modules into
  `sys.modules`;
- diagnostic source does not import solver layers, CLI modules, native modules,
  `choose_leaving_row`, dynamic import helpers, environment variables, filesystem
  readers, subprocesses, platform helpers, backend selector code, or solver factories;
- public CLI solver choices remain unchanged;
- public `Solution` schema remains free of backend/native diagnostic fields;
- existing Phase 9 backend boundary, capability, adapter, conformance, generic
  unavailable-native diagnostics, selector, parity, and ratio-test fixture tests still
  pass.

## Required checks

Run:

```powershell
pytest tests/unit/test_tableau_ratio_native_diagnostics.py
pytest tests/unit/test_tableau_ratio_parity.py
pytest tests/unit/test_backend_boundary_smoke.py
pytest tests/unit/test_backend_capability_records.py
pytest tests/unit/test_python_backend_adapter.py
pytest tests/unit/test_backend_conformance.py
pytest tests/unit/test_unavailable_native_backend_diagnostics.py
pytest tests/unit/test_backend_selector.py
pytest tests/unit/test_backend_parity_records.py
pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py
python scripts/check_quality.py
git diff --check
```

## Acceptance criteria

- Passive candidate-specific unavailable-native diagnostic records are added.
- Diagnostic records are immutable and validate candidate id, backend id, status, reason,
  tolerance label, and message.
- Tests cover deterministic record order, validation, immutability, import boundaries,
  source boundaries, unchanged public CLI choices, and unchanged public `Solution`
  schema.
- Existing Phase 9 boundary and ratio-test fixture tests still pass.
- No native kernel is implemented or approved.
- No solver behavior, solver dispatch, public CLI behavior, JSON schemas, examples,
  roadmap files, phase files, notes, native implementation files, dependencies, build
  files, or packaging files are changed.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- implementing the diagnostics requires changing `choose_leaving_row` or any solver
  source;
- implementing the diagnostics requires probing native code or runtime availability;
- implementing the diagnostics requires executing ratio tests, solver calls, or parity
  comparisons;
- implementing the diagnostics requires CLI or JSON schema changes;
- implementing the diagnostics requires native implementation modules, native
  dependencies, build files, or packaging files;
- existing Phase 9 records need a source change to support this task;
- tests can pass only by modifying forbidden files;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260604-06-01_ratio-test-native-diagnostics_report.md` with:

- objective;
- risk level and approval confirmation;
- task ID scan result;
- files changed;
- implementation summary;
- diagnostic coverage summary;
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
- diagnostic coverage summary;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no native kernel was implemented or approved;
- confirmation that no solver behavior, solver dispatch, CLI behavior, JSON schema,
  roadmap, phase, notes, native, dependency, build, or packaging files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
