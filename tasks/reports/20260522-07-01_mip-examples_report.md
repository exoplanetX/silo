# MIP Regression Examples Report

## Summary

Added checked-in MIP JSON examples and regression tests for the native branch-and-bound Python API. This task did not add MIP CLI behavior and did not change JSON schema, solution schema, LP solver behavior, presolve behavior, or branch-and-bound algorithms.

## Examples Added

- `examples/mip/binary_knapsack.json`
- `examples/mip/binary_choice.json`
- `examples/mip/integer_allocation.json`
- `examples/mip/mixed_binary_integer.json`
- `examples/mip/mixed_continuous_integer.json`
- `examples/mip/infeasible_binary.json`

## Regression Coverage

Added regression coverage that checks every `examples/mip/*.json` file has an expectation, every expectation file exists, every example is readable by `read_json_model()`, default `BranchAndBoundSolver` solves examples with expected statuses and objectives, selected examples solve with `RevisedSimplexSolver`, expected primal values match for unique-solution examples, infeasibility is reported correctly, and detailed branch-and-bound results expose node/log data.

## Files Changed

- Added MIP JSON examples under `examples/mip/`.
- Added `tests/regression/test_mip_json_examples.py`.
- Added `docs/mip_examples.md`.
- Updated `docs/json_model_format.md`.
- Updated `docs/lp_solver.md`.
- Updated `README.md`.
- Updated `tasks/phases/phase_05_branch_and_bound.md`.
- Added `tasks/codex/20260522-07-01_mip-examples.md`.
- Added `tasks/reports/20260522-07-01_mip-examples_report.md`.

## Tests Added

Added 24 regression tests for checked-in MIP JSON examples and Python API branch-and-bound behavior.

## Tests Run

- `pytest tests/regression/test_mip_json_examples.py`
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

All checks passed. The MIP JSON regression test reports 24 passing tests. The full test suite reports 397 passing tests. `python scripts/check_quality.py` also reports 397 passing tests and all checks passed. Module and console CLI smoke commands returned expected help, version, solve, and compare outputs.

## Notes for Next Task

Phase 5G: MIP CLI naming and exposure design note.
