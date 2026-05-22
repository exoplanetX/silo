# MIP CLI Regression Matrix Report

Task ID: 20260523-03-01

Objective: Add a focused subprocess regression matrix for the public `silo mip-solve` CLI behavior without changing solver source code, CLI semantics, or JSON schemas.

Files changed:

- `tests/regression/test_mip_cli_regression_matrix.py`
- `docs/mip_solve_cli.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260523-03-01_mip-cli-regression_report.md`

Regression cases added:

- `python -m silo.cli.main mip-solve` and `silo mip-solve` for `binary_knapsack.json`, expecting `optimal` with objective `22`.
- `python -m silo.cli.main mip-solve` and `silo mip-solve` for `integer_allocation.json`, expecting `optimal` with objective `7`.
- `python -m silo.cli.main mip-solve` and `silo mip-solve` for `mixed_binary_integer.json`, expecting `optimal` with objective `11`.
- `python -m silo.cli.main mip-solve` and `silo mip-solve` for `mixed_continuous_integer.json`, expecting `optimal` with objective `11`.
- `python -m silo.cli.main mip-solve` and `silo mip-solve` for `infeasible_binary.json`, expecting status `infeasible`, objective `null`, and exit code `1`.
- `--lp-solver revised` coverage for `binary_knapsack.json` through both module and console-script entrypoints.
- `solve examples/mip/binary_knapsack.json` coverage confirming that the LP `solve` command does not silently dispatch to MIP.
- LP `solve` and `compare` coverage for `examples/json/production.json`, confirming unchanged existing LP behavior.

Checks run:

- `python -m pip install -e ".[dev]"`
- `pytest tests/regression/test_mip_cli_regression_matrix.py`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json`
- `python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json --lp-solver revised`
- `silo mip-solve examples/mip/binary_knapsack.json`
- `silo mip-solve examples/mip/binary_knapsack.json --lp-solver revised`

Results:

- Editable install completed successfully.
- The new regression matrix passed with 18 tests.
- Full `pytest` passed with 431 tests.
- `python scripts/check_quality.py` passed.
- All four required explicit MIP CLI commands returned `optimal` with objective `22`.
- No solver source code, CLI implementation, model schema, or solution schema was changed.

Git status before:

```text
## main...origin/main [ahead 1]
```

Git status after:

```text
Pending final local commit and push attempt at report-writing time.
```

Local commit hash:

```text
Pending final commit creation; the final response records the created hash.
```

Push attempted:

```text
Pending final push attempt because the user explicitly requested push if possible.
```

Issues or conflicts:

- The repository already had one local commit ahead of `origin/main` before this task began: `aa29d29 docs(tasks): smoke test SILO development operator`.
- The first targeted regression run exposed a local multi-Python environment mismatch: `pytest` used a Python environment without the editable install while the shell `python` install used another environment. The subprocess regression helper now explicitly prepends the repository `src` path to `PYTHONPATH`, so module invocation tests the current source tree without changing CLI behavior.

Next recommended atomic task:

Create a Phase 5J task to decide and document whether MIP solve output should expose node-count or detailed branch-and-bound diagnostics, without implementing cuts, heuristics, callbacks, or external solver calls.
