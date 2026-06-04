# Task Report: 20260604-04-01 Ratio-Test Parity Fixtures

## Task Objective

Add passive parity fixture records and validation tests for the selected Phase 9 native
kernel candidate `tableau_leaving_row_ratio_test`.

## Scope Summary

- Added immutable tableau ratio-test parity fixture records.
- Added deterministic fixture coverage for the selected candidate's passive input and
  expected-output boundary.
- Added validation, immutability, import-boundary, source-boundary, and CLI unchanged
  tests.
- Did not implement native code.
- Did not call LP, MIP, external, native, or dispatch solvers.
- Did not change solver dispatch, CLI behavior, JSON schemas, dependencies, build files,
  roadmap files, or phase files.

## Files Changed

- `src/silo/interfaces/tableau_ratio_parity.py`
- `tests/unit/test_tableau_ratio_parity.py`
- `tasks/codex/20260604-04-01_ratio-test-parity-fixtures.md`
- `tasks/reports/20260604-04-01_ratio-test-parity-fixtures_report.md`

## Fixture Coverage

The passive fixture tuple covers:

- single eligible leaving row;
- multiple eligible rows with a unique minimum ratio;
- equal ratios with smaller-row-index tie break;
- pivot coefficient exactly equal to tolerance ignored;
- pivot coefficients below tolerance, zero, and negative ignored;
- no eligible row returning `None`;
- a small production-style tableau row set with slack columns and RHS in the final
  column.

The fixture module normalizes rows to immutable tuples of finite floats and validates
rectangular shape, entering-column bounds, expected-row bounds, nonnegative finite
tolerance, and non-boolean numeric/index fields.

## Checks Run

- `pytest tests/unit/test_tableau_ratio_parity.py` - passed, 29 tests.
- `pytest tests/unit/test_backend_boundary_smoke.py` - passed, 4 tests.
- `pytest tests/unit/test_backend_capability_records.py` - passed, 12 tests.
- `pytest tests/unit/test_python_backend_adapter.py` - passed, 6 tests.
- `pytest tests/unit/test_backend_conformance.py` - passed, 15 tests.
- `pytest tests/unit/test_unavailable_native_backend_diagnostics.py` - passed, 8 tests.
- `pytest tests/unit/test_backend_selector.py` - passed, 13 tests.
- `pytest tests/unit/test_backend_parity_records.py` - passed, 21 tests.
- `pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_mip_solve.py`
  - passed, 48 tests.
- `python scripts/check_quality.py` - passed, 951 tests.
- `git diff --check` - passed.

## Git Status

- Before execution: branch `main`; working tree only had the untracked issued task file
  `tasks/codex/20260604-04-01_ratio-test-parity-fixtures.md`.
- After implementation and before commit: expected new passive interface module, new
  test module, issued task file, and this report.
- Local commit before push attempt: `bcec49ab9658ad90102868e68e447bd6734e5c6e`.
- Push mode: `push-on-success`.
- Push attempted: yes.
- Push result: failed. `git push` could not connect to `github.com` on port 443.
  The local commit was preserved, and this report was amended locally to record the
  failure. No second push attempt was made.

## Deviations From Scope

None.

## Unresolved Issues

None for this atomic task.

## Next Recommended Atomic Task

Add passive unavailable-native diagnostic records for the selected
`tableau_leaving_row_ratio_test` candidate, without native implementation, solver
dispatch, CLI changes, JSON schema changes, dependency changes, or build-system changes.
