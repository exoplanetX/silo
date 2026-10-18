# Development Companion Learning Series

## Metadata / authority
- ID: 20261018-02-01_learning-series
- Type/risk: user-approved documentation organization and learning-delivery rules;
  L3 limited to project documentation governance, with no solver/phase change
- Phase reference: explicit user process request on 2026-10-18
- Git mode: local-commit; report: tasks/reports/20261018-02-01_learning-series_report.md
- ID scan: today's existing task block is 01 (revisions 01/02); use new block 02

## Objective
Create a dedicated, incrementally maintained learning series with stable lesson IDs,
chronological and thematic reading views, a reusable writing structure, exercises,
solutions, code/test/task provenance and explicit research value/limits. Seed it
from the completed LP dual material. Make future mathematical/algorithmic development
deliver a new or updated lesson; keep routine housekeeping proportionate.

## Scope lock / allowed changes
learning/** Markdown content; docs/README.md and docs/lp_duality.md; notes/README.md;
root README.md, CONTRIBUTING.md, AGENTS.md, tasks/README.md; dated learning-series
entries in .silo-dos/project_profile.md and technical_route.md; this task/report only.
Use clean learning-series worktree based on bb6baff, then fast-forward the single
commit into unchanged primary main. The user continues from the known local-ahead
baseline; no push. Preserve five untracked research notes and all existing contracts.

## Design
learning/lessons/L0001-lp-duality/ is the first stable lesson identity. Lesson order
is independent of future book chapter order. One canonical teaching body lives in
learning; docs/lp_duality.md retains current reference semantics and its existing URL.
Keep historical notes and tasks at their old paths; add role/navigation entries.
Include prerequisites, notation/assumptions, hand computation, derivation, code map,
reproducible verification, research connections, limits and practice/answers. Do not
label planned content as completed or finite checks as proofs. No book build system.

## Forbidden changes
No src/tests/examples/scripts/runtime/dependency changes; no solver fixes, phase or
native decisions; no edits/moves/renames of old task contracts or reports, research
notes, skills/agents or user conversations; no generated binaries/datasets or push.

## Checks / acceptance
Validate new/changed local Markdown links, stable unique IDs and source paths;
execute the lesson's Python example and independently check exercise answers.
Confirm runtime trees and historical task/report paths unchanged; diff whitespace
checks pass. Docs-only work does not require rerunning the full solver suite.
Record the current verified code baseline and review/verification scope honestly.

## Stop / report
Unexpected tracked edits or need for executable/forbidden changes: preserve work and
report a bounded follow-up. Report directory design, migrations/compatibility, rules,
checks, Git state, commit/integration and preserved notes. Stop after this one task.
