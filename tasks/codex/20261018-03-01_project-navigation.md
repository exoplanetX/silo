# Project Navigation and Traceability

## Metadata / authority
- ID: 20261018-03-01_project-navigation
- Objective: establish a compact current project entry and a mechanically checked task index while preserving existing solver/file identities.
- Type/risk: L3 scoped task-system documentation and validation maintenance, authorized by the user's 2026-10-18 request to begin the reviewed organization after GitHub synchronization.
- Phase reference: administrative maintenance of existing Phase 0-9 records; no phase transition.
- Git mode: local-commit; no push of this new task is included.
- Report: tasks/reports/20261018-03-01_project-navigation_report.md
- Learning delivery: not applicable; no mathematical or solver behavior changes.
- Model recommendation: GPT-6 Sol / high for cross-file consistency, medium for routine prose.

## Context / baseline
Primary main and live GitHub main are bdddf5851b72397c641c3dd872a306f66a12b296.
Existing untracked notes/26..30 are unrelated active research assets. Preserve their
paths and bytes. Work in a clean managed worktree at this baseline and fast-forward
the single resulting commit into primary only if its tracked HEAD is unchanged.
Task-ID scan found 20261018 block 01 revisions 01/02 and block 02 revision 01;
03-01 is unused in both tasks/codex and tasks/reports.

## Allowed changes / scope lock
- .silo-dos/project_profile.md: concise current snapshot, source/identity map and current recommendations.
- .silo-dos/technical_route.md: decision boundaries, referencing the snapshot instead of duplicating dated execution history.
- .silo-dos/decision_log.md: current-entry pointer and a new explicit superseding organization entry; preserve historical decision entries.
- tasks/README.md: current-entry/index/exception/check maintenance rules and prospective task/report baseline guidance.
- tasks/INDEX.md: deterministic derived navigation, no inferred execution-success claims.
- tasks/history_exceptions.json: exact existing ID collisions and documented early record gaps; no blanket exemptions for new collisions.
- scripts/check_project_structure.py and scripts/check_quality.py: lightweight standard-library structure validation and quality entry integration.
- docs/development_layout.md and docs/README.md, README.md, CONTRIBUTING.md, AGENTS.md: navigation, actual implementation entrypoints/import boundaries, stable-path and environment guidance.
- CHANGELOG.md and CITATION.cff: unreleased development metadata consistency without version bump, tag or release.
- This new contract and its matching report only within tasks/codex and tasks/reports.

All supporting edits serve the same navigation/traceability objective. Existing file
paths remain stable. Document remaining asset-ingestion work rather than executing it.

## Forbidden changes
No src, tests, examples, learning bodies, phase files, old contracts/reports or research
notes changes. No archive/move/rename of existing files, external research script import,
solver/API/CLI/schema/convention changes, dependencies/build/packaging changes, skill or
agent changes, native work, phase start/closure, release/tag, push or second task.

## Checks / acceptance
- Current snapshot clearly links completed baseline/oracle/LP-dual/learning work and separates recommendations from approval. No stale next-action instructions remain in the refreshed current entry/route.
- Deterministic task index links every contract/report, labels historical ID collisions and gaps, and does not equate a report's existence with execution success.
- Structure checker accepts exactly the recorded historical collision groups, rejects additional collisions, malformed identities and unmatched new reports, checks metadata versions, current documentation links, core isolation and import cycles. Unexecuted issued tasks may lack reports.
- Fresh index regeneration is idempotent; altered index and deliberate invalid fixtures are rejected. Use temporary fixtures rather than adding solver tests.
- Targeted Ruff and the full quality entry pass; report actual results. Validate changed Markdown targets and balanced fences.
- git diff --check and cached checks pass; old contracts/reports and src/tests/examples/notes/learning remain byte-identical to baseline.
- Integrate by fast-forward only, verify original note hashes, report live/tracked Git state honestly.

## Stop conditions / report
Stop for unexpected tracked edits, moved baseline, required solver/phase/skill changes,
unexplained historical exceptions, failed checks, or need to rewrite immutable history.
Report changed files, task-ID scan, checks, true commit reference, push skipped, before/
after Git state, preserved notes, management debt and one next recommended atomic task.
Do not automatically issue or execute the research-asset ingestion task.
