# Revised Diagnostics Alignment Report

## Summary

Aligned revised simplex and tableau public diagnostics on small deterministic LPs. Added parity tests for optimal, infeasible, and unbounded cases, normalized tableau nonbasic basis status to `nonbasic_lower`, and documented the shared public reduced-cost convention.

## Diagnostics Checked

The parity tests compare solver status, objective value, primal values, slack values, reduced costs, basis statuses, and empty dual values where meaningful. Degenerate equality examples validate feasibility and objective value without requiring the same optimal `x, y` split.

## Reduced-Cost Convention

Public reduced costs now use `c_j - pi^T A_j` for original variables in maximization LPs. Basic variables should report approximately zero reduced cost, and nonbasic lower-bound variables should report nonpositive reduced costs at optimum.

## Dual-Value Design Note

Created `notes/11_dual_values_design.md`. The note explains why `dual_values` remains empty, identifies `pi^T = c_B^T B^{-1}` as the candidate equality-form multiplier, and records row-normalization and original-row mapping issues for a future dual-value task.

## Files Changed

- `src/silo/lp/simplex/tableau.py`
- `tests/unit/test_tableau_solution_details.py`
- `tests/unit/test_revised_tableau_parity.py`
- `docs/cli_solve.md`
- `docs/lp_solver.md`
- `notes/11_dual_values_design.md`
- `tasks/phases/phase_03_revised_simplex.md`
- `tasks/codex/20260520-08-01_diag-dual-note.md`
- `tasks/reports/20260520-08-01_diag-dual-note_report.md`

## Tests Added

Added `tests/unit/test_revised_tableau_parity.py` with cases for:

- standard production LP;
- single-variable LP with objective constant;
- `>=` row Phase I LP;
- degenerate equality-row LP;
- infeasible LP;
- unbounded LP;
- reduced-cost sign parity for a nonbasic lower-bound variable.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json`

## Results

All checks passed. The full test suite reported `104 passed`.

## Notes for Next Task

Phase 3E should add a revised simplex backend option to the CLI for controlled comparison against the tableau backend.
