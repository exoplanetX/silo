# Codex Task 20260520-01-01: Expose Tableau Solution Details

## Task Metadata

Task file:

```text
tasks/codex/20260520-01-01_tableau-details.md
```

Execution report file:

```text
tasks/reports/20260520-01-01_tableau-details_report.md
```

Recommended local commit message:

```text
Expose tableau solution details
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO currently has a dense educational tableau simplex solver with Phase I / Phase II support.

The current tableau solver supports continuous maximization LPs with:

```text
maximize   c^T x + c0
subject to <=, >=, and = linear rows
           x >= 0
           no finite variable upper bounds
           no nonzero variable lower bounds
           continuous variables only
```

The current solver can:

- normalize negative RHS rows;
- add slack, surplus, and artificial variables;
- run Phase I;
- detect infeasible LPs;
- remove artificial columns;
- restore the original objective;
- run Phase II;
- return status, objective value, and primal values.

The next step is to expose more LP-solver-like solution information from the tableau result.

This task should add basic solution diagnostics:

```text
constraint slack values
reduced costs for original variables
basis status for original variables
```

This task should **not** add dual values yet. Leave `dual_values` empty for tableau solutions unless a very simple and fully tested convention already exists. Dual values should be a later task.

------

## 2. Goal

Enhance the tableau solver output so that an optimal solution contains:

1. primal values for original variables;
2. objective value;
3. constraint slack values for original model constraints;
4. reduced costs for original variables;
5. basis status for original variables.

The implementation should remain small, readable, and consistent with the current tableau sign convention.

------

## 3. Save This Task File

Create the following file:

```text
tasks/codex/20260520-01-01_tableau-details.md
```

Save this full task prompt into that file.

Do not edit, rename, delete, or move any existing files under:

```text
tasks/codex/
```

This task may only add the new task file above.

------

## 4. Allowed Files to Modify

You may modify:

```text
src/silo/core/solution.py
src/silo/io/solution_writer.py
src/silo/lp/simplex/tableau.py
tests/unit/test_tableau_simplex.py
tests/unit/test_solution_writer.py
```

You may add a new focused test file if it improves clarity:

```text
tests/unit/test_tableau_solution_details.py
```

You may create the execution report:

```text
tasks/reports/20260520-01-01_tableau-details_report.md
```

Do not modify unrelated modules.

------

## 5. Do Not Do

Do not implement dual values in this task.

Do not implement revised simplex.

Do not implement dual simplex.

Do not implement presolve.

Do not implement branch-and-bound or MIP.

Do not add cuts.

Do not add decomposition.

Do not add stochastic or robust optimization.

Do not add native backend code.

Do not support finite variable upper bounds.

Do not support nonzero variable lower bounds.

Do not support integer or binary variables.

Do not support minimization unless it is already supported elsewhere.

Do not add SciPy, HiGHS, GLPK, or any external solver call.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. Solution Dataclass Requirements

Update:

```text
src/silo/core/solution.py
```

Add fields for basic LP diagnostics:

```python
slack_values: dict[str, float] = field(default_factory=dict)
basis_status: dict[str, str] = field(default_factory=dict)
```

The resulting `Solution` dataclass should support at least:

```python
status
objective_value
primal_values
slack_values
dual_values
reduced_costs
basis_status
message
```

Keep field defaults backward-compatible.

Do not remove or rename existing fields.

Do not add complex custom classes to `Solution` in this task.

------

## 7. Slack Value Convention

Implement slack values for original model constraints.

For each original constraint, compute activity:

```text
activity_i = sum_j a_ij x_j
```

Then use the following public slack convention:

### `<=` row

```text
slack_i = rhs_i - activity_i
```

Example:

```text
x <= 5, x = 3  -> slack = 2
```

### `>=` row

```text
slack_i = activity_i - rhs_i
```

Example:

```text
x >= 2, x = 5 -> slack = 3
```

### `=` row

Use signed residual:

```text
slack_i = rhs_i - activity_i
```

For a feasible equality row, this should be zero within tolerance.

Use the original constraint sense and original RHS, not the normalized RHS.

Clean near-zero values to `0.0` using the existing tolerance convention.

------

## 8. Reduced Cost Convention

The current tableau is a maximization tableau.

The internal objective row convention is:

```text
objective_row[j] = - reduced_cost_j
```

for non-RHS columns after the objective row has been canonicalized.

Therefore public reduced costs for original variables should be:

```text
reduced_cost_j = - objective_row[j]
```

Only expose reduced costs for original decision variables, not slack, surplus, or artificial variables.

At an optimal maximization solution, nonbasic variables at their lower bound should have reduced costs less than or equal to zero under this convention.

Document this convention in code comments or tests.

------

## 9. Basis Status Convention

Expose basis status for original variables only.

Use:

```text
"basic"
"nonbasic"
```

The `basis_status` dictionary should map original variable names to one of these two strings.

Example:

```python
{
    "x": "basic",
    "y": "nonbasic",
}
```

Do not expose internal slack, surplus, or artificial variable basis status in public `Solution.basis_status` yet.

------

## 10. Tableau Implementation Requirements

Update:

```text
src/silo/lp/simplex/tableau.py
```

Add helper methods or functions as needed.

Suggested additions:

```python
def reduced_costs(self) -> dict[str, float]:
    ...

def basis_status(self) -> dict[str, str]:
    ...

def _constraint_slacks(model: Model, primal_values: dict[str, float]) -> dict[str, float]:
    ...
```

Alternative names are acceptable if clear.

When `TableauSimplexSolver.solve()` returns an optimal `Solution`, it should populate:

```python
Solution(
    status=SolverStatus.OPTIMAL,
    objective_value=...,
    primal_values=...,
    slack_values=...,
    reduced_costs=...,
    basis_status=...,
    dual_values={},
    message="Tableau simplex solved the LP.",
)
```

For non-optimal statuses such as `INFEASIBLE`, `UNBOUNDED`, `ITERATION_LIMIT`, or `ERROR`, it is acceptable to leave these diagnostic dictionaries empty.

------

## 11. Solution Writer Requirements

Update:

```text
src/silo/io/solution_writer.py
```

The JSON solution writer should include the new fields:

```json
{
  "status": "...",
  "objective_value": ...,
  "primal_values": {...},
  "slack_values": {...},
  "dual_values": {...},
  "reduced_costs": {...},
  "basis_status": {...},
  "message": "..."
}
```

Keep deterministic JSON formatting.

Update tests accordingly.

------

## 12. Required Tests

Add or update tests to cover the following.

### 12.1 Existing solver tests still pass

All current tests from the tableau MVP and Phase I tasks must continue to pass.

### 12.2 Slack values for `<=` rows

Example:

```text
maximize x
subject to x <= 5
           x >= 0
```

Expected optimum:

```text
x = 5
slack for row = 0
```

Also include a case where a `<=` row is nonbinding if easy.

Example:

```text
maximize x
subject to x <= 3
           x <= 5
```

Expected:

```text
x = 3
slack for first row = 0
slack for second row = 2
```

### 12.3 Slack values for `>=` rows

Example:

```text
maximize x
subject to x >= 2
           x <= 5
           x >= 0
```

Expected optimum:

```text
x = 5
slack for x >= 2 row = 3
slack for x <= 5 row = 0
```

### 12.4 Slack values for equality rows

Example:

```text
maximize x + y
subject to x + y = 4
           x <= 3
           y <= 3
           x, y >= 0
```

Expected:

```text
objective = 4
equality slack/residual = 0
```

Do not require a unique basis or unique primal split if the optimum is degenerate.

### 12.5 Reduced costs for original variables

Use a test where one original variable is nonbasic at zero with a negative reduced cost under the maximization convention.

Example:

```text
maximize x - y
subject to x <= 1
           y <= 1
           x, y >= 0
```

Expected optimum:

```text
x = 1
y = 0
objective = 1
reduced_costs["x"] = 0
reduced_costs["y"] = -1
basis_status["x"] = "basic"
basis_status["y"] = "nonbasic"
```

If the tableau basis makes `x` nonbasic due to a degenerate alternative, choose a different simple model where basis status is deterministic.

### 12.6 Basis status for original variables

Test that all original variables appear in `basis_status`.

For a simple one-variable LP:

```text
maximize 2x + 1
subject to x <= 4
```

Expected:

```text
basis_status["x"] == "basic"
```

For the reduced-cost test above:

```text
basis_status["y"] == "nonbasic"
```

### 12.7 Solution writer includes new fields

Update or add a test using `tmp_path` to ensure `write_solution_json()` writes:

```text
slack_values
basis_status
reduced_costs
```

and preserves deterministic formatting.

------

## 13. Numerical Tolerance

Use:

```text
silo.utils.numerics.DEFAULT_TOLERANCE
```

Use `_clean_zero()` or equivalent to avoid returning values such as:

```text
-0.0
1e-15
```

for slacks, reduced costs, and primal values.

Do not introduce a separate tolerance constant.

------

## 14. Execution Report

Create:

```text
tasks/reports/20260520-01-01_tableau-details_report.md
```

The report should include:

```markdown
# Tableau Solution Details Report

## Summary

## Public Solution Fields Added

## Reduced-Cost Convention

## Files Changed

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend the next step. Likely candidates:

```text
Phase 2D: add CLI solve support for JSON LP fixtures using tableau simplex.
```

or:

```text
Phase 3 preparation: draft revised simplex design notes.
```

Choose based on what seems most appropriate after implementation.

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
```

If the console script is available, also run:

```bash
silo --help
silo --version
```

Fix any failures.

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
git commit -m "Expose tableau solution details"
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

1. `tasks/codex/20260520-01-01_tableau-details.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `tasks/reports/20260520-01-01_tableau-details_report.md` exists.
4. `Solution` supports `slack_values` and `basis_status` fields.
5. Optimal tableau solutions populate primal values, slack values, reduced costs, and basis status.
6. Public reduced costs use the documented maximization convention `reduced_cost = -objective_row[column]`.
7. Slack values are computed from original constraints, not normalized rows.
8. Equality-row slack/residual is tested.
9. `write_solution_json()` includes the new fields.
10. Existing Phase I / Phase II tableau behavior remains unchanged.
11. No dual values are implemented in this task.
12. No revised simplex, presolve, MIP, cuts, decomposition, stochastic/robust, native backend, or external solver call is added.
13. `pytest` passes.
14. `python scripts/check_quality.py` passes.
15. CLI help/version commands work.
16. A local commit is created with message:

```text
Expose tableau solution details
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
