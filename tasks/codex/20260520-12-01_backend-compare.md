# Codex Task 20260520-12-01: Add Backend Comparison Command

## Task Metadata

Task file:

```text
tasks/codex/20260520-12-01_backend-compare.md
```

Execution report file:

```text
tasks/reports/20260520-12-01_backend-compare_report.md
```

Recommended local commit message:

```text
Add backend comparison command
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO currently has two native LP backends:

```text
tableau
revised
```

The CLI already supports backend selection for solving:

```bash
silo solve MODEL_PATH --solver tableau
silo solve MODEL_PATH --solver revised
```

The revised backend now also has a conservative warm-start interface, but the CLI does not expose warm-start behavior. That is fine.

The next useful developer-facing tool is a comparison command that runs both native LP backends on the same JSON model and reports whether their public outputs agree.

This command is meant for regression, debugging, and future solver development. It should not expand solver mathematics.

------

## 2. Goal

Add a CLI command:

```bash
silo compare MODEL_PATH
```

that:

1. reads a JSON model;
2. solves it with `TableauSimplexSolver`;
3. solves it with `RevisedSimplexSolver`;
4. compares public solution outputs;
5. prints deterministic comparison JSON to stdout by default;
6. optionally writes the comparison JSON to a file;
7. returns an exit code indicating whether the backends are consistent.

After this task, these commands should work:

```bash
silo compare examples/json/production.json
silo compare examples/json/ge_row.json
silo compare examples/json/equality_row.json
silo compare examples/json/infeasible.json
silo compare examples/json/production.json --output outputs/production_compare.json
python -m silo.cli.main compare examples/json/production.json
```

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260520-12-01_backend-compare.md
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
src/silo/cli/solvers.py
src/silo/io/solution_writer.py
tests/unit/test_cli.py
tests/unit/test_cli_solve.py
docs/cli_solve.md
docs/lp_solver.md
README.md
```

You may add:

```text
src/silo/cli/compare.py
tests/unit/test_cli_compare.py
docs/backend_compare.md
tasks/reports/20260520-12-01_backend-compare_report.md
```

If a shared serialization helper already exists in `solution_writer.py`, reuse it.

If no helper exists, create small helpers such as:

```python
solution_to_dict(solution: Solution) -> dict[str, object]
solution_to_json(solution: Solution) -> str
```

Keep them deterministic and compatible with existing solution JSON tests.

Do not modify solver implementation files unless the comparison tests expose a clear public-output bug. If a solver bug is found, keep the fix minimal and explain it in the report.

------

## 5. Do Not Do

Do not add a new solver algorithm.

Do not change tableau simplex mathematical behavior.

Do not change revised simplex mathematical behavior unless a clear public-output bug is found.

Do not expose warm-start behavior through CLI in this task.

Do not implement dual values.

Do not implement dual simplex.

Do not implement presolve.

Do not implement MIP.

Do not add cuts.

Do not add decomposition.

Do not add stochastic or robust optimization.

Do not add native backend code.

Do not add external solver calls.

Do not add runtime dependencies.

Do not change the JSON model schema.

Do not change the public solution JSON schema.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not commit generated files under `outputs/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. CLI Interface Requirements

Add a new command:

```bash
silo compare MODEL_PATH
```

Required positional argument:

```text
MODEL_PATH
```

Optional argument:

```text
--output / -o
```

If `--output` is provided, write the comparison JSON to that path.

If `--output` is not provided, print the comparison JSON to stdout.

Do not require users to specify solvers for this command. It should always compare:

```text
tableau
revised
```

Do not add external solver names.

------

## 7. Comparison JSON Schema

The command should produce deterministic JSON with this general structure:

```json
{
  "model_path": "examples/json/production.json",
  "consistent": true,
  "tolerance": 1e-09,
  "checks": {
    "status_match": true,
    "objective_match": true,
    "primal_max_abs_diff": 0.0,
    "slack_max_abs_diff": 0.0,
    "reduced_cost_max_abs_diff": 0.0,
    "basis_status_match": true,
    "dual_values_empty": true
  },
  "tableau": {
    "status": "optimal",
    "objective_value": 21.0,
    "primal_values": {},
    "slack_values": {},
    "dual_values": {},
    "reduced_costs": {},
    "basis_status": {},
    "message": "..."
  },
  "revised": {
    "status": "optimal",
    "objective_value": 21.0,
    "primal_values": {},
    "slack_values": {},
    "dual_values": {},
    "reduced_costs": {},
    "basis_status": {},
    "message": "..."
  }
}
```

Exact field ordering should be deterministic. Use existing JSON serialization conventions where possible.

### 7.1 Required top-level fields

The comparison JSON must include:

```text
model_path
consistent
tolerance
checks
tableau
revised
```

### 7.2 Required `checks` fields

At minimum include:

```text
status_match
objective_match
primal_max_abs_diff
slack_max_abs_diff
reduced_cost_max_abs_diff
basis_status_match
dual_values_empty
```

You may add extra fields if useful, but do not make the output overly complex.

### 7.3 Solution payloads

The `tableau` and `revised` solution payloads should use the same schema as `silo solve` output:

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

Do not add solver-specific fields inside the solution payloads.

------

## 8. Consistency Rule

Define a simple, conservative consistency rule.

The comparison should be considered consistent if:

1. solver statuses match;
2. if both solvers are optimal, objective values match within tolerance;
3. both solvers keep `dual_values == {}`.

Do not require primal-value equality for all optimal cases, because degenerate LPs may have multiple optimal primal solutions.

However, still report:

```text
primal_max_abs_diff
slack_max_abs_diff
reduced_cost_max_abs_diff
basis_status_match
```

so developers can inspect differences.

For non-optimal matching statuses such as `infeasible` or `unbounded`, consistency should be true if statuses match and dual values are empty.

### 8.1 Degenerate examples

For examples like the equality-row JSON model, tableau and revised simplex may return different optimal `x, y` splits. That should not automatically make `consistent = false` if objective values and statuses agree.

### 8.2 Reduced costs

Reduced-cost differences should be reported but should not necessarily determine `consistent`, because degenerate bases may differ.

If a deterministic nondegenerate reduced-cost test already exists, leave that to regression tests.

------

## 9. Exit Code Requirements

The `compare` command should use:

```text
0 = comparison completed and consistent is true
1 = comparison completed but consistent is false, or model read/solve error prevents comparison
2 = argparse usage error
```

Examples:

```bash
silo compare examples/json/production.json
```

should return `0`.

```bash
silo compare examples/json/infeasible.json
```

should return `0` if both backends return `infeasible`.

A missing model file should return `1` and print a clear error to stderr.

------

## 10. Error Handling Requirements

### 10.1 Missing model path

If the model path does not exist:

```text
Error: model file not found: <path>
```

Return exit code `1`.

### 10.2 Invalid JSON or invalid model

If `read_json_model()` raises `ValueError`, print a clear error to stderr:

```text
Error: failed to read model: ...
```

Return exit code `1`.

### 10.3 One backend returns ERROR

If one backend returns `ERROR` and the other does not, output comparison JSON and return `1`.

If both return `ERROR`, then `status_match = true`; whether `consistent` is true can follow the general status rule. Prefer `consistent = true` if both statuses match and comparison completed.

------

## 11. Implementation Suggestions

Add a focused helper module:

```text
src/silo/cli/compare.py
```

Possible functions:

```python
def compare_backends(model_path: str | Path) -> dict[str, object]:
    ...

def comparison_to_json(payload: dict[str, object]) -> str:
    ...

def max_abs_diff(left: dict[str, float], right: dict[str, float]) -> float | None:
    ...

def solution_payload(solution: Solution) -> dict[str, object]:
    ...
```

Alternative structure is acceptable if readable.

Use:

```text
silo.utils.numerics.DEFAULT_TOLERANCE
```

for numeric comparisons.

Do not add a separate tolerance option in this first task unless it is trivial and tested. Default tolerance is enough.

------

## 12. Tests Required

Add:

```text
tests/unit/test_cli_compare.py
```

or an equivalent focused test file.

### 12.1 Compare production example

Test:

```bash
silo compare examples/json/production.json
```

Expected:

```text
exit code = 0
consistent = true
status_match = true
objective_match = true
tableau.status = optimal
revised.status = optimal
```

### 12.2 Compare `>=` example

Test:

```bash
silo compare examples/json/ge_row.json
```

Expected:

```text
exit code = 0
consistent = true
both statuses = optimal
objective_match = true
```

### 12.3 Compare equality example

Test:

```bash
silo compare examples/json/equality_row.json
```

Expected:

```text
exit code = 0
consistent = true
both statuses = optimal
objective_match = true
```

Do not require primal values to match exactly.

### 12.4 Compare infeasible example

Test:

```bash
silo compare examples/json/infeasible.json
```

Expected:

```text
exit code = 0
consistent = true
both statuses = infeasible
```

### 12.5 Output file

Test:

```bash
silo compare examples/json/production.json --output <tmp_path>/compare.json
```

Expected:

```text
exit code = 0
file exists
JSON contains required top-level fields
```

### 12.6 Missing path

Test missing model path.

Expected:

```text
exit code = 1
stderr contains "model file not found"
```

### 12.7 Solution schema

Test that both `tableau` and `revised` payloads include:

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

### 12.8 Existing CLI tests

Existing `solve` CLI tests must continue to pass.

Do not break `silo solve`.

------

## 13. Documentation Requirements

Create:

```text
docs/backend_compare.md
```

This document should explain:

```text
silo compare MODEL_PATH
silo compare MODEL_PATH --output compare.json
```

It should include:

1. purpose of comparison command;
2. what backends are compared;
3. meaning of `consistent`;
4. meaning of major `checks` fields;
5. why primal values may differ in degenerate LPs;
6. exit codes.

Keep it concise.

Update:

```text
docs/cli_solve.md
```

Add a short link or note pointing to `docs/backend_compare.md`.

Update:

```text
README.md
```

Only add a short mention if appropriate, such as:

```text
Use `silo compare MODEL_PATH` to compare tableau and revised native backends on the same JSON model.
```

Do not make README too long.

------

## 14. Execution Report

Create:

```text
tasks/reports/20260520-12-01_backend-compare_report.md
```

The report should include:

```markdown
# Backend Comparison Command Report

## Summary

## User-Facing Command

## Comparison Semantics

## Files Changed

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend one next step.

Likely candidates:

```text
Phase 4A: start presolve and scaling design note.
```

or:

```text
Phase 3I: add lightweight performance/regression timing for backend comparison.
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
python -m silo.cli.main compare examples/json/production.json
python -m silo.cli.main compare examples/json/ge_row.json
python -m silo.cli.main compare examples/json/equality_row.json
python -m silo.cli.main compare examples/json/infeasible.json
```

If the console script is available, also run:

```bash
silo --help
silo --version
silo compare examples/json/production.json
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
git commit -m "Add backend comparison command"
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

1. `tasks/codex/20260520-12-01_backend-compare.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `silo compare MODEL_PATH` command exists.
4. `silo compare examples/json/production.json` returns exit code `0`.
5. `silo compare examples/json/ge_row.json` returns exit code `0`.
6. `silo compare examples/json/equality_row.json` returns exit code `0`.
7. `silo compare examples/json/infeasible.json` returns exit code `0` when both backends agree on infeasibility.
8. Comparison JSON includes `model_path`, `consistent`, `tolerance`, `checks`, `tableau`, and `revised`.
9. Both solution payloads use the same schema as `silo solve`.
10. `--output` writes comparison JSON to file.
11. Missing file path returns exit code `1` with a clear stderr message.
12. Existing `silo solve` behavior is unchanged.
13. No solver algorithm scope is expanded.
14. No external solver dependency or call is introduced.
15. `docs/backend_compare.md` exists.
16. `tasks/reports/20260520-12-01_backend-compare_report.md` exists.
17. `pytest` passes.
18. `python scripts/check_quality.py` passes.
19. CLI help/version/solve/compare commands work.
20. A local commit is created with message:

```text
Add backend comparison command
```

1. The task is not pushed unless the user explicitly instructs Codex to push.
