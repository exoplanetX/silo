# Codex Task 20260520-11-01: Add Revised Simplex Warm Start Interface

## Task Metadata

Task file:

```text
tasks/codex/20260520-11-01_revised-warmstart.md
```

Execution report file:

```text
tasks/reports/20260520-11-01_revised-warmstart_report.md
```

Recommended local commit message:

```text
Add revised simplex warm-start interface
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO currently has:

1. a tableau simplex backend;
2. a revised simplex backend;
3. Phase I / Phase II support in both backends;
4. CLI backend selection through `--solver tableau` and `--solver revised`;
5. regression tests comparing tableau and revised backends on JSON examples.

The revised simplex solver now has enough structure to begin supporting warm starts and reoptimization. This is important for future layers:

```text
branch-and-bound node reoptimization
Benders master reoptimization
column generation master reoptimization
small RHS or objective changes
```

This task should introduce a **conservative warm-start interface** for the revised simplex solver.

It should not implement MIP, dual simplex, presolve, or advanced basis repair.

------

## 2. Goal

Add a warm-start / reoptimization interface to `RevisedSimplexSolver`.

After this task, revised simplex should be able to:

1. solve a model normally;
2. return the final standard-form problem and final basis through a detailed result object;
3. accept a valid basis as an optional warm start for supported no-artificial-column models;
4. reuse a basis for a closely related model with the same standard-form column structure;
5. reject invalid or unsupported warm-start bases clearly;
6. preserve the existing `solve(model) -> Solution` public interface.

The key idea is:

```python
solution = RevisedSimplexSolver().solve(model)
details = RevisedSimplexSolver().solve_with_details(model)
warm_details = RevisedSimplexSolver().solve_with_details(model2, basis=details.basis)
```

Exact method names may vary if a clearer design is chosen, but `solve(model)` must remain backward-compatible.

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260520-11-01_revised-warmstart.md
```

Save this full task prompt into that file.

Do not edit, rename, delete, or move any existing files under:

```text
tasks/codex/
```

This task may only add the new task file above.

------

## 4. Allowed Files to Modify or Add

You may modify:

```text
src/silo/lp/simplex/revised.py
src/silo/lp/simplex/basis.py
tests/unit/test_revised_simplex.py
docs/lp_solver.md
tasks/phases/phase_03_revised_simplex.md
```

You may add:

```text
tests/unit/test_revised_warm_start.py
tasks/reports/20260520-11-01_revised-warmstart_report.md
```

You may modify `standard_form.py` only if a small helper is needed for validating standard-form compatibility.

Do not modify tableau simplex behavior.

Do not modify CLI solve behavior.

------

## 5. Do Not Do

Do not implement dual simplex.

Do not implement MIP.

Do not implement branch-and-bound.

Do not implement presolve.

Do not implement cuts.

Do not implement decomposition.

Do not implement stochastic or robust optimization.

Do not add native backend code.

Do not add external solver calls.

Do not add new runtime dependencies.

Do not support minimization.

Do not support finite variable upper bounds.

Do not support nonzero variable lower bounds.

Do not support integer or binary variables.

Do not add public dual values.

Do not change the CLI backend interface in this task.

Do not change the JSON model format.

Do not change the solution JSON schema.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. Scope of Warm Start Support

This first warm-start task should be conservative.

### 6.1 Supported warm-start scope

Support warm-start basis reuse for models whose standard-form problem has:

```text
no artificial columns
same transformed column count
same transformed row count
valid basis dimensions
primal feasible basic solution under the supplied basis
```

This means warm-start support is primarily for already feasible slack-basis LPs such as:

```text
maximize c^T x + c0
subject to A x <= b
           b >= 0
           x >= 0
```

and small modifications where the basis remains valid.

### 6.2 Unsupported warm-start scope

Do not require warm-start support for models that need artificial variables:

```text
>= rows
= rows
negative RHS rows requiring artificial variables
```

For these models, `solve(model)` should continue to work using revised Phase I, but a user-supplied warm-start basis may be rejected for now.

If the solver receives a user-supplied basis for an artificial-column model, return a clear `ERROR` solution in the detailed result, for example:

```text
Warm-start basis is not supported for models requiring artificial variables yet.
```

This keeps the first warm-start interface simple and safe.

------

## 7. Detailed Result Dataclass

Add a small detailed result dataclass in:

```text
src/silo/lp/simplex/revised.py
```

Suggested name:

```python
@dataclass(frozen=True)
class RevisedSimplexResult:
    solution: Solution
    problem: StandardFormProblem | None = None
    basis: Basis | None = None
    iterations: int = 0
    used_warm_start: bool = False
```

You may include additional small fields if useful, such as:

```python
phase: str | None = None
```

but keep the dataclass simple.

### Requirements

1. `solution` is always present.
2. `problem` should be present when standard-form construction succeeded.
3. `basis` should be the final basis when solving reaches `OPTIMAL`.
4. `basis` may be present for some non-optimal statuses if meaningful, but it is acceptable to leave it `None`.
5. `iterations` should count pivot iterations in the relevant solve path.
6. `used_warm_start` should be `True` only when a user-supplied basis was accepted.

------

## 8. Public Solver Methods

Keep the existing method:

```python
def solve(self, model: Model) -> Solution:
    ...
```

It should continue to return only `Solution`.

Add a detailed method:

```python
def solve_with_details(
    self,
    model: Model,
    basis: Basis | None = None,
) -> RevisedSimplexResult:
    ...
```

or a similarly named method.

`solve()` should call `solve_with_details(model).solution` internally.

Do not break existing tests that call `solve()`.

------

## 9. Warm-Start Validation

When a user supplies a `Basis`, validate it against the standard-form problem:

```python
basis.validate(column_count=len(problem.columns), row_count=len(problem.row_names))
```

Then check primal feasibility:

```text
B x_B = b
x_B >= -tolerance
```

If the basis is structurally invalid, return:

```text
SolverStatus.ERROR
```

with a clear message.

If the basis is structurally valid but primal infeasible, return:

```text
SolverStatus.ERROR
```

with a clear message such as:

```text
Warm-start basis is not primal feasible.
```

Do not silently repair an invalid or infeasible warm-start basis.

Do not run Phase I to repair a user-supplied invalid basis in this task.

------

## 10. Standard-Form Compatibility

A supplied basis uses standard-form column indices.

For this first implementation, assume the caller is responsible for passing a basis compatible with the current model's standard-form transformation.

However, add defensive validation:

1. column count matches;
2. row count matches;
3. basis covers all columns;
4. basis has one basic column per row.

Optional but useful:

If `RevisedSimplexResult.problem` from one solve is reused with a modified model, the tests should ensure that the transformed column layout is unchanged.

Do not implement a complex basis mapping layer in this task.

------

## 11. Revised Iteration Refactor

The revised simplex code may already have an internal run helper.

Refactor as needed so that both cold start and warm start use the same iteration code.

Preferred structure:

```python
def _solve_standard_form(
    problem: StandardFormProblem,
    initial_basis: Basis,
    iteration_limit: int,
    phase_name: str,
) -> InternalRunResult:
    ...
```

This helper should return:

```text
status
basis
state
iterations
message
```

The final public `RevisedSimplexResult` should use these values.

Do not duplicate the revised simplex loop.

------

## 12. Iteration Counting

For this task, count pivot operations.

If the supplied warm-start basis is already optimal, `iterations` should be:

```text
0
```

Add a test for this.

If the solver starts from the default slack basis and pivots twice, `iterations` should be 2.

Do not require exact iteration counts for degenerate Phase I examples.

------

## 13. Solution Behavior

The returned `Solution` should remain unchanged in schema and meaning.

On optimal solve, it should still include:

```text
objective_value
primal_values
slack_values
dual_values = {}
reduced_costs
basis_status
message
```

Do not add final basis to `Solution`.

Basis belongs to `RevisedSimplexResult`, not public solution JSON.

------

## 14. Tests Required

Add:

```text
tests/unit/test_revised_warm_start.py
```

### 14.1 `solve()` remains backward-compatible

Test that:

```python
solution = RevisedSimplexSolver().solve(model)
```

still returns a `Solution` and solves production LP.

### 14.2 `solve_with_details()` returns final basis

For a simple LP:

```text
maximize 2x + 1
subject to x <= 4
```

Expected:

```text
solution.status = OPTIMAL
basis is not None
problem is not None
basis validates against problem
```

### 14.3 Warm start with final optimal basis

Solve a simple model once:

```python
details = solver.solve_with_details(model)
```

Then solve the same model again with:

```python
warm_details = solver.solve_with_details(model, basis=details.basis)
```

Expected:

```text
status = OPTIMAL
used_warm_start = True
iterations = 0
objective matches
primal values match
```

### 14.4 Reoptimization after RHS change

Use a one-variable LP.

First model:

```text
maximize 2x
subject to x <= 4
```

Solve and get final basis.

Second model with same structure but changed RHS:

```text
maximize 2x
subject to x <= 5
```

Solve second model with the first model's final basis.

Expected:

```text
status = OPTIMAL
used_warm_start = True
x = 5
objective = 10
```

This demonstrates basic RHS reoptimization when the basis remains feasible and optimal.

### 14.5 Warm start with invalid basis

Create an invalid basis, for example wrong row count or missing columns.

Expected:

```text
solution.status = ERROR
message mentions invalid basis or warm-start basis
```

### 14.6 Warm start with infeasible basis

Create a structurally valid basis that produces negative basic values if practical.

If this is hard to create without unsupported model features, skip this specific test and explain in the report.

Do not overcomplicate the implementation just to force this test.

### 14.7 Warm start rejected for artificial-column model

Use a model requiring artificial columns:

```text
maximize x
subject to x >= 2
     and x <= 5
```

Call:

```python
solver.solve_with_details(model, basis=some_basis)
```

Expected:

```text
solution.status = ERROR
message mentions warm-start not supported for artificial-variable models
```

Normal `solver.solve(model)` should still solve this model.

### 14.8 Iteration count for cold solve

For a model that needs at least one pivot, verify that cold solve returns:

```text
iterations > 0
```

Do not require exact count unless deterministic and simple.

------

## 15. Existing Tests Must Still Pass

Existing tests for:

```text
tableau simplex
revised simplex
backend regression
CLI solve
JSON examples
solution writer
standard form
basis
```

must continue to pass.

Do not alter expected behavior of existing tests unless they expose a genuine bug.

------

## 16. Documentation Update

Update:

```text
docs/lp_solver.md
```

Add a concise section:

```markdown
## Revised Simplex Warm Starts

`RevisedSimplexSolver.solve_with_details()` returns a detailed result containing the final standard-form problem and basis. A compatible basis can be supplied to `solve_with_details()` to warm start another solve. This is currently a conservative interface intended for small LPs with the same standard-form structure; artificial-variable warm starts and basis mapping across model transformations remain future work.
```

Do not overstate reoptimization support.

Do not claim MIP node reoptimization is implemented.

------

## 17. Execution Report

Create:

```text
tasks/reports/20260520-11-01_revised-warmstart_report.md
```

The report should include:

```markdown
# Revised Simplex Warm Start Report

## Summary

## Interface Added

## Supported Warm-Start Scope

## Unsupported Warm-Start Cases

## Files Changed

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend one next step.

Likely candidates:

```text
Phase 3H: add a small backend comparison command or developer utility.
```

or:

```text
Phase 4A: start presolve/scaling design note.
```

Choose based on what seems most natural after completing this task.

Do not record execution results by editing the issued task file.

------

## 18. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json --solver tableau
python -m silo.cli.main solve examples/json/production.json --solver revised
```

If the console script is available, also run:

```bash
silo --help
silo --version
silo solve examples/json/production.json --solver tableau
silo solve examples/json/production.json --solver revised
```

Fix any failures.

------

## 19. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Add revised simplex warm-start interface"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 20. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260520-11-01_revised-warmstart.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. A detailed revised-simplex result dataclass exists.
4. `RevisedSimplexSolver.solve(model)` remains backward-compatible and returns `Solution`.
5. `RevisedSimplexSolver.solve_with_details(model, basis=None)` or equivalent exists.
6. The detailed result exposes final `problem`, final `basis`, `solution`, `iterations`, and `used_warm_start`.
7. Supplying a final optimal basis for the same model results in an optimal warm-start solve with zero pivots.
8. A simple RHS-change reoptimization test passes.
9. Invalid warm-start basis returns `ERROR`.
10. Warm-start basis for artificial-column models is rejected clearly, while normal solve still works.
11. Existing revised Phase I behavior is preserved.
12. Existing backend regression tests still pass.
13. No CLI behavior is changed.
14. No public solution JSON schema is changed.
15. No dual values are implemented.
16. No external solver dependency or call is introduced.
17. `tasks/reports/20260520-11-01_revised-warmstart_report.md` exists.
18. `pytest` passes.
19. `python scripts/check_quality.py` passes.
20. CLI help/version/solve commands work.
21. A local commit is created with message:

```text
Add revised simplex warm-start interface
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
