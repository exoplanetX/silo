# SILO Codex Task: Research Brain Bridge

## Task Metadata

- Task ID: `20260607-07-01`
- Slug: `research-brain-bridge`
- Risk level: L3 strategic process-governance design
- Explicit approval: the user explicitly approved executing exactly one L3 design-only
  SILO-DOS v0.4 Research Brain Bridge Design task.
- Task type: SILO-DOS v0.4 process-governance design
- Mode: SILO-DOS Mode A auto-one
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260607-07-01_research-brain-bridge_report.md`

## Objective

Design how SILO-DOS v0.4 connects the repository-local `.silo-dos/` mirror with the
remote Research Brain as a long-term experience and decision-memory center.

## Design Goal

Define the dynamic decision chain:

```text
local .silo-dos mirror -> Research Brain query packet -> user decision
```

Define the experience flows:

```text
local reports / experience_map / decisions -> Research Brain export
Research Brain experience / phase playbooks -> local mirror preload
```

## Primary Inputs

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/self_evolution.md`
- `.silo-dos/local_skill_integration_design.md`
- `tasks/reports/20260606-01-01_silo-dos-v04-local-mirror-pilot_report.md`
- `tasks/reports/20260607-03-01_v04-smoke-test_report.md`
- `tasks/reports/20260607-06-01_v04-hard-stop-smoke_report.md`
- `tasks/README.md`
- `AGENTS.md`

## Scope Lock

This is a design-only and process-governance-only task. It must define how local
repository evidence, Research Brain experience, and user decisions interact without
implementing connector logic, changing task-system rules, changing solver behavior, or
starting any new phase.

## Required Design Coverage

The design note must cover:

1. Local mirror and Research Brain roles.
2. Decision Lookup Chain.
3. Research Brain Query Packet.
4. Research Brain Export Packet.
5. Research Brain Import / Preload Protocol.
6. Phase Entry Intelligence Preparation.
7. Experience Map extraction.
8. Degraded mode when Research Brain is unavailable.
9. Safety boundaries.
10. Non-goals.

## Allowed Changes

- `.silo-dos/research_brain_bridge.md`
- `tasks/codex/20260607-07-01_research-brain-bridge.md`
- `tasks/reports/20260607-07-01_research-brain-bridge_report.md`

## Forbidden Changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify existing `.silo-dos/` files.
- Do not modify existing notes.
- Do not modify `tasks/README.md`.
- Do not modify `AGENTS.md`.
- Do not modify the local `silo-development-operator` skill.
- Do not implement Google Drive or Research Brain connector logic.
- Do not write to Research Brain.
- Do not create templates yet.
- Do not start Phase 10.
- Do not close Phase 9.
- Do not implement native backend.
- Do not change CLI behavior.
- Do not change JSON schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection behavior.
- Do not issue or execute another task.

## Required Checks

Run at least:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
```

Also run `git diff --cached --check` before committing.

No solver tests are required unless executable files are unexpectedly modified. Do not
run native build commands or native tooling.

## Acceptance Criteria

- Exactly one L3 design-only task is issued and executed.
- The task ID uses the next available `20260607` task block and does not collide with
  existing task or report prefixes.
- `.silo-dos/research_brain_bridge.md` is created.
- The design note defines the local mirror, Research Brain, and user roles.
- The design note defines the Research Brain Query Packet.
- The design note defines the Research Brain Export Packet.
- The design note defines the Research Brain Import / Preload Protocol.
- The design note defines phase-entry intelligence preparation.
- The design note defines experience-map extraction from historical SILO reports.
- The design note defines degraded mode and safety boundaries.
- Forbidden files and behaviors are not changed.
- Required checks pass.
- Repository changes are committed locally.
- Push is attempted once after checks pass.
- Remote Sync Proof is recorded in the report or final response.

## Report Requirements

Create the matching report with:

- task objective;
- risk level and explicit approval;
- task ID scan result;
- files changed;
- local mirror files inspected;
- design summary;
- Research Brain bridge model;
- query, export, and import packet definitions;
- phase preload protocol;
- degraded mode behavior;
- safety boundaries;
- checks run and results;
- remote sync proof;
- commit hash, or a note that the final hash is recorded in the final response because
  the report is committed before the final commit hash exists;
- push result, or a note that the final push result is recorded in the final response
  after the push attempt;
- next recommended action.

## Stop Conditions

Stop and report if:

- the worktree is dirty before execution with unrelated files;
- `origin/main...HEAD` is not `0 0` before execution;
- a required `.silo-dos/` input is missing;
- task ID selection collides with an existing task or report prefix;
- completing the task would require forbidden file changes;
- completing the task would require Research Brain connector implementation;
- completing the task would require writing to Research Brain;
- completing the task would require solver source, tests, examples, roadmap, phase-file,
  local skill, task-system rule, CLI, schema, dependency, build, packaging, native
  backend, dispatch, or backend-selection changes;
- any required check fails;
- the task would need a second atomic objective.
