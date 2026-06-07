# Task Report: 20260607-07-01 Research Brain Bridge

## Task Objective

Design how SILO-DOS v0.4 connects the repository-local `.silo-dos/` mirror with the
remote Research Brain as a long-term experience and decision-memory center.

The design defines:

```text
local .silo-dos mirror -> Research Brain query packet -> user decision
```

and:

```text
local reports / experience_map / decisions -> Research Brain export
Research Brain experience / phase playbooks -> local mirror preload
```

## Risk Level And Explicit Approval

- Risk level: L3 strategic process-governance design.
- Explicit approval: the user explicitly approved executing exactly one L3 design-only
  SILO-DOS v0.4 Research Brain Bridge Design task.
- Execution mode: SILO-DOS Mode A auto-one.
- Git mode: `push-on-success`.

Reason for L3 classification: the task designs how local repository memory, Research
Brain memory, and user decision gates interact. It is process-governance architecture,
even though it does not modify solver behavior or task-system rules.

## Task ID Scan Result

Existing `20260607-*` task/report prefixes before this task:

- `20260607-01-01_silo-dos-v04-local-skill-integration-design`
- `20260607-02-01_silo-dev-operator-v04`
- `20260607-03-01_v04-smoke-test`
- `20260607-04-01_v04-smoke-test-repeat`
- `20260607-05-01_v04-decision-chain-smoke`
- `20260607-06-01_v04-hard-stop-smoke`

Selected and executed task ID:

- `20260607-07-01_research-brain-bridge`

No collision was found.

## Files Changed

- `.silo-dos/research_brain_bridge.md`
- `tasks/codex/20260607-07-01_research-brain-bridge.md`
- `tasks/reports/20260607-07-01_research-brain-bridge_report.md`

## Local Mirror Files Inspected

Primary local mirror files inspected:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/self_evolution.md`
- `.silo-dos/local_skill_integration_design.md`

Recent reports inspected:

- `tasks/reports/20260606-01-01_silo-dos-v04-local-mirror-pilot_report.md`
- `tasks/reports/20260607-03-01_v04-smoke-test_report.md`
- `tasks/reports/20260607-06-01_v04-hard-stop-smoke_report.md`

Supporting rule files inspected:

- `tasks/README.md`
- `AGENTS.md`

## Design Summary

Created `.silo-dos/research_brain_bridge.md` as a design-only bridge between local
SILO-DOS repository memory and remote Research Brain memory.

The design states that:

- `.silo-dos/` is the repository-local execution mirror.
- Research Brain is the long-term experience center.
- Research Brain is not a hard dependency for every task.
- Research Brain can propose, compare, and recall, but cannot approve repository
  execution.
- The user remains the final authority for unresolved decisions and all L2/L3 gates.
- Durable user decisions should later be mirrored into `.silo-dos/` and exported to
  Research Brain when appropriate.

## Research Brain Bridge Model

The bridge model has three layers:

1. Local mirror lookup. Codex first checks current user instruction, issued task
   contract, `.silo-dos/`, `tasks/README.md`, `AGENTS.md`, recent reports, and source
   notes.
2. Research Brain query. If local evidence is missing, stale, conflicting, or too narrow
   for a strategic decision, Codex prepares a Research Brain Query Packet.
3. User decision. If Research Brain cannot resolve the decision, or if Research Brain
   conflicts with repository-local evidence, Codex stops for a user Decision Packet.

Execution remains repository-local. Research Brain advice becomes durable only through a
later scoped repository task.

## Query, Export, And Import Packet Definitions

The design defines a Research Brain Query Packet with these fields:

- `decision_question`
- `current_phase_or_corridor`
- `task_objective`
- `risk_classification`
- `files_likely_to_change`
- `local_mirror_lookup_result`
- `missing_evidence`
- `requested_research_brain_experience`
- `candidate_options`
- `recommended_fallback_if_unavailable`
- `safety_boundaries`
- `local_artifact_to_update_if_resolved`

The design defines a Research Brain Export Packet with these fields:

- `export_subject`
- `source_repository`
- `source_files`
- `phase_or_corridor`
- `task_ids_or_report_ids`
- `decision_ids`
- `experience_patterns`
- `risk_patterns`
- `failure_or_recovery_patterns`
- `milestone_or_phase_lessons`
- `standing_approval_candidates`
- `local_boundaries`
- `recommended_research_brain_tags`
- `not_for_export`

The design defines a Research Brain Preload Packet with these fields:

- `preload_context`
- `target_project_or_phase`
- `local_project_state`
- `user_strategic_goal`
- `relevant_prior_projects`
- `phase_playbooks`
- `known_risk_patterns`
- `standing_approval_candidates`
- `failure_recovery_patterns`
- `recommended_local_mirror_updates`
- `items_requiring_user_decision`
- `items_to_ignore_for_this_project`

## Phase Preload Protocol

Before starting a new phase or new solver project, the design requires a preload step
that combines:

- local project state from `.silo-dos/`, `ROADMAP.md`, `tasks/phases/`, reports, and
  notes;
- Research Brain prior experience, including phase playbooks and known failure modes;
- the user's current strategic goals and risk tolerance.

The preload output should be a local proposal or phase-entry decision packet, not
immediate implementation. A repository update requires a scoped task unless the current
task explicitly allows the target local mirror file.

## Degraded Mode Behavior

When Research Brain is unavailable:

- the local mirror remains authoritative for repository execution;
- Codex may continue only inside the approved local technical route;
- L0/L1 work may proceed only when `.silo-dos/`, the issued task contract, and Remote
  Sync Proof are sufficient;
- uncertain strategic decisions fall back to a user Decision Packet;
- no L2/L3 movement may proceed based on missing Research Brain access;
- Research Brain import/export is skipped and recorded as unavailable when relevant.

## Safety Boundaries

The design states that Research Brain advice must not override:

- explicit user instruction;
- an issued task contract;
- `tasks/README.md`;
- `AGENTS.md`;
- `.silo-dos/technical_route.md`;
- `.silo-dos/decision_log.md`;
- `.silo-dos/standing_approval_profile.md`;
- `.silo-dos/remote_sync_proof.md`;
- L2 and L3 hard stops;
- one-task-at-a-time execution;
- allowed and forbidden file lists;
- required checks and stop conditions.

It also states that Research Brain must not silently approve phase starts, phase
closures, native implementation, dependencies, build or packaging changes, solver
dispatch, public CLI changes, JSON schema changes, solver behavior changes, local skill
edits, or task-system rule changes.

## Checks Run And Results

- `git status --short` - passed; output showed only the expected scoped files:

```text
?? .silo-dos/research_brain_bridge.md
?? tasks/codex/20260607-07-01_research-brain-bridge.md
?? tasks/reports/20260607-07-01_research-brain-bridge_report.md
```

- `git branch --show-current` - passed; branch `main`.
- `git log --oneline -5` - passed; latest commit before this task was
  `7e13454 docs(tasks): smoke test v04 hard stops`.
- `git rev-list --left-right --count origin/main...HEAD` - passed; output `0 0` before
  this task created a repository commit.
- `git diff --check` - passed.

`git diff --cached --check` is run after staging; final response records the result.

No solver tests were run because this task did not modify executable files. No native
build commands or native tooling were run.

## Deviations From Scope

None.

## Boundary Status

- Solver source code was not modified.
- Tests were not modified.
- Examples were not modified.
- `ROADMAP.md` was not modified.
- Files under `tasks/phases/` were not modified.
- Existing `.silo-dos/` files were not modified.
- Existing notes were not modified.
- `tasks/README.md` was not modified.
- `AGENTS.md` was not modified.
- The local `silo-development-operator` skill was not modified.
- Research Brain connector logic was not implemented.
- No write to Research Brain was attempted.
- No templates were created.
- Phase 10 was not started.
- Phase 9 was not closed.
- Native backend was not implemented.
- CLI behavior was not changed.
- JSON schemas were not changed.
- Dependencies were not added.
- Build and packaging files were not modified.
- Solver dispatch and backend selection behavior were not changed.
- No second task was issued or executed.

## Remote Sync Proof

Pre-execution proof:

- `git status --short`: clean.
- `git branch --show-current`: `main`.
- `git log --oneline -5`: latest commit before execution was
  `7e13454 docs(tasks): smoke test v04 hard stops`.
- `git rev-list --left-right --count origin/main...HEAD`: `0 0`.
- `git push result`: not attempted before execution.
- `remote_sync_status`: `synchronized_with_origin`.

Final proof is recorded after checks, commit, and push attempt.

## Commit Hash

Final commit hash is recorded in the final response because the report is committed
before the final commit hash exists.

## Push Result

Push is attempted after checks pass and the local commit is created. Final push result is
recorded in the final response.

## Next Recommended Action

No immediate next task is required.

If the user later wants to operationalize the bridge, the next separate candidate is a
design or connector-specific task for Research Brain tooling. That would require a new
explicit scope and must not be inferred from this design-only task.
