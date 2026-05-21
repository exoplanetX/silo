# Phase 5: MIP Branch-and-Bound

## Goal

Implement a minimal branch-and-bound solver for small MIP instances using the LP relaxation interface.

Phase 5 begins with the design note in `notes/15_branch_and_bound_design.md`. The note defines the first supported MIP class, LP-relaxation boundary, branching rule, node selection rule, incumbent handling, pruning logic, status mapping, deterministic test fixtures, and implementation sequence.

Phase 5B adds the MIP-to-LP relaxation builder. It converts binary and bounded nonnegative integer variables into continuous relaxation variables and explicit upper-bound rows while keeping tableau and revised simplex behavior unchanged.

Phase 5C adds deterministic MIP search dataclasses and pure helpers for nodes, branching constraints, branching-variable selection, incumbent updates, node logs, prune reasons, depth-first node selection, and deterministic node ids. It still does not implement the branch-and-bound solve loop.

Phase 5D adds the first pure depth-first branch-and-bound solver for small binary maximization MIPs. It uses the MIP relaxation builder, native LP backends, first-fractional binary branching, incumbent updates, node logs, and deterministic left-before-right child processing. General bounded integer variables and CLI integration remain future work.

Phase 5E extends the same depth-first branch-and-bound loop to bounded nonnegative integer variables. Binary variables, bounded integer variables, and compatible continuous variables are supported through LP relaxations with explicit upper-bound rows; CLI integration, cuts, heuristics, callbacks, and advanced MIP features remain future work.

## Scope

This phase covers node representation, incumbent management, branching decisions, node selection, LP relaxation calls, pruning, and final MIP status.

## Expected Files

- `src/silo/mip/branch_and_bound.py`
- `src/silo/mip/relaxation.py`
- `src/silo/mip/node.py`
- `src/silo/mip/tree.py`
- `src/silo/mip/incumbent.py`
- `src/silo/mip/branching.py`
- `src/silo/mip/node_selection.py`
- `tests/unit/test_mip_relaxation.py`
- `tests/unit/test_branch_and_bound.py`

## Algorithmic Requirements

Use deterministic branching and node selection. Start with binary and bounded integer variables. Prune infeasible nodes, bound-dominated nodes, and integral relaxation solutions.

## Testing Requirements

Add tests for binary knapsack, simple binary choice, bounded nonnegative integer maximization, infeasible MIP, incumbent update, pruning reasons, relaxation construction, and deterministic node order.

## Do Not Do

Do not add cuts, heuristics, callbacks, or commercial solver dependencies in the native algorithm.

## Acceptance Criteria

Pure branch-and-bound solves small MIP fixtures and reports clear node counts, incumbent value, and final status.
