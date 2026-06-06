# Task: SILO-DOS v0.4 Local Skill Integration Design

## Metadata

- Task ID: `20260607-01-01`
- Slug: `silo-dos-v04-local-skill-integration-design`
- Date: 2026-06-07
- Mode: review-gated design task
- Risk level: L3 strategic / process-governance design
- Task type: SILO-DOS process design
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260607-01-01_silo-dos-v04-local-skill-integration-design_report.md`

## Objective

Create a design note for integrating SILO-DOS v0.4 local mirror behavior into the local
`silo-development-operator` skill, without modifying the skill yet.

The design must specify how a future local skill upgrade should use `.silo-dos/` as the
primary repository-local decision mirror while preserving one-task-at-a-time execution,
risk gates, task ID scanning, report creation, commit/push rules, and user authority over
L2/L3 decisions.

## Context

SILO-DOS v0.4 now has a repository-local mirror under `.silo-dos/`:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/self_evolution.md`

The local mirror pilot audit concluded that `.silo-dos/` is usable as a local decision
mirror, while local skill v0.4 integration remains future work:

- `tasks/reports/20260606-01-01_silo-dos-v04-local-mirror-pilot_report.md`

The current local operator skill remains `silo-development-operator v0.3`. Updating that
skill is L3 process-governance work. This task is design-only and must not modify the
skill.

## Scope Lock

Solve exactly one primary problem:

```text
Design the future v0.4 local skill integration boundary.
```

Do not implement the integration. Do not modify the local skill. Do not start another
SILO task.

## Allowed Changes

- Create `.silo-dos/local_skill_integration_design.md`.
- Create the matching report:
  `tasks/reports/20260607-01-01_silo-dos-v04-local-skill-integration-design_report.md`.

## Forbidden Changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify existing notes.
- Do not modify existing `.silo-dos/` files.
- Do not create additional `.silo-dos/` files beyond
  `.silo-dos/local_skill_integration_design.md`.
- Do not modify `tasks/README.md`.
- Do not modify `AGENTS.md`.
- Do not modify existing task files under `tasks/codex/`.
- Do not modify the local `silo-development-operator` skill.
- Do not start Phase 10.
- Do not close Phase 9.
- Do not implement native backend.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection behavior.
- Do not change public CLI behavior.
- Do not change JSON model or solution schemas.
- Do not execute a second task.

## Required Design Content

The design note must cover:

1. Purpose of local skill v0.4 integration.
2. Why the current v0.3 skill is still too dependent on scattered repository inputs.
3. Required input lookup order:
   - current user instruction;
   - issued task contract, when executing a specific task;
   - `.silo-dos/project_profile.md`;
   - `.silo-dos/technical_route.md`;
   - `.silo-dos/decision_log.md`;
   - `.silo-dos/remote_sync_proof.md`;
   - `.silo-dos/standing_approval_profile.md`;
   - `.silo-dos/experience_map.md`;
   - `.silo-dos/self_evolution.md`;
   - `tasks/README.md`, `AGENTS.md`, `ROADMAP.md`, `tasks/phases/`, and recent reports;
   - Research Brain only when local mirror evidence is missing;
   - user decision for conflicts or L2/L3 gates.
4. Mode A behavior under v0.4.
5. Mode B behavior under v0.4.
6. Mode C behavior under v0.4.
7. Risk classification changes or confirmations for L0/L1/L2/L3.
8. Remote Sync Proof preflight and end-of-run behavior.
9. Standing Approval Profile interaction.
10. Decision Packet, Failure Packet, and Scope Expansion Packet behavior.
11. Self-Evolution Loop behavior, including when to propose future skill edits.
12. How to avoid circular or stale local mirror assumptions.
13. How to handle Research Brain vs local mirror disagreement.
14. Migration plan from v0.3 to v0.4.
15. v0.4 local skill integration non-goals.
16. Candidate follow-up atomic tasks.

## Required Report Content

The matching report must include:

- task objective;
- risk level;
- task ID scan result;
- files changed;
- local mirror files inspected;
- design note summary;
- whether the local skill was modified;
- whether solver source, tests, examples, CLI behavior, JSON schemas, roadmap, phase
  files, native backend, dependencies, build files, or dispatch behavior changed;
- checks run and results;
- deviations from scope, if any;
- git status before and after;
- remote sync proof;
- commit hash;
- push result;
- next recommended action.

## Required Checks

Run at least:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
```

Before committing, also run:

```text
git diff --cached --check
```

Do not run full solver tests because this task must not modify executable files. Do not
run native build commands or native tooling.

## Stop Conditions

Stop and report instead of proceeding if:

- the worktree is dirty before execution except for this task file after issuance;
- the task ID collides with an existing task/report prefix;
- completing the design requires modifying the local skill;
- completing the design requires modifying solver source, tests, examples, `ROADMAP.md`,
  phase files, existing notes, `tasks/README.md`, `AGENTS.md`, or existing `.silo-dos/`
  files;
- the design appears to approve actual v0.4 skill implementation rather than define a
  future review gate;
- Phase 9 closure, Phase 10 planning, Phase 10 implementation, or native implementation
  becomes necessary;
- required checks fail and the fix is outside the allowed files.

## Acceptance Criteria

- `.silo-dos/local_skill_integration_design.md` exists and is design-only.
- The design states that local skill edits remain a future L3 task requiring explicit
  approval.
- The design uses `.silo-dos/` as the primary local mirror without replacing
  `tasks/README.md`, `AGENTS.md`, `ROADMAP.md`, phase files, or issued task contracts.
- The design preserves Mode A/B/C, L0/L1/L2/L3 gates, one-task-at-a-time execution,
  remote sync proof, reports, commit/push rules, and packet behavior.
- The design explicitly preserves Phase 9 parked status, native implementation defer
  status, and Phase 10 not-started status.
- The matching report is created.
- Required checks pass.
- Only allowed files are changed.

## Final Response Requirements

Report only:

- task path;
- design note path;
- report path;
- whether the design task completed;
- whether the local skill was modified;
- checks run;
- commit hash;
- whether push succeeded;
- next recommended action.
