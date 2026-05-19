# SILO Task Directory Rules

## 1. Purpose of `tasks/`

The `tasks/` directory is not a general notes folder. It is used to manage long-term phase plans, issued Codex task prompts, and optional execution reports.

## 2. Folder Roles

```text
tasks/phases/
```

Long-term phase roadmap files. These describe solver-development phases, goals, scope, expected files, testing requirements, and acceptance criteria. They are not one-off Codex commands.

```text
tasks/codex/
```

Issued Codex task prompts. These are the task instructions sent to Codex for execution.

Files under `tasks/codex/` are immutable after creation. Coding agents may read them, but must not edit, rename, delete, or move existing files unless the user explicitly asks for task-file maintenance.

```text
tasks/reports/
```

Optional execution reports. If Codex or another agent needs to record what was done, what tests passed, or what failed, the report must be created here instead of modifying the issued task file.

## 3. Naming Rules

For long-term phase files:

```text
tasks/phases/phase_XX_short-name.md
```

Examples:

```text
tasks/phases/phase_01_model_core.md
tasks/phases/phase_02_tableau_simplex.md
```

For issued Codex task files:

```text
tasks/codex/YYYYMMDD-TT-RR_slug.md
```

Where:

```text
YYYYMMDD = date
TT       = task block number on that date, fixed two digits
RR       = revision number of that task block, fixed two digits
slug     = short kebab-case task label, preferably 1-3 words
```

Examples:

```text
tasks/codex/20260519-01-01_phase-num.md
tasks/codex/20260519-02-01_task-rules.md
tasks/codex/20260519-03-01_model-core.md
tasks/codex/20260519-03-02_model-core.md
```

Meaning:

```text
20260519-03-01_model-core.md
```

means the first version of the third task block issued on 2026-05-19.

For execution reports:

```text
tasks/reports/YYYYMMDD-TT-RR_slug_report.md
```

Example:

```text
tasks/reports/20260519-02-01_task-rules_report.md
```

## 4. Revision Rule

Do not overwrite an issued Codex task file to revise it.

If a task needs revision, create a new file with an incremented `RR` value.

Example:

```text
tasks/codex/20260519-03-01_model-core.md
tasks/codex/20260519-03-02_model-core.md
```

## 5. Rule Change Rule

If the task system itself needs to change in the future, `tasks/README.md` must be updated first or in the same commit.

No future task-directory restructuring should be done without updating this rule file.
