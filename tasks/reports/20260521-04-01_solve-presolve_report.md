# Solve Presolve Flag Report

## Summary

Added an explicit `--presolve` flag to `silo solve`. The default solve path remains unchanged. When requested, the CLI runs conservative presolve before solving, maps presolve-proved infeasible or unbounded cases directly to ordinary `Solution` JSON, and recovers original-space solutions after solving a reduced model.

## User-Facing Command

Supported commands:

```bash
silo solve examples/json/production.json --presolve
silo solve examples/json/production.json --solver tableau --presolve
silo solve examples/json/production.json --solver revised --presolve
```

The `--presolve` option is accepted by the shared parser but is used only by `solve`.

## Presolve Status Mapping

- `PresolveStatus.INFEASIBLE` maps to `SolverStatus.INFEASIBLE`, ordinary solution JSON, and exit code `1`.
- `PresolveStatus.UNBOUNDED` maps to `SolverStatus.UNBOUNDED`, ordinary solution JSON, and exit code `1`.
- `PresolveStatus.REDUCED` and `PresolveStatus.NO_CHANGE` continue to the selected LP backend and use the backend status to determine the solve exit code.

## Recovery Behavior

For reduced models, the selected solver runs on `presolve_result.model`. The returned solution is passed through `presolve_result.recover_solution()` so fixed variables are restored in original model space, fixed variables receive basis status `"fixed"`, and objective values are not double counted.

## Files Changed

- `src/silo/cli/main.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_cli_solve_presolve.py`
- `docs/cli_solve.md`
- `docs/presolve_cli.md`
- `README.md`
- `tasks/phases/phase_04_presolve_scaling.md`

## Tests Added

- Default solve behavior remains unchanged.
- Solve with `--presolve` on an unchanged model.
- Solve with `--solver revised --presolve`.
- Presolve-detected infeasible empty row maps to solution status `infeasible`.
- Presolve-detected unbounded empty column maps to solution status `unbounded`.
- Fixed-variable recovery through tableau.
- Fixed-variable recovery through revised simplex.
- Output-file solve with `--presolve`.
- CLI help text includes `--presolve`.

## Tests Run

- `pytest tests/unit/test_cli.py tests/unit/test_cli_solve.py tests/unit/test_cli_solve_presolve.py tests/unit/test_cli_presolve.py tests/unit/test_cli_compare.py -q`
- `ruff check src/silo/cli tests/unit/test_cli.py tests/unit/test_cli_solve_presolve.py tests/unit/test_cli_solve.py`
- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json --solver tableau`
- `python -m silo.cli.main solve examples/json/production.json --solver revised`
- `python -m silo.cli.main solve examples/json/production.json --presolve`
- `python -m silo.cli.main solve examples/json/production.json --solver revised --presolve`
- `python -m silo.cli.main presolve examples/json/production.json`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json --presolve`
- `silo presolve examples/json/production.json`
- `silo compare examples/json/production.json`

## Results

All checks passed. The full test suite contains 208 passing tests. CLI help, version, solve, solve-with-presolve, presolve, and compare smoke tests passed for both module and console entry points.

## Notes for Next Task

Phase 4H: presolve repeated-pass design for rows made empty by fixed-variable elimination.
