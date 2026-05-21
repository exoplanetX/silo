# Phase 4 Regression Checklist Report

## Summary

Added a Phase 4 regression checklist and CLI matrix tests that lock the current public behavior for all checked-in JSON examples across solve, presolve, and compare commands. No solver, presolve, CLI semantics, JSON schema, or solution schema behavior was changed.

## Examples Covered

- `production.json`
- `ge_row.json`
- `equality_row.json`
- `infeasible.json`
- `fixed_var_recovery.json`
- `repeated_empty_row.json`
- `presolve_infeasible_after_fixed.json`

## Command Matrix Covered

- `silo solve MODEL_PATH`
- `silo solve MODEL_PATH --solver tableau`
- `silo solve MODEL_PATH --solver revised`
- `silo solve MODEL_PATH --presolve`
- `silo solve MODEL_PATH --solver tableau --presolve`
- `silo solve MODEL_PATH --solver revised --presolve`
- `silo presolve MODEL_PATH`
- `silo compare MODEL_PATH`

## Files Changed

- `docs/phase4_regression_checklist.md`
- `tests/regression/test_phase4_cli_regression_matrix.py`
- `README.md`
- `docs/cli_solve.md`
- `docs/presolve_cli.md`
- `docs/backend_compare.md`
- `tasks/phases/phase_04_presolve_scaling.md`
- `tasks/codex/20260521-09-01_phase4-regress.md`
- `tasks/reports/20260521-09-01_phase4-regress_report.md`

## Tests Added

- Scan all `examples/json/*.json` files and require explicit Phase 4 expectations.
- Verify every expectation references an existing example.
- Matrix-test default solve, tableau solve, revised solve, and all three presolve solve variants.
- Matrix-test `silo presolve` statuses.
- Matrix-test `silo compare` consistency and backend statuses.
- Smoke-check standard solution, presolve, and compare JSON fields.

## Tests Run

```text
pytest tests/regression/test_phase4_cli_regression_matrix.py
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json
python -m silo.cli.main solve examples/json/production.json --presolve
python -m silo.cli.main presolve examples/json/production.json
python -m silo.cli.main compare examples/json/production.json
silo --help
silo --version
silo solve examples/json/production.json
silo solve examples/json/production.json --presolve
silo presolve examples/json/production.json
silo compare examples/json/production.json
git diff --check
```

## Results

The Phase 4 matrix test passed with 64 cases. Editable dev install completed successfully. Full `pytest` passed with 298 tests. `python scripts/check_quality.py` passed. Module and console CLI smoke commands completed successfully. `git diff --check` reported no whitespace issues.

## Notes for Next Task

Phase 4M: final Phase 4 cleanup and documentation pass before starting Phase 5 branch-and-bound design.
