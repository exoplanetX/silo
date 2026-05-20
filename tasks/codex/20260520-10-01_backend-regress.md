# Codex Task 20260520-10-01: Add Backend Regression Tests

## Task Metadata

Task file:

```text
tasks/codex/20260520-10-01_backend-regress.md
```

Execution report file:

```text
tasks/reports/20260520-10-01_backend-regress_report.md
```

Recommended local commit message:

```text
Add backend regression tests
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO now has two native LP solver backends:

```text
tableau
revised
```

The CLI supports selecting the backend:

```bash
silo solve MODEL_PATH --solver tableau
silo solve MODEL_PATH --solver revised
```

The current user-facing JSON examples are under:

```text
examples/json/
```

Previous tasks added examples such as:

```text
examples/json/production.json
examples/json/ge_row.json
examples/json/equality_row.json
examples/json/infeasible.json
```

Before moving toward warm starts, reoptimization, presolve, or MIP, SILO should have regression tests that compare tableau and revised simplex on all public JSON examples.

This task should add regression coverage only. It should not expand solver algorithms.

------

## 2. Goal

Add backend regression tests that verify tableau and revised simplex remain aligned on user-facing JSON examples.

The tests should protect:

1. solver status consistency;
2. objective-value consistency where optimal;
3. primal and slack consistency where solutions are unique or deterministic;
4. feasibility and objective consistency where optima are degenerate;
5. reduced-cost sign consistency on selected deterministic examples;
6. CLI backend behavior for both `--solver tableau` and `--solver revised`;
7. solution JSON schema consistency.

This task is meant to make future changes safer.

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260520-10-01_backend-regress.md
```

Save this full task prompt into that file.

Do not edit, rename, delete, or move any existing files under:

```text
tasks/codex/
```

This task may only add the new task file above.

------

## 4. Allowed Files to Modify or Add

You may add:

```text
tests/regression/test_json_backend_regression.py
tasks/reports/20260520-10-01_backend-regress_report.md
```

You may add one additional small user-facing example if useful:

```text
examples/json/unbounded.json
```

If you add `examples/json/unbounded.json`, you may update:

```text
docs/json_model_format.md
docs/cli_solve.md
README.md
```

only with a short mention of the new example.

You may modify existing CLI tests only if needed to avoid duplication or integrate the new regression tests:

```text
tests/unit/test_cli_solve.py
```

You may modify solver code only if the new regression tests reveal a clear bug in public diagnostics. If this happens, keep the fix minimal and explain it in the report.

------

## 5. Do Not Do

Do not add new solver algorithms.

Do not change tableau solver mathematical behavior.

Do not change revised simplex mathematical behavior unless a regression test exposes a clear public-output bug.

Do not implement warm starts.

Do not implement reoptimization.

Do not implement presolve.

Do not implement MIP.

Do not add cuts, decomposition, stochastic programming, robust optimization, or native backend code.

Do not implement dual values.

Do not add external solver calls.

Do not add runtime dependencies.

Do not change the JSON model schema.

Do not change the solution JSON schema.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not commit generated files under `outputs/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. Regression Test Location

Create:

```text
tests/regression/test_json_backend_regression.py
```

If `tests/regression/` does not exist, create it.

The tests should be deterministic and readable.

Use direct solver calls for most tests:

```python
from silo.io.json_reader import read_json_model
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.lp.simplex.revised import RevisedSimplexSolver
```

Use CLI invocation only for CLI-specific backend tests.

------

## 7. Example Coverage

Regression tests should cover all JSON files in:

```text
examples/json/
```

At minimum, cover:

```text
production.json
ge_row.json
equality_row.json
infeasible.json
```

If you add an unbounded example, also cover:

```text
unbounded.json
```

Suggested unbounded example:

```text
maximize x + y
subject to y <= 1
           x, y >= 0
```

Expected status:

```text
unbounded
```

Keep the example small and readable.

------

## 8. Expected Outcome Map

Create a small expected-outcome map in the test file.

Example structure:

```python
EXAMPLE_EXPECTATIONS = {
    "production.json": {
        "status": SolverStatus.OPTIMAL,
        "objective_value": 21.0,
        "unique_primal": {"x1": 2.0, "x2": 3.0},
    },
    "ge_row.json": {
        "status": SolverStatus.OPTIMAL,
        "objective_value": 5.0,
        "unique_primal": {"x": 5.0},
    },
    "equality_row.json": {
        "status": SolverStatus.OPTIMAL,
        "objective_value": 4.0,
        "degenerate": True,
    },
    "infeasible.json": {
        "status": SolverStatus.INFEASIBLE,
    },
}
```

You may adjust names and structure.

If the test scans all files in `examples/json/`, assert that every file has an expectation entry. This prevents undocumented examples from silently escaping regression coverage.

------

## 9. Direct Backend Parity Requirements

For each example:

1. read model with `read_json_model()`;
2. solve with `TableauSimplexSolver`;
3. solve with `RevisedSimplexSolver`;
4. compare outputs according to the expectation.

### 9.1 Status

For every example:

```text
tableau_solution.status == expected_status
revised_solution.status == expected_status
tableau_solution.status == revised_solution.status
```

### 9.2 Objective value

For optimal examples:

```text
tableau objective == expected objective
revised objective == expected objective
tableau objective == revised objective
```

Use `pytest.approx`.

### 9.3 Unique primal solutions

For examples with unique primal solutions, compare:

```text
tableau primal values
revised primal values
expected primal values
```

Use tolerance.

### 9.4 Degenerate optimal examples

For degenerate examples such as the equality-row model:

Do not require tableau and revised simplex to return the same `x, y` split.

Instead verify for each solver:

```text
status = optimal
objective_value matches expected
original constraints are feasible through slack values
equality residual is zero within tolerance
```

### 9.5 Slack values

For nondegenerate examples, compare slack values between tableau and revised.

For degenerate examples, only check feasibility and expected binding rows.

### 9.6 Reduced costs

For examples where reduced costs are deterministic and already covered by existing tests, it is acceptable to assert parity.

At minimum, include or reuse a deterministic reduced-cost parity case such as:

```text
maximize x - y
subject to x <= 1
           y <= 1
           x, y >= 0
```

This model does not need to be a user-facing JSON example if it already exists in unit tests. But this regression file should include one reduced-cost sign parity assertion if not already fully covered.

### 9.7 Dual values

Both solvers should still report:

```python
dual_values == {}
```

Do not implement dual values.

------

## 10. CLI Backend Regression Requirements

Add tests that invoke the CLI backend option.

Preferred approach:

```python
from silo.cli.main import main
```

using injected argv, if available.

Alternatively use subprocess if existing CLI tests already do that.

Required CLI cases:

### 10.1 Production with tableau

```bash
silo solve examples/json/production.json --solver tableau
```

Expected:

```text
exit code = 0
status = optimal
objective_value = 21
```

### 10.2 Production with revised

```bash
silo solve examples/json/production.json --solver revised
```

Expected:

```text
exit code = 0
status = optimal
objective_value = 21
```

### 10.3 Infeasible with both backends

```bash
silo solve examples/json/infeasible.json --solver tableau
silo solve examples/json/infeasible.json --solver revised
```

Expected:

```text
exit code = 1
status = infeasible
```

### 10.4 Optional unbounded with both backends

If `examples/json/unbounded.json` is added:

```bash
silo solve examples/json/unbounded.json --solver tableau
silo solve examples/json/unbounded.json --solver revised
```

Expected:

```text
exit code = 1
status = unbounded
```

------

## 11. Solution JSON Schema Consistency

Add a regression check that both CLI backends return JSON with the same top-level fields:

```text
status
objective_value
primal_values
slack_values
dual_values
reduced_costs
basis_status
message
```

Do not require identical `message` text between backends.

------

## 12. Helper Functions

Use small test helpers if useful.

Suggested helpers:

```python
def solve_with_both_backends(path: Path) -> tuple[Solution, Solution]:
    ...

def assert_solution_status(solution: Solution, status: SolverStatus) -> None:
    ...

def assert_close_mapping(actual: dict[str, float], expected: dict[str, float]) -> None:
    ...

def assert_json_solution_fields(payload: dict[str, object]) -> None:
    ...
```

Keep helpers local to the regression test file unless broadly useful.

------

## 13. Documentation Update

If adding:

```text
examples/json/unbounded.json
```

then update documentation briefly.

Suggested note in `docs/cli_solve.md` or `docs/json_model_format.md`:

```text
examples/json/unbounded.json demonstrates an unbounded LP and returns status "unbounded".
```

Do not expand documentation too much.

------

## 14. Execution Report

Create:

```text
tasks/reports/20260520-10-01_backend-regress_report.md
```

The report should include:

```markdown
# Backend Regression Tests Report

## Summary

## Examples Covered

## Backend Comparisons

## Files Changed

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend one next step.

Likely candidates:

```text
Phase 3G: implement warm-start/reoptimization interface for revised simplex.
```

or:

```text
Phase 3G: add a small benchmark/regression command for comparing native backends.
```

Choose based on what seems most natural after completing this task.

Do not record execution results by editing the issued task file.

------

## 15. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json --solver tableau
python -m silo.cli.main solve examples/json/production.json --solver revised
python -m silo.cli.main solve examples/json/infeasible.json --solver tableau
python -m silo.cli.main solve examples/json/infeasible.json --solver revised
```

If `examples/json/unbounded.json` is added, also run:

```bash
python -m silo.cli.main solve examples/json/unbounded.json --solver tableau
python -m silo.cli.main solve examples/json/unbounded.json --solver revised
```

The unbounded and infeasible commands are expected to return nonzero exit codes. Do not treat the nonzero code itself as failure if the solution JSON status is correct.

If the console script is available, also run:

```bash
silo --help
silo --version
silo solve examples/json/production.json --solver tableau
silo solve examples/json/production.json --solver revised
```

Fix any unexpected failures.

------

## 16. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Add backend regression tests"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 17. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260520-10-01_backend-regress.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `tests/regression/test_json_backend_regression.py` exists or equivalent regression coverage is added.
4. All JSON examples under `examples/json/` have explicit expectations.
5. Tableau and revised backends are compared on `production.json`.
6. Tableau and revised backends are compared on `ge_row.json`.
7. Tableau and revised backends are compared on `equality_row.json`.
8. Tableau and revised backends are compared on `infeasible.json`.
9. If `unbounded.json` is added, both backends are compared on it.
10. CLI backend tests cover tableau and revised on at least production and infeasible examples.
11. Solution JSON schema consistency is tested for both backends.
12. Dual values remain empty.
13. No solver algorithm scope is expanded.
14. No external solver dependency or call is introduced.
15. `tasks/reports/20260520-10-01_backend-regress_report.md` exists.
16. `pytest` passes.
17. `python scripts/check_quality.py` passes.
18. CLI help/version/solve commands work.
19. A local commit is created with message:

```text
Add backend regression tests
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
