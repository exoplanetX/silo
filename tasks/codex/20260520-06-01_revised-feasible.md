# Codex Task 20260520-06-01: Add Revised Simplex Feasible-Basis Solver

## Task Metadata

Task file:

```text
tasks/codex/20260520-06-01_revised-feasible.md
```

Execution report file:

```text
tasks/reports/20260520-06-01_revised-feasible_report.md
```

Recommended local commit message:

```text
Add revised simplex feasible-basis solver
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO now has:

1. a dense tableau simplex solver with Phase I / Phase II;
2. JSON input and CLI solve workflow;
3. solution diagnostics from tableau;
4. a revised simplex design note;
5. a standard-form builder;
6. a `Basis` dataclass.

The current standard-form builder is in:

```text
src/silo/lp/simplex/standard_form.py
```

It provides:

```text
StandardFormProblem
StandardColumn
build_standard_form(model)
```

The current basis abstraction is in:

```text
src/silo/lp/simplex/basis.py
```

It provides:

```text
Basis
BASIC
NONBASIC_LOWER
```

This task implements only the first revised simplex solving path:

```text
Phase 3B: primal revised simplex for already feasible slack-basis LPs
```

Do not implement revised Phase I yet.

------

## 2. Goal

Add a small readable primal revised simplex solver that works only when the standard-form problem already has a feasible slack basis.

The solver should support the following model class:

```text
maximize   c^T x + c0
subject to A x <= b
           b >= 0
           x >= 0
           variables continuous
           no finite upper bounds
           no nonzero lower bounds
```

This class produces a standard-form problem with:

```text
no artificial columns
initial slack basis
feasible initial basic solution
```

The solver should:

1. build standard form;
2. reject standard-form problems with artificial columns;
3. use the initial basis from `StandardFormProblem`;
4. compute basic primal values via dense linear algebra;
5. compute reduced costs for nonbasic variables;
6. choose deterministic entering columns;
7. perform the ratio test;
8. pivot using the `Basis` dataclass;
9. detect optimality;
10. detect unboundedness;
11. return a `Solution` with primal values, slack values, reduced costs, basis status, objective value, and message.

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260520-06-01_revised-feasible.md
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
src/silo/lp/simplex/revised.py
tests/unit/test_revised_simplex.py
tasks/reports/20260520-06-01_revised-feasible_report.md
```

You may update:

```text
src/silo/lp/simplex/__init__.py
docs/lp_solver.md
tasks/phases/phase_03_revised_simplex.md
```

only if useful.

You may add small helper functions to:

```text
src/silo/lp/simplex/standard_form.py
src/silo/lp/simplex/basis.py
```

only if they are general and tested.

Do not modify tableau simplex behavior.

Do not modify CLI solve behavior in this task.

------

## 5. Do Not Do

Do not implement revised simplex Phase I.

Do not support standard-form problems with artificial columns.

Do not support `>=` or `=` rows in the revised solver yet.

Do not support negative RHS rows requiring artificial variables.

Do not support minimization.

Do not support finite variable upper bounds.

Do not support nonzero variable lower bounds.

Do not support integer or binary variables.

Do not implement dual simplex.

Do not implement presolve.

Do not implement MIP.

Do not add cuts, decomposition, stochastic programming, robust optimization, or native backend code.

Do not add external solver calls.

Do not add new runtime dependencies beyond existing `numpy`.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. Revised Solver Interface

Create:

```text
src/silo/lp/simplex/revised.py
```

Implement a solver class:

```python
class RevisedSimplexSolver(LPSolver):
    def __init__(self, iteration_limit: int = 10_000) -> None:
        ...

    def solve(self, model: Model) -> Solution:
        ...
```

The class should follow the same public solver pattern as `TableauSimplexSolver`.

For this task, if `build_standard_form(model)` yields any artificial columns, return:

```python
Solution(
    status=SolverStatus.ERROR,
    message="Revised simplex feasible-basis solver does not support artificial columns yet."
)
```

or similarly clear wording.

Do not silently fall back to tableau simplex.

------

## 7. Dense Linear Algebra Requirements

Use existing `numpy` dependency.

For a standard-form problem:

```text
maximize c^T x + c0
subject to A x = b
           x >= 0
```

At each iteration:

```text
B = A[:, basic_columns]
N = A[:, nonbasic_columns]
x_B = solve(B, b)
pi = solve(B.T, c_B)
reduced_cost_j = c_j - pi^T A_j
```

Use dense arrays for this first implementation.

Handle linear algebra failures cleanly:

```python
Solution(status=SolverStatus.NUMERICAL_ISSUE, message="...")
```

Do not implement factorization updates.

Do not cache inverse matrices.

Do not use explicit matrix inverse unless only for debugging. Prefer `numpy.linalg.solve`.

------

## 8. Maximization Reduced-Cost Convention

For the revised simplex implementation, use mathematical maximization reduced costs:

```text
reduced_cost_j = c_j - pi^T A_j
```

For maximization with nonbasic variables at lower bound zero, optimality is:

```text
reduced_cost_j <= tolerance for all nonbasic j
```

Choose the first nonbasic column with:

```text
reduced_cost_j > tolerance
```

as the entering column.

Public `Solution.reduced_costs` for original variables should follow the same sign convention as the current tableau public output if possible.

Add tests that compare revised reduced costs against tableau reduced costs on small `<=` LPs.

If a sign mismatch is found, do not hide it. Add a short comment explaining the convention and align the public output with existing tableau solution conventions.

------

## 9. Ratio Test

For an entering column `j`, compute direction:

```text
d = B^{-1} A_j
```

For primal feasibility with `x_B >= 0`, only rows with:

```text
d_i > tolerance
```

restrict the step.

Ratio:

```text
theta_i = x_B_i / d_i
```

Choose the leaving row by minimum ratio. Break ties by row order.

If no `d_i > tolerance`, return:

```text
UNBOUNDED
```

with a clear message.

------

## 10. Basis Updates

Use the existing `Basis.pivot()` method.

At pivot:

```text
new_basis = basis.pivot(leaving_row, entering_column)
```

Do not mutate `Basis` in place.

After pivot, validate the basis if helpful:

```python
basis.validate(column_count=..., row_count=...)
```

------

## 11. Solution Construction

On optimal termination, return a `Solution` with:

```text
status = OPTIMAL
objective_value
primal_values
slack_values
dual_values = {}
reduced_costs
basis_status
message
```

### 11.1 Primal values

Expose original variables only.

Use `StandardFormProblem.columns` and `original_variable_count`.

### 11.2 Slack values

Compute slacks from the original model constraints, not from transformed rows.

Use the same convention as tableau:

```text
<= : rhs - activity
>= : activity - rhs
=  : rhs - activity
```

Since this task only solves `<=` rows, tests should still use this helper in a way that will work later.

### 11.3 Reduced costs

Expose reduced costs for original variables only.

Basic original variables should have reduced cost approximately zero.

Nonbasic original variables should show their mathematical reduced cost under the public convention.

### 11.4 Basis status

Expose basis status for original variables only.

Use:

```text
basic
nonbasic_lower
```

The status strings should match constants in `basis.py`.

### 11.5 Objective value

Compute:

```text
objective = c^T x + objective_constant
```

Clean near-zero values using existing tolerance.

------

## 12. Iteration Limit

If the iteration limit is reached, return:

```text
ITERATION_LIMIT
```

with a clear message.

Add a stable test for `iteration_limit=0`.

------

## 13. Unsupported Cases

For this first revised solver, unsupported cases should return `ERROR` rather than raising uncaught exceptions from `solve()`.

Unsupported cases include:

```text
>= rows producing artificial columns
= rows producing artificial columns
negative RHS rows that produce artificial columns
minimization
finite upper bounds
nonzero lower bounds
integer/binary variables
```

For invalid model construction caught before standard form, catch `ValueError` and return:

```python
Solution(status=SolverStatus.ERROR, message=str(exc))
```

------

## 14. Tests Required

Add:

```text
tests/unit/test_revised_simplex.py
```

### 14.1 Single-variable LP

Model:

```text
maximize 2x + 1
subject to x <= 4
           x >= 0
```

Expected:

```text
status = OPTIMAL
x = 4
objective = 9
basis_status["x"] = "basic"
```

### 14.2 Production LP

Use the same production LP as tableau:

```text
maximize 3x1 + 5x2
subject to x1 + 2x2 <= 8
           3x1 + 2x2 <= 12
           x1, x2 >= 0
```

Expected:

```text
status = OPTIMAL
x1 = 2
x2 = 3
objective = 21
```

### 14.3 Compare against tableau

For at least two `<=` LPs, compare:

```text
status
objective_value
primal_values
slack_values
basis_status for original variables where deterministic
```

between `RevisedSimplexSolver` and `TableauSimplexSolver`.

Do not require exact matching of internal structural variables.

### 14.4 Reduced-cost example

Use a case such as:

```text
maximize x - y
subject to x <= 1
           y <= 1
           x, y >= 0
```

Expected:

```text
x = 1
y = 0
objective = 1
reduced_costs["x"] approximately 0
reduced_costs["y"] approximately -1
basis_status["x"] == "basic"
basis_status["y"] == "nonbasic_lower"
```

If this example yields deterministic basis issues, choose a similarly simple deterministic example.

### 14.5 Unbounded LP

Example:

```text
maximize x + y
subject to y <= 1
           x, y >= 0
```

Expected:

```text
UNBOUNDED
```

### 14.6 Unsupported artificial-column case

Example:

```text
maximize x
subject to x >= 2
           x <= 5
```

Expected:

```text
ERROR
message mentions artificial columns or feasible-basis limitation
```

### 14.7 Unsupported equality case

Example:

```text
maximize x
subject to x = 1
```

Expected:

```text
ERROR
```

### 14.8 Iteration limit

For `iteration_limit=0`, expected:

```text
ITERATION_LIMIT
```

on a model that would otherwise require solving.

### 14.9 Numerical issue path

If easy and stable, test singular basis handling through a lower-level helper. Do not overcomplicate this.

------

## 15. Documentation Update

If updating:

```text
docs/lp_solver.md
```

add a short section:

```markdown
## Revised Simplex Feasible-Basis Path

SILO now includes an initial primal revised simplex implementation for small LPs that already have a feasible slack basis. This path is intentionally narrower than the tableau solver: it currently supports only continuous maximization LPs with nonnegative variables and `<=` rows that produce no artificial variables. Phase I support for the revised simplex layer is planned later.
```

Do not imply revised simplex has full Phase I support.

------

## 16. Execution Report

Create:

```text
tasks/reports/20260520-06-01_revised-feasible_report.md
```

The report should include:

```markdown
# Revised Simplex Feasible-Basis Report

## Summary

## Mathematical Scope

## Files Changed

## Solver Behavior

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend:

```text
Phase 3C: add revised-simplex Phase I basis construction for artificial-column cases.
```

or, if implementation reveals another priority:

```text
Phase 3C: refactor standard-form solution reconstruction helpers.
```

Do not record execution results by editing the issued task file.

------

## 17. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json
```

If the console script is available, also run:

```bash
silo --help
silo --version
silo solve examples/json/production.json
```

Fix any failures.

------

## 18. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Add revised simplex feasible-basis solver"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 19. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260520-06-01_revised-feasible.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `src/silo/lp/simplex/revised.py` exists.
4. `RevisedSimplexSolver` exists and implements `solve(model)`.
5. The solver handles already feasible slack-basis `<=` LPs.
6. The solver returns `OPTIMAL` for the single-variable LP.
7. The solver returns `OPTIMAL` for the production LP.
8. The solver returns `UNBOUNDED` for a simple unbounded LP.
9. The solver returns `ERROR` for artificial-column cases such as `>=` or `=` rows.
10. The solver returns `ITERATION_LIMIT` when iteration limit is zero.
11. Optimal revised solutions include objective value, primal values, slack values, reduced costs, and basis status.
12. Revised simplex results are compared against tableau on small `<=` LPs.
13. No revised Phase I implementation is added.
14. No tableau solver behavior is changed.
15. No CLI solve behavior is changed.
16. No external solver dependency or call is introduced.
17. `tasks/reports/20260520-06-01_revised-feasible_report.md` exists.
18. `pytest` passes.
19. `python scripts/check_quality.py` passes.
20. CLI help/version/solve commands work.
21. A local commit is created with message:

```text
Add revised simplex feasible-basis solver
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
