# Binary Branch-and-Bound Solver Report

## Summary

Implemented the first native branch-and-bound solving loop for small binary maximization MIPs. The implementation remains narrow and educational: it supports binary variables plus optional continuous variables that satisfy the current LP relaxation boundary. It does not add CLI behavior, general integer support, cuts, heuristics, callbacks, external solver calls, or schema changes.

## Supported Scope

The solver supports maximization models with linear rows, binary variables with `[0, 1]` bounds, and optional continuous variables with lower bound `0` and no finite upper bound. General integer variables, minimization, nonzero lower bounds, and finite upper bounds on continuous variables return `SolverStatus.ERROR` with a clear message.

## Search Strategy

The solver uses deterministic depth-first search. It builds LP relaxations with `build_lp_relaxation()`, solves them with a native LP backend, branches on the first fractional binary variable in model order, creates left and right children with floor/ceil branching constraints, and pushes right before left so the left child is processed first by the LIFO stack.

## Solver Behavior

`BranchAndBoundSolver.solve()` returns a public `Solution`. `solve_with_details()` returns `BranchAndBoundResult` with processed/created/pruned counts, incumbent value, best bound, and a tuple of `NodeLogEntry` records. MIP public solutions expose status, objective, primal values, and message; LP relaxation slacks, duals, reduced costs, and basis status are not exposed as MIP solution fields.

## Files Changed

- `src/silo/mip/branch_and_bound.py`
- `src/silo/mip/__init__.py`
- `tests/unit/test_binary_branch_and_bound.py`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/codex/20260522-05-01_bnb-binary.md`
- `tasks/reports/20260522-05-01_bnb-binary_report.md`

## Tests Added

Added binary branch-and-bound tests for binary choice, binary knapsack, fractional LP relaxation branching, infeasible binary MIP, unsupported integer variables, unsupported minimization, node limit behavior, incumbent details, deterministic child order, bound-dominated pruning, revised simplex backend injection, and LP error propagation.

## Tests Run

- `pytest tests/unit/test_binary_branch_and_bound.py`
- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json`
- `silo compare examples/json/production.json`
- `git diff --check`

## Results

All checks passed. The full test suite reports 363 passing tests. `python scripts/check_quality.py` also reports 363 passing tests and all checks passed. Module and console CLI smoke commands returned expected help, version, solve, and compare outputs.

## Notes for Next Task

Phase 5E: bounded nonnegative integer variables.
