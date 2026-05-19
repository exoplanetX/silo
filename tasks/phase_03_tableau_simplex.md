# Phase 3: Tableau Simplex

## Goal

Implement an educational tableau simplex solver for small continuous LPs.

## Scope

This phase covers standard-form conversion, slack variables, Phase I and Phase II, pivot selection, ratio test, infeasible and unbounded detection, and known-solution LP tests.

## Expected Files

- `src/silo/lp/simplex/tableau.py`
- `src/silo/lp/simplex/phase_one.py`
- `src/silo/lp/simplex/phase_two.py`
- `src/silo/lp/simplex/pivot.py`
- `src/silo/lp/simplex/pricing.py`
- `src/silo/lp/simplex/ratio_test.py`
- `tests/unit/test_tableau_simplex.py`

## Algorithmic Requirements

Implement a readable reference version for small dense LPs. Support `<=`, `>=`, and `=` rows through explicit transformation. Detect optimal, infeasible, and unbounded statuses. Keep pivot choices deterministic.

## Testing Requirements

Use known-solution LPs, infeasible examples, unbounded examples, equality rows, and degeneracy smoke cases. Tests should check status, objective value, and primal values within a documented tolerance.

## Do Not Do

Do not optimize for large sparse models. Do not add revised simplex or advanced numerical scaling in this phase.

## Acceptance Criteria

The tableau solver solves small fixtures correctly and returns clear messages for unsupported or failed cases.
