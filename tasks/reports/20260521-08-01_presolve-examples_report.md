# Presolve Recovery Examples Report

## Summary

Added checked-in JSON examples for fixed-variable presolve recovery, repeated-pass empty-row removal, original-space slack recovery, and presolve-detected infeasibility after fixed-variable elimination. Added regression coverage that exercises these examples through the public CLI paths.

## Examples Added

- `examples/json/fixed_var_recovery.json`
- `examples/json/repeated_empty_row.json`
- `examples/json/presolve_infeasible_after_fixed.json`

## Behaviors Covered

- `fixed_var_recovery.json` solves with `--presolve`, restores fixed variable `x = 2`, and reports original-space slacks for `capacity` and `y_limit`.
- `repeated_empty_row.json` solves with `--presolve`, removes `x_eq_2` after a later repeated pass, restores `x = 2`, and reports original-space slack for the removed row.
- `presolve_infeasible_after_fixed.json` applies fixed-variable elimination and then detects the resulting infeasible empty row.
- Default solve without `--presolve` remains unchanged for fixed-bound examples and returns `error`.

## Tests Added

- `tests/regression/test_presolve_json_examples.py`
- Updated JSON backend example expectations so the new presolve-only examples remain explicitly accounted for by the existing `examples/json` scan.

## Tests Run

```text
pytest tests/regression/test_presolve_json_examples.py tests/regression/test_json_backend_regression.py tests/unit/test_cli_presolve.py tests/unit/test_cli_solve_presolve.py
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/fixed_var_recovery.json --presolve
python -m silo.cli.main solve examples/json/repeated_empty_row.json --presolve
python -m silo.cli.main presolve examples/json/repeated_empty_row.json
python -m silo.cli.main presolve examples/json/presolve_infeasible_after_fixed.json
python -m silo.cli.main compare examples/json/production.json
silo --help
silo --version
silo solve examples/json/fixed_var_recovery.json --presolve
silo solve examples/json/repeated_empty_row.json --presolve
silo presolve examples/json/repeated_empty_row.json
silo presolve examples/json/presolve_infeasible_after_fixed.json
silo compare examples/json/production.json
git diff --check
```

## Results

Targeted regression tests passed. Editable dev install completed successfully. Full `pytest` passed with 234 tests. `python scripts/check_quality.py` passed. Module and console CLI smoke commands completed successfully. `git diff --check` reported no whitespace issues.

## Notes for Next Task

Phase 4L: presolve solve/compare regression checklist.
