# Codex Task: Add Task ID Uniqueness Rules

## Task Metadata

Task ID: 20260522-03-01
Task slug: task-id-uniqueness
Task type: process-design
Related phase: task-system / development-process
Git mode: local-commit
Expected report path: tasks/reports/20260522-03-01_task-id-uniqueness_report.md

## Objective

Update the SILO task-system rules so that future Codex task files cannot reuse an existing `YYYYMMDD-TT-RR` prefix for a different task slug.

This task must not rename, edit, delete, or move existing issued task files. The goal is to strengthen future task issuing rules while preserving the existing immutable task history.

## Context

The SILO task system uses issued task files under:

```text
tasks/codex/YYYYMMDD-TT-RR_slug.md
```

A recent process task revealed that two different task files may share the same `YYYYMMDD-TT-RR` prefix with different slugs. This creates ambiguity because the prefix is intended to identify a task block and revision.

The existing duplicate should be treated as historical task-system debt. Do not rename existing task files in this task. Instead, add forward-looking rules to prevent future collisions.

## Scope Lock

This task is atomic.

Primary objective:

- Add task ID uniqueness and pre-issue scan rules to `tasks/README.md` and `AGENTS.md`.

Allowed changes:

- `tasks/README.md`
- `AGENTS.md`
- `tasks/reports/20260522-03-01_task-id-uniqueness_report.md`

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not rename, edit, delete, or move existing files under `tasks/codex/`.
- Do not rename, edit, delete, or move existing files under `tasks/phases/`.
- Do not modify `CONTRIBUTING.md` in this task.
- Do not modify `README.md` or `ROADMAP.md`.
- Do not push to GitHub unless explicitly instructed by the user.

Stop conditions:

- If fixing the issue appears to require renaming existing task files, stop and report instead.
- If existing task IDs conflict, document the conflict as historical task-system debt but do not modify those files.
- If unrelated repository changes are present before starting, inspect and report them before modifying files.

## Required Updates to tasks/README.md

Add a rule under the naming or SILO-DOS section clarifying task ID uniqueness.

The rule must state:

1. The `YYYYMMDD-TT-RR` prefix must be unique for a specific issued task identity.
2. Two different slugs must not share the same `YYYYMMDD-TT-RR` prefix.
3. `RR` is only for revising the same task block.
4. A new unrelated task on the same date must use the next available `TT`.
5. Before creating a new task file, Codex must scan existing files under `tasks/codex/` and `tasks/reports/` for the same date prefix.
6. If a collision is found, Codex must choose the next available `TT` rather than reusing the prefix.
7. Existing historical collisions should not be repaired by renaming immutable task files unless the user explicitly requests task-file maintenance.

## Required Updates to AGENTS.md

Update the task management rules so that AI coding agents must:

1. Check existing `tasks/codex/` filenames before creating a new task.
2. Avoid reusing an existing `YYYYMMDD-TT-RR` prefix for a different slug.
3. Use `RR` only for revisions of the same task block.
4. Use the next available `TT` for a new unrelated task.
5. Treat historical collisions as reportable task-system debt, not as permission to rename immutable task files.

## Acceptance Criteria

This task is complete only if:

1. `tasks/README.md` defines task ID uniqueness.
2. `tasks/README.md` defines a pre-issue scan rule.
3. `AGENTS.md` tells AI coding agents to avoid task ID collisions.
4. Existing `tasks/codex/` files are not renamed or modified.
5. Existing `tasks/phases/` files are not renamed or modified.
6. No solver source code is modified.
7. No tests are modified.
8. A report is created at the expected report path.

## Required Checks

Run at least:

```bash
git status --short
git diff --check
```

Do not run heavy solver tests for this process-only documentation task.

## Report Requirements

Create:

```text
tasks/reports/20260522-03-01_task-id-uniqueness_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Summary of task ID rule updates:
Known historical collisions:
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

After completing the update and report:

```bash
git add tasks/README.md AGENTS.md tasks/reports/20260522-03-01_task-id-uniqueness_report.md
git commit -m "docs(tasks): add task ID uniqueness guard"
```

Do not push unless the user explicitly requests it.

## Final Response

When finished, report only:

- whether `tasks/README.md` was updated;
- whether `AGENTS.md` was updated;
- whether the report was created;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.

---

这个任务完成后，再走：

```text
T4: CONTRIBUTING.md workflow pointer
T5: docs/lp_solver.md MIP CLI consistency cleanup
T6: silo-development-operator skill
```

所以当前流程修改的关键判断是：**先补“任务编号唯一性防线”，再继续完善外部贡献说明，最后才写自动调度 skill。**
