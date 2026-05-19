# Revised Simplex Design Note Report

## Summary

Created a revised simplex design note for Phase 3 before implementation begins. The note fixes the intended mathematical form, basis representation, iteration convention, solution diagnostics, reoptimization interface, module layout, testing strategy, staged implementation sequence, and first-task exclusions.

## Files Changed

- `notes/10_revised_simplex_design.md`
- `docs/lp_solver.md`
- `tasks/phases/phase_03_revised_simplex.md`
- `tasks/codex/20260520-04-01_revised-note.md`
- `tasks/reports/20260520-04-01_revised-note_report.md`

## Main Design Decisions

- Keep tableau simplex as the small-instance reference implementation and test oracle.
- Target equality standard form first: `maximize c^T x + c0`, `A x = b`, `x >= 0`.
- Introduce a future `Basis` abstraction with deterministic basic and nonbasic column ordering.
- Use mathematical reduced costs directly in revised simplex and test their relation to tableau output conventions.
- Leave dual values empty until row multiplier sign and normalization conventions are tested.
- Stage implementation through standard-form building, feasible-basis revised simplex, Phase I, diagnostics parity, and warm-start support.

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

- `pytest`: 61 passed
- `python scripts/check_quality.py`: 61 passed and ruff all checks passed
- CLI help/version/solve commands: passed

## Notes for Next Task

Phase 3A: implement standard-form builder and `Basis` dataclass.
