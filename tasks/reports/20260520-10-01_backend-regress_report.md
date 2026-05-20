# Backend Regression Tests Report

## Summary

Added regression coverage that compares the tableau and revised native LP backends on all current user-facing JSON examples under `examples/json/`. The tests also check CLI backend behavior and solution JSON schema consistency.

## Examples Covered

- `production.json`
- `ge_row.json`
- `equality_row.json`
- `infeasible.json`

No new JSON example was added in this task.

## Backend Comparisons

Direct backend tests now verify:

- status consistency for all examples;
- objective consistency for optimal examples;
- primal and slack consistency for unique-primal examples;
- feasibility and binding equality residual for the degenerate equality example;
- empty `dual_values` for both backends;
- reduced-cost sign parity on a deterministic `maximize x - y` model.

CLI regression tests verify `--solver tableau` and `--solver revised` on production and infeasible examples, including solution JSON top-level fields.

## Files Changed

- `tests/regression/test_json_backend_regression.py`
- `tasks/codex/20260520-10-01_backend-regress.md`
- `tasks/reports/20260520-10-01_backend-regress_report.md`

## Tests Added

Added `tests/regression/test_json_backend_regression.py` with direct solver parity tests, reduced-cost sign parity, CLI backend checks, and schema consistency checks.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json --solver tableau`
- `python -m silo.cli.main solve examples/json/production.json --solver revised`
- `python -m silo.cli.main solve examples/json/infeasible.json --solver tableau`
- `python -m silo.cli.main solve examples/json/infeasible.json --solver revised`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json --solver tableau`
- `silo solve examples/json/production.json --solver revised`

## Results

All checks passed. The full test suite reported `125 passed`. The infeasible CLI commands returned exit code `1` with solution JSON status `infeasible`, as expected.

## Notes for Next Task

Phase 3G should implement a warm-start/reoptimization interface for revised simplex, now that backend parity is protected by regression tests.
