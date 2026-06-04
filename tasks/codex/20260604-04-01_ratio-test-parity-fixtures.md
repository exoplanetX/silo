# 20260604-04-01 Tableau Ratio-Test Parity Fixtures

## Task metadata

- Task ID: 20260604-04-01
- Slug: ratio-test-parity-fixtures
- Mode: SILO-DOS Mode A auto-one / review-gated L1 execution
- Task type: controlled implementation
- Risk level: L1 controlled implementation
- Phase reference: Phase 9 native backend
- Design note: `notes/22_native_kernel_candidate_selection.md`
- Prior report: `tasks/reports/20260604-03-01_native-kernel-selection_report.md`
- Git mode: push-on-success
- Expected report: `tasks/reports/20260604-04-01_ratio-test-parity-fixtures_report.md`

## Objective

Add passive parity fixture records for the `tableau_leaving_row_ratio_test` native-kernel
candidate, without native implementation, solver dispatch, solver behavior changes, CLI
changes, JSON schema changes, native dependencies, build changes, or packaging changes.

## Review gate

This task is L1 because it adds passive fixture records and validation tests backed by
`notes/22_native_kernel_candidate_selection.md`.

Mode A may execute this task only after the user explicitly approves this specific L1
task. If explicit approval is absent, stop after issuing this task and do not execute it.

Reclassify and stop before execution as L2 or L3 if implementation would call
`choose_leaving_row`, run parity comparisons, change solver dispatch, alter default
tableau simplex behavior, modify public CLI behavior, modify JSON schemas, add native
dependencies, add build or packaging files, create native implementation files, or approve
native implementation.

## Context

The Phase 9 native-kernel candidate selection note selected exactly one first candidate:
`tableau_leaving_row_ratio_test`, corresponding to Python reference behavior in
`silo.lp.simplex.ratio_test.choose_leaving_row`.

The note explicitly requires a passive fixture task before any native implementation.
The fixture records should describe deterministic Python-reference expectations, not
execute the Python function and not call any native implementation.

## Scope lock

Add only passive fixture records and validation tests for the selected ratio-test
candidate. The records may store tableau rows, entering-column index, tolerance metadata,
and expected leaving-row index, but they must not call solvers, execute ratio tests, read
model files, dispatch to backends, probe native code, or expose public CLI/JSON behavior.

## Allowed changes

- `src/silo/interfaces/tableau_ratio_parity.py`
- `tests/unit/test_tableau_ratio_parity.py`
- `tasks/codex/20260604-04-01_ratio-test-parity-fixtures.md`
- `tasks/reports/20260604-04-01_ratio-test-parity-fixtures_report.md`

## Forbidden changes

- Do not modify `src/silo/lp/simplex/ratio_test.py`.
- Do not modify any solver source outside the new passive interface fixture module.
- Do not modify existing backend interface records.
- Do not modify `src/silo/interfaces/__init__.py`.
- Do not modify tests other than the new fixture tests.
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
- Do not call `choose_leaving_row` from the fixture module.
- Do not read model fixture JSON files.
- Do not close Phase 9.
- Do not start Phase 10 or any future phase.
- Do not issue or execute another task.

## Implementation requirements

Add `src/silo/interfaces/tableau_ratio_parity.py` with passive records only:

- define an immutable fixture record for the `tableau_leaving_row_ratio_test` candidate;
- include fields for fixture id, rows, entering-column index, expected leaving-row index,
  tolerance, tolerance label, and message;
- normalize rows into deterministic immutable tuples of tuples of floats;
- validate that rows are nonempty, rectangular, finite, and wide enough to include an
  entering column plus a right-hand-side column;
- validate that `entering_column` is an integer, nonnegative, and not the
  right-hand-side column;
- validate that `expected_leaving_row` is either `None` or a valid row index;
- reject boolean values for numeric or index fields;
- validate finite nonnegative tolerance;
- provide a deterministic tuple of passive fixtures covering:
  - a single eligible leaving row;
  - multiple eligible rows with a unique minimum ratio;
  - equal ratios breaking by smaller row index;
  - a pivot coefficient exactly equal to tolerance, which must be ignored;
  - pivot coefficients below tolerance, zero, or negative, which must be ignored;
  - no eligible row, returning `None`;
  - a small production-style tableau row set derived from existing Python fixture
    conventions without reading fixture files at runtime;
- expose a function returning the fixture tuple;
- keep the module passive: it must not call `choose_leaving_row`, import solver layers,
  import CLI modules, import native modules, dynamically import modules, read environment
  variables, read fixture files, dispatch to backends, or execute comparisons.

The fixture module must not include:

- `solve` methods;
- solver factories;
- native implementation helpers;
- parity comparison runners;
- fixture file readers;
- calls to LP or MIP solvers;
- calls to external solvers;
- hidden fallback execution;
- environment-variable reads;
- dynamic imports;
- native availability probing;
- CLI or JSON schema integration.

## Required tests

Add `tests/unit/test_tableau_ratio_parity.py` covering:

- the fixture tuple is deterministic and includes the required fixture ids in fixed
  order;
- rows normalize to immutable tuples of tuples of floats;
- fixture records are immutable;
- blank fixture ids and tolerance labels are rejected;
- non-rectangular rows are rejected;
- empty rows are rejected;
- nonfinite row values are rejected;
- invalid entering-column indexes are rejected;
- boolean entering-column and expected-row values are rejected;
- expected leaving-row indexes outside the row range are rejected;
- negative or nonfinite tolerance values are rejected;
- importing the fixture module does not load optional native modules into `sys.modules`;
- fixture source does not import solver layers, CLI modules, native modules,
  `choose_leaving_row`, dynamic import helpers, environment variables, fixture readers,
  or solver factories;
- existing public CLI solver choices remain unchanged;
- existing Phase 9 backend boundary, capability, adapter, conformance, diagnostics,
  selector, and parity tests still pass.

## Required checks

Run:

```powershell
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

- Passive tableau ratio-test parity fixture records are added.
- The fixture set covers the required deterministic cases from
  `notes/22_native_kernel_candidate_selection.md`.
- Fixtures are immutable and validate labels, row shape, finite numeric values, indexes,
  expected row bounds, and tolerance.
- Tests cover validation, immutability, deterministic fixture order, import boundaries,
  source boundaries, and unchanged public CLI solver choices.
- Existing Phase 9 boundary tests still pass.
- No native kernel is implemented or approved.
- No solver behavior, solver dispatch, public CLI behavior, JSON schemas, examples,
  roadmap files, phase files, notes, native implementation files, dependencies, build
  files, or packaging files are changed.
- The required report is created.
- Required checks pass.
- No second task is issued or executed.

## Stop conditions

Stop and report without modifying forbidden files if:

- implementing the fixtures requires changing `choose_leaving_row` or any solver source;
- implementing the fixtures requires executing ratio tests or parity comparisons;
- implementing the fixtures requires CLI or JSON schema changes;
- implementing the fixtures requires native implementation modules, native probing,
  native dependencies, build files, or packaging files;
- existing Phase 9 source records need a source change to support this task;
- tests can pass only by modifying forbidden files;
- the task ID collides with an existing task or report.

## Report requirements

Create `tasks/reports/20260604-04-01_ratio-test-parity-fixtures_report.md` with:

- objective;
- risk level and approval confirmation;
- task ID scan result;
- files changed;
- implementation summary;
- fixture coverage summary;
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
- fixture coverage summary;
- checks run and results;
- commit hash;
- whether push succeeded;
- confirmation that no native kernel was implemented or approved;
- confirmation that no solver behavior, solver dispatch, CLI behavior, JSON schema,
  roadmap, phase, notes, native, dependency, build, or packaging files were changed;
- next recommended task and whether approval is required;
- confirmation that no second task was issued or executed.
