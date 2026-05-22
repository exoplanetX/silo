# MIP Diagnostics Design Report

Task ID: 20260523-04-01

Objective: Create a design note for future `silo mip-solve` diagnostics output without modifying solver source code, CLI behavior, tests, JSON model schema, or solution JSON schema.

Files changed:

- `notes/17_mip_diagnostics_output_design.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260523-04-01_mip-diagnostics-design_report.md`

Summary of design decisions:

- Keep default `silo mip-solve` output as the existing compact solution JSON.
- Make diagnostics opt-in through a future flag such as `--details`.
- Recommend a wrapper output under `--details` with top-level `solution` and `diagnostics` objects.
- Recommend minimal summary diagnostics: `node_count`, `nodes_processed`, `nodes_created`, `nodes_pruned`, `incumbent_value`, `best_bound`, `relative_gap`, `termination_reason`, `node_limit`, and `lp_solver`.
- Define `node_count` as a user-facing alias for `nodes_processed`.
- Keep detailed `node_log` out of default output and out of the first summary diagnostics contract.
- Reserve node logs for a later explicit flag such as `--node-log` or a level-valued details mode.
- Treat diagnostics strings such as `optimality_proven` and `node_limit` as output diagnostics, not new solver statuses.
- Leave LP `solve` and `compare` outputs unchanged.

Task ID pre-issue scan result:

- Existing `tasks/codex/` filenames for 2026-05-23 were scanned.
- `20260523-04-01` exists as the current provided task file: `tasks/codex/20260523-04-01.md`.
- No existing report was found for `20260523-04-01`.
- The provided task file name lacks the slug required by `tasks/README.md`, but this execution did not rename or modify it because files under `tasks/codex/` are immutable and outside the allowed change list.
- The report path `tasks/reports/20260523-04-01_mip-diagnostics-design_report.md` does not collide with an existing report.

Checks run:

- `git status --short`
- `git diff --check`

Git status before:

```text
?? tasks/codex/20260523-04-01.md
```

Git status after:

```text
 M tasks/phases/phase_05_branch_and_bound.md
?? notes/17_mip_diagnostics_output_design.md
?? tasks/codex/20260523-04-01.md
?? tasks/reports/20260523-04-01_mip-diagnostics-design_report.md
```

Local commit hash:

```text
Pending local commit creation; the final response records the created hash.
```

Push attempted:

```text
Pending local commit creation. The user has previously requested automatic push after task execution when possible; the final response records whether push completed or failed.
```

Issues or conflicts:

- The task file was present as an untracked file before execution and remains untracked because the task allowed changes do not include `tasks/codex/`.
- No solver source code, CLI implementation, tests, JSON model schema, or solution JSON schema was modified.
- Solver tests were intentionally not run because the task explicitly required only `git status --short` and `git diff --check` and said not to run solver tests.

Next recommended atomic task:

Implement `silo mip-solve --details` summary diagnostics using the wrapper contract from `notes/17_mip_diagnostics_output_design.md`, while keeping default `silo mip-solve` output unchanged.
