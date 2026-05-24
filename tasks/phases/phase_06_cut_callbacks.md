# Phase 6: Cut Generation and Callbacks

## Goal

Define a conservative cut and callback layer that can be enabled experimentally without disrupting pure branch-and-bound.

Phase 6A records the cut-generation and callback boundary design in `notes/18_cut_callback_boundary_design.md`; it is design-only and includes no implementation.

Phase 6B adds immutable cut candidate and cut metadata dataclasses with validation and canonical-key tests; it does not implement cut pools, separators, callbacks, or branch-and-bound integration.

Phase 6C adds a deterministic in-memory cut pool with duplicate detection, activation queries, and node-local scope clearing tests; it still does not implement separators, callbacks, or branch-and-bound integration.

Phase 6D adds a no-op separator boundary with separator protocol tests; it does not implement real cut families, callbacks, or branch-and-bound integration.

Phase 6E adds read-only callback event records and no-op callback dispatch tests; it does not integrate callbacks into branch-and-bound or change solver behavior.

Phase 6F adds optional no-op separator and callback integration points to branch-and-bound behind disabled defaults, with no-regression tests proving default behavior remains unchanged; it does not materialize cuts or implement real cut families.

Phase 6G adds a deterministic toy upper-bound separator for tiny documented fixtures; it does not integrate the separator into default branch-and-bound behavior or make performance claims.

Phase 6H audits the conservative cut/callback boundary completion status in `tasks/reports/20260524-11-01_phase6-completion-audit_report.md`; it does not close Phase 6 or start Phase 7.

Phase 6I records explicit user approval to close Phase 6 for the current conservative cut/callback boundary scope; this bookkeeping points to the completion audit and does not start Phase 7.

## Scope

This phase introduces separators, a cut pool, duplicate handling, optional callback hooks, and tests for cut lifecycle behavior.

## Expected Files

- `src/silo/cuts/separator.py`
- `src/silo/cuts/cut_pool.py`
- `src/silo/mip/branch_and_bound.py`
- `tests/unit/test_cut_pool.py`
- `tests/unit/test_cut_callbacks.py`

## Algorithmic Requirements

Cuts must be represented as linear constraints with documented validity scope. Separators should return candidate cuts without mutating core model state directly.

## Testing Requirements

Add tests for adding cuts, duplicate detection, optional cut activation, and no-regression behavior when cuts are disabled.

## Do Not Do

Do not implement a large family of cuts before the cut API is stable. Do not let callbacks silently change solver conventions.

## Acceptance Criteria

The branch-and-bound solver can run with cuts disabled or with a simple separator enabled, and both paths remain deterministic.
