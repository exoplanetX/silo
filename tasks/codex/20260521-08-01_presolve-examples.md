# Codex Task 20260521-08-01: Add Presolve Recovery Examples

## Task Metadata

Task file:

```text
tasks/codex/20260521-08-01_presolve-examples.md
```

Execution report file:

```text
tasks/reports/20260521-08-01_presolve-examples_report.md
```

Recommended local commit message:

```text
Add presolve recovery JSON examples
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO currently supports:

- `silo solve MODEL_PATH`;
- `silo solve MODEL_PATH --solver tableau`;
- `silo solve MODEL_PATH --solver revised`;
- `silo solve MODEL_PATH --presolve`;
- `silo presolve MODEL_PATH`;
- `silo compare MODEL_PATH`.

The presolve layer now supports:

- feasible empty-row removal;
- empty-column diagnostics;
- fixed-variable elimination;
- repeated-pass presolve;
- original-space slack recovery;
- coefficient-range scaling diagnostics.

The previous Phase 4J task added original-space slack recomputation after presolve recovery. The next step is to add user-facing JSON examples and regression tests so this behavior can be exercised from the command line.

This task should add examples only and regression coverage. It should not expand solver algorithms or presolve transformations.

------

## 2. Goal

Add small checked-in JSON examples under:

```text
examples/json/
```

that demonstrate:

1. fixed-variable elimination;
2. repeated-pass presolve where fixed-variable elimination creates a removable empty row;
3. original-space slack recovery for removed rows;
4. presolve-detected infeasibility after repeated-pass reduction;
5. optional comparison between `tableau` and `revised` when appropriate.

After this task, users should be able to run commands such as:

```bash
silo solve examples/json/fixed_var_recovery.json --presolve
silo presolve examples/json/fixed_var_recovery.json
silo solve examples/json/repeated_empty_row.json --presolve
silo presolve examples/json/repeated_empty_row.json
```

and see behavior documented by tests.

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260521-08-01_presolve-examples.md
```

Save this full task prompt into that file.

Important: the task file must contain this full task prompt. Do not leave it empty.

Do not edit, rename, delete, or move any existing files under:

```text
tasks/codex/
```

This task may only add the new task file above.

------

## 4. Allowed Files to Modify or Add

You may add JSON examples:

```text
examples/json/fixed_var_recovery.json
examples/json/repeated_empty_row.json
examples/json/presolve_infeasible_after_fixed.json
```

You may add tests:

```text
tests/regression/test_presolve_json_examples.py
```

You may update:

```text
docs/json_model_format.md
docs/cli_solve.md
docs/presolve_cli.md
README.md
tasks/phases/phase_04_presolve_scaling.md
```

You may create:

```text
tasks/reports/20260521-08-01_presolve-examples_report.md
```

Do not modify tableau simplex implementation.

Do not modify revised simplex implementation.

Do not modify presolver implementation unless the new examples reveal a clear bug.

Do not change CLI behavior unless a test reveals a serialization bug.

------

## 5. Do Not Do

Do not add new presolve reductions.

Do not change repeated-pass presolve logic.

Do not change original-space slack recovery logic unless a clear bug is revealed.

Do not add automatic scaling.

Do not implement MIP.

Do not add cuts, decomposition, stochastic programming, robust optimization, or native backend code.

Do not add external solver calls.

Do not add runtime dependencies.

Do not change JSON model schema.

Do not change solution JSON schema.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not commit generated output files under `outputs/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. JSON Examples to Add

### 6.1 `fixed_var_recovery.json`

Add:

```text
examples/json/fixed_var_recovery.json
```

Model:

```text
maximize 3x + 2y
subject to x + y <= 5
           y <= 3
           x fixed at 2
           y >= 0
```

Use JSON variable bounds:

```json
{"name": "x", "lower": 2.0, "upper": 2.0, "type": "continuous"}
{"name": "y", "lower": 0.0, "upper": null, "type": "continuous"}
```

Expected after `silo solve --presolve`:

```text
status = optimal
x = 2
y = 3
objective_value = 12
slack_values["capacity"] = 0
slack_values["y_limit"] = 0
basis_status["x"] = "fixed"
```

This example demonstrates fixed-variable elimination and original-space recovery.

------

### 6.2 `repeated_empty_row.json`

Add:

```text
examples/json/repeated_empty_row.json
```

Model:

```text
maximize y
subject to x = 2
           y <= 3
           x fixed at 2
           y >= 0
```

Expected repeated-pass behavior:

1. fixed-variable elimination removes `x`;
2. row `x_eq_2` becomes `0 = 0`;
3. repeated-pass presolve removes `x_eq_2`;
4. solving the reduced model gives `y = 3`;
5. recovered solution restores `x = 2`;
6. recovered slack values include the original removed row:

```text
slack_values["x_eq_2"] = 0
```

Expected after `silo solve --presolve`:

```text
status = optimal
x = 2
y = 3
objective_value = 3
basis_status["x"] = "fixed"
slack_values["x_eq_2"] = 0
slack_values["y_limit"] = 0
```

This example demonstrates repeated-pass presolve and original-space slack recomputation.

------

### 6.3 `presolve_infeasible_after_fixed.json`

Add:

```text
examples/json/presolve_infeasible_after_fixed.json
```

Model:

```text
maximize y
subject to x <= 1
           y <= 3
           x fixed at 2
           y >= 0
```

Expected repeated-pass behavior:

1. fixed-variable elimination removes `x`;
2. row `x_limit` becomes `0 <= -1`;
3. repeated-pass presolve detects infeasible empty row;
4. `silo solve --presolve` returns ordinary solution JSON with status `infeasible`.

Expected after `silo solve --presolve`:

```text
exit code = 1
status = infeasible
message mentions presolve or empty row
```

Expected after `silo presolve`:

```text
exit code = 0
presolve.status = infeasible
reductions include fixed_variable x
```

------

## 7. Regression Tests Required

Add:

```text
tests/regression/test_presolve_json_examples.py
```

Use existing CLI testing style if available.

At minimum, test the following.

### 7.1 All new examples can be read

Use:

```python
read_json_model(path)
```

for all new JSON files.

Expected: no `ValueError`.

### 7.2 `fixed_var_recovery.json` solve with tableau + presolve

Command equivalent:

```bash
silo solve examples/json/fixed_var_recovery.json --solver tableau --presolve
```

Expected:

```text
exit code = 0
status = optimal
objective_value = 12
primal_values["x"] = 2
primal_values["y"] = 3
basis_status["x"] = "fixed"
slack_values["capacity"] = 0
```

### 7.3 `fixed_var_recovery.json` solve with revised + presolve

Command equivalent:

```bash
silo solve examples/json/fixed_var_recovery.json --solver revised --presolve
```

Expected same public solution fields.

### 7.4 `repeated_empty_row.json` solve with tableau + presolve

Expected:

```text
exit code = 0
status = optimal
objective_value = 3
primal_values["x"] = 2
primal_values["y"] = 3
slack_values["x_eq_2"] = 0
basis_status["x"] = "fixed"
```

### 7.5 `repeated_empty_row.json` solve with revised + presolve

Expected same public solution fields.

### 7.6 `repeated_empty_row.json` presolve diagnostics

Command equivalent:

```bash
silo presolve examples/json/repeated_empty_row.json
```

Expected:

```text
exit code = 0
presolve.status = reduced
fixed_variables includes x
reductions include fixed_variable x
reductions include empty_row x_eq_2
```

Reduction order should be:

```text
fixed_variable x
empty_row x_eq_2
```

because the empty row is exposed in a later repeated pass.

### 7.7 `presolve_infeasible_after_fixed.json` solve with presolve

Command equivalent:

```bash
silo solve examples/json/presolve_infeasible_after_fixed.json --presolve
```

Expected:

```text
exit code = 1
status = infeasible
message mentions presolve or empty row
```

### 7.8 `presolve_infeasible_after_fixed.json` presolve diagnostics

Command equivalent:

```bash
silo presolve examples/json/presolve_infeasible_after_fixed.json
```

Expected:

```text
exit code = 0
presolve.status = infeasible
reductions include fixed_variable x
warnings include empty_row_infeasible
```

### 7.9 Default solve without presolve remains unchanged

For `fixed_var_recovery.json`, `silo solve` without `--presolve` may return `ERROR` because finite/nonzero fixed bounds remain unsupported by simplex. That is acceptable.

Test only if useful:

```bash
silo solve examples/json/fixed_var_recovery.json
```

Expected:

```text
exit code = 1
status = error
```

Do not change default solve behavior.

------

## 8. Documentation Updates

Update:

```text
docs/cli_solve.md
```

Add a small subsection under presolve usage:

```markdown
### Presolve recovery examples
```

Mention:

```bash
silo solve examples/json/fixed_var_recovery.json --presolve
silo solve examples/json/repeated_empty_row.json --presolve
silo solve examples/json/presolve_infeasible_after_fixed.json --presolve
```

Update:

```text
docs/presolve_cli.md
```

Mention the same examples and clarify that `silo presolve` can show reductions before solving.

Update:

```text
docs/json_model_format.md
```

Add a brief note that fixed variables can be represented with equal lower and upper bounds:

```json
{"name": "x", "lower": 2.0, "upper": 2.0, "type": "continuous"}
```

Update:

```text
README.md
```

Only add a concise line if appropriate. Do not make README long.

------

## 9. Execution Report

Create:

```text
tasks/reports/20260521-08-01_presolve-examples_report.md
```

The report should include:

```markdown
# Presolve Recovery Examples Report

## Summary

## Examples Added

## Behaviors Covered

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend one next step.

Likely candidates:

```text
Phase 5A: branch-and-bound design note.
```

or:

```text
Phase 4L: presolve solve/compare regression checklist.
```

Choose based on what seems most natural after completing this task.

Do not record execution results by editing the issued task file.

------

## 10. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/fixed_var_recovery.json --presolve
python -m silo.cli.main solve examples/json/repeated_empty_row.json --presolve
python -m silo.cli.main presolve examples/json/repeated_empty_row.json
python -m silo.cli.main presolve examples/json/presolve_infeasible_after_fixed.json
python -m silo.cli.main compare examples/json/production.json
```

If the console script is available, also run:

```bash
silo --help
silo --version
silo solve examples/json/fixed_var_recovery.json --presolve
silo solve examples/json/repeated_empty_row.json --presolve
silo presolve examples/json/repeated_empty_row.json
```

Fix any failures.

------

## 11. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Add presolve recovery JSON examples"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 12. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260521-08-01_presolve-examples.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `examples/json/fixed_var_recovery.json` exists.
4. `examples/json/repeated_empty_row.json` exists.
5. `examples/json/presolve_infeasible_after_fixed.json` exists.
6. New examples are valid JSON models readable by `read_json_model`.
7. `fixed_var_recovery.json` solves optimally with `--presolve`.
8. `repeated_empty_row.json` solves optimally with `--presolve`.
9. `presolve_infeasible_after_fixed.json` returns infeasible with `--presolve`.
10. `silo presolve repeated_empty_row.json` reports both fixed-variable and empty-row reductions.
11. Recovered solution JSON includes fixed variables and original-space slacks.
12. Default solve behavior without `--presolve` is unchanged.
13. No solver implementation behavior is changed.
14. No new presolve reductions are added.
15. No JSON model schema changes are made.
16. No solution JSON schema changes are made.
17. Documentation mentions the new examples.
18. `tasks/reports/20260521-08-01_presolve-examples_report.md` exists.
19. `pytest` passes.
20. `python scripts/check_quality.py` passes.
21. CLI help/version/solve/presolve/compare commands work.
22. A local commit is created with message:

```text
Add presolve recovery JSON examples
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
