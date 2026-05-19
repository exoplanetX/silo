# Tableau Solution Details Report

## Summary

Extended tableau simplex optimal solutions with basic LP diagnostics while leaving dual values empty. Optimal tableau solves now return primal values, original-constraint slack values, original-variable reduced costs, and original-variable basis status.

## Public Solution Fields Added

- `slack_values: dict[str, float]`
- `basis_status: dict[str, str]`

## Reduced-Cost Convention

The tableau is a maximization tableau whose canonical objective row stores `objective_row[j] = -reduced_cost_j`. Public reduced costs for original decision variables are therefore reported as `-objective_row[j]`. Slack, surplus, and artificial variables are not exposed in public reduced costs.

## Files Changed

- `src/silo/core/solution.py`
- `src/silo/io/solution_writer.py`
- `src/silo/lp/simplex/tableau.py`
- `tests/unit/test_solution_writer.py`
- `tests/unit/test_tableau_solution_details.py`
- `tasks/codex/20260520-01-01_tableau-details.md`
- `tasks/reports/20260520-01-01_tableau-details_report.md`

## Tests Added

- Slack values for binding and nonbinding `<=` rows.
- Slack values for original `>=` rows after Phase I normalization.
- Equality-row residual slack.
- Reduced costs and basis status for original variables.
- JSON solution writer output for `slack_values` and `basis_status`.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `silo --help`
- `silo --version`

## Results

- `pytest`: 49 passed
- `python scripts/check_quality.py`: 49 passed and ruff all checks passed
- CLI help/version commands: passed

## Notes for Next Task

Phase 2D should add CLI solve support for JSON LP fixtures using the tableau simplex solver, so these solution diagnostics can be inspected from command-line runs.
