# Scaling Diagnostics Report

## Summary

Implemented diagnostic-only coefficient-range scaling analysis for presolve. The presolver now includes populated `ScalingDiagnostics` on every result path without changing solver behavior, CLI behavior, model coefficients, JSON formats, or solution schemas.

## Diagnostics Added

`analyze_scaling(model)` computes matrix coefficient maximum, minimum nonzero coefficient, coefficient ratio, maximum RHS magnitude, maximum objective coefficient magnitude, and deterministic warnings. Constraint coefficient ranges only count coefficients with absolute value greater than `DEFAULT_TOLERANCE`.

## Warning Rules

Warnings are emitted in deterministic order: near-zero constraint coefficients in constraint and coefficient iteration order, near-zero objective coefficients in objective iteration order, large coefficient ratio, large RHS magnitude, and large objective magnitude. The large warning thresholds are `1e8`.

## Presolver Integration

`Presolver.run()` analyzes scaling immediately after model validation and carries the diagnostics through `INFEASIBLE`, `UNBOUNDED`, `REDUCED`, and `NO_CHANGE` returns. Scaling warnings remain in `result.scaling.warnings` and do not change `PresolveStatus`.

## Files Changed

- `src/silo/presolve/scaling.py`
- `src/silo/presolve/presolver.py`
- `src/silo/presolve/__init__.py`
- `tests/unit/test_scaling_diagnostics.py`
- `tests/unit/test_presolve_scaling_integration.py`
- `tests/unit/test_presolve_core.py`
- `docs/lp_solver.md`
- `tasks/phases/phase_04_presolve_scaling.md`

## Tests Added

- Empty/no-coefficient scaling diagnostics.
- Matrix coefficient max, minimum nonzero coefficient, and ratio.
- RHS magnitude.
- Objective coefficient magnitude.
- Near-zero constraint and objective coefficient warnings.
- Large coefficient-ratio, RHS, and objective warnings.
- Deterministic warning order.
- Presolver integration for no-change, reduced, infeasible, and unbounded returns.
- Scaling warnings that do not change presolve status.

## Tests Run

- `pytest tests/unit/test_scaling_diagnostics.py tests/unit/test_presolve_scaling_integration.py tests/unit/test_presolve_core.py tests/unit/test_empty_row_diagnostics.py tests/unit/test_empty_column_diagnostics.py tests/unit/test_fixed_variable_presolve.py -q`
- `ruff check src/silo/presolve tests/unit/test_scaling_diagnostics.py tests/unit/test_presolve_scaling_integration.py tests/unit/test_presolve_core.py`
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

All checks passed. The full test suite now contains 190 passing tests. CLI help, version, solve, and compare smoke tests passed for both module and console entry points.

## Notes for Next Task

Phase 4F: optional CLI flag for presolve diagnostics.
