# Codex Task: Add MIP CLI Regression Matrix

## Task Metadata

Task ID: 20260523-03-01
Task slug: mip-cli-regression
Task type: regression-test
Related phase: Phase 5 / MIP branch-and-bound CLI
Git mode: local-commit
Expected report path: tasks/reports/20260523-03-01_mip-cli-regression_report.md

## Objective

Add a focused regression matrix for the `silo mip-solve` CLI command.

The goal is to lock down user-facing MIP CLI behavior across Python module invocation and installed console-script invocation without changing solver algorithms, JSON schemas, or existing LP command semantics.

## Context

SILO now exposes supported MIP solving through:

```bash
silo mip-solve MODEL_PATH
python -m silo.cli.main mip-solve MODEL_PATH
```

Existing unit tests cover the direct `main(argv)` path. The next useful Phase 5 task is a regression matrix that exercises command-line subprocess behavior for checked-in MIP examples and verifies that `silo solve` remains the LP-only command path.

Relevant existing files include:

- `src/silo/cli/main.py`
- `src/silo/cli/mip_solve.py`
- `tests/unit/test_cli_mip_solve.py`
- `tests/regression/test_phase4_cli_regression_matrix.py`
- `examples/mip/`
- `docs/mip_solve_cli.md`
- `tasks/phases/phase_05_branch_and_bound.md`

## Scope Lock

This task is atomic.

Primary objective:

- Add regression coverage for the public `mip-solve` command-line behavior.

Allowed changes:

- `tests/regression/test_mip_cli_regression_matrix.py`
- `docs/mip_solve_cli.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260523-03-01_mip-cli-regression_report.md`

Forbidden changes:

- Do not modify solver source code.
- Do not modify `BranchAndBoundSolver`.
- Do not modify LP backends.
- Do not modify presolve.
- Do not modify JSON model schema.
- Do not modify solution JSON schema.
- Do not add new CLI commands.
- Do not change `silo solve` semantics.
- Do not add cuts, heuristics, callbacks, branch-and-cut, or external solver calls.
- Do not modify existing files under `tasks/codex/`.
- Do not modify existing files under `tasks/phases/` except the allowed Phase 5 note above.
- Do not push to GitHub unless explicitly instructed by the user.

## Stop Conditions

Stop and report instead of proceeding if:

- adding the regression matrix requires changing solver behavior;
- the current `mip-solve` CLI output is inconsistent with documented solution JSON schema;
- subprocess-based console-script invocation is unavailable after editable install;
- unrelated repository changes are present before starting and make the regression scope ambiguous.

## Required Checks

Run at least:

```bash
python -m pip install -e ".[dev]"
pytest tests/regression/test_mip_cli_regression_matrix.py
pytest
python scripts/check_quality.py
python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json
python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json --lp-solver revised
silo mip-solve examples/mip/binary_knapsack.json
silo mip-solve examples/mip/binary_knapsack.json --lp-solver revised
git diff --check
```

The infeasible MIP example should be tested by the regression suite and should return solution status `infeasible` with exit code `1`.

## Acceptance Criteria

This task is complete only if:

1. A MIP CLI regression test file exists under `tests/regression/`.
2. The regression matrix covers module invocation with `python -m silo.cli.main`.
3. The regression matrix covers console-script invocation with `silo`.
4. Binary knapsack returns `optimal` with objective `22`.
5. Integer allocation returns `optimal` with objective `7`.
6. Mixed binary/integer returns `optimal` with objective `11`.
7. Mixed continuous/integer returns `optimal` with objective `11`.
8. Infeasible binary returns status `infeasible` and exit code `1`.
9. `--lp-solver revised` is covered for at least one MIP example.
10. `silo solve examples/mip/binary_knapsack.json` does not silently dispatch to MIP.
11. Existing LP solve and compare behavior remains unchanged.
12. No solver source code is modified.
13. No JSON model or solution schema is changed.
14. `pytest` passes.
15. `python scripts/check_quality.py` passes.
16. A report is created at the expected report path.

## Report Requirements

Create:

```text
tasks/reports/20260523-03-01_mip-cli-regression_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Regression cases added:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

## Git Instructions

Default Git mode for this task is:

```text
local-commit
```

After completing the implementation and checks:

```bash
git add tests/regression/test_mip_cli_regression_matrix.py docs/mip_solve_cli.md tasks/phases/phase_05_branch_and_bound.md tasks/reports/20260523-03-01_mip-cli-regression_report.md
git commit -m "test(cli): add MIP CLI regression matrix"
```

Do not push unless the user explicitly requests it.

## Final Response

When finished, report only:

- whether the regression matrix was added;
- whether documentation or phase notes were updated;
- whether checks passed;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.
