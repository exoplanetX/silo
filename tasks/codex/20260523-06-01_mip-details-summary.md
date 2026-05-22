# Codex Task: Implement MIP CLI Summary Diagnostics

## Task Metadata

Task ID: 20260523-06-01
Task slug: mip-details-summary
Task type: implementation
Related phase: Phase 5 / MIP branch-and-bound diagnostics
Git mode: push-on-success
Expected report path: tasks/reports/20260523-06-01_mip-details-summary_report.md

## Objective

Implement opt-in summary diagnostics for `silo mip-solve` using a `--details` flag while
preserving the existing compact default solution JSON output.

This task implements only the summary diagnostics contract designed in
`notes/17_mip_diagnostics_output_design.md`. It must not add detailed node-log output,
change the default `mip-solve` output shape, or change `silo solve` behavior.

## Context

Phase 5J designed the future MIP diagnostics output contract. The design recommends:

- default `silo mip-solve MODEL_PATH` continues to emit the existing solution JSON object;
- `silo mip-solve MODEL_PATH --details` emits a wrapper object with top-level `solution`
  and `diagnostics` objects;
- summary diagnostics include node counts, incumbent value, best bound, relative gap,
  termination reason, node limit, and LP relaxation backend name;
- detailed `node_log` output remains out of scope for the first implementation.

The current Python MIP API already exposes `BranchAndBoundSolver.solve_with_details()`,
which returns `solution`, `nodes_processed`, `nodes_created`, `nodes_pruned`,
`incumbent_value`, `best_bound`, `log`, and `status_message`.

Relevant files:

- `notes/17_mip_diagnostics_output_design.md`
- `src/silo/cli/main.py`
- `src/silo/cli/mip_solve.py`
- `src/silo/mip/branch_and_bound.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_cli_mip_solve.py`
- `tests/regression/test_mip_cli_regression_matrix.py`
- `docs/mip_solve_cli.md`

## Scope Lock

This task is atomic.

Primary objective:

- Add opt-in `--details` summary diagnostics to `silo mip-solve`.

Allowed changes:

- `src/silo/cli/main.py`
- `src/silo/cli/mip_solve.py`
- `tests/unit/test_cli.py`
- `tests/unit/test_cli_mip_solve.py`
- `tests/regression/test_mip_cli_regression_matrix.py`
- `docs/mip_solve_cli.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260523-06-01_mip-details-summary_report.md`

Supporting allowed change:

- `tasks/codex/20260523-06-01_mip-details-summary.md` may be committed as the issued task
  contract for this execution.

Forbidden changes:

- Do not modify branch-and-bound search logic.
- Do not modify LP solvers.
- Do not modify presolve.
- Do not modify JSON model schema.
- Do not modify the compact default solution JSON schema.
- Do not add detailed `node_log` output.
- Do not add cuts, heuristics, callbacks, branch-and-cut, MIP presolve, or external solver
  calls.
- Do not change `silo solve` semantics.
- Do not modify existing files under `tasks/codex/`.
- Do not enter Phase 6.

## Required Behavior

Add a `--details` flag to `silo mip-solve`.

Without `--details`, existing behavior must remain unchanged:

```bash
silo mip-solve examples/mip/binary_knapsack.json
```

continues to emit the compact solution JSON object with fields:

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

With `--details`, emit a wrapper object:

```json
{
  "solution": {
    "status": "optimal",
    "objective_value": 22.0,
    "primal_values": {
      "item_1": 0.0,
      "item_2": 1.0,
      "item_3": 1.0
    },
    "slack_values": {},
    "dual_values": {},
    "reduced_costs": {},
    "basis_status": {},
    "message": "Branch-and-bound solved the MIP."
  },
  "diagnostics": {
    "node_count": 0,
    "nodes_processed": 0,
    "nodes_created": 0,
    "nodes_pruned": 0,
    "incumbent_value": 22.0,
    "best_bound": 22.0,
    "relative_gap": 0.0,
    "termination_reason": "optimality_proven",
    "node_limit": 10000,
    "lp_solver": "tableau"
  }
}
```

The numeric values above are illustrative except for known example objective values and
status-derived fields. Implementation tests should assert deterministic values where the
current solver already provides them, but should avoid pretending that this task changes
branch-and-bound logic.

The diagnostics object must include:

- `node_count`
- `nodes_processed`
- `nodes_created`
- `nodes_pruned`
- `incumbent_value`
- `best_bound`
- `relative_gap`
- `termination_reason`
- `node_limit`
- `lp_solver`

Definitions:

- `node_count` must equal `nodes_processed`.
- `relative_gap` is `null` when either `incumbent_value` or `best_bound` is missing.
- Otherwise `relative_gap = abs(best_bound - incumbent_value) / max(1.0, abs(incumbent_value))`.
- For `optimal`, `termination_reason` must be `optimality_proven`.
- For `infeasible`, `termination_reason` must be `infeasible`.
- For `unbounded`, `termination_reason` must be `unbounded`.
- For `iteration_limit`, `termination_reason` must be `node_limit`.
- For `numerical_issue`, `termination_reason` must be `numerical_issue`.
- For `error`, `termination_reason` must be `error`.

The `--output` flag must write the selected output mode:

- compact solution JSON when `--details` is absent;
- wrapper JSON when `--details` is present.

## Stop Conditions

Stop and report instead of proceeding if:

- implementing `--details` requires changing branch-and-bound search behavior;
- implementing `--details` requires changing the compact default solution JSON schema;
- `BranchAndBoundSolver.solve_with_details()` lacks enough information for the required
  summary diagnostics;
- the existing CLI parser cannot support `--details` without altering unrelated command
  semantics;
- unrelated dirty repository changes appear and make the scope ambiguous.

## Required Checks

Run at least:

```bash
pytest tests/unit/test_cli.py tests/unit/test_cli_mip_solve.py
pytest tests/regression/test_mip_cli_regression_matrix.py
pytest
python scripts/check_quality.py
python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json --details
silo mip-solve examples/mip/binary_knapsack.json --details
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. `silo mip-solve --details` is accepted by the CLI parser.
2. Default `silo mip-solve` output remains the compact solution JSON object.
3. `--details` output has top-level `solution` and `diagnostics` objects.
4. The `solution` object inside the wrapper uses the same solution fields as compact
   output.
5. The `diagnostics` object includes every required summary field.
6. `node_count` equals `nodes_processed`.
7. Optimal MIP details report `termination_reason` as `optimality_proven`.
8. Infeasible MIP details report `termination_reason` as `infeasible` and keep exit code
   `1`.
9. Node-limit details report `termination_reason` as `node_limit` and keep status
   `iteration_limit`.
10. `relative_gap` is `0.0` for proven optimal examples when incumbent and bound are both
    available.
11. `--output` writes the wrapper when `--details` is present.
12. No detailed `node_log` appears in public CLI output.
13. `silo solve` and LP compare behavior remain unchanged.
14. No solver source code outside the CLI layer is modified.
15. `pytest` and `python scripts/check_quality.py` pass.
16. A report is created at the expected report path.

## Report Requirements

Create:

```text
tasks/reports/20260523-06-01_mip-details-summary_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Summary of implementation:
Diagnostics fields implemented:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

## Git Instructions

Git mode:

```text
push-on-success
```

After successful implementation and checks:

```bash
git add tasks/codex/20260523-06-01_mip-details-summary.md src/silo/cli/main.py src/silo/cli/mip_solve.py tests/unit/test_cli.py tests/unit/test_cli_mip_solve.py tests/regression/test_mip_cli_regression_matrix.py docs/mip_solve_cli.md tasks/phases/phase_05_branch_and_bound.md tasks/reports/20260523-06-01_mip-details-summary_report.md
git commit -m "feat(cli): add MIP summary diagnostics"
git push origin main
```

If push fails, preserve the local commit, record the failure in the report, and report the
failure clearly in the final response.

## Final Response

When finished, report only:

- whether `silo mip-solve --details` summary diagnostics were implemented;
- whether default `mip-solve` output remains unchanged;
- whether docs, tests, and report were updated;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
