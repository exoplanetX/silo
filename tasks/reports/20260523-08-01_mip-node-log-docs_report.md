# MIP Node-Log Docs Report

Task ID: 20260523-08-01

Objective: Document `silo mip-solve --details --node-log` stdout and `--output` usage
with one representative node-log entry shape, without changing solver source code, tests,
CLI behavior, JSON schemas, or branch-and-bound logic.

Files changed:

- `tasks/codex/20260523-08-01_mip-node-log-docs.md`
- `docs/mip_solve_cli.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260523-08-01_mip-node-log-docs_report.md`

Documentation updates:

- Added a stdout command example for `silo mip-solve examples/mip/binary_knapsack.json
  --details --node-log`.
- Added an output-file command example for `silo mip-solve examples/mip/binary_knapsack.json
  --details --node-log --output outputs/knapsack_node_log.json`.
- Added one representative node-log entry shape with the stable public fields only.
- Clarified that node logs are deterministic diagnostic trace output, not stable
  mathematical solution fields.
- Preserved the existing note that generated files under `outputs/` are local run
  artifacts and should not be committed.
- Added the Phase 5M documentation follow-up note.

Checks run:

- `git status --short`
- `python -m silo.cli.main mip-solve examples/mip/binary_knapsack.json --details --node-log`
- `silo mip-solve examples/mip/binary_knapsack.json --details --node-log`
- `git diff --check`

Results:

- Both node-log CLI commands returned wrapper JSON with `diagnostics.node_log`.
- The representative entry in the documentation matches the current first node-log entry
  shape for the binary knapsack example.
- `git diff --check` passed.
- No solver source code, tests, CLI behavior, JSON schemas, or generated JSON output files
  were modified or added.

Git status before:

```text
?? tasks/codex/20260523-08-01_mip-node-log-docs.md
```

Git status after:

```text
 M docs/mip_solve_cli.md
 M tasks/phases/phase_05_branch_and_bound.md
?? tasks/codex/20260523-08-01_mip-node-log-docs.md
?? tasks/reports/20260523-08-01_mip-node-log-docs_report.md
```

Local commit hash:

```text
Created locally; the final response records the amended commit hash.
```

Push attempted:

```text
Yes. Two push attempts failed because GitHub could not be reached over port 443. The local
commit is preserved and remains ahead of `origin/main`.
```

Issues or conflicts:

- The issued task Git mode is `local-commit`, but the user explicitly requested push if
  possible for this execution.
- No unrelated dirty repository changes were present before implementation.

Next recommended atomic task:

Run a Phase 5 completion audit to decide whether Phase 5 is complete enough to close or
whether one more narrow stabilization task is needed before considering Phase 6.
