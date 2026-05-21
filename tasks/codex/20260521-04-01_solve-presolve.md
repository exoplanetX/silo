# Codex Task 20260521-04-01: Add Optional Presolve Solve Flag

## Task Metadata

Task file:

```text
tasks/codex/20260521-04-01_solve-presolve.md
```

Execution report file:

```text
tasks/reports/20260521-04-01_solve-presolve_report.md
```

Recommended local commit message:

```text
Add optional presolve flag to solve command
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

- `silo solve MODEL_PATH`;
- `silo solve MODEL_PATH --solver tableau`;
- `silo solve MODEL_PATH --solver revised`;
- `silo compare MODEL_PATH`;
- `silo presolve MODEL_PATH`.

The `presolve` command is diagnostic-only and already outputs presolve/scaling JSON.

The presolve layer can currently detect and handle:

- feasible empty-row removal;
- infeasible empty rows;
- empty-column unboundedness diagnostics;
- empty-column warnings;
- fixed-variable elimination;
- solution recovery for fixed variables;
- coefficient-range and scaling diagnostics.

However, the `solve` command does not yet offer a way to explicitly run presolve before solving.

This task adds an **optional** `--presolve` flag to the `solve` command.

------

## 2. Goal

Add a controlled solve path:

```bash
silo solve MODEL_PATH --presolve
```

and:

```bash
silo solve MODEL_PATH --solver revised --presolve
silo solve MODEL_PATH --solver tableau --presolve
```

When `--presolve` is provided, the CLI should:

1. read the JSON model;
2. run `Presolver().run(model)`;
3. if presolve proves infeasible or unbounded, return a corresponding `Solution` JSON without calling a simplex solver;
4. otherwise solve the presolved model with the selected solver;
5. recover the original-space solution using `PresolveResult.recover_solution()`;
6. output the same solution JSON schema as normal `silo solve`.

When `--presolve` is not provided, existing `silo solve` behavior must remain unchanged.

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260521-04-01_solve-presolve.md
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
src/silo/cli/main.py
tests/unit/test_cli_solve.py
docs/cli_solve.md
docs/presolve_cli.md
README.md
tasks/phases/phase_04_presolve_scaling.md
```

You may add:

```text
tests/unit/test_cli_solve_presolve.py
tasks/reports/20260521-04-01_solve-presolve_report.md
```

You may modify presolve code only if a test exposes a real recovery or status-mapping bug:

```text
src/silo/presolve/presolver.py
```

Do not modify tableau or revised simplex algorithms unless a clear bug is exposed by this task.

------

## 5. Do Not Do

Do not make presolve run by default.

Do not change `silo solve MODEL_PATH` behavior without `--presolve`.

Do not change `silo compare` behavior.

Do not change `silo presolve` behavior.

Do not add presolve diagnostics into solution JSON.

Do not change solution JSON schema.

Do not change JSON model format.

Do not implement new presolve reductions.

Do not implement automatic scaling.

Do not implement MIP.

Do not add cuts, decomposition, stochastic programming, robust optimization, or native backend code.

Do not add external solver calls.

Do not add runtime dependencies.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not commit generated files under `outputs/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. CLI Interface Requirements

Add an optional flag:

```text
--presolve
```

Usage:

```bash
silo solve examples/json/production.json --presolve
silo solve examples/json/production.json --solver tableau --presolve
silo solve examples/json/production.json --solver revised --presolve
```

The flag should be meaningful only for `solve`.

Current CLI uses a simple parser with shared options. It is acceptable for `--presolve` to exist as a global parser option if that keeps changes small, but behavior should be documented and tested for `solve`.

If you choose to refactor to subparsers, keep backward compatibility and update tests carefully. Do not overcomplicate the CLI.

------

## 7. Solve Behavior with Presolve

### 7.1 Default behavior unchanged

Without `--presolve`:

```bash
silo solve MODEL_PATH
```

should behave exactly as before.

Default solver remains:

```text
tableau
```

### 7.2 Presolve path

With `--presolve`:

```bash
silo solve MODEL_PATH --presolve
```

the CLI should run:

```python
presolve_result = Presolver().run(model)
```

Then inspect:

```python
presolve_result.diagnostics.status
```

### 7.3 PresolveStatus.INFEASIBLE

If presolve status is `INFEASIBLE`, do not call a simplex solver.

Return solution JSON:

```json
{
  "status": "infeasible",
  "objective_value": null,
  "primal_values": {},
  "slack_values": {},
  "dual_values": {},
  "reduced_costs": {},
  "basis_status": {},
  "message": "Presolve detected infeasibility: ..."
}
```

Exit code:

```text
1
```

### 7.4 PresolveStatus.UNBOUNDED

If presolve status is `UNBOUNDED`, do not call a simplex solver.

Return solution JSON:

```json
{
  "status": "unbounded",
  "objective_value": null,
  "primal_values": {},
  "slack_values": {},
  "dual_values": {},
  "reduced_costs": {},
  "basis_status": {},
  "message": "Presolve detected unboundedness: ..."
}
```

Exit code:

```text
1
```

### 7.5 PresolveStatus.REDUCED or NO_CHANGE

If presolve status is `REDUCED` or `NO_CHANGE`, solve:

```python
presolve_result.model
```

using the selected solver.

Then recover:

```python
solution = presolve_result.recover_solution(solution)
```

Return the recovered `Solution`.

Exit code:

```text
0 if recovered solution status is OPTIMAL
1 otherwise
```

------

## 8. Solution JSON Schema

Do not change the solution JSON schema.

The output should continue to include:

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

Do not add:

```text
presolve
reductions
scaling
```

to `silo solve` output.

Users who want presolve diagnostics should use:

```bash
silo presolve MODEL_PATH
```

------

## 9. Recovery Requirements

When presolve removes fixed variables, the final solution should be recovered in original model space.

Example:

Original model:

```text
maximize 3x + 2y
subject to x + y <= 5
x = 2
y >= 0
```

Presolved model:

```text
maximize 2y + 6
subject to y <= 3
```

Expected recovered solution:

```text
x = 2
y = 3
objective = 12
basis_status["x"] = "fixed"
```

The recovered objective should not double count fixed-variable contribution.

------

## 10. Tests Required

Add:

```text
tests/unit/test_cli_solve_presolve.py
```

### 10.1 Default solve remains unchanged

Test:

```bash
silo solve examples/json/production.json
```

Expected:

```text
exit code = 0
status = optimal
objective_value = 21
```

This protects default behavior.

### 10.2 Solve with presolve on unchanged model

Test:

```bash
silo solve examples/json/production.json --presolve
```

Expected:

```text
exit code = 0
status = optimal
objective_value = 21
```

### 10.3 Solve with presolve and revised backend

Test:

```bash
silo solve examples/json/production.json --solver revised --presolve
```

Expected:

```text
exit code = 0
status = optimal
objective_value = 21
```

### 10.4 Presolve detects infeasibility

Use a temporary JSON model with an infeasible empty row:

```text
0 <= -1
```

Run:

```bash
silo solve infeasible_empty_row.json --presolve
```

Expected:

```text
exit code = 1
solution status = infeasible
message mentions presolve
```

Do not call solver.

### 10.5 Presolve detects unboundedness

Use a temporary JSON model with an empty positive-objective column:

```text
maximize x
x appears in no constraints
x >= 0
no upper bound
```

Run:

```bash
silo solve unbounded_empty_column.json --presolve
```

Expected:

```text
exit code = 1
solution status = unbounded
message mentions presolve
```

### 10.6 Fixed-variable recovery with tableau backend

Use a temporary JSON model:

```text
maximize 3x + 2y
subject to x + y <= 5
x fixed at 2
y >= 0
```

Run:

```bash
silo solve fixed_var.json --solver tableau --presolve
```

Expected:

```text
exit code = 0
status = optimal
primal_values["x"] = 2
primal_values["y"] = 3
objective_value = 12
basis_status["x"] = "fixed"
```

### 10.7 Fixed-variable recovery with revised backend

Same model:

```bash
silo solve fixed_var.json --solver revised --presolve
```

Expected same recovered original-space values.

### 10.8 Output file with presolve

Test:

```bash
silo solve fixed_var.json --presolve --output <tmp_path>/solution.json
```

Expected:

```text
exit code = 0
file exists
solution JSON includes recovered fixed variable
```

### 10.9 Presolve flag does not affect compare

Existing compare tests should continue to pass.

Do not add `--presolve` to compare in this task.

### 10.10 Presolve diagnostics command unchanged

Existing `silo presolve` tests must still pass.

------

## 11. Parser Tests

Update parser tests so `--presolve` appears in help text.

If invalid command usage occurs, argparse should still return exit code `2`.

If `--presolve` is accepted globally due to the current parser structure, document that it is used only by `solve`. Do not add complex enforcement unless it is easy and tested.

------

## 12. Documentation Requirements

Update:

```text
docs/cli_solve.md
```

Add a section:

```markdown
## Optional Presolve Before Solving
```

Explain:

```bash
silo solve examples/json/production.json --presolve
silo solve examples/json/production.json --solver revised --presolve
```

Clarify:

```text
--presolve is opt-in.
Default solve behavior does not run presolve.
Presolve diagnostics are not included in solution JSON.
Use silo presolve MODEL_PATH to inspect diagnostics.
```

Update:

```text
docs/presolve_cli.md
```

Add a short note that `silo presolve` is diagnostic-only, while `silo solve --presolve` applies safe presolve before solving.

Update:

```text
README.md
```

Add at most one concise line in the CLI section.

Do not over-expand README.

------

## 13. Execution Report

Create:

```text
tasks/reports/20260521-04-01_solve-presolve_report.md
```

The report should include:

```markdown
# Solve Presolve Flag Report

## Summary

## User-Facing Command

## Presolve Status Mapping

## Recovery Behavior

## Files Changed

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
Phase 4H: presolve repeated-pass design for rows made empty by fixed-variable elimination.
```

Choose based on what seems most natural after completing this task.

Do not record execution results by editing the issued task file.

------

## 14. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json --solver tableau
python -m silo.cli.main solve examples/json/production.json --solver revised
python -m silo.cli.main solve examples/json/production.json --presolve
python -m silo.cli.main solve examples/json/production.json --solver revised --presolve
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

## 15. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Add optional presolve flag to solve command"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 16. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260521-04-01_solve-presolve.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `silo solve MODEL_PATH` default behavior remains unchanged.
4. `silo solve MODEL_PATH --presolve` runs `Presolver` before solving.
5. `--presolve` works with `--solver tableau`.
6. `--presolve` works with `--solver revised`.
7. Presolve-detected infeasibility maps to solution status `infeasible` and exit code `1`.
8. Presolve-detected unboundedness maps to solution status `unbounded` and exit code `1`.
9. Fixed-variable recovery works through CLI solve with tableau backend.
10. Fixed-variable recovery works through CLI solve with revised backend.
11. Solution JSON schema remains unchanged.
12. Presolve diagnostics are not injected into solve output.
13. Existing `silo presolve` behavior remains unchanged.
14. Existing `silo compare` behavior remains unchanged.
15. No new presolve reductions are implemented.
16. No automatic scaling is implemented.
17. No solver algorithm behavior is changed.
18. No JSON model schema changes are made.
19. No external solver dependency or call is introduced.
20. `tasks/reports/20260521-04-01_solve-presolve_report.md` exists.
21. `pytest` passes.
22. `python scripts/check_quality.py` passes.
23. CLI help/version/solve/presolve/compare commands work.
24. A local commit is created with message:

```text
Add optional presolve flag to solve command
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
