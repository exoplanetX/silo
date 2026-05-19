# Standard Form and Basis Report

## Summary

Added Phase 3A infrastructure for revised simplex without implementing revised simplex iterations. The new standard-form builder transforms supported LP models into equality form and records transformed columns, RHS values, objective coefficients, artificial columns, and an initial deterministic basis.

## Files Changed

- `src/silo/lp/simplex/basis.py`
- `src/silo/lp/simplex/standard_form.py`
- `tests/unit/test_basis.py`
- `tests/unit/test_standard_form.py`
- `docs/lp_solver.md`
- `tasks/codex/20260520-05-01_stdform-basis.md`
- `tasks/reports/20260520-05-01_stdform-basis_report.md`

## Standard-Form Scope

The builder supports the same LP class as the tableau simplex path: maximization models with `<=`, `>=`, and `=` rows, continuous nonnegative variables, no finite upper bounds, and no nonzero lower bounds. It normalizes negative RHS rows, adds slack variables for `<=` rows, surplus plus artificial variables for `>=` rows, and artificial variables for equality rows.

## Basis Semantics

`Basis` records ordered `basic_columns` and `nonbasic_columns`, validates coverage and disjointness, reports `basic` or `nonbasic_lower` status, and returns a new basis on pivot without mutating the original basis. Pivoting removes the entering column from the nonbasic list and appends the leaving basic column deterministically.

## Tests Added

- Standard-form transformation tests for `<=`, `>=`, equality, and negative RHS rows.
- Unsupported-model tests for minimization, finite upper bounds, nonzero lower bounds, integer variables, and binary variables.
- Basis validation tests for duplicates, overlap, missing columns, out-of-range columns, and wrong row counts.
- Basis status and pivot tests.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json`

## Results

- `pytest`: 83 passed
- `python scripts/check_quality.py`: 83 passed and ruff all checks passed
- CLI help/version/solve commands: passed

## Notes for Next Task

Phase 3B: implement primal revised simplex for already feasible slack-basis LPs.
