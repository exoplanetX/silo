# Revised Simplex Warm Start Report

## Summary

Added a conservative warm-start interface for `RevisedSimplexSolver` while preserving the existing `solve(model) -> Solution` behavior. The new detailed solve path exposes the final standard-form problem, final basis, pivot iteration count, and whether a user-supplied basis was accepted.

## Interface Added

- `RevisedSimplexResult`
- `RevisedSimplexSolver.solve_with_details(model, basis=None)`

`solve()` now delegates to `solve_with_details(model).solution`, so existing public solver calls remain backward-compatible.

## Supported Warm-Start Scope

Warm starts are supported for compatible no-artificial-column standard-form models. A supplied `Basis` must validate against the current standard-form column and row counts, cover all columns, and produce a primal feasible basic solution.

## Unsupported Warm-Start Cases

Warm-start bases are rejected for models requiring artificial variables. Invalid bases and primal-infeasible bases return `SolverStatus.ERROR` with clear messages. No basis repair, Phase I repair, dual simplex, presolve, or basis mapping across transformed model structures was added.

## Files Changed

- `src/silo/lp/simplex/revised.py`
- `tests/unit/test_revised_warm_start.py`
- `docs/lp_solver.md`
- `tasks/phases/phase_03_revised_simplex.md`
- `tasks/codex/20260520-11-01_revised-warmstart.md`
- `tasks/reports/20260520-11-01_revised-warmstart_report.md`

## Tests Added

Added tests for:

- `solve()` backward compatibility;
- detailed result problem and basis exposure;
- warm start with a final optimal basis and zero pivots;
- simple RHS reoptimization with a reused feasible optimal basis;
- structurally invalid warm-start basis rejection;
- primal-infeasible warm-start basis rejection;
- artificial-column model warm-start rejection while normal solve still works;
- cold solve positive pivot-count reporting.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json --solver tableau`
- `python -m silo.cli.main solve examples/json/production.json --solver revised`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json --solver tableau`
- `silo solve examples/json/production.json --solver revised`

## Results

All checks passed. The final full test run reported `133 passed`.

## Notes for Next Task

Phase 3H should add a small backend comparison command or developer utility so warm-start and backend parity checks can be exercised outside the unit test suite.
