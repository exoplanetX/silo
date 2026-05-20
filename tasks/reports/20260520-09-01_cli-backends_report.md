# CLI Solver Backend Report

## Summary

Added explicit CLI solver-backend selection. Users can now run the default tableau backend or select the revised simplex backend through `--solver`.

## User-Facing Commands Added

```bash
silo solve examples/json/production.json --solver tableau
silo solve examples/json/production.json --solver revised
python -m silo.cli.main solve examples/json/production.json --solver revised
```

Output-file writing also works with the revised backend:

```bash
silo solve examples/json/production.json --solver revised --output outputs/production_revised_solution.json
```

## Default Solver

The default solver remains `tableau`. Existing `silo solve MODEL_PATH` behavior is preserved.

## Files Changed

- `src/silo/cli/main.py`
- `src/silo/cli/solvers.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_cli_solve.py`
- `docs/cli_solve.md`
- `docs/lp_solver.md`
- `README.md`
- `tasks/codex/20260520-09-01_cli-backends.md`
- `tasks/reports/20260520-09-01_cli-backends_report.md`

## Tests Added

Added CLI tests for:

- default solver remaining `tableau`;
- explicit `--solver tableau`;
- explicit `--solver revised`;
- revised backend on production, `>=` Phase I, equality Phase I, and infeasible examples;
- output-file writing with `--solver revised`;
- invalid solver names rejected by argparse;
- unsupported binary model returning solver-level `error` through the revised backend.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json`
- `python -m silo.cli.main solve examples/json/production.json --solver tableau`
- `python -m silo.cli.main solve examples/json/production.json --solver revised`
- `python -m silo.cli.main solve examples/json/ge_row.json --solver revised`
- `python -m silo.cli.main solve examples/json/equality_row.json --solver revised`
- `python -m silo.cli.main solve examples/json/infeasible.json --solver revised`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json --solver tableau`
- `silo solve examples/json/production.json --solver revised`

## Results

All checks passed. The full test suite reported `114 passed`. The revised infeasible CLI command returned exit code `1` with solution JSON status `infeasible`, as expected.

## Notes for Next Task

Phase 3F should add revised-vs-tableau regression tests for all JSON examples before introducing a warm-start/reoptimization interface.
