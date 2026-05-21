# Empty Row and Column Diagnostics Report

## Summary

Implemented conservative empty-row and empty-column presolve diagnostics on top of the existing immutable presolve result objects. The implementation does not connect presolve to solvers, CLI commands, or JSON schemas.

## Empty Row Behavior

`Presolver.run()` now detects empty rows using `DEFAULT_TOLERANCE`. Feasible empty rows are removed from a copied model, recorded in `removed_rows`, and represented by deterministic `ReductionType.EMPTY_ROW` records. Infeasible empty rows return `PresolveStatus.INFEASIBLE` with a warning and leave the original model unchanged.

## Empty Column Behavior

Empty columns are inspected in model variable order. A maximization variable with a positive objective coefficient, no nonzero constraint coefficients, and no finite upper bound returns `PresolveStatus.UNBOUNDED`. Other empty columns produce deterministic `empty_column` warnings without removing variables.

## Files Changed

- `src/silo/presolve/presolver.py`
- `src/silo/presolve/column_diagnostics.py`
- `tests/unit/test_empty_row_diagnostics.py`
- `tests/unit/test_empty_column_diagnostics.py`
- `docs/lp_solver.md`
- `tasks/phases/phase_04_presolve_scaling.md`

## Tests Added

- Feasible empty `<=`, `>=`, and `=` row removal.
- Infeasible empty `<=`, `>=`, and `=` row detection.
- Near-zero row coefficients treated as empty.
- Empty-column unboundedness detection.
- Empty-column warnings for zero and negative objective coefficients.
- Nonempty column warning suppression.
- Deterministic empty-column warning order.

## Tests Run

- `ruff check src/silo/presolve tests/unit/test_empty_row_diagnostics.py tests/unit/test_empty_column_diagnostics.py tests/unit/test_presolve_core.py`
- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json --solver tableau`
- `python -m silo.cli.main solve examples/json/production.json --solver revised`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo compare examples/json/production.json`

## Results

All checks passed. The full test suite now contains 165 passing tests. CLI help, version, solve, and compare smoke tests passed for both module and console entry points.

## Notes for Next Task

Phase 4D: implement fixed-variable elimination with solution reconstruction.
