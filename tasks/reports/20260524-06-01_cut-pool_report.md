# Deterministic Cut Pool Report

Task ID: 20260524-06-01

Objective:
Add a deterministic cut pool with duplicate detection, activation, and scope-clearing
tests, building only on the Phase 6 cut candidate dataclasses.

Files changed:

- `tasks/codex/20260524-06-01_cut-pool.md`
- `src/silo/cuts/cut_pool.py`
- `src/silo/cuts/__init__.py`
- `tests/unit/test_cut_pool.py`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-06-01_cut-pool_report.md`

Implementation summary:

- Replaced the placeholder `CutPool` with a deterministic in-memory cut pool.
- Added `CutPoolAddResult` for accepted and duplicate add outcomes.
- Added duplicate detection using `CutCandidate.canonical_key()`, with optional
  cut-pool variable ordering.
- Stored accepted cuts in deterministic insertion order.
- Returned active cut views for a queried node without mutating stored cut state.
- Supported global cuts and node-local cuts with explicit node ids.
- Added clearing of expired node-local cuts by an explicit active-node-id set.
- Exported `CutPool` and `CutPoolAddResult` from `silo.cuts`.
- Added a brief Phase 6C note to `tasks/phases/phase_06_cut_callbacks.md`.

Tests added:

- Unique cuts are accepted and stored in insertion order.
- Duplicate cuts are reported without appending a second stored cut.
- Duplicate detection works with an explicit variable order.
- Active cuts for a node include global cuts and matching node-local cuts only.
- Active cut queries do not mutate stored cut state.
- Expired node-local cuts are cleared while global cuts and active node-local cuts remain.
- Non-`CutCandidate` values are rejected.
- Node-local cuts without a node id are rejected.
- Global cuts with a node id are rejected.
- Duplicate initial cuts are rejected.
- Public exports from `silo.cuts` include the cut-pool API.

Checks run:

- `git status --short`
- `pytest tests/unit/test_cut_pool.py`
- `python scripts/check_quality.py` (first run failed after all tests passed because ruff
  required import sorting in `src/silo/cuts/cut_pool.py`)
- `ruff check src/silo/cuts/cut_pool.py --fix`
- `pytest tests/unit/test_cut_pool.py`
- `python scripts/check_quality.py`
- `git diff --check`

Results:

- Targeted cut-pool tests passed with 10 tests.
- Full quality check passed with 484 tests and ruff checks.
- `git diff --check` passed.
- No branch-and-bound search logic was modified.
- No MIP node ordering, pruning, branching, or incumbent behavior was modified.
- No LP solver or presolve behavior was modified.
- No separators were implemented.
- No callbacks were implemented.
- No CLI behavior was changed.
- No JSON schemas were changed.
- No examples were changed.
- No additional Phase 6 task was issued or executed.

Deviations from scope:

- None.

Git status before:

```text
## main...origin/main
```

Git status after implementation before report:

```text
 M src/silo/cuts/__init__.py
 M src/silo/cuts/cut_pool.py
 M tasks/phases/phase_06_cut_callbacks.md
?? tasks/codex/20260524-06-01_cut-pool.md
?? tests/unit/test_cut_pool.py
```

Local commit hash:

```text
Created after this report is staged; the final response records the final commit hash.
```

Push attempted:

```text
Pending final push attempt because the task Git mode is `push-on-success`; the final
response records whether push completed or failed.
```

Unresolved issues:

- None for this atomic task.

Next recommended atomic task:

Add a no-op separator boundary and separator protocol tests without changing
branch-and-bound behavior.
