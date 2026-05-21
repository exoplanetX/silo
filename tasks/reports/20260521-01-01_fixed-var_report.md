# Fixed-Variable Presolve Report

## Summary

Implemented conservative fixed-variable elimination in the presolve layer without connecting presolve to the CLI or LP solvers by default. Fixed variables are removed from the returned presolved model, and their values are stored for original-space solution recovery.

## Transformation Behavior

Variables with equal lower and upper bounds are eliminated in model variable order. Their values are substituted into constraint right-hand sides, removed from constraint coefficients, and added to the objective constant through their objective contribution. The original model is not mutated. Empty-row reductions remain ordered before fixed-variable reductions, and fixed-variable reductions use `ReductionType.FIXED_VARIABLE`.

Rows made empty by fixed-variable substitution are left for a future repeated-pass presolve design. This task does not introduce iterative presolve loops.

## Recovery Behavior

`PresolveResult.recover_solution()` copies the solver-space solution, restores fixed variable primal values, marks fixed variables with basis status `"fixed"`, and adds zero reduced costs for fixed variables. It preserves status, message, objective value, dual values, and slack values. Slack recomputation is deferred.

## Files Changed

- `src/silo/presolve/__init__.py`
- `src/silo/presolve/fixed_variable.py`
- `src/silo/presolve/presolver.py`
- `tests/unit/test_fixed_variable_presolve.py`
- `docs/lp_solver.md`
- `tasks/phases/phase_04_presolve_scaling.md`

## Tests Added

- Fixed variable removal and model transformation.
- Original model immutability.
- Multiple fixed variables with deterministic reduction order.
- Fixed variable absent from a row.
- Rows made empty by fixed-variable elimination remain for future passes.
- Solution recovery with tableau solve on the presolved model.
- Objective recovery without double counting.
- Non-optimal status and message preservation.
- Filtering of transformed-only variables during solution recovery.
- Combined empty-row and fixed-variable reductions.

## Tests Run

- `pytest tests/unit/test_presolve_core.py tests/unit/test_empty_row_diagnostics.py tests/unit/test_empty_column_diagnostics.py tests/unit/test_fixed_variable_presolve.py -q`
- `ruff check src/silo/presolve tests/unit/test_fixed_variable_presolve.py tests/unit/test_presolve_core.py`
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

All checks passed. The full test suite now contains 175 passing tests. CLI help, version, solve, and compare smoke tests passed for both module and console entry points.

## Notes for Next Task

Phase 4E: coefficient-range and scaling diagnostics.
