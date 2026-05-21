# Phase 4 Regression Checklist

## Purpose

This checklist records the public Phase 4 CLI behavior before the project moves toward Phase 5 MIP work. It covers all checked-in JSON examples and the current solve, presolve, and backend-compare commands.

## Example Coverage

Every file under `examples/json/` must have an explicit entry in `tests/regression/test_phase4_cli_regression_matrix.py`.

Covered examples:

- `production.json`
- `ge_row.json`
- `equality_row.json`
- `infeasible.json`
- `fixed_var_recovery.json`
- `repeated_empty_row.json`
- `presolve_infeasible_after_fixed.json`

## Command Matrix

Each solve cell is `exit/status`. `presolve` is the `silo presolve` exit/status. `compare` is the `silo compare` exit/consistency and backend statuses.

| Example | solve | tableau | revised | solve --presolve | tableau --presolve | revised --presolve | presolve | compare |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `production.json` | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/no_change | 0/consistent optimal-optimal |
| `ge_row.json` | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/no_change | 0/consistent optimal-optimal |
| `equality_row.json` | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/optimal | 0/no_change | 0/consistent optimal-optimal |
| `infeasible.json` | 1/infeasible | 1/infeasible | 1/infeasible | 1/infeasible | 1/infeasible | 1/infeasible | 0/no_change | 0/consistent infeasible-infeasible |
| `fixed_var_recovery.json` | 1/error | 1/error | 1/error | 0/optimal | 0/optimal | 0/optimal | 0/reduced | 0/consistent error-error |
| `repeated_empty_row.json` | 1/error | 1/error | 1/error | 0/optimal | 0/optimal | 0/optimal | 0/reduced | 0/consistent error-error |
| `presolve_infeasible_after_fixed.json` | 1/error | 1/error | 1/error | 1/infeasible | 1/infeasible | 1/infeasible | 0/infeasible | 0/consistent error-error |

## Expected Statuses

General LP examples solve optimally with both native backends and remain `no_change` under the current conservative presolve layer.

`infeasible.json` is infeasible for both solver backends. Current presolve does not detect this general infeasibility, so `silo presolve` reports `no_change`; `silo solve --presolve` still returns infeasible after the selected backend solves the unchanged model.

## Notes on Presolve-Only Examples

The fixed-bound examples intentionally return `error` without `--presolve` because the native simplex backends do not directly support fixed nonzero bounds. With `--presolve`, fixed-variable elimination produces a supported presolved model or detects an infeasible empty row.

`repeated_empty_row.json` also verifies that repeated-pass presolve removes the row exposed by fixed-variable elimination and that recovered solution JSON contains original-space slacks.

## Notes on Compare

`silo compare` does not run presolve. For general LP examples, it compares optimal backend solutions. For presolve-only fixed-bound examples, it verifies that both raw backends consistently reject the unsupported fixed-bound model with `error`.

## How to Run the Regression Tests

```bash
pytest tests/regression/test_phase4_cli_regression_matrix.py
```

For the broader Phase 4 regression sweep, run:

```bash
pytest
python scripts/check_quality.py
```
