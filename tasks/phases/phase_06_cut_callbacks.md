# Phase 6: Cut Generation and Callbacks

## Goal

Define a conservative cut and callback layer that can be enabled experimentally without disrupting pure branch-and-bound.

Phase 6A records the cut-generation and callback boundary design in `notes/18_cut_callback_boundary_design.md`; it is design-only and includes no implementation.

Phase 6B adds immutable cut candidate and cut metadata dataclasses with validation and canonical-key tests; it does not implement cut pools, separators, callbacks, or branch-and-bound integration.

Phase 6C adds a deterministic in-memory cut pool with duplicate detection, activation queries, and node-local scope clearing tests; it still does not implement separators, callbacks, or branch-and-bound integration.

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
