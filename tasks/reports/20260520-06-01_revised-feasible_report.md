# Revised Simplex Feasible-Basis Report

## Summary

Added the first revised simplex solving path for LPs that already have a feasible slack basis. The solver builds standard form, rejects artificial-column cases, uses dense `numpy.linalg.solve` for basis systems, performs deterministic pricing and ratio tests, pivots through the `Basis` dataclass, and returns public `Solution` diagnostics on optimal termination.

## Mathematical Scope

This implementation supports continuous maximization LPs with nonnegative variables, no finite upper bounds, no nonzero lower bounds, `<=` rows, and nonnegative RHS values that produce no artificial variables. It intentionally rejects `>=`, `=`, and negative-RHS cases that require artificial columns because revised Phase I is not implemented yet.

## Files Changed

- `src/silo/lp/simplex/revised.py`
- `tests/unit/test_revised_simplex.py`
- `docs/lp_solver.md`
- `tasks/codex/20260520-06-01_revised-feasible.md`
- `tasks/reports/20260520-06-01_revised-feasible_report.md`

## Solver Behavior

- Uses mathematical maximization reduced costs `c_j - pi^T A_j`.
- Chooses the first nonbasic column with positive reduced cost above tolerance.
- Uses minimum ratio over positive direction components, with row-order tie breaking.
- Returns `UNBOUNDED` when no positive direction component restricts the entering variable.
- Returns `ITERATION_LIMIT` when the configured iteration budget is exhausted.
- Returns `ERROR` for artificial-column cases and unsupported model classes.
- Returns `NUMERICAL_ISSUE` for dense basis-system failures.

## Tests Added

- Single-variable feasible `<=` LP.
- Production LP.
- Tableau comparison on two small `<=` LPs.
- Reduced-cost and basis-status example with a nonbasic original variable.
- Unbounded LP.
- Artificial-column rejection for `>=`, `=`, and negative-RHS cases.
- Unsupported minimization, finite upper bound, nonzero lower bound, integer, and binary cases.
- Iteration-limit behavior.

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

- `pytest`: 93 passed
- `python scripts/check_quality.py`: 93 passed and ruff all checks passed
- CLI help/version/solve commands: passed

## Notes for Next Task

Phase 3C: add revised-simplex Phase I basis construction for artificial-column cases.
