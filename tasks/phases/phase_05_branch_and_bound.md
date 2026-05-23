# Phase 5: MIP Branch-and-Bound

## Goal

Implement a minimal branch-and-bound solver for small MIP instances using the LP relaxation interface.

Phase 5 begins with the design note in `notes/15_branch_and_bound_design.md`. The note defines the first supported MIP class, LP-relaxation boundary, branching rule, node selection rule, incumbent handling, pruning logic, status mapping, deterministic test fixtures, and implementation sequence.

Phase 5B adds the MIP-to-LP relaxation builder. It converts binary and bounded nonnegative integer variables into continuous relaxation variables and explicit upper-bound rows while keeping tableau and revised simplex behavior unchanged.

Phase 5C adds deterministic MIP search dataclasses and pure helpers for nodes, branching constraints, branching-variable selection, incumbent updates, node logs, prune reasons, depth-first node selection, and deterministic node ids. It still does not implement the branch-and-bound solve loop.

Phase 5D adds the first pure depth-first branch-and-bound solver for small binary maximization MIPs. It uses the MIP relaxation builder, native LP backends, first-fractional binary branching, incumbent updates, node logs, and deterministic left-before-right child processing. General bounded integer variables and CLI integration remain future work.

Phase 5E extends the same depth-first branch-and-bound loop to bounded nonnegative integer variables. Binary variables, bounded integer variables, and compatible continuous variables are supported through LP relaxations with explicit upper-bound rows; CLI integration, cuts, heuristics, callbacks, and advanced MIP features remain future work.

Phase 5F adds checked-in MIP JSON examples and regression tests for the Python branch-and-bound API before CLI exposure.

Phase 5G drafts the MIP CLI exposure design note before implementing a command.

Phase 5H exposes the first `silo mip-solve` CLI command with LP relaxation backend selection, node-limit handling, solution JSON output, and deterministic regression tests.

Phase 5I adds a subprocess regression matrix for module and console-script MIP CLI invocation while confirming that `silo solve` remains the LP-only command path.

Phase 5J designs the future MIP diagnostics output contract, keeping default `mip-solve` solution JSON compact while reserving opt-in summary diagnostics and optional node logs for later implementation tasks.

Phase 5K implements the first opt-in `silo mip-solve --details` summary diagnostics wrapper while keeping the default compact solution JSON unchanged and leaving detailed node logs for later work.

Phase 5L adds optional `silo mip-solve --details --node-log` output for stable per-node branch-and-bound diagnostics without changing search logic, default output, or summary-only diagnostics.

Phase 5M documents the node-log CLI workflow, including stdout and `--output` examples, without changing solver behavior.

Phase 5N records a completion audit in `tasks/reports/20260524-01-01_phase5-completion-audit_report.md`; it recommends user closure review before any roadmap status change or Phase 6 transition.

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
