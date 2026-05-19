# Phase 3: Revised Simplex and Basis Reoptimization

## Goal

Introduce basis-oriented LP solving and prepare the LP layer for reoptimization in MIP and decomposition.

## Scope

This phase adds explicit basis state, reduced-cost computation, primal feasibility checks, and a revised simplex loop for small LPs.

The Phase 3 implementation should follow `notes/10_revised_simplex_design.md`. Start with a standard-form builder and a `Basis` dataclass before adding the revised simplex loop.

## Expected Files

- `src/silo/lp/simplex/basis.py`
- `src/silo/lp/simplex/standard_form.py`
- `src/silo/lp/simplex/factorization.py`
- `src/silo/lp/simplex/revised.py`
- `src/silo/lp/base.py`
- `tests/unit/test_revised_simplex.py`

## Algorithmic Requirements

Represent basic and nonbasic variables explicitly. Compute primal values and reduced costs from the current basis. Allow deterministic initialization from a simple slack basis when available.

## Testing Requirements

Compare revised simplex against tableau simplex on shared fixtures. Add tests for basis updates, reduced costs, infeasible basis detection, and simple RHS reoptimization.

## Do Not Do

Do not implement industrial sparse factorization, crash basis heuristics, or advanced anti-degeneracy techniques yet.

## Acceptance Criteria

Revised simplex matches tableau results on small LP fixtures and exposes basis information for future MIP use.
