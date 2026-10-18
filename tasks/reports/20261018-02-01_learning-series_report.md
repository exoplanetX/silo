# Development Companion Learning Series — Execution Report

## Objective / result

Established `learning/` for a systematic Chinese development companion series with
stable lesson identity and both chronological and thematic reading views. Material
can be reorganized into topics/course/book chapters without renaming lesson IDs.
L0001 curates the existing LP dual lesson and adds prerequisites, explicit source/code
mapping, a research-interface discussion, and five exercises with separate solutions.

## Structure / migration

- `learning/README.md`: role, directory structure, numbering, task-to-lesson relationship.
- `learning/CATALOG.md`: chronological catalog and thematic book/course view; planned
  topics are explicitly unfilled, not represented as completed content.
- `learning/WRITING_GUIDE.md`: ten-part structure, metadata, provenance, evidence,
  revisions, exercise IDs and later editorial use.
- `learning/GLOSSARY.md`, `learning/templates/lesson.md`: shared terms and reusable template.
- `learning/lessons/L0001-lp-duality/{README,exercises,solutions}.md`: first checked lesson.
- `docs/lp_duality.md`: retain old URL and current API semantics as a concise reference;
  canonical teaching body now lives under learning instead of maintaining two full copies.
- `docs/README.md`, `notes/README.md` and root README: project role/navigation entries.
- CONTRIBUTING, AGENTS, tasks/README section 6.8: prospective learning-delivery rules.
- Dated local project/route entries plus matching task/report.

No existing task contract/report or research note was moved, renamed or rewritten.
No runtime, tests, examples, scripts, dependencies or solver capabilities changed.
The user asked to reorganize project folders; no user conversation was created or moved.

## Learning delivery rule

Future tasks about models, algorithms, conventions, numerics or correctness must name
the new/updated lesson inside scope and report actual verification. A lesson can grow
across several atomic tasks. Routine administrative work may explain why no new body
is needed. This task seeds the convention prospectively rather than retrofitting old
immutable contracts. One canonical teaching body lives in learning; API/current usage
remain in docs and exploratory history in notes.

## Checks

- Read-only documentation validation covered **19 Markdown files and 94 local links**;
  all targets exist. Code fences are balanced; the single stable L0001 identity matches
  its directory, catalog and full verified-code hash. All ten standard sections exist.
  Exercise/solution IDs match E01..E05 with no missing IDs.
- The complete lesson Python example executed under both tableau and revised backends,
  with primal=dual objective 13. E01-E03 executed on both backends: targets 16, 13, 19,
  expected original multipliers/reduced costs and independent optimality checks passed.
- E04's zero-gap invalid witness was rejected with dual_violation=1. E05's sign identity
  was checked with exact Fraction arithmetic on a finite input; its general relationship
  is supported by the written algebra, not generalized from the finite calculation.
- L0001 is marked checked after these actual checks, dated 2026-10-18, with verified code
  `bb6bafff1cea78943eb8ae9d4b1a1b7d2a4dc52b` and explicit development/curation provenance.
- No changes to src/tests/examples/scripts/pyproject.toml; historical tracked task/report
  files unchanged. New task/report are the only additions in those task subdirectories.
- `git diff --check` passed; Git reported only LF/CRLF normalization notices.

Checks are limited to affected documentation and mathematical examples. No full solver
rerun is required by this documentation-only task. Prior 1364-test evidence remains
attributed to the preceding LP development report, not presented as a fresh result.
The existing primary Python environment and unchanged solver baseline were reused.

## Git / boundaries

Before: primary main at bb6baff, origin/main at a4814f4, ahead/behind `0 2`, five
untracked notes/26..30. The user explicitly requested this reorganization on that
known local baseline. Implementation is in a clean managed learning-series worktree
based on bb6baff to preserve those unrelated files. Task ID scan found block 01 with
revisions 01/02; new block 02 revision 01 was issued.

Git mode local-commit, no push. Commit reference is the commit containing this report,
subject `docs: establish development companion learning series`, parent bb6baff.
Fast-forward into primary only if its tracked HEAD remains unchanged; verify original
note hashes. Expected final main: only the same five untracked notes, ahead three
(`0 3`), remote_sync_status dirty_worktree with local_ahead_origin. Final response
records actual commit and integration verification after commit.

No phase transition, native change, new skill/agent or publication occurred. The series
is growing source material, with checked examples and explicit code baselines; it is
not claimed to be a complete textbook or publication-reviewed manuscript.

## Next

Future mathematical work should update or add its companion lesson using the new
guide. The next solver recommendation remains revised Phase-I cleanup provenance;
that work should update L0001's known boundary and verification record. No solver task
is issued or executed by this documentation reorganization.
