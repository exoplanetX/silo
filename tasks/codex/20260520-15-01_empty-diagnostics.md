# Codex Task 20260520-15-01: Add Empty Row and Column Diagnostics

## Task Metadata

Task file:

```text
tasks/codex/20260520-15-01_empty-diagnostics.md
```

Execution report file:

```text
tasks/reports/20260520-15-01_empty-diagnostics_report.md
```

Recommended local commit message:

```text
Add empty row and column presolve diagnostics
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO now has the Phase 4B presolve core objects:

```text
PresolveStatus
PresolveWarning
PresolveDiagnostics
ReductionType
ReductionRecord
ScalingDiagnostics
PresolveResult
Presolver
```

The current `Presolver.run(model)` is a conservative no-op: it validates the model, returns the same model object, records no reductions, and reports `NO_CHANGE`.

This task implements the first real presolve diagnostics and safe reductions:

```text
empty-row detection
empty-row feasible removal
empty-row infeasibility detection
empty-column diagnostics
empty-column unboundedness detection for simple maximization cases
```

This task should remain conservative and traceable.

------

## 2. Goal

Add empty-row and empty-column presolve diagnostics on top of the existing immutable presolve result objects.

After this task, `Presolver().run(model)` should be able to:

1. detect empty constraint rows;
2. remove feasible empty rows with a `ReductionRecord`;
3. detect infeasible empty rows and return `PresolveStatus.INFEASIBLE`;
4. detect empty variables/columns;
5. detect simple empty-column unboundedness for maximization models with positive objective coefficient and no finite upper bound;
6. record empty-column diagnostics as warnings or notes when no status conclusion is made;
7. preserve traceability through deterministic diagnostics and reduction metadata.

This task should not connect presolve to the CLI or solvers.

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260520-15-01_empty-diagnostics.md
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
src/silo/presolve/presolver.py
src/silo/presolve/diagnostics.py
src/silo/presolve/reductions.py
tests/unit/test_presolve_core.py
docs/lp_solver.md
tasks/phases/phase_04_presolve_scaling.md
```

You may add:

```text
src/silo/presolve/row_reduction.py
src/silo/presolve/column_diagnostics.py
tests/unit/test_empty_row_diagnostics.py
tests/unit/test_empty_column_diagnostics.py
tasks/reports/20260520-15-01_empty-diagnostics_report.md
```

You may update exports in:

```text
src/silo/presolve/__init__.py
```

Do not modify tableau simplex implementation.

Do not modify revised simplex implementation.

Do not modify CLI solve or compare behavior.

------

## 5. Do Not Do

Do not implement fixed-variable elimination.

Do not implement singleton-row bound tightening.

Do not implement general redundancy detection.

Do not implement duplicate-row removal.

Do not implement automatic scaling.

Do not implement presolve solution reconstruction beyond metadata records.

Do not connect presolve to `silo solve`.

Do not connect presolve to tableau or revised simplex.

Do not change JSON model format.

Do not change solution JSON schema.

Do not implement MIP.

Do not add cuts, decomposition, stochastic programming, robust optimization, or native backend code.

Do not add external solver calls.

Do not add runtime dependencies.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. Empty Row Definitions

A constraint row is empty if all its coefficients are zero within the existing tolerance:

```text
abs(coefficient) <= DEFAULT_TOLERANCE
```

A row with an empty coefficient dictionary is also empty.

Use:

```text
silo.utils.numerics.DEFAULT_TOLERANCE
```

Do not introduce a new tolerance constant.

------

## 7. Empty Row Feasibility Rules

For an empty row, evaluate feasibility using the original row sense and RHS.

### 7.1 `<=` row

```text
0 <= rhs
```

Feasible if:

```text
rhs >= -tolerance
```

Infeasible if:

```text
rhs < -tolerance
```

### 7.2 `>=` row

```text
0 >= rhs
```

Feasible if:

```text
rhs <= tolerance
```

Infeasible if:

```text
rhs > tolerance
```

### 7.3 `=` row

```text
0 = rhs
```

Feasible if:

```text
abs(rhs) <= tolerance
```

Infeasible if:

```text
abs(rhs) > tolerance
```

Clean near-zero RHS values to `0.0` in reduction metadata when appropriate.

------

## 8. Empty Row Behavior

### 8.1 Feasible empty rows

Feasible empty rows should be removed from the returned presolved model.

The presolve result should include:

```text
diagnostics.status = REDUCED
changed = True
removed_rows contains the row names
reductions contains one ReductionRecord per removed row
```

Each reduction record should use:

```text
ReductionType.EMPTY_ROW
```

Recommended record fields:

```python
ReductionRecord(
    reduction_type=ReductionType.EMPTY_ROW,
    target=constraint.name,
    description="Removed feasible empty row.",
    data=reduction_data(
        sense=constraint.sense.value,
        rhs=cleaned_rhs,
    ),
)
```

The returned model should preserve:

```text
same model name
same variables
same objective
same nonempty constraints in original order
```

Do not mutate the original input model in place.

### 8.2 Infeasible empty rows

If any infeasible empty row is found, return a `PresolveResult` with:

```text
diagnostics.status = INFEASIBLE
changed = False
model is the original model
message mentions the infeasible empty row
```

Also include a warning such as:

```python
PresolveWarning(
    code="empty_row_infeasible",
    message="Empty row is infeasible.",
    source=constraint.name,
)
```

It is acceptable to include a `ReductionRecord` for the diagnostic, but do not mark it as a successful reduction.

Prefer stopping after the first infeasible empty row for clear behavior.

------

## 9. Empty Column Definitions

A variable column is empty if the variable does not appear with a nonzero coefficient in any constraint row:

```text
abs(coefficient) > DEFAULT_TOLERANCE
```

means present.

Coefficients missing from a constraint are zero.

Use deterministic variable order from `model.variable_names()`.

------

## 10. Empty Column Behavior

Empty columns should be diagnostic-only in this task unless they imply a very simple unboundedness conclusion.

### 10.1 Simple unboundedness detection

For a maximization model, if a variable:

```text
has no nonzero coefficients in any constraint
has objective coefficient > tolerance
has no finite upper bound
```

then the model is unbounded.

Return:

```text
diagnostics.status = UNBOUNDED
changed = False
model is the original model
message mentions the unbounded empty column
```

Add a warning:

```python
PresolveWarning(
    code="empty_column_unbounded",
    message="Empty column with positive objective coefficient and no finite upper bound makes the model unbounded.",
    source=variable.name,
)
```

Do not remove variables in this case.

### 10.2 Empty column non-unbounded diagnostics

If an empty column does not imply unboundedness, record a warning or note.

For example, if objective coefficient is zero or negative in a maximization model:

```python
PresolveWarning(
    code="empty_column",
    message="Variable does not appear in any constraint.",
    source=variable.name,
)
```

Do not remove the variable yet.

Do not add the variable to `removed_variables` in this task.

Do not set `changed = True` solely for empty-column diagnostics.

------

## 11. Result Status Priority

Use deterministic status priority:

1. validate model first;
2. if an infeasible empty row exists, return `INFEASIBLE`;
3. else if an unbounded empty column exists, return `UNBOUNDED`;
4. else remove feasible empty rows if any and return `REDUCED`;
5. else return `NO_CHANGE`.

If feasible empty rows and empty-column warnings both exist, return `REDUCED` and include warnings.

If no reductions exist but warnings exist, keep status `NO_CHANGE`.

------

## 12. Presolver.run() Requirements

Update:

```text
src/silo/presolve/presolver.py
```

`Presolver.run(model)` should now:

1. call `model.validate()`;
2. inspect empty rows;
3. inspect empty columns;
4. return an appropriate `PresolveResult`.

Preserve `Presolver.apply(model)` behavior cautiously.

Recommended:

```python
def apply(self, model: Model) -> Model:
    return self.run(model).model
```

If presolve status is `INFEASIBLE` or `UNBOUNDED`, returning the original model is acceptable.

Document this behavior in code comments or tests if needed.

------

## 13. Model Copying Requirement

When removing feasible empty rows, do not mutate the original `Model`.

Create a new `Model` with:

```text
same name
same variables list content
same objective
constraints excluding removed empty rows
```

It is acceptable for `Variable`, `Constraint`, and `Objective` objects to be reused because they are dataclass-like immutable or treated as immutable.

The original model must still contain the removed row after presolve.

Add a test for this.

------

## 14. Diagnostics Determinism

Diagnostics should be deterministic:

```text
removed_rows in original constraint order
warnings in deterministic scan order
reductions in original constraint order
notes deterministic
```

Do not use unordered sets when building public tuples unless sorted.

------

## 15. Tests Required: Empty Rows

Add:

```text
tests/unit/test_empty_row_diagnostics.py
```

Test at least:

### 15.1 Feasible empty `<=` row removed

Model:

```text
0 <= 5
x <= 3
maximize x
```

Expected:

```text
status = REDUCED
changed = True
removed_rows includes empty row
returned model excludes empty row
original model still includes empty row
ReductionType.EMPTY_ROW record exists
```

### 15.2 Feasible empty `>=` row removed

Model:

```text
0 >= -1
x <= 3
maximize x
```

Expected: removed.

### 15.3 Feasible empty equality row removed

Model:

```text
0 = 0
x <= 3
maximize x
```

Expected: removed.

### 15.4 Infeasible empty `<=` row

Model:

```text
0 <= -1
```

Expected:

```text
status = INFEASIBLE
changed = False
message mentions row name
warning code = empty_row_infeasible
```

### 15.5 Infeasible empty `>=` row

Model:

```text
0 >= 1
```

Expected: infeasible.

### 15.6 Infeasible empty equality row

Model:

```text
0 = 1
```

Expected: infeasible.

### 15.7 Near-zero coefficient treated as empty

A row with coefficient below tolerance should be treated as empty.

Use `DEFAULT_TOLERANCE / 10`.

Expected: behavior follows empty-row rules.

------

## 16. Tests Required: Empty Columns

Add:

```text
tests/unit/test_empty_column_diagnostics.py
```

Test at least:

### 16.1 Empty column with positive objective is unbounded

Model:

```text
maximize x
subject to y <= 1
x appears in no constraints
x >= 0, no upper bound
```

Expected:

```text
status = UNBOUNDED
changed = False
message mentions x
warning code = empty_column_unbounded
```

### 16.2 Empty column with zero objective gets warning only

Model:

```text
maximize y
subject to y <= 1
x appears in no constraints
objective coefficient of x = 0
```

Expected:

```text
status = NO_CHANGE
changed = False
warning code = empty_column
source = x
```

### 16.3 Empty column with negative objective gets warning only

Model:

```text
maximize y - x
subject to y <= 1
x appears in no constraints
```

Expected:

```text
status = NO_CHANGE
warning code = empty_column
```

### 16.4 Nonempty column does not warn

Model:

```text
maximize x
subject to x <= 1
```

Expected:

```text
no empty-column warning for x
```

### 16.5 Deterministic warning order

If multiple empty columns exist, warnings should follow model variable order.

------

## 17. Existing Tests Must Still Pass

All existing tests must continue to pass, including:

```text
tableau simplex
revised simplex
CLI solve
CLI compare
backend regression
standard form
basis
presolve core
scaling diagnostics
```

Do not change solver outputs.

------

## 18. Documentation Update

Update:

```text
docs/lp_solver.md
```

Add a concise note:

```markdown
## Empty-Row and Empty-Column Presolve Diagnostics

The presolver now detects feasible empty rows, infeasible empty rows, and simple empty-column unboundedness. Feasible empty rows are removed from the returned presolved model with traceable reduction records. Empty columns are diagnostic-only except when a nonconstrained variable with positive maximization objective and no finite upper bound proves unboundedness.
```

Update:

```text
tasks/phases/phase_04_presolve_scaling.md
```

only if useful.

Do not over-expand documentation.

------

## 19. Execution Report

Create:

```text
tasks/reports/20260520-15-01_empty-diagnostics_report.md
```

The report should include:

```markdown
# Empty Row and Column Diagnostics Report

## Summary

## Empty Row Behavior

## Empty Column Behavior

## Files Changed

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend:

```text
Phase 4D: implement fixed-variable elimination with solution reconstruction.
```

Do not record execution results by editing the issued task file.

------

## 20. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json --solver tableau
python -m silo.cli.main solve examples/json/production.json --solver revised
python -m silo.cli.main compare examples/json/production.json
```

If the console script is available, also run:

```bash
silo --help
silo --version
silo compare examples/json/production.json
```

Fix any failures.

------

## 21. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Add empty row and column presolve diagnostics"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 22. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260520-15-01_empty-diagnostics.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `Presolver.run()` detects feasible empty rows.
4. Feasible empty rows are removed from the returned model, not from the original model.
5. Feasible empty-row reductions use `ReductionType.EMPTY_ROW`.
6. Infeasible empty `<=`, `>=`, and `=` rows return `PresolveStatus.INFEASIBLE`.
7. Empty-column unboundedness is detected for a positive-objective unconstrained variable with no finite upper bound in maximization.
8. Empty columns that do not prove unboundedness generate deterministic warnings but do not remove variables.
9. Diagnostics and reductions are deterministic.
10. Existing solver, CLI, compare, backend regression, standard-form, basis, and presolve core tests still pass.
11. No fixed-variable elimination is implemented.
12. No automatic scaling is implemented.
13. No presolve integration with CLI or solvers is added.
14. No JSON model or solution schema changes are made.
15. No external solver dependency or call is introduced.
16. `tasks/reports/20260520-15-01_empty-diagnostics_report.md` exists.
17. `pytest` passes.
18. `python scripts/check_quality.py` passes.
19. CLI help/version/solve/compare commands work.
20. A local commit is created with message:

```text
Add empty row and column presolve diagnostics
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
