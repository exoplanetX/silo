# Presolve Diagnostics CLI Report

## Summary

Added a developer-facing `silo presolve MODEL_PATH` command that reads a JSON model, runs `Presolver().run(model)`, and emits deterministic presolve and scaling diagnostics JSON. The command is diagnostic-only and does not change `silo solve` or `silo compare` behavior.

## User-Facing Command

The command supports stdout output:

```bash
silo presolve examples/json/production.json
```

and file output:

```bash
silo presolve examples/json/production.json --output outputs/production_presolve.json
```

The Python module entry point also works:

```bash
python -m silo.cli.main presolve examples/json/production.json
```

## JSON Output Schema

The payload includes top-level `model_path`, `presolve`, `reductions`, and `scaling` fields. Presolve warnings and scaling warnings are serialized separately. Reduction records include `type`, `target`, `description`, and deterministic `data`.

## Exit-Code Convention

The command returns `0` when diagnostics are produced, including presolve statuses such as `infeasible` and `unbounded`. It returns `1` for model read/write failures and uses argparse's `2` for usage errors.

## Files Changed

- `src/silo/cli/main.py`
- `src/silo/cli/presolve.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_cli_presolve.py`
- `docs/presolve_cli.md`
- `docs/cli_solve.md`
- `docs/lp_solver.md`
- `README.md`

## Tests Added

- Presolve command stdout JSON.
- Presolve command output file.
- Infeasible empty-row diagnostics returning exit code `0`.
- Empty-column unbounded diagnostics returning exit code `0`.
- Fixed-variable reduction serialization.
- Scaling warnings that do not change presolve status.
- Missing model path returning exit code `1`.
- Parser support and help text for `presolve`.
- Parser rejection of unknown commands.

## Tests Run

- `pytest tests/unit/test_cli.py tests/unit/test_cli_presolve.py tests/unit/test_cli_solve.py tests/unit/test_cli_compare.py -q`
- `ruff check src/silo/cli tests/unit/test_cli.py tests/unit/test_cli_presolve.py`
- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main presolve examples/json/production.json`
- `python -m silo.cli.main solve examples/json/production.json --solver tableau`
- `python -m silo.cli.main solve examples/json/production.json --solver revised`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo presolve examples/json/production.json`
- `silo compare examples/json/production.json`

## Results

All checks passed. The full test suite contains 200 passing tests. CLI help, version, presolve, solve, and compare smoke tests passed for both module and console entry points.

## Notes for Next Task

Phase 4G: optional presolve integration path for solve commands behind an explicit flag.
