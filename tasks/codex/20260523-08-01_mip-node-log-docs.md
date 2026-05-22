# Codex Task: Document MIP Node-Log CLI Examples

## Task Metadata

Task ID: 20260523-08-01
Task slug: mip-node-log-docs
Task type: documentation
Related phase: Phase 5 / MIP branch-and-bound diagnostics
Git mode: local-commit
Expected report path: tasks/reports/20260523-08-01_mip-node-log-docs_report.md

## Objective

Add a concise user-facing documentation example for `silo mip-solve --details --node-log`
and `--output`, including one representative node-log entry shape, without changing solver
source code, tests, CLI behavior, JSON schemas, or branch-and-bound logic.

## Context

The latest completed task, `20260523-07-01_mip-node-log`, added optional node-log
diagnostics behind:

```bash
silo mip-solve MODEL_PATH --details --node-log
```

The implementation preserves:

- default compact `silo mip-solve MODEL_PATH` solution JSON;
- summary-only `silo mip-solve MODEL_PATH --details` output without `node_log`;
- node-log output only when both `--details` and `--node-log` are present.

The latest report recommends a small documentation follow-up before a broader Phase 5
completion audit. This task should make the new output mode easier to discover and use
without adding new behavior.

Relevant files:

- `docs/mip_solve_cli.md`
- `notes/17_mip_diagnostics_output_design.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260523-07-01_mip-node-log_report.md`

## Scope Lock

This task is atomic.

Primary objective:

- Document the implemented `--details --node-log` CLI workflow and output-file behavior.

Allowed changes:

- `docs/mip_solve_cli.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260523-08-01_mip-node-log-docs_report.md`

Supporting allowed change:

- `tasks/codex/20260523-08-01_mip-node-log-docs.md` may be committed as the issued task
  contract for this execution.

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify CLI behavior.
- Do not modify branch-and-bound search logic.
- Do not modify node ordering, pruning rules, incumbent updates, LP solvers, or presolve.
- Do not modify JSON model schema.
- Do not modify compact solution JSON schema.
- Do not add generated JSON output files to git.
- Do not enter Phase 6.
- Do not modify existing files under `tasks/codex/`.

## Required Documentation Content

Update `docs/mip_solve_cli.md` to include:

1. A short example command for stdout node-log output:

```bash
silo mip-solve examples/mip/binary_knapsack.json --details --node-log
```

2. A short example command for writing node-log wrapper JSON:

```bash
silo mip-solve examples/mip/binary_knapsack.json --details --node-log --output outputs/knapsack_node_log.json
```

3. A representative single node-log entry shape containing only the stable public fields:

```json
{
  "node_id": 0,
  "depth": 0,
  "lp_status": "optimal",
  "lp_objective": 24.0,
  "prune_reason": "not_pruned",
  "branching_variable": "item_3",
  "incumbent_value": null,
  "message": "Branched on first fractional integer-restricted variable."
}
```

4. A brief note that the exact node log is deterministic for the current implementation but
should be treated as diagnostic trace output, not as a stable mathematical solution field.

5. A brief note that generated files under `outputs/` remain local run artifacts and should
not be committed.

Update `tasks/phases/phase_05_branch_and_bound.md` with a one-sentence Phase 5M note that
records the documentation follow-up.

## Stop Conditions

Stop and report instead of proceeding if:

- documenting the example requires changing CLI behavior;
- documenting the example requires changing tests or solver source code;
- the current node-log output contradicts the intended example shape;
- unrelated dirty repository changes appear and make documentation scope ambiguous.

## Required Checks

Run at least:

```bash
git status --short
python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json --details --node-log
silo mip-solve examples/mip/binary_knapsack.json --details --node-log
git diff --check
```

Do not run the full solver test suite unless the documentation change unexpectedly touches
executable files. Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. `docs/mip_solve_cli.md` documents `--details --node-log` stdout usage.
2. `docs/mip_solve_cli.md` documents `--details --node-log --output` usage.
3. The documentation includes one representative node-log entry shape with the public
   fields only.
4. The documentation states that generated `outputs/` files should not be committed.
5. `tasks/phases/phase_05_branch_and_bound.md` records the Phase 5M documentation step.
6. No solver source code is modified.
7. No tests are modified.
8. No generated JSON output files are committed.
9. `git diff --check` passes.
10. A report is created at the expected report path.

## Report Requirements

Create:

```text
tasks/reports/20260523-08-01_mip-node-log-docs_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Documentation updates:
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
local-commit
```

After successful documentation updates and checks:

```bash
git add tasks/codex/20260523-08-01_mip-node-log-docs.md docs/mip_solve_cli.md tasks/phases/phase_05_branch_and_bound.md tasks/reports/20260523-08-01_mip-node-log-docs_report.md
git commit -m "docs(cli): add MIP node-log examples"
```

Do not push unless explicitly instructed by the user.

## Final Response

When finished, report only:

- whether node-log CLI examples were documented;
- whether the Phase 5 note was updated;
- whether checks passed;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.
