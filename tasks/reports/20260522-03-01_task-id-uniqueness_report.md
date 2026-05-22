# Task ID Uniqueness Report

Task ID: 20260522-03-01

Objective: Add forward-looking task ID uniqueness and pre-issue scan rules to `tasks/README.md` and `AGENTS.md` without renaming immutable task history.

Files changed:

- `tasks/README.md`
- `AGENTS.md`
- `tasks/codex/20260522-03-01_task-id-uniqueness.md`
- `tasks/reports/20260522-03-01_task-id-uniqueness_report.md`

Summary of task ID rule updates:

- Added a `Task ID Uniqueness` rule to `tasks/README.md`.
- Defined `YYYYMMDD-TT-RR` as the unique prefix for a specific issued task identity.
- Clarified that two different slugs must not share the same `YYYYMMDD-TT-RR` prefix.
- Clarified that `RR` is only for revisions of the same task block.
- Required new unrelated tasks on the same date to use the next available `TT`.
- Required a pre-issue scan of existing `tasks/codex/` and `tasks/reports/` filenames before creating a new task file.
- Updated `AGENTS.md` so AI coding agents must avoid task ID collisions and treat historical collisions as reportable task-system debt.

Known historical collisions:

- `tasks/codex/20260522-01-01_phase4-cleanup.md`
- `tasks/codex/20260522-01-01_sdos-rules.md`
- `tasks/codex/20260522-02-01_agents-sdos-sync.md`
- `tasks/codex/20260522-02-01_bnb-note.md`
- `tasks/codex/20260522-03-01_mip-relax.md`
- `tasks/codex/20260522-03-01_task-id-uniqueness.md`
- `tasks/reports/20260522-01-01_phase4-cleanup_report.md`
- `tasks/reports/20260522-01-01_sdos-rules_report.md`
- `tasks/reports/20260522-02-01_agents-sdos-sync_report.md`
- `tasks/reports/20260522-02-01_bnb-note_report.md`
- `tasks/reports/20260522-03-01_mip-relax_report.md`
- `tasks/reports/20260522-03-01_task-id-uniqueness_report.md`

Checks run:

- `git status --short`
- `git diff --check`
- Lightweight documentation tooling inspection: no markdown linting or documentation check is configured in `pyproject.toml` or `scripts/`.

Git status before:

```text
## main...origin/main
?? tasks/codex/20260522-03-01_task-id-uniqueness.md
```

Git status after:

```text
 M AGENTS.md
 M tasks/README.md
?? tasks/codex/20260522-03-01_task-id-uniqueness.md
?? tasks/reports/20260522-03-01_task-id-uniqueness_report.md
```

Local commit hash:

```text
Pending local commit. The final response records the created commit hash because a report cannot contain the hash of the commit that adds it without changing that hash.
```

Push attempted:

```text
Pending. The task declares Git mode `local-commit`, while the active user preference asks Codex to push after tasks when possible. The final response records whether a push was attempted and whether it succeeded.
```

Issues or conflicts:

- Existing task ID collisions were found and recorded as historical task-system debt.
- No existing files under `tasks/codex/` or `tasks/phases/` were renamed, moved, deleted, or modified.
- The new task file itself reuses an existing `20260522-03-01` prefix. It is recorded above as part of the historical collision set and was not renamed in this task.
- The new task file had pasted markdown wrapper artifacts and was cleaned before being committed as a new task file.
- No automated markdown linting or documentation check is configured.

Next recommended atomic task:

T4: add a concise `CONTRIBUTING.md` workflow pointer to `tasks/README.md` and `AGENTS.md`.
