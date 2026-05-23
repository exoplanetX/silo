# Codex Task: Upgrade SILO Development Operator to v0.2

## Task Metadata

Task ID: 20260524-03-01
Task slug: silo-dev-operator-v02
Task type: process-tooling
Related system: SILO-DOS / Codex skill workflow control
Risk level: L0 safe process-tooling
Git mode: local-commit
Expected report path: tasks/reports/20260524-03-01_silo-dev-operator-v02_report.md

## Objective

Upgrade `silo-development-operator` to v0.2 so SILO-DOS can reduce manual copying between
ChatGPT and Codex while preserving one-task-at-a-time safety, task ID scanning, scope
locks, reports, commits, push rules, and explicit phase-transition approvals.

Do not execute solver development work as part of this process-tooling task.

## Context

The current SILO-DOS workflow is stable and has successfully managed Phase 5 through
completion and closure bookkeeping. However, the current `silo-development-operator`
skill only issues one task and stops. This still requires too much manual coordination
between ChatGPT and Codex.

The user wants an upgraded skill that preserves safety while supporting controlled
automation modes:

- Mode A: `auto-one`
- Mode B: `review-gated`
- Mode C: `principal mode`

The upgrade must keep the existing SILO-DOS principles:

- one task at a time;
- immutable issued task files;
- task ID scan before issuance;
- scope locks;
- required reports;
- commit and push rules;
- no phase start without explicit user approval;
- no phase closure without explicit user approval.

Relevant inputs:

- `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md`
- `tasks/README.md`
- `AGENTS.md`
- recent reports under `tasks/reports/`

## Scope Lock

This task is atomic.

Primary objective:

- Update the local `silo-development-operator` skill instructions to v0.2 with explicit
  Mode A / Mode B / Mode C workflow control and risk classification rules.

Allowed changes:

- `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md`
- `tasks/reports/20260524-03-01_silo-dev-operator-v02_report.md`

Supporting allowed change:

- `tasks/codex/20260524-03-01_silo-dev-operator-v02.md` may be committed as the issued
  task contract for this execution.

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not start Phase 6.
- Do not issue Phase 6 implementation work.
- Do not create or execute any solver-development task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Skill Upgrade Content

Update `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md` to identify the
skill as v0.2 and define all three workflow modes.

### Mode A: auto-one

Define Mode A as the default daily development mode.

Mode A must:

- read required repository inputs;
- scan task IDs before issuing a task;
- generate exactly one task;
- classify task risk;
- auto-execute only eligible low-risk tasks;
- run required checks;
- create the required report;
- commit locally after checks pass when the task Git mode requires it;
- attempt push only when the task Git mode or explicit user instruction permits it;
- stop after one atomic task.

Mode A must never continue to a second task.

### Mode B: review-gated

Define Mode B as the mode for medium/high-risk changes and predefined review gates.

Mode B must:

- generate exactly one task;
- classify task risk;
- stop before predefined gates that need user review;
- use review gates for public contract changes, schema changes, algorithmic changes,
  phase-transition preparation, or any task whose scope cannot be verified safely;
- preserve task ID scan, scope lock, report, commit, and push rules.

### Mode C: principal mode

Define Mode C as the strategic planning mode.

Mode C must:

- convert the user's high-level solver design principles and phase goals into phase plans,
  scope boundaries, non-goals, and candidate atomic task sequences;
- avoid implementation execution;
- avoid modifying solver source code or tests unless a separate issued task later permits
  it;
- never execute code implementation.

## Required Risk Levels

The upgraded skill must define these risk levels:

### L0 safe

Includes:

- docs;
- reports;
- task-system cleanup;
- audits;
- bookkeeping;
- regression-test additions.

### L1 controlled implementation

Includes:

- narrow implementation tasks already backed by design notes and explicit acceptance
  criteria.

### L2 high-risk

Includes:

- solver core algorithms;
- LP/MIP search logic;
- public CLI contract;
- JSON schema;
- presolve;
- backend behavior.

### L3 strategic

Includes:

- phase start;
- phase closure;
- architecture redesign;
- new solver capability line.

## Required Execution Policy

The upgraded skill must state:

- Mode A may auto-execute L0 tasks.
- Mode A may auto-execute L1 tasks only when they are explicitly approved and backed by a
  design note plus acceptance criteria.
- Mode A must stop before executing L2 tasks.
- Mode A must stop before executing L3 tasks.
- Mode B must stop at review gates.
- Mode C must never execute implementation.
- All modes must preserve one-task-at-a-time execution.
- All modes must preserve task ID scan, scope lock, report, commit, and push rules.
- No mode may start a new phase without explicit user approval.
- No mode may close a phase without explicit user approval.
- No mode may silently expand a task after execution begins.
- If push fails, the local commit must be preserved and the failure must be reported and
  recorded in the report.

## Required Compatibility Behavior

The v0.2 skill must remain compatible with the current planning-only usage:

- If the user asks only to issue a task, the skill must issue exactly one task and stop.
- If the user asks to inspect a task, the skill must not execute it.
- If the user asks to execute a specific issued task, Codex should follow the issued task
  contract rather than inventing a new task.
- If the user does not specify a mode, the skill should default to Mode A only for future
  SILO-DOS runs that ask the operator to continue development. It should not retroactively
  execute tasks that were merely issued for inspection.

## Stop Conditions

Stop and report instead of proceeding if:

- the existing skill file cannot be read;
- the requested v0.2 behavior would contradict `tasks/README.md` or `AGENTS.md`;
- implementing v0.2 requires changing solver source code, tests, `ROADMAP.md`, phase
  files, or Phase 6 materials;
- the task-system rules need a repository rule change before the skill can be upgraded;
- the upgrade would remove one-task-at-a-time safety;
- unrelated dirty repository changes make the process-tooling scope ambiguous.

## Required Checks

Run at least:

```bash
git status --short
git diff --check
```

Also verify that:

```text
C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md
```

exists after the update and includes v0.2, Mode A, Mode B, Mode C, L0, L1, L2, and L3.

Do not run the full solver test suite unless executable project files are modified
unexpectedly. Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. The local `silo-development-operator` skill identifies itself as v0.2.
2. The skill defines Mode A: `auto-one`.
3. The skill defines Mode B: `review-gated`.
4. The skill defines Mode C: `principal mode`.
5. The skill defines risk levels L0, L1, L2, and L3 with the required categories.
6. The skill states the execution policy for all three modes.
7. The skill preserves one-task-at-a-time execution.
8. The skill preserves task ID scan, scope lock, report, commit, and push rules.
9. The skill states that no mode may start or close a phase without explicit user
   approval.
10. No solver source code is modified.
11. No tests are modified.
12. `ROADMAP.md` is not modified.
13. No phase files are modified.
14. Phase 6 is not started and no Phase 6 implementation task is issued.
15. A report is created at the expected report path.
16. `git diff --check` passes.

## Report Requirements

Create:

```text
tasks/reports/20260524-03-01_silo-dev-operator-v02_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Skill changes:
Risk policy added:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

The report must explicitly state that no solver source code, tests, `ROADMAP.md`, phase
files, or Phase 6 work were modified or created.

## Git Instructions

Git mode:

```text
local-commit
```

After successful skill update and checks:

```bash
git add tasks/codex/20260524-03-01_silo-dev-operator-v02.md tasks/reports/20260524-03-01_silo-dev-operator-v02_report.md
git add C:/Users/xuning/.codex/skills/silo-development-operator/SKILL.md
git commit -m "docs(tasks): upgrade SILO operator skill"
```

Do not push unless explicitly instructed by the user.

## Final Response

When finished, report only:

- whether the `silo-development-operator` skill was upgraded to v0.2;
- whether Mode A / Mode B / Mode C were added;
- whether L0 / L1 / L2 / L3 risk policy was added;
- whether checks passed;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.
