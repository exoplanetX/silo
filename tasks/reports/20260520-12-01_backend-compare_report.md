# Backend Comparison Command Report

## Summary

Added a developer-facing `silo compare MODEL_PATH` command that solves a JSON LP with both native backends and reports deterministic comparison JSON. The command is intended for regression and debugging, not for expanding solver mathematics.

## User-Facing Command

```bash
silo compare examples/json/production.json
silo compare examples/json/production.json --output outputs/production_compare.json
python -m silo.cli.main compare examples/json/production.json
```

## Comparison Semantics

The comparison is consistent when statuses match, optimal objective values match within `DEFAULT_TOLERANCE`, and both backends keep `dual_values` empty. Primal values, slack values, reduced costs, and basis statuses are still reported for diagnostics, but primal equality is not required for consistency because degenerate LPs can have multiple optimal solutions.

## Files Changed

- `src/silo/cli/compare.py`
- `src/silo/cli/main.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_cli_compare.py`
- `docs/backend_compare.md`
- `docs/cli_solve.md`
- `README.md`
- `tasks/codex/20260520-12-01_backend-compare.md`
- `tasks/reports/20260520-12-01_backend-compare_report.md`

## Tests Added

Added focused CLI compare tests for:

- production example consistency;
- `>=` row example consistency;
- equality-row example consistency without requiring primal equality;
- infeasible example consistency;
- output-file writing;
- missing model path error handling;
- solution payload schema consistency;
- mismatch-key diff behavior.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json --solver tableau`
- `python -m silo.cli.main solve examples/json/production.json --solver revised`
- `python -m silo.cli.main compare examples/json/production.json`
- `python -m silo.cli.main compare examples/json/ge_row.json`
- `python -m silo.cli.main compare examples/json/equality_row.json`
- `python -m silo.cli.main compare examples/json/infeasible.json`
- `silo --help`
- `silo --version`
- `silo compare examples/json/production.json`

## Results

All checks passed. The full test suite reported `142 passed`.

## Notes for Next Task

Phase 4A should start the presolve and scaling design note, since backend parity and comparison tooling are now in place.
