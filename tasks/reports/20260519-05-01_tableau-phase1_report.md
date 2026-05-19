# Tableau Phase I Report

## Summary

Added a readable dense-tableau Phase I / Phase II flow to the native tableau simplex solver. The solver now normalizes negative RHS rows, builds slack, surplus, and artificial variables, runs Phase I for an initial feasible basis, detects infeasible LPs through the artificial objective, removes artificial columns, restores the original objective, and then runs Phase II.

## Mathematical Scope

Supported models remain continuous maximization LPs with nonnegative variables, no finite upper bounds, and no nonzero lower bounds. Constraint rows may now use `<=`, `>=`, or `=`. Minimization, finite upper bounds, nonzero lower bounds, integer variables, binary variables, revised simplex, dual simplex, presolve, MIP, cuts, decomposition, stochastic/robust extensions, and external solver calls remain unsupported.

## Files Changed

- `src/silo/lp/simplex/tableau.py`
- `tests/unit/test_tableau_simplex.py`
- `tasks/codex/20260519-05-01_tableau-phase1.md`
- `tasks/reports/20260519-05-01_tableau-phase1_report.md`

## Tests Added

- Phase I objective canonicalization for an artificial-variable basis.
- Feasible `>=` row solved through Phase I.
- Objective constant preservation after Phase I / Phase II transition.
- Feasible equality row solved through Phase I.
- Negative RHS normalization.
- Phase I infeasibility detection.
- Equality row with zero RHS.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `silo --help`
- `silo --version`

## Results

- `pytest`: 45 passed
- `python scripts/check_quality.py`: 45 passed and ruff all checks passed
- CLI help/version commands: passed

## Notes for Next Task

Phase 2C should expose tableau solution details such as slack values, reduced costs, and basic-variable metadata before adding broader CLI solve workflows.
