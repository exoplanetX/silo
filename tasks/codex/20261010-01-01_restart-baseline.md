# Restart Development Baseline

## Metadata
- Task ID: 20261010-01-01_restart-baseline
- Type: authorized recovery / maintenance
- Risk: L0 documentation; controlled mechanical lint cleanup
- Phase reference: existing educational reference milestone; no phase transition
- Git mode: local-commit
- Report: tasks/reports/20261010-01-01_restart-baseline_report.md

## Objective and authorization
Restore an understandable, runnable development baseline before the two status repairs explicitly requested by the user on 2026-10-10. The user authorized this ordered sequence; finish each atomic task and its commit before issuing the next. Local-ahead state from these authorized local commits is expected and does not authorize a push.

## Scope lock / allowed changes
- .gitignore: preserve resfs historical notes locally as ignored reference material.
- docs/development_restart.md: record current state, historical-note inventory, environment and checks.
- .silo-dos/project_profile.md and technical_route.md: replace stale next-action suggestions with the approved maintenance corridor; preserve phase/native decisions.
- Existing source lines flagged UP038 by Ruff: mechanical isinstance union spelling only.
- Ignored .venv: install the existing package with existing host dependencies; no dependency declaration changes.
- This new task contract and matching execution report.

## Forbidden changes
No algorithm behavior, public API/CLI/schema, dependency/build declarations, historical tasks/reports, raw historical notes, or phase status changes. No skill changes, native implementation, phase start/closure or push.

## Required checks
Inventory and hash resfs files; establish .venv; pytest; Ruff over src/tests/examples/scripts; git diff --check; inspect diff for mechanical-only source changes.

## Acceptance criteria
Historical notes preserved byte-for-byte and clearly marked historical; working tree clean after local commit; package console script usable; existing 975 tests pass; Ruff passes; local mirror records the authorized status-repair corridor and unresolved bugs.

## Stop conditions
Unexpected user changes, failures requiring unrelated algorithm edits, or need for dependency/build/phase changes. Report wider findings rather than fixing them here.

## Report requirements
Record files, checks, environment, task ID scan, user authorization, before/after Git state, commit reference, no-push result, unresolved status defects and next presolve task.
