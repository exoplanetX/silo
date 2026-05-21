# Bounded Integer Branch-and-Bound Report

## Summary

Extended the native branch-and-bound solver from binary-only MIPs to bounded nonnegative integer variables. The solver remains deterministic, depth-first, pure branch-and-bound, and LP-relaxation based. No CLI behavior, JSON schema, solution schema, LP solver behavior, presolve behavior, cuts, heuristics, callbacks, or external solver calls were added.

## Supported Scope

`BranchAndBoundSolver` now supports maximization models with binary variables, bounded nonnegative integer variables, and optional continuous variables with lower bound `0` and no finite upper bound. Integer variables must have lower bound `0` and a finite integer-valued upper bound.

## Validation Changes

The previous binary-only validation now returns all integer-restricted variable names in model order, including both binary and integer variables. It rejects minimization, binary variables outside `[0, 1]`, integer variables with infinite or non-integer upper bounds, integer variables with nonzero lower bounds, continuous variables with finite upper bounds, and continuous variables with nonzero lower bounds.

## Branching Behavior

Branching continues to use the first fractional integer-restricted variable in original model order. Binary and integer variables use the same floor/ceil branching rule, so a value such as `x = 1.5` creates `x <= 1` and `x >= 2`. Incumbent candidates round all integer-restricted variables within `DEFAULT_INTEGER_TOLERANCE` and leave continuous variables unchanged.

## Files Changed

- `src/silo/mip/branch_and_bound.py`
- `tests/unit/test_binary_branch_and_bound.py`
- `tests/unit/test_integer_branch_and_bound.py`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/codex/20260522-06-01_bnb-integer.md`
- `tasks/reports/20260522-06-01_bnb-integer_report.md`

## Tests Added

Added bounded integer branch-and-bound tests for a single bounded integer variable, bounded integer allocation, mixed binary/integer models, mixed continuous/integer models, integer branching above one, unbounded integer rejection, non-integer upper-bound rejection, nonzero integer lower-bound rejection, continuous finite-upper-bound rejection, and revised simplex backend injection.

## Tests Run

- `pytest tests/unit/test_integer_branch_and_bound.py tests/unit/test_binary_branch_and_bound.py`
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

All checks passed. The targeted binary/integer branch-and-bound tests report 22 passing tests. The full test suite reports 373 passing tests. `python scripts/check_quality.py` also reports 373 passing tests and all checks passed. Module and console CLI smoke commands returned expected help, version, solve, and compare outputs.

## Notes for Next Task

Phase 5F: MIP regression examples and documentation before CLI exposure.
