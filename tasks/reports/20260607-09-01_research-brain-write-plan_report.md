# Task Report: 20260607-09-01 Research Brain Write Plan

## Task Objective

Review `.silo-dos/research_brain_export_v1.md` and design a safe local write plan for
how that export should later be written into the remote Research Brain.

This task created a local plan only. It did not write to Google Drive, Research Brain,
external services, or any connector.

## Risk Level And Approval

- Risk level: L3 design-only process-governance write plan, executed as a scoped local
  documentation/process task.
- Approval: the user requested SILO-DOS Mode A auto-one and scoped this Research Brain
  Export Review and Write Plan task.
- Reason: the task designs a future external-memory write workflow. It does not perform
  the external write, modify solver behavior, change local skill behavior, change public
  contracts, start Phase 10, or implement native backend work.

## Task ID Scan Result

Existing `20260607-*` task/report prefixes before this task:

- `20260607-01-01_silo-dos-v04-local-skill-integration-design`
- `20260607-02-01_silo-dev-operator-v04`
- `20260607-03-01_v04-smoke-test`
- `20260607-04-01_v04-smoke-test-repeat`
- `20260607-05-01_v04-decision-chain-smoke`
- `20260607-06-01_v04-hard-stop-smoke`
- `20260607-07-01_research-brain-bridge`
- `20260607-08-01_research-brain-export-v1`

Selected and executed task ID:

- `20260607-09-01_research-brain-write-plan`

No collision was found.

## Files Changed

- `.silo-dos/research_brain_write_plan.md`
- `tasks/codex/20260607-09-01_research-brain-write-plan.md`
- `tasks/reports/20260607-09-01_research-brain-write-plan_report.md`

## Inputs Reviewed

- `.silo-dos/research_brain_export_v1.md`
- `.silo-dos/research_brain_bridge.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/self_evolution.md`
- `tasks/reports/20260607-08-01_research-brain-export-v1_report.md`
- `tasks/README.md`
- `AGENTS.md`

## Write-Readiness Assessment

The export packet is ready for user review, but not approved for direct external
writing. It is structured, source-linked, and clear about current SILO status, SILO-DOS
v0.4 rules, durable decisions, reusable patterns, phase playbooks, risk gates, failure
recovery patterns, and Research Brain bridge boundaries.

Stable long-term knowledge suitable for later Research Brain storage after user review:

- SILO-DOS v0.4 local mirror architecture.
- Local mirror vs Research Brain division of responsibility.
- Decision chain: local mirror -> Research Brain query packet -> user decision.
- L0/L1/L2/L3 risk gates and standing approval boundaries.
- Remote Sync Proof and push-failure recovery.
- Phase closure, phase parking, deferred implementation, and native implementation gate
  patterns.
- Design-only planning does not imply implementation approval.

Project-specific items that should remain primarily repo-local and be exported only as
context:

- exact SILO phase status;
- exact task/report ids;
- current Phase 9 parked route;
- selected native candidate `tableau_leaving_row_ratio_test`;
- native defer and Phase 10 not-started status;
- exact local `.silo-dos/` file paths and Git sync history.

User review is needed before any external write to choose final Research Brain target
structure, document format, manual vs connector-assisted workflow, level of detail, and
versioning cadence.

## Proposed Target Structure

Recommended Research Brain structure:

```text
Research Brain / Solver Development OS / SILO-DOS / Overview
Research Brain / Solver Development OS / SILO-DOS / Experience Maps
Research Brain / Solver Development OS / SILO-DOS / Decision Memory
Research Brain / Solver Development OS / Phase Playbooks
Research Brain / Solver Development OS / Risk Patterns
Research Brain / Solver Development OS / Failure Recovery Patterns
Research Brain / Solver Development OS / Project Profiles / SILO
```

The plan also suggests related slots for Remote Sync Proof, Standing Approval Profiles,
Research Brain Bridge, and Import Preload Protocols. These are proposed names only; no
external location was created or modified.

## Document Split Plan

Recommended split:

```text
one master overview + several focused Research Brain documents
```

Recommended focused entries:

- `SILO-DOS v0.4 Overview`
- `SILO Solver Reference Milestone Summary`
- `Experience Map`
- `Decision Memory`
- `Phase Playbooks`
- `Risk and Gate Patterns`
- `Failure and Recovery Patterns`
- `Research Brain Bridge Protocol`
- `Import / Preload Protocol`

The master overview should link the focused entries rather than duplicate all content.

## Write Order

Recommended write order:

1. `SILO-DOS v0.4 Overview`.
2. `SILO Solver Reference Milestone Summary`.
3. `Experience Map`.
4. `Decision Memory`.
5. `Phase Playbooks`.
6. `Risk and Gate Patterns`.
7. `Failure and Recovery Patterns`.
8. `Research Brain Bridge Protocol`.
9. `Import / Preload Protocol`.

## Manual Vs Connector-Assisted Workflow

Manual workflow is safest for the first write because the user controls target structure,
content, and destination. It avoids accidental external writes and avoids treating this
plan as connector approval.

Connector-assisted workflow should be used only in a later scoped task that explicitly
allows external connector use and identifies the exact target documents to create. The
connector task must still record local proof, preserve `.silo-dos/` as execution source
of truth, and never let Research Brain content override local route or approval gates.

## Metadata Schema

Each Research Brain entry should include:

```text
title:
category:
source_repository:
source_report_ids:
source_silo_dos_files:
version:
date:
status:
update_trigger:
related_decisions:
related_phases:
transferability:
scope:
non_goals:
safety_boundaries:
local_source_of_truth:
```

## Versioning And Update Policy

Use sequential export versions such as:

```text
SILO-DOS-RB-EXPORT-V1
SILO-DOS-RB-EXPORT-V2
SILO-DOS-RB-EXPORT-V3
```

Regenerate or revise Research Brain entries when a phase starts or closes, Phase 9 moves
out of parked state, Phase 10 planning starts, native implementation is approved,
rejected, or permanently parked, the local skill changes, `.silo-dos/` structure changes,
standing approval changes, repeated failures create a new high-confidence recovery
pattern, or Research Brain import/preload workflow is implemented or revised.

To avoid stale advice, Research Brain entries should point back to repo files and
reports, include update triggers, and be checked against current
`.silo-dos/technical_route.md` before use.

## Safety Boundaries

Research Brain advice must not override:

- explicit user instruction;
- issued task contracts;
- `tasks/README.md`;
- `AGENTS.md`;
- `.silo-dos/technical_route.md`;
- `.silo-dos/decision_log.md`;
- `.silo-dos/standing_approval_profile.md`;
- `.silo-dos/remote_sync_proof.md`;
- L2/L3 gates;
- one-task-at-a-time execution;
- allowed and forbidden file lists;
- required checks;
- current local Git sync state.

Research Brain advice must not silently approve phase start, phase closure, native
implementation, dependency/build/packaging changes, solver dispatch or backend selector
changes, public CLI changes, JSON schema changes, solver behavior changes, local skill
edits, task-system rule changes, or Phase 10 work.

## Recommended Next Action

Pause and wait for user review.

The export is ready for user review. Direct external writing should not happen
automatically. If the user later approves writing to Research Brain, create several
focused entries plus one overview. `.silo-dos/` remains the repository-local execution
source of truth.

No immediate solver task is required. No Phase 10 work is approved. Native
implementation remains deferred and unapproved.

## Checks Run And Results

- `git status --short` - passed; output showed only the expected scoped files:

```text
?? .silo-dos/research_brain_write_plan.md
?? tasks/codex/20260607-09-01_research-brain-write-plan.md
?? tasks/reports/20260607-09-01_research-brain-write-plan_report.md
```

- `git branch --show-current` - passed; branch `main`.
- `git log --oneline -5` - passed:

```text
d8f122c docs(silo-dos): add research brain export packet
647c30a docs(silo-dos): design research brain bridge
7e13454 docs(tasks): smoke test v04 hard stops
f6532a6 docs(tasks): smoke test v04 decision chain
5060048 docs(tasks): repeat silo dos v04 smoke test
```

- `git rev-list --left-right --count origin/main...HEAD` - passed; output `0 0`.
- `git diff --check` - passed; no output.
- `git diff --cached --check` - passed after staging; no output.

No full solver tests were run because this task did not modify executable files. No
native build commands or native tooling were run.

## Remote Sync Proof

Pre-execution proof:

- `git status --short`: clean before task artifacts were created.
- `git branch --show-current`: `main`.
- `git log --oneline -5`: latest commit before execution was
  `d8f122c docs(silo-dos): add research brain export packet`.
- `git rev-list --left-right --count origin/main...HEAD`: `0 0`.
- `git push result`: not attempted before execution.
- `remote_sync_status`: `synchronized_with_origin`.

Post-push-attempt proof before recording this failure in the report:

- `git status --short`: clean.
- `git branch --show-current`: `main`.
- `git log --oneline -5`:

```text
d00d504 docs(silo-dos): plan research brain write workflow
d8f122c docs(silo-dos): add research brain export packet
647c30a docs(silo-dos): design research brain bridge
7e13454 docs(tasks): smoke test v04 hard stops
f6532a6 docs(tasks): smoke test v04 decision chain
```

- `git rev-list --left-right --count origin/main...HEAD`: `0 1`.
- `git push result`: failed.
- `remote_sync_status`: `push_failed`.

## Deviations From Scope

None.

## Boundary Status

- No solver source code was modified.
- No tests were modified.
- No examples were modified.
- `ROADMAP.md` was not modified.
- Files under `tasks/phases/` were not modified.
- Existing `.silo-dos/` files were not modified; only
  `.silo-dos/research_brain_write_plan.md` was added.
- Existing notes were not modified.
- The local `silo-development-operator` skill was not modified.
- Phase 10 was not started.
- Native backend was not implemented.
- CLI behavior was not changed.
- JSON schemas were not changed.
- Dependencies were not added.
- Build and packaging files were not modified.
- Solver dispatch and backend selection behavior were not changed.
- No write to Google Drive, Research Brain, or external services was attempted.
- No connector call was made.
- No second task was issued or executed.

## Commit Hash

Initial local commit before recording push failure:

```text
d00d504 docs(silo-dos): plan research brain write workflow
```

The final amended commit hash is recorded in the final response.

## Push Result

Push failed:

```text
fatal: unable to access 'https://github.com/exoplanetX/silo.git/': Failed to connect to github.com port 443 after 21098 ms: Couldn't connect to server
```

The local commit is preserved. Start with sync-only recovery before another development
task unless the user explicitly approves continuing despite `push_failed`.

## Next Recommended Action

Pause for user review of `.silo-dos/research_brain_write_plan.md`.

Before starting another development task, run a sync-only recovery or verify that
`origin/main...HEAD` returns `0 0`.
