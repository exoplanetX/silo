# Cut Candidate Dataclasses Report

Task ID: 20260524-05-01

Objective:
Add immutable cut candidate and cut metadata dataclasses with validation and stable
canonical-key behavior, backed by deterministic unit tests.

Files changed:

- `tasks/codex/20260524-05-01_cut-dataclasses.md`
- `src/silo/cuts/candidate.py`
- `src/silo/cuts/__init__.py`
- `tests/unit/test_cut_candidate.py`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-05-01_cut-dataclasses_report.md`

Implementation summary:

- Added `CutValidityScope` with `global` and `node_local` values.
- Added `CutActivityState` with `candidate`, `accepted`, `active`, `duplicate`,
  `rejected`, and `expired` values.
- Added immutable `CutMetadata`.
- Added immutable `CutCandidate`.
- Normalized cut candidate coefficients into immutable sorted tuple storage.
- Added deterministic `canonical_key()` support with default variable-name ordering and
  optional caller-provided variable order.
- Exported the new dataclasses and enums from `silo.cuts`.
- Added a brief Phase 6B note to `tasks/phases/phase_06_cut_callbacks.md`.

Validation behavior:

- Rejects empty coefficient maps.
- Rejects empty variable names.
- Rejects nonfinite coefficients.
- Rejects all-zero coefficient vectors.
- Rejects nonfinite RHS values.
- Rejects empty source separator names.
- Rejects nonempty but blank cut ids when provided.
- Rejects nonpositive or nonfinite tolerances.
- Rejects negative node ids.
- Normalizes `ConstraintSense`, cut validity scope, cut activity state, tolerance, RHS,
  and coefficient values.

Tests added:

- Valid global cut candidate construction.
- Valid node-local metadata construction.
- Metadata immutability.
- Cut candidate immutability.
- Defensive coefficient copy and normalization.
- Invalid coefficient, RHS, source, tolerance, and node-id cases.
- Stable canonical key independent of input coefficient insertion order.
- Canonical key respecting explicit variable order.
- Public exports from `silo.cuts`.

Checks run:

- `git status --short`
- `pytest tests/unit/test_cut_candidate.py`
- `python scripts/check_quality.py` (first run failed on a ruff import-location warning
  after all tests passed)
- `python scripts/check_quality.py` (second run passed)
- `git diff --check`

Results:

- Targeted cut candidate tests passed with 23 tests.
- Full quality check passed with 474 tests and ruff checks.
- `git diff --check` passed.
- No cut pool behavior was implemented.
- No separators were implemented.
- No callbacks were implemented.
- No branch-and-bound integration was implemented.
- No branch-and-bound behavior was changed.
- No CLI behavior was changed.
- No JSON schemas were changed.
- No examples were modified.
- No additional Phase 6 task was issued or executed.

Git status before:

```text
## main...origin/main
?? tasks/codex/20260524-05-01_cut-dataclasses.md
```

Git status after:

```text
 M src/silo/cuts/__init__.py
 M tasks/phases/phase_06_cut_callbacks.md
?? src/silo/cuts/candidate.py
?? tasks/codex/20260524-05-01_cut-dataclasses.md
?? tests/unit/test_cut_candidate.py
?? tasks/reports/20260524-05-01_cut-dataclasses_report.md
```

Local commit hash:

```text
Created locally; the final response records the final amended commit hash.
```

Push attempted:

```text
Pending final push attempt because the task Git mode is `push-on-success`; the final
response records whether push completed or failed.
```

Issues or conflicts:

- The first `python scripts/check_quality.py` run failed only because ruff required
  `Iterable` and `Mapping` to be imported from `collections.abc`; the import was corrected
  and the second quality run passed.
- No unrelated dirty changes were present before execution.

Next recommended atomic task:

Add a deterministic cut pool with duplicate detection, activation, and scope-clearing
tests.
