# Phase 6: Branch and Bound

## Goal

Implement a minimal branch-and-bound solver for small MIP instances using the LP relaxation interface.

## Scope

This phase covers node representation, incumbent management, branching decisions, node selection, LP relaxation calls, pruning, and final MIP status.

## Expected Files

- `src/silo/mip/branch_and_bound.py`
- `src/silo/mip/node.py`
- `src/silo/mip/tree.py`
- `src/silo/mip/incumbent.py`
- `src/silo/mip/branching.py`
- `src/silo/mip/node_selection.py`
- `tests/unit/test_branch_and_bound.py`

## Algorithmic Requirements

Use deterministic branching and node selection. Start with binary and bounded integer variables. Prune infeasible nodes, bound-dominated nodes, and integral relaxation solutions.

## Testing Requirements

Add tests for binary knapsack, a small integer minimization model, infeasible MIP, incumbent update, and deterministic node order.

## Do Not Do

Do not add cuts, heuristics, callbacks, or commercial solver dependencies in the native algorithm.

## Acceptance Criteria

Pure branch-and-bound solves small MIP fixtures and reports clear node counts, incumbent value, and final status.
