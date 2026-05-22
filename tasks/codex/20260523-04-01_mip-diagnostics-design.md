# Codex Task: Design MIP Solve Diagnostics Output

## Task Metadata

Task ID: 20260523-04-01
Task slug: mip-diagnostics-design
Task type: design-note
Related phase: Phase 5 / MIP branch-and-bound diagnostics
Git mode: local-commit
Expected report path: tasks/reports/20260523-04-01_mip-diagnostics-design_report.md

## Objective

Create a design note deciding whether and how `silo mip-solve` should expose node-count
and detailed branch-and-bound diagnostics.

This is a design-only task. Do not modify solver source code, CLI behavior, tests, JSON
schema, or solution output in this task.

## Pre-Issue Task ID Check

Before creating this task file or report, scan existing filenames under:

```text
tasks/codex/
tasks/reports/
```

If `20260523-04-01` already exists for a different slug, use the next available `TT`
value and update the task ID, task filename, report filename, and metadata consistently.

## Context

The MIP CLI regression matrix is now in place. It verifies public `silo mip-solve`
behavior through both module invocation and console-script invocation.

Current documentation still states that there is no MIP detailed JSON or node-count JSON
yet. The Phase 5 acceptance criteria mention clear node counts, incumbent value, and
final status. Before implementing diagnostics, SILO needs a design note that defines the
output contract.

Relevant files:

- `src/silo/mip/branch_and_bound.py`
- `src/silo/mip/node.py`
- `src/silo/mip/incumbent.py`
- `src/silo/cli/mip_solve.py`
- `docs/mip_solve_cli.md`
- `docs/lp_solver.md`
- `notes/15_branch_and_bound_design.md`
- `notes/16_mip_cli_exposure_design.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tests/regression/test_mip_cli_regression_matrix.py`

## Scope Lock

This task is atomic.

Primary objective:

- Create a design note for MIP solve diagnostics output.

Allowed changes:

- `notes/17_mip_diagnostics_output_design.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260523-04-01_mip-diagnostics-design_report.md`

Forbidden changes:

- Do not modify solver source code.
- Do not modify CLI implementation.
- Do not modify tests.
- Do not modify JSON model schema.
- Do not modify solution JSON schema.
- Do not add node-count output yet.
- Do not add detailed branch-and-bound JSON yet.
- Do not add cuts, heuristics, callbacks, branch-and-cut, or external solver calls.
- Do not modify existing files under `tasks/codex/`.
- Do not modify existing files under `tasks/phases/` except the allowed Phase 5 note above.
- Do not push to GitHub unless explicitly instructed by the user.

## Required Design Content

Create `notes/17_mip_diagnostics_output_design.md` with the following sections:

1. Purpose and motivation.
2. Current MIP CLI output contract.
3. Diagnostic information available or expected from branch-and-bound.
4. Recommended minimal diagnostic fields.
5. Whether diagnostics should be always included or opt-in.
6. Proposed JSON structure.
7. Backward compatibility considerations.
8. CLI flag design, if any.
9. Testing implications.
10. Out-of-scope items.

The design should explicitly discuss at least:

- `node_count`;
- `nodes_processed`;
- `incumbent_value`;
- `best_bound`;
- `relative_gap`;
- `termination_reason`;
- `node_limit`;
- whether to include a detailed `node_log`;
- whether detailed logs should be hidden behind a flag such as `--details`;
- whether the default solution JSON should remain compact.

## Acceptance Criteria

This task is complete only if:

1. `notes/17_mip_diagnostics_output_design.md` is created.
2. The note recommends a minimal diagnostics output contract.
3. The note discusses backward compatibility with existing solution JSON.
4. The note distinguishes compact default output from optional detailed diagnostics.
5. The note defines follow-up implementation tasks but does not implement them.
6. `tasks/phases/phase_05_branch_and_bound.md` is updated to mention Phase 5J design work.
7. No solver source code is modified.
8. No tests are modified.
9. No JSON schema or CLI behavior is changed.
10. A report is created at the expected report path.

## Required Checks

Run at least:

```bash
git status --short
git diff --check
```

Do not run solver tests for this design-only task.

## Report Requirements

Create:

```text
tasks/reports/20260523-04-01_mip-diagnostics-design_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Summary of design decisions:
Task ID pre-issue scan result:
Checks run:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

## Git Instructions

Default Git mode:

```text
local-commit
```

After completing the design note and report:

```bash
git add notes/17_mip_diagnostics_output_design.md tasks/phases/phase_05_branch_and_bound.md tasks/reports/20260523-04-01_mip-diagnostics-design_report.md
git commit -m "docs(mip): design diagnostics output contract"
```

Do not push unless the user explicitly requests it.

## Final Response

When finished, report only:

- whether the diagnostics design note was created;
- whether the Phase 5 note was updated;
- whether checks passed;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.
