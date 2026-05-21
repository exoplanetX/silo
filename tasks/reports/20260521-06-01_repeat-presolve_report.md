# Repeated-Pass Presolve Report

## Summary

Implemented repeated-pass presolve in `Presolver.run()`. The loop repeatedly composes the existing conservative structural reductions: feasible empty-row removal and fixed-variable elimination. No new presolve rule was added.

## Pass Ordering

Each pass uses deterministic order:

1. Check infeasible empty rows on the current model.
2. Inspect empty columns on the current model.
3. Remove feasible empty rows in current constraint order.
4. Eliminate fixed variables in current variable order.

Scaling diagnostics are computed once on the original submitted model.

## Termination Behavior

The loop stops when a pass applies no structural reduction. Terminal infeasible empty-row and empty-column unboundedness statuses preserve any reductions already applied and return the current model at the detection point. A private pass guard uses `number_of_variables + number_of_constraints + 1`.

## Recovery Behavior

`PresolveResult.fixed_values` now accumulates fixed variables across passes. `recover_solution()` continues to restore fixed primal values, fixed basis statuses, zero reduced costs, and the presolved solution objective without adding the fixed-objective contribution again.

## Files Changed

- `src/silo/presolve/presolver.py`
- `tests/unit/test_fixed_variable_presolve.py`
- `tests/unit/test_cli_solve_presolve.py`
- `tests/unit/test_repeated_presolve.py`
- `docs/lp_solver.md`
- `tasks/phases/phase_04_presolve_scaling.md`
- `tasks/codex/20260521-06-01_repeat-presolve.md`
- `tasks/reports/20260521-06-01_repeat-presolve_report.md`

## Tests Added

- Fixed-variable elimination creates a feasible empty equality row removed in a later pass.
- Fixed-variable elimination creates an infeasible empty row detected in a later pass.
- Multiple fixed variables create a feasible empty row with deterministic reduction order.
- Diagnostic-only empty-column warnings do not trigger another pass.
- Solution recovery restores fixed variables after repeated passes.
- CLI `solve --presolve` recovers a solution after repeated-pass reductions.

No natural empty-column-unboundedness-after-prior-reductions case was added. With the current reduction scope, feasible empty-row removal only deletes rows with no nonzero current coefficients, and fixed-variable elimination does not remove nonfixed variable occurrences; therefore these reductions do not naturally reveal a previously constrained nonfixed variable as an empty unbounded column.

## Tests Run

```text
pytest tests/unit/test_repeated_presolve.py tests/unit/test_fixed_variable_presolve.py tests/unit/test_empty_row_diagnostics.py tests/unit/test_empty_column_diagnostics.py tests/unit/test_cli_solve_presolve.py
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json --presolve
python -m silo.cli.main presolve examples/json/production.json
python -m silo.cli.main compare examples/json/production.json
silo --help
silo --version
silo solve examples/json/production.json --presolve
silo presolve examples/json/production.json
silo compare examples/json/production.json
```

## Results

All targeted tests passed. Full `pytest` passed with 214 tests. `python scripts/check_quality.py` passed. Module and console CLI smoke commands all completed successfully.

## Notes for Next Task

Phase 4J: original-space slack recomputation after presolve recovery.
