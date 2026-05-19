# Codex Task 20260519-04-02: Review Tableau MVP

## Task Metadata

Task file:

```text
tasks/codex/20260519-04-02_tableau-cleanup.md
~~~

Execution report file:

```text
tasks/reports/20260519-04-02_tableau-cleanup_report.md
```

Recommended local commit message:

```text
Review tableau simplex MVP
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

This task should create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO has completed the following recent stages:

- Phase 0 scaffold.
- Task-directory rules under `tasks/README.md`.
- Phase 1 model core and canonicalization.
- Phase 2A tableau simplex MVP.

The current tableau simplex MVP has introduced a first working native LP solver for small dense LPs. The MVP is intentionally limited to the following standard form:

```text
maximize   c^T x + c0
subject to A x <= b
           x >= 0
           b >= 0
           x continuous
```

The current implementation is expected to support:

- slack-variable tableau construction;
- deterministic entering-column rule;
- deterministic leaving-row ratio test;
- pivot operation;
- optimal status;
- unbounded status;
- unsupported-model rejection;
- primal values for original variables;
- objective value including objective constant.

This cleanup task is **not** meant to add new mathematical scope. It is a review, tightening, and test-strengthening task for the current MVP.

------

## 2. Goal

Review and clean up the tableau simplex MVP so that it is mathematically clear, deterministic, well-tested, and ready for the next Phase 2B task.

The expected outcome is:

1. the existing tableau MVP remains limited and readable;
2. pivot logic is clear and not error-prone;
3. objective constant handling is explicitly tested;
4. unbounded and unsupported cases are tested;
5. tolerance behavior is documented through tests where appropriate;
6. task execution is reported under `tasks/reports/`;
7. existing issued task files under `tasks/codex/` are not modified.

------

## 3. Save This Task File

Create the following file if it does not already exist:

```text
tasks/codex/20260519-04-02_tableau-cleanup.md
```

Save this full task prompt into that file.

Do not edit, rename, delete, or move any existing files under:

```text
tasks/codex/
```

This task may only add the new task file above.

------

## 4. Allowed Files to Modify

You may modify only the following implementation and test files unless there is a clear reason:

```text
src/silo/lp/simplex/tableau.py
src/silo/lp/simplex/pricing.py
src/silo/lp/simplex/ratio_test.py
tests/unit/test_tableau_simplex.py
```

You may also create or update the execution report:

```text
tasks/reports/20260519-04-02_tableau-cleanup_report.md
```

You may update minor documentation comments in the same files if needed.

Do not modify unrelated modules.

------

## 5. Do Not Do

Do not implement Phase I.

Do not support `>=` constraints.

Do not support equality constraints.

Do not support minimization models.

Do not support finite upper bounds.

Do not support nonzero lower bounds.

Do not support integer or binary variables.

Do not implement revised simplex.

Do not implement presolve.

Do not implement MIP.

Do not add SciPy, HiGHS, GLPK, or any external solver call.

Do not change the Apache-2.0 `LICENSE`.

Do not change package metadata unless required by tests.

Do not modify existing files under `tasks/codex/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. Mathematical Scope to Preserve

The current MVP should continue to accept only this class:

```text
maximize   c^T x + c0
subject to A x <= b
           x >= 0
           b >= 0
           x continuous
```

The solver should reject unsupported models with `SolverStatus.ERROR` and a clear message.

For this cleanup task, keep `SolverStatus.ERROR` for unsupported models. Do not introduce a new status enum such as `UNSUPPORTED_MODEL` in this task.

------

## 7. Code Review Requirements

Review these functions and classes carefully:

```text
SimplexTableau.from_model
SimplexTableau.pivot
SimplexTableau.primal_values
SimplexTableau.objective_value
TableauSimplexSolver.solve
choose_entering_column
choose_leaving_row
_validate_supported_standard_form
```

### 7.1 Pivot Operation

Inspect the pivot logic for readability and correctness.

The current pivot operation should:

1. divide the pivot row by the pivot element;
2. eliminate the entering-column coefficient from all other constraint rows;
3. eliminate the entering-column coefficient from the objective row;
4. update the basis for the pivot row.

Make the code clearer if there are confusing variable names or shadowing. For example, avoid list-comprehension variable names that shadow important variables such as `pivot_value`.

Do not change the algorithmic behavior unless a bug is found.

### 7.2 Objective Value

Verify that the objective value includes the objective constant.

For the initial objective:

```text
maximize c^T x + c0
```

the returned optimal objective should be:

```text
c^T x* + c0
```

Add or keep tests that explicitly verify nonzero objective constants.

### 7.3 Entering Column Rule

Keep the entering-column rule deterministic.

For this MVP, it is acceptable to choose the first negative coefficient in the objective row under tolerance.

Do not switch to steepest-edge pricing, largest coefficient, Bland's full rule, or any advanced rule.

### 7.4 Leaving Row Rule

Keep the leaving-row rule deterministic.

The leaving row should be selected by the minimum nonnegative ratio among rows with positive pivot coefficient. Ties should be resolved deterministically by row order.

Add or keep a test that verifies tie behavior if it is simple and useful.

### 7.5 Tolerance

Use the existing numerical tolerance convention from:

```text
silo.utils.numerics.DEFAULT_TOLERANCE
```

Do not introduce multiple competing tolerance constants.

If a tolerance-related behavior is clarified, add a small test.

### 7.6 Unsupported Models

Make sure unsupported inputs return:

```python
Solution(status=SolverStatus.ERROR, message="...")
```

The message should be clear enough for a user to understand why the model is unsupported.

At minimum, unsupported tests should cover:

- minimization;
- non-`<=` constraints;
- finite upper bounds;
- nonzero lower bounds;
- integer or binary variables;
- negative RHS.

------

## 8. Test Requirements

Update or extend:

```text
tests/unit/test_tableau_simplex.py
```

The test file should remain readable and deterministic.

At minimum, tests should cover:

### 8.1 Tableau Construction

Test that a simple model is converted into a tableau with:

- original variable names;
- slack variable names;
- correct initial basis;
- correct constraint rows;
- correct objective row;
- correct RHS.

### 8.2 Single-Variable LP

Example:

```text
maximize 2x + 1
subject to x <= 4
           x >= 0
```

Expected solution:

```text
x = 4
objective = 9
status = OPTIMAL
```

### 8.3 Two-Variable Production LP

Keep or improve the production LP test.

Example:

```text
maximize 3x1 + 5x2
subject to x1 + 2x2 <= 8
           3x1 + 2x2 <= 12
           x1, x2 >= 0
```

Expected solution:

```text
x1 = 2
x2 = 3
objective = 21
status = OPTIMAL
```

### 8.4 Objective Constant

Add a specific test where objective constant is nonzero and the optimum is not zero.

The test should fail if the constant is dropped.

### 8.5 Unbounded LP

Example structure:

```text
maximize x + y
subject to y <= 1
           x, y >= 0
```

Expected status:

```text
UNBOUNDED
```

### 8.6 Unsupported Input Tests

Add or keep tests for:

```text
minimization model -> ERROR
>= row -> ERROR
= row -> ERROR
finite variable upper bound -> ERROR
nonzero variable lower bound -> ERROR
integer variable -> ERROR
binary variable -> ERROR
negative RHS -> ERROR
```

### 8.7 Iteration Limit

Add a small test for `iteration_limit=0` if it is meaningful and stable.

Expected behavior:

```text
ITERATION_LIMIT
```

Do not create artificial cycling examples in this task.

------

## 9. Expected Implementation Style

Keep code simple and educational.

Use explicit names such as:

```text
pivot_element
normalized_pivot_row
row_multiplier
objective_multiplier
```

rather than ambiguous names.

Prefer small helper functions only when they improve readability.

Do not over-abstract the tableau MVP.

Do not introduce plugin systems or callback systems in this task.

------

## 10. Execution Report

After completing the code and tests, create:

```text
tasks/reports/20260519-04-02_tableau-cleanup_report.md
```

The report should include:

```markdown
# Tableau MVP Cleanup Report

## Summary

## Files Changed

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", briefly state what should be done in the next task, likely:

```text
Phase 2B: add Phase I support for >=, =, and infeasible LP detection.
```

Do not modify the issued task file under `tasks/codex/` to record execution results.

------

## 11. Local Checks

Run the following commands:

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

## 12. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Review tableau simplex MVP"
```

Do not push unless the user explicitly asks you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 13. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260519-04-02_tableau-cleanup.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `tasks/reports/20260519-04-02_tableau-cleanup_report.md` exists.
4. Tableau pivot logic is reviewed and made clearer if needed.
5. Objective constant handling is explicitly tested.
6. Production LP and single-variable LP tests pass.
7. Unbounded LP detection is tested.
8. Unsupported input tests cover minimization, `>=`, `=`, finite upper bounds, nonzero lower bounds, integer/binary variables, and negative RHS.
9. No Phase I implementation is added.
10. No minimization, `>=`, equality, finite-upper-bound, nonzero-lower-bound, integer, or binary support is added.
11. No external solver dependency or call is introduced.
12. `pytest` passes.
13. `python scripts/check_quality.py` passes.
14. CLI help/version commands work.
15. A local commit is created with message:

```text
Review tableau simplex MVP
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
