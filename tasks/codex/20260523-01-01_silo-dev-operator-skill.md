# Codex Task: Create silo-development-operator Skill

## Task Metadata

Task ID: 20260523-01-01
Task slug: silo-dev-operator-skill
Task type: process-tooling
Related phase: task-system / development-process
Git mode: local-commit
Expected report path: tasks/reports/20260523-01-01_silo-dev-operator-skill_report.md

## Objective

Create the first version of the `silo-development-operator` Codex skill.

This skill should help Codex issue the next SILO development task from repository state. It must read the SILO-DOS rules, phase plans, roadmap, and prior reports, then generate one compliant atomic task under `tasks/codex/`.

The first version is a planner / task issuer only. It must not execute solver code changes automatically.

## Pre-Issue Task ID Check

Before creating this task file or report, scan existing filenames under:

```text
tasks/codex/
tasks/reports/
```

If `20260523-01-01` already exists for a different slug, do not reuse it. Use the next available `TT` value and update the task ID, task filename, report filename, and metadata consistently.

## Context

The SILO repository now has a working development-process layer:

- `tasks/README.md` defines task directory rules and SILO-DOS.
- `AGENTS.md` defines AI coding agent rules.
- `CONTRIBUTING.md` points human contributors to the task system.
- Task ID uniqueness and pre-issue scan rules are in place.
- Execution reports are used as project memory.

The next step is to create a Codex skill that turns this process into a repeatable workflow.

The user’s local Codex skills directory is expected to be:

```text
C:\Users\xuning\.codex\skills
```

Create the skill under:

```text
C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md
```

If the path does not exist, create the necessary directory. If the environment uses a different home path, resolve the equivalent user Codex skills directory and record the actual path in the report.

## Scope Lock

This task is atomic.

Primary objective:

- Create the first version of the `silo-development-operator` skill.

Allowed changes:

- `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md`
- `tasks/reports/20260523-01-01_silo-dev-operator-skill_report.md`

Optional allowed change if useful for version tracking:

- `tasks/codex/20260523-01-01_silo-dev-operator-skill.md`

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify `tasks/README.md`.
- Do not modify `AGENTS.md`.
- Do not modify `CONTRIBUTING.md`.
- Do not modify `README.md`, `ROADMAP.md`, `docs/`, or `notes/`.
- Do not modify existing files under `tasks/codex/`.
- Do not modify existing files under `tasks/phases/`.
- Do not create a new solver feature.
- Do not make the skill auto-execute implementation tasks.
- Do not push to GitHub unless explicitly instructed by the user.

Stop conditions:

- If the local Codex skills directory cannot be found or created, stop and report.
- If an existing `silo-development-operator` skill already exists, do not overwrite it blindly. Inspect it and either preserve it or create a backup before replacing.
- If creating the skill appears to require changing repository task-system rules, stop and report instead.
- If unrelated repository changes are present before starting, inspect and report them before modifying files.

## Required Skill Behavior

Create a `SKILL.md` for `silo-development-operator`.

The skill must define itself as a SILO project development operator.

It should support these user intents:

```text
continue SILO
continue next SILO task
issue next SILO task
plan next SILO task
generate next Codex task
```

The skill must do the following:

1. Read `tasks/README.md`.
2. Read `AGENTS.md`.
3. Read `ROADMAP.md`.
4. Inspect `tasks/phases/`.
5. Inspect recent `tasks/reports/`.
6. Scan `tasks/codex/` and `tasks/reports/` for task ID collisions.
7. Select exactly one next candidate atomic task.
8. Generate one task file under `tasks/codex/`.
9. Ensure the task includes:
   - task metadata;
   - objective;
   - context;
   - scope lock;
   - allowed changes;
   - forbidden changes;
   - stop conditions;
   - required checks;
   - acceptance criteria;
   - report requirements;
   - Git mode;
   - final response requirements.
10. Stop after issuing the task.

The skill must not:

- execute the generated task;
- modify solver source code;
- modify tests;
- automatically push to GitHub;
- automatically enter the next phase;
- generate multiple tasks in one invocation;
- ignore task ID pre-issue scanning.

## Required SKILL.md Structure

The skill should include at least these sections:

```markdown
# silo-development-operator

## Purpose

## When to Use This Skill

## Inputs the Skill Must Read

## Operating Principles

## Task Selection Procedure

## Task ID Procedure

## Task Generation Requirements

## Scope Lock Requirements

## Git Mode Rules

## Report Requirements

## Stop Conditions

## Output Format

## Non-Goals
```

## Core Design Requirements

The skill must treat `tasks/README.md` as the source of truth for task rules.

The skill must treat `AGENTS.md` as the agent-facing rule file.

The skill must use `ROADMAP.md` and `tasks/phases/` for phase context, but it must not mark phases complete or enter a new phase without explicit user approval.

The skill must use recent reports in `tasks/reports/` to understand what was just completed.

The skill must distinguish between:

```text
planning / task issuing
```

and

```text
task execution
```

The first version of this skill is only for planning and task issuing.

## Acceptance Criteria

This task is complete only if:

1. `silo-development-operator/SKILL.md` is created in the local Codex skills directory.
2. The skill clearly follows SILO-DOS.
3. The skill generates only one atomic task per invocation.
4. The skill includes task ID pre-issue scan rules.
5. The skill refuses to auto-execute implementation changes.
6. The skill uses `tasks/README.md`, `AGENTS.md`, `ROADMAP.md`, `tasks/phases/`, and `tasks/reports/` as inputs.
7. No solver source code is modified.
8. No tests are modified.
9. No existing task file is modified.
10. A report is created at the expected report path.

## Required Checks

Run at least:

```bash
git status --short
git diff --check
```

Also verify that the skill file exists at the expected path.

Do not run solver tests for this process-tooling task.

## Report Requirements

Create the matching report under `tasks/reports/`.

The report must include:

```text
Task ID:
Objective:
Skill path created:
Files changed:
Summary of skill behavior:
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

Default Git mode for this task is:

```text
local-commit
```

Since the skill file is outside the repository, only commit repository-tracked files such as the task file and report.

After completing the update and report:

```bash
git add tasks/codex/20260523-01-01_silo-dev-operator-skill.md tasks/reports/20260523-01-01_silo-dev-operator-skill_report.md
git commit -m "docs(tasks): add SILO development operator skill task"
```

Do not push unless the user explicitly requests it.

## Final Response

When finished, report only:

- whether the skill file was created;
- the local skill path;
- whether the report was created;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.

这个任务完成后，下一步不要马上恢复 solver 开发。先测试一次 skill：让它根据现有 repo 状态生成一个“下一步任务”，但不执行该任务。
