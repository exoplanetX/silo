# Codex Task: Synchronize AGENTS.md with SILO-DOS Rules

## Task Metadata

Task ID: 20260522-02-01
Task slug: agents-sdos-sync
Task type: process-design
Related phase: task-system / development-process
Git mode: local-commit
Expected report path: tasks/reports/20260522-02-01_agents-sdos-sync_report.md

## Objective

Update `AGENTS.md` so that AI coding agents explicitly follow the SILO Development Operating System rules now defined in `tasks/README.md`.

This task must not change solver code, tests, phase plans, or existing issued task files. The goal is only to synchronize the agent-facing rules with the task-system rules.

## Context

`tasks/README.md` now defines SILO-DOS, including:

- phase-to-task rule;
- atomic task rule;
- scope lock rule;
- Git mode rule;
- execution report rule;
- one-step execution rule;
- responsibility boundary among the user, ChatGPT, Codex, and GitHub.

However, `AGENTS.md` still contains only the older task management rules. Since AI coding agents may read `AGENTS.md` before or alongside `tasks/README.md`, the agent-facing file must explicitly point to `tasks/README.md` as the source of task-system truth and summarize the execution rules agents must obey.

## Scope Lock

This task is atomic.

Primary objective:

- Synchronize `AGENTS.md` with the SILO-DOS rules in `tasks/README.md`.

Allowed changes:

- `AGENTS.md`
- `tasks/reports/20260522-02-01_agents-sdos-sync_report.md`

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify `tasks/README.md`.
- Do not modify existing files under `tasks/codex/`.
- Do not modify existing files under `tasks/phases/`.
- Do not modify `CONTRIBUTING.md` in this task.
- Do not modify `README.md` or `ROADMAP.md`.
- Do not push to GitHub unless explicitly instructed by the user.

Stop conditions:

- If `AGENTS.md` and `tasks/README.md` appear to conflict, preserve `tasks/README.md` as the source of truth and document the conflict in the report.
- If updating `AGENTS.md` requires changing task naming rules, stop and report.
- If unrelated repository changes are present before starting, inspect and report them before modifying files.

## Required AGENTS.md Updates

Update the `Task Management Rules` section in `AGENTS.md` so that it clearly states:

1. `tasks/README.md` is the source of truth for task directory rules and SILO-DOS.
2. AI coding agents must read `tasks/README.md` before issuing or executing task files.
3. Long-term development knowledge belongs in `tasks/phases/`.
4. Issued Codex task contracts belong in `tasks/codex/`.
5. Execution memory belongs in `tasks/reports/`.
6. Files under `tasks/codex/` are immutable after creation.
7. Each Codex task must be atomic and solve exactly one primary problem.
8. Each task must obey its scope lock, allowed changes, forbidden changes, stop conditions, required checks, acceptance criteria, expected report path, and Git mode.
9. Codex must stop after one atomic task and must not automatically continue to the next task.
10. Codex must not automatically enter a new phase or expand task scope without explicit user instruction.
11. Default Git mode is `local-commit` unless the task states otherwise.
12. Codex must not push to GitHub unless the task Git mode is `push-on-success`, the task is `sync-only`, or the user explicitly requests a push.
13. Push failure is non-fatal and must be recorded in the execution report.
14. If a broader issue is discovered, Codex should document it in the report instead of fixing it inside the current task.
15. If task-system rules need to change, `tasks/README.md` must be updated first or in the same commit.

Keep the existing solver architecture rules at the top of `AGENTS.md`. Do not weaken or remove the existing dependency-direction, external-solver, testing, and mathematical-convention rules.

## Acceptance Criteria

This task is complete only if:

1. `AGENTS.md` explicitly references `tasks/README.md` as the source of truth for task rules.
2. `AGENTS.md` summarizes the SILO-DOS execution rules relevant to AI coding agents.
3. The existing solver architecture rules remain intact.
4. No solver source code is modified.
5. No tests are modified.
6. No existing task file is modified.
7. A report is created at the expected report path.

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
tasks/reports/20260522-02-01_agents-sdos-sync_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Summary of AGENTS.md updates:
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
git add AGENTS.md tasks/reports/20260522-02-01_agents-sdos-sync_report.md
git commit -m "docs(agents): align AI agent rules with SILO-DOS"
```

Do not push unless the user explicitly requests it.

## Final Response

When finished, report only:

- whether `AGENTS.md` was updated;
- whether the report was created;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.

---

这一步完成后，流程规则才算真正进入“Codex 可执行”的状态。然后再做一个很小的 `CONTRIBUTING.md` 指针任务，最后才开始写 `silo-development-operator` skill。
