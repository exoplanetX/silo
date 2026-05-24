# Codex Task: Upgrade SILO-DOS Operator to v0.3

## Task Metadata

Task ID: 20260524-12-01
Task slug: silo-dos-v03-decision-packets
Task type: process-tooling
Related system: SILO-DOS / silo-development-operator
Risk level: L0 safe process-tooling
Git mode: local-commit
Expected report path: tasks/reports/20260524-12-01_silo-dos-v03-decision-packets_report.md

## Objective

Upgrade the local `silo-development-operator` skill to v0.3 so SILO-DOS automatically
produces structured decision packets whenever it stops at a risk gate, test failure, or
scope-expansion boundary.

The purpose is to reduce manual diagnosis and copying between Codex and ChatGPT while
preserving one-task-at-a-time safety and explicit user approval for high-risk actions.

Do not modify solver source code, tests, roadmap, phase files, or any Phase 6/Phase 7
implementation work.

## Pre-Issue Task ID Check

Before creating this task file or report, scan existing filenames under:

```text
tasks/codex/
tasks/reports/
```

If `20260524-12-01` already exists for a different slug, use the next available `TT`
value and update the task ID, task filename, report filename, and metadata consistently.

## Context

SILO-DOS v0.2 already supports:

- Mode A: auto-one
- Mode B: review-gated
- Mode C: principal mode
- L0 / L1 / L2 / L3 risk classification
- one-task-at-a-time execution
- task ID scanning
- scope locks
- report, commit, and push rules
- explicit approval for phase starts and closures

Recent use showed that Mode A correctly stops before L2/L3 tasks, but the user still has
to manually ask Codex for a decision packet. v0.3 should make such packets automatic.

The latest Phase 6 completion audit concluded `ready_for_user_closure_review`, but this
task must not close Phase 6 and must not start Phase 7.

## Scope Lock

This task is atomic.

Primary objective:

- Update the local `silo-development-operator` skill to v0.3 with automatic
  decision-packet behavior.

Allowed changes:

- `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md`
- `tasks/reports/20260524-12-01_silo-dos-v03-decision-packets_report.md`

Supporting allowed change:

- `tasks/codex/20260524-12-01_silo-dos-v03-decision-packets.md`

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify CLI behavior.
- Do not modify JSON schemas.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not close Phase 6.
- Do not start Phase 7.
- Do not issue Phase 7 tasks.
- Do not create or execute any solver-development task.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required v0.3 Skill Additions

Update `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md` to identify
the skill as v0.3 and preserve all v0.2 behavior.

Add the following required behavior.

### 1. Automatic Decision Packet for L2/L3 Gates

Whenever Mode A or Mode B stops because a task is classified as L2 or L3, the skill must
automatically output a structured decision packet.

The user should not need to ask separately for a decision packet.

The packet must include:

```text
Decision Packet

Task:
Risk level:
Why stopped:
Likely files:
Behavior/invariants that must remain unchanged:
Required no-regression tests:
Possible failure modes:
Recommended option: approve / revise / reject
Exact approval sentence:
```

The skill may recommend approve, revise, or reject, but it must not self-approve L2 or L3
execution.

### 2. Failure Packet for Failed Checks

If required checks fail during task execution, the skill must stop before expanding scope
and output:

```text
Failure Packet

Task:
Failing command:
Failure summary:
Likely cause:
Is the fix inside current scope?
Fix risk level:
Recommended action:
Exact approval sentence if scope expansion is needed:
```

The skill must not silently broaden the task to fix failures outside the issued scope.

### 3. Scope Expansion Packet

If completing a task appears to require modifying forbidden files or changing forbidden
behavior, the skill must stop and output:

```text
Scope Expansion Packet

Original task:
Blocked reason:
Forbidden file or behavior involved:
Why current scope is insufficient:
Recommended new atomic task:
Risk level:
Approval needed:
```

### 4. User Approval Profile

Add a default approval profile that records the user's standing preferences.

Auto-acceptable categories:

```text
L0 docs / reports / audits / bookkeeping
L1 dataclasses / protocol / no-op boundary / regression tests
L1 tasks backed by design notes and explicit acceptance criteria
```

Always require explicit approval:

```text
branch-and-bound search-control changes
LP/MIP solver core algorithm changes
public CLI contract changes
JSON schema changes
phase start or closure
new dependencies
non-no-op cut integration
callback mutation capability
cut materialization into LP relaxations
```

The profile must guide recommendations, but it must not override explicit user approval
requirements.

### 5. End-of-Run Digest

At the end of every executed task, the skill should output a short digest:

```text
SILO-DOS Run Digest

Task:
Mode:
Risk:
Files changed:
Checks:
Commit:
Push:
Boundary status:
Next:
```

Detailed reports still belong under `tasks/reports/`.

### 6. Preserve Existing v0.2 Behavior

The v0.3 skill must preserve:

- Mode A: auto-one
- Mode B: review-gated
- Mode C: principal mode
- L0 / L1 / L2 / L3 risk classification
- one-task-at-a-time execution
- task ID scan
- scope lock
- report creation
- commit and push rules
- no phase start without explicit user approval
- no phase closure without explicit user approval

## Stop Conditions

Stop and report instead of proceeding if:

- the existing skill file cannot be read;
- the requested v0.3 behavior contradicts `tasks/README.md` or `AGENTS.md`;
- updating the skill would require modifying solver source code, tests, `ROADMAP.md`,
  phase files, or Phase 7 materials;
- the upgrade would allow AI to self-approve L2/L3 execution;
- the upgrade would weaken one-task-at-a-time safety;
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

exists after the update and includes:

```text
v0.3
Decision Packet
Failure Packet
Scope Expansion Packet
User Approval Profile
End-of-Run Digest
Mode A
Mode B
Mode C
L0
L1
L2
L3
```

Do not run the full solver test suite unless executable project files are modified
unexpectedly.

## Acceptance Criteria

This task is complete only if:

1. The local `silo-development-operator` skill identifies itself as v0.3.
2. The skill automatically emits Decision Packets for L2/L3 gates.
3. The skill automatically emits Failure Packets for failed checks.
4. The skill automatically emits Scope Expansion Packets for required out-of-scope
   changes.
5. The skill includes the User Approval Profile.
6. The skill includes the End-of-Run Digest format.
7. Mode A / Mode B / Mode C are preserved.
8. L0 / L1 / L2 / L3 risk policy is preserved.
9. One-task-at-a-time execution is preserved.
10. The skill states that AI may recommend approve/revise/reject but may not self-approve
    L2/L3 execution.
11. No solver source code is modified.
12. No tests are modified.
13. `ROADMAP.md` is not modified.
14. No phase files are modified.
15. Phase 6 is not closed.
16. Phase 7 is not started.
17. A report is created at the expected report path.
18. `git diff --check` passes.

## Report Requirements

Create:

```text
tasks/reports/20260524-12-01_silo-dos-v03-decision-packets_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Skill changes:
Decision-packet behavior added:
Failure-packet behavior added:
Scope-expansion behavior added:
User approval profile added:
End-of-run digest added:
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
files, Phase 6 closure, or Phase 7 work were modified or created.

## Git Instructions

Git mode:

```text
local-commit
```

After successful skill update and checks:

```bash
git add tasks/codex/20260524-12-01_silo-dos-v03-decision-packets.md tasks/reports/20260524-12-01_silo-dos-v03-decision-packets_report.md
git commit -m "docs(tasks): upgrade SILO-DOS decision packets"
```

The skill file is outside the repository and should be updated locally but cannot be
tracked by the SILO repository unless separately versioned.

Do not push unless explicitly instructed by the user.

## Final Response

When finished, report only:

- whether `silo-development-operator` was upgraded to v0.3;
- whether Decision Packet / Failure Packet / Scope Expansion Packet behavior was added;
- whether User Approval Profile and End-of-Run Digest were added;
- whether checks passed;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.
