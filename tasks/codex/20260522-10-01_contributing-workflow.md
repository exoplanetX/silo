# Codex Task: Add CONTRIBUTING Workflow Pointer

## Task Metadata

Task ID: 20260522-10-01
Task slug: contributing-workflow
Task type: process-design
Related phase: task-system / development-process
Git mode: local-commit
Expected report path: tasks/reports/20260522-10-01_contributing-workflow_report.md

## Objective

Add a concise AI/Codex-assisted development workflow pointer to `CONTRIBUTING.md`.

The goal is to make human-facing contribution guidance consistent with `tasks/README.md` and `AGENTS.md`, without duplicating the full SILO-DOS rule set.

## Pre-Issue Task ID Check

Before creating this task file or report, scan existing filenames under:

```text
tasks/codex/
tasks/reports/
```

The originally requested `20260522-04-01` prefix already exists for a different slug. This task uses the next available `TT` value, so the adjusted task ID is `20260522-10-01`.

## Context

The SILO project now has:

- `tasks/README.md` as the source of truth for task directory rules and SILO-DOS;
- `AGENTS.md` as the AI coding agent rule file;
- atomic task, scope lock, Git mode, report, and one-step execution rules.

`CONTRIBUTING.md` currently explains development setup, tests, module boundaries, deterministic tests, and generated files. It should now include a short pointer for AI/Codex-assisted development so contributors know where process rules live.

## Scope Lock

This task is atomic.

Primary objective:

- Add a concise AI/Codex workflow pointer to `CONTRIBUTING.md`.

Allowed changes:

- `CONTRIBUTING.md`
- `tasks/reports/20260522-10-01_contributing-workflow_report.md`

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify `tasks/README.md`.
- Do not modify `AGENTS.md`.
- Do not rename, edit, delete, or move existing files under `tasks/codex/`.
- Do not rename, edit, delete, or move existing files under `tasks/phases/`.
- Do not modify `README.md` or `ROADMAP.md`.
- Do not push to GitHub unless explicitly instructed by the user.

Stop conditions:

- If the intended task ID collides with an existing task or report prefix, choose the next available `TT` and report the adjustment.
- If changing `CONTRIBUTING.md` appears to require changing task-system rules, stop and report instead.
- If unrelated repository changes are present before starting, inspect and report them before modifying files.

## Required CONTRIBUTING.md Update

Add a short section such as:

```markdown
## AI/Codex-Assisted Development

AI-assisted development must follow the repository task system.

- `tasks/README.md` is the source of truth for task directory rules and SILO-DOS.
- `AGENTS.md` defines agent-facing solver and workflow rules.
- Long-term phase plans belong under `tasks/phases/`.
- Issued Codex task contracts belong under `tasks/codex/`.
- Execution reports belong under `tasks/reports/`.
- Codex tasks should be atomic, scope-locked, and executed one at a time.
- Do not modify existing issued task files unless the user explicitly requests task-file maintenance.
- Pushes to GitHub should follow the task-declared Git mode or explicit user instruction.
```

Keep this section concise. Do not copy the full SILO-DOS rule set into `CONTRIBUTING.md`.

## Acceptance Criteria

This task is complete only if:

1. `CONTRIBUTING.md` points contributors to `tasks/README.md`.
2. `CONTRIBUTING.md` points AI coding agents to `AGENTS.md`.
3. The section mentions `tasks/phases/`, `tasks/codex/`, and `tasks/reports/`.
4. The section mentions atomic, scope-locked, one-task-at-a-time execution.
5. The section does not duplicate the full SILO-DOS rules.
6. No solver source code is modified.
7. No tests are modified.
8. No existing task file is modified.
9. A report is created at the expected report path.

## Required Checks

Run at least:

```bash
git status --short
git diff --check
```

Do not run heavy solver tests for this process-only documentation task.

## Report Requirements

Create the matching report under `tasks/reports/`.

The report must include:

```text
Task ID:
Objective:
Files changed:
Summary of CONTRIBUTING.md updates:
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

After completing the update and report:

```bash
git add CONTRIBUTING.md tasks/reports/20260522-10-01_contributing-workflow_report.md
git commit -m "docs(contributing): add AI-assisted workflow pointer"
```

Do not push unless the user explicitly requests it.

## Final Response

When finished, report only:

- whether `CONTRIBUTING.md` was updated;
- whether the report was created;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.

这个做完后，下一步就是一个小的文档一致性修正：`docs/lp_solver.md` 里关于 MIP CLI 的旧表述。然后再进入 `silo-development-operator` skill。
