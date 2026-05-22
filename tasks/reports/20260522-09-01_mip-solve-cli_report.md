# MIP Solve CLI Report

## Summary

Added the first public MIP CLI command, `silo mip-solve MODEL_PATH`, backed by the existing native `BranchAndBoundSolver`. The implementation preserves existing LP `silo solve` behavior and keeps LP backend selection separate from MIP solving.

No solver algorithm, JSON model schema, solution JSON schema, presolve behavior, or external solver dependency was changed.

## User-Facing Command

```bash
silo mip-solve examples/mip/binary_knapsack.json
```

The command is also available through module invocation:

```bash
python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json
```

## Flags Added

- `--lp-solver tableau|revised`
- `--node-limit N`
- `--output` / `-o`

`--lp-solver` selects the LP relaxation backend used internally by branch-and-bound. The existing `--solver` flag remains reserved for `silo solve`.

## Exit-Code Behavior

- `0`: MIP solution status is `optimal`.
- `1`: MIP solution status is non-optimal, or a read/write error occurs.
- `2`: argparse usage error, including invalid `--lp-solver` or invalid `--node-limit`.

The infeasible MIP example returns status `infeasible` and exit code `1`.

## Files Changed

- `src/silo/cli/main.py`
- `src/silo/cli/mip_solve.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_cli_mip_solve.py`
- `docs/mip_solve_cli.md`
- `docs/mip_examples.md`
- `docs/cli_solve.md`
- `README.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/codex/20260522-09-01_mip-solve-cli.md`
- `tasks/reports/20260522-09-01_mip-solve-cli_report.md`

## Tests Added

- Default `mip-solve` binary knapsack solve.
- Integer allocation solve.
- Mixed binary/integer solve.
- Mixed continuous/integer solve.
- Infeasible binary solve with nonzero exit code.
- Revised LP relaxation backend selection.
- Node-limit handling.
- Output-file writing.
- Missing-path handling.
- Invalid LP solver rejection.
- Negative node-limit rejection.
- Rejection of `--solver` for `mip-solve`.
- Regression check that `silo solve` still solves LP examples.
- Regression check that `silo solve examples/mip/binary_knapsack.json` does not silently dispatch to MIP.

## Tests Run

- `pytest tests/unit/test_cli_mip_solve.py`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json`
- `python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json --lp-solver revised`
- `python -m silo.cli.main mip-solve examples/mip/infeasible_binary.json`
- `python -m silo.cli.main solve examples/json/production.json`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo mip-solve examples/mip/binary_knapsack.json`
- `silo mip-solve examples/mip/binary_knapsack.json --lp-solver revised`
- `silo solve examples/json/production.json`
- `silo compare examples/json/production.json`
- `git diff --check`

## Results

All required checks passed.

## Notes for Next Task

Phase 5I: MIP CLI regression matrix.
