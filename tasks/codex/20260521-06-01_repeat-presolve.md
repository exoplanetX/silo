# Codex Task 20260521-06-01: Add Repeated-Pass Presolve Loop

## Task Metadata

Task file:

```text
tasks/codex/20260521-06-01_repeat-presolve.md
```

Execution report file:

```text
tasks/reports/20260521-06-01_repeat-presolve_report.md
```

Recommended local commit message:

```text
Add repeated-pass presolve loop
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO currently has a conservative presolve layer with:

- empty-row diagnostics and feasible empty-row removal;
- empty-column diagnostics and simple empty-column unboundedness detection;
- fixed-variable elimination with solution recovery;
- coefficient-range and scaling diagnostics;
- `silo presolve MODEL_PATH`;
- optional `silo solve MODEL_PATH --presolve`.

A repeated-pass presolve design note has been created at:

```text
notes/13_repeated_presolve_design.md
```

The design note explains that a single presolve pass is not always enough. For example, fixed-variable elimination can create a new empty row:

```text
x fixed at 2
constraint: x = 2
```

After substituting `x = 2`, the row becomes:

```text
0 = 0
```

which should then be removed as a feasible empty row in a subsequent pass.

This task implements the first repeated-pass presolve loop.

------

## 2. Goal

Update `Presolver.run(model)` so that it repeats existing structural passes until no additional structural changes occur.

The repeated loop should compose the existing conservative reductions:

```text
feasible empty-row removal
fixed-variable elimination
```

It should also continue to perform terminal diagnostics:

```text
infeasible empty-row detection
empty-column unboundedness detection
```

The resulting behavior should be deterministic, traceable, and recoverable.

This task should not introduce new presolve rules.

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260521-06-01_repeat-presolve.md
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
tests/unit/test_fixed_variable_presolve.py
tests/unit/test_empty_row_diagnostics.py
tests/unit/test_empty_column_diagnostics.py
docs/lp_solver.md
tasks/phases/phase_04_presolve_scaling.md
```

You may add:

```text
tests/unit/test_repeated_presolve.py
tasks/reports/20260521-06-01_repeat-presolve_report.md
```

You may update:

```text
src/silo/presolve/__init__.py
```

only if a new public helper is added, though this task should preferably keep changes inside `presolver.py`.

Do not modify tableau simplex implementation.

Do not modify revised simplex implementation.

Do not modify CLI behavior unless existing CLI tests must be adjusted for changed presolve output details.

------

## 5. Do Not Do

Do not add new presolve reductions.

Do not implement singleton-row bound tightening.

Do not implement duplicate-row removal.

Do not implement general redundancy detection.

Do not implement automatic scaling.

Do not change scaling diagnostics semantics.

Do not connect presolve to solve by default.

Do not change `silo solve` behavior without `--presolve`.

Do not change `silo presolve` JSON schema.

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

## 6. Repeated-Pass Scope

Repeated passes should include only existing structural reductions:

```text
1. feasible empty-row removal
2. fixed-variable elimination
```

Diagnostics that do not structurally change the model should not trigger another pass.

Examples of diagnostic-only events:

```text
empty-column warning
scaling warning
near-zero coefficient warning
large coefficient ratio warning
```

------

## 7. Pass Ordering

Use deterministic pass ordering.

Recommended structure:

```text
1. validate original model
2. compute scaling diagnostics on the original model once
3. initialize current_model = original model
4. repeat structural passes:
   a. check infeasible empty rows on current_model
   b. inspect empty columns on current_model
   c. remove feasible empty rows from current_model
   d. eliminate fixed variables from current_model
   e. if no feasible empty rows removed and no fixed variables eliminated, stop
5. return final PresolveResult
```

Important:

- Scaling diagnostics should describe the original submitted model, not the final presolved model.
- Empty-column diagnostics should be evaluated on the current model in each pass because previous reductions may change the structural model.
- If empty-column warnings are produced in the final no-change pass, they should appear in the final diagnostics.
- If terminal unboundedness is detected after earlier reductions, return `UNBOUNDED` with accumulated reductions preserved.

------

## 8. Status Priority

Use this status priority:

```text
INFEASIBLE empty row
UNBOUNDED empty column
REDUCED
NO_CHANGE
```

### 8.1 Infeasibility

If an infeasible empty row is detected in any pass:

```text
status = INFEASIBLE
```

If earlier reductions were already applied, preserve them in `reductions` and set:

```text
changed = True
```

If no reductions were applied before infeasibility, set:

```text
changed = False
```

The returned model should be the current model at the point where infeasibility was detected.

### 8.2 Unboundedness

If empty-column unboundedness is detected in any pass:

```text
status = UNBOUNDED
```

If earlier reductions were already applied, preserve them and set `changed = True`.

If no reductions were applied before unboundedness, set `changed = False`.

### 8.3 Reduced

If at least one structural reduction is applied and no terminal status occurs:

```text
status = REDUCED
changed = True
```

### 8.4 No change

If no structural reductions occur and no terminal status occurs:

```text
status = NO_CHANGE
changed = False
```

Scaling warnings alone should not change this status.

Empty-column warnings alone should not change this status.

------

## 9. Reduction Ordering

Reduction records must be deterministic.

Use this rule:

```text
Pass order first.
Within each pass:
  1. EMPTY_ROW reductions in current model constraint order.
  2. FIXED_VARIABLE reductions in current model variable order.
```

Example:

Pass 1 eliminates fixed variable `x`.

Pass 2 removes row `balance` that became empty after `x` substitution.

Reduction order should be:

```text
FIXED_VARIABLE x
EMPTY_ROW balance
```

because `x` was reduced in pass 1 and `balance` was reduced in pass 2.

Do not reorder reductions globally by type.

------

## 10. Diagnostics Aggregation

The final `PresolveDiagnostics` should include:

```text
removed_rows
fixed_variables
warnings
notes
```

### 10.1 removed_rows

Accumulate all feasible empty rows removed across all passes.

Order:

```text
pass order, then constraint order within pass
```

### 10.2 fixed_variables

Accumulate all fixed variables eliminated across all passes.

Order:

```text
pass order, then variable order within pass
```

### 10.3 warnings

For this first repeated-pass implementation, use the warnings from the final diagnostic pass unless a terminal status occurs.

If terminal infeasibility or unboundedness occurs, include the warning that explains the terminal status.

Do not overbuild warning history in this task.

### 10.4 notes

Optional. If used, keep deterministic and concise.

------

## 11. Fixed Values and Recovery

`PresolveResult.fixed_values` should accumulate fixed values across all passes.

`PresolveResult.recover_solution()` should continue to restore all fixed variables.

If multiple fixed variables are eliminated across passes, all should be restored.

The recovered solution should still:

```text
preserve objective_value
restore fixed primal_values
set fixed basis_status to "fixed"
set fixed reduced_costs to 0.0
preserve status and message
```

Do not implement original-space slack recomputation in this task. That is planned for a future Phase 4J task.

------

## 12. Pass Limit

Add a simple safety guard.

Recommended default:

```text
max_passes = number_of_variables + number_of_constraints + 1
```

Because each current structural reduction removes at least one row or variable, this limit should not be reached in normal operation.

Do not expose this as a public CLI option.

If the limit is reached, raise a clear internal error or return a clear presolve diagnostic. Prefer keeping this simple; this condition should be unreachable under the current reduction rules.

If you add a constructor option such as:

```python
class Presolver:
    def __init__(self, max_passes: int | None = None) -> None:
        ...
```

then test it minimally. Otherwise, a private guard inside `run()` is acceptable.

------

## 13. Implementation Guidance

`Presolver.run()` is currently somewhat linear. Refactor carefully.

Suggested helpers inside `presolver.py`:

```python
@dataclass(frozen=True)
class StructuralPassResult:
    model: Model
    reductions: tuple[ReductionRecord, ...]
    removed_rows: tuple[str, ...]
    fixed_values: tuple[FixedValue, ...]
    fixed_variables: tuple[str, ...]
    changed: bool

def _run_structural_pass(model: Model) -> StructuralPassResult:
    ...
```

Alternative structure is acceptable.

Avoid duplicating the fixed-variable elimination logic. Use the existing:

```python
eliminate_fixed_variables(model)
```

Avoid duplicating empty-column logic. Use the existing:

```python
inspect_empty_columns(model)
```

Keep implementation readable.

------

## 14. Tests Required

Add:

```text
tests/unit/test_repeated_presolve.py
```

### 14.1 Fixed variable creates feasible empty equality row

Original model:

```text
maximize y
subject to x = 2
           y <= 3
x fixed at 2
```

First pass eliminates `x`.

Second pass removes the now-empty equality row.

Expected:

```text
status = REDUCED
changed = True
fixed_variables includes x
removed_rows includes row x_eq_2
reductions include FIXED_VARIABLE x before EMPTY_ROW x_eq_2
final model has only y and y <= 3
```

### 14.2 Fixed variable creates infeasible empty row

Original model:

```text
maximize y
subject to x <= 1
           y <= 3
x fixed at 2
```

After eliminating `x`, row becomes:

```text
0 <= -1
```

Expected:

```text
status = INFEASIBLE
changed = True
reductions include FIXED_VARIABLE x
message mentions infeasible empty row
final result preserves fixed_values for x
```

### 14.3 Multiple fixed variables create feasible empty row

Original model:

```text
x + z = 3
x fixed at 2
z fixed at 1
```

Expected:

```text
status = REDUCED
fixed_variables = (x, z) in model order
row removed in a later pass
reduction order deterministic
```

### 14.4 Diagnostic-only warnings do not trigger another pass

Create a model with scaling warning or empty-column warning but no structural reductions.

Expected:

```text
status = NO_CHANGE
changed = False
no reductions
```

### 14.5 Empty-column unboundedness after prior reductions if possible

If a simple case exists where earlier reductions reveal an empty-column unboundedness, add it.

If no natural case exists under current reduction scope, do not force it.

Mention this in the report.

### 14.6 Recovery still restores fixed variables after repeated passes

Use the model from 14.1.

Run presolve, solve final model with tableau or revised solver, recover solution.

Expected:

```text
x restored
y solved correctly
objective not double counted
basis_status["x"] == "fixed"
```

### 14.7 Existing fixed-variable tests still pass

Do not remove existing tests in `tests/unit/test_fixed_variable_presolve.py`.

Adjust them only if expectations need to account for repeated-pass behavior. For example, tests that previously expected rows made empty by fixed-variable substitution to remain may now need to expect removal.

If updating such tests, make the new behavior explicit.

------

## 15. Update Previous Tests Carefully

There may be an existing test that says:

```text
Rows made empty by fixed-variable elimination remain for future passes.
```

This expectation should now change because this task implements the future pass.

Update that test to verify the new repeated-pass behavior.

Do not delete the conceptual coverage; convert it to a repeated-pass test.

------

## 16. CLI Behavior Tests

Existing CLI tests should continue to pass.

Because `silo solve --presolve` now benefits from repeated-pass presolve, add one CLI-level test if simple:

Temporary JSON model:

```text
x = 2
x fixed at 2
y <= 3
maximize y
```

Run:

```bash
silo solve model.json --presolve
```

Expected:

```text
status = optimal
x restored
y = 3
```

Do not overexpand CLI tests.

------

## 17. Documentation Update

Update:

```text
docs/lp_solver.md
```

Add or revise a concise note:

```markdown
## Repeated-Pass Presolve

The presolver now repeats conservative structural passes until no further empty-row or fixed-variable reductions are exposed. This allows fixed-variable elimination to create feasible empty rows that can be removed in a later pass. Diagnostics-only warnings do not trigger additional passes.
```

Update:

```text
tasks/phases/phase_04_presolve_scaling.md
```

only if useful.

Do not over-expand documentation.

------

## 18. Execution Report

Create:

```text
tasks/reports/20260521-06-01_repeat-presolve_report.md
```

The report should include:

```markdown
# Repeated-Pass Presolve Report

## Summary

## Pass Ordering

## Termination Behavior

## Recovery Behavior

## Files Changed

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend:

```text
Phase 4J: original-space slack recomputation after presolve recovery.
```

Do not record execution results by editing the issued task file.

------

## 19. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json --presolve
python -m silo.cli.main presolve examples/json/production.json
python -m silo.cli.main compare examples/json/production.json
```

If the console script is available, also run:

```bash
silo --help
silo --version
silo solve examples/json/production.json --presolve
silo presolve examples/json/production.json
silo compare examples/json/production.json
```

Fix any failures.

------

## 20. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Add repeated-pass presolve loop"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 21. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260521-06-01_repeat-presolve.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `Presolver.run()` repeats structural passes until no further structural change occurs.
4. Structural passes include feasible empty-row removal and fixed-variable elimination only.
5. Diagnostic-only warnings do not trigger another pass.
6. Fixed-variable elimination can create a feasible empty row that is removed in a later pass.
7. Fixed-variable elimination can create an infeasible empty row that is detected in a later pass.
8. Reduction order is deterministic and follows pass order.
9. `removed_rows`, `fixed_variables`, and `fixed_values` accumulate across passes.
10. Recovery still restores all fixed variables.
11. Existing empty-row, empty-column, fixed-variable, scaling, CLI, solver, and backend regression tests pass.
12. `silo solve --presolve` still works.
13. No new presolve rule is added.
14. No automatic scaling is implemented.
15. No solver algorithm behavior is changed.
16. No JSON model or solution schema changes are made.
17. `tasks/reports/20260521-06-01_repeat-presolve_report.md` exists.
18. `pytest` passes.
19. `python scripts/check_quality.py` passes.
20. CLI help/version/solve/presolve/compare commands work.
21. A local commit is created with message:

```text
Add repeated-pass presolve loop
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
