# Phase 7: Decomposition Layer

## Goal

Add educational master-subproblem abstractions for decomposition methods after the LP and MIP layers have stable interfaces.

## Scope

This phase covers master problem wrappers, subproblem wrappers, Benders-style iteration structure, column-generation iteration structure, and small examples that expose decomposition logic.

## Expected Files

- `src/silo/decomposition/master.py`
- `src/silo/decomposition/subproblem.py`
- `src/silo/decomposition/benders.py`
- `src/silo/decomposition/column_generation.py`
- `tests/unit/test_decomposition.py`

## Algorithmic Requirements

Keep decomposition methods explicit and educational. Benders and column-generation modules should communicate through model, solution, cut, or column objects with documented assumptions. Iteration logs should be deterministic.

## Testing Requirements

Add toy Benders and column-generation smoke tests once the dependent LP layer is available. Tests should verify subproblem status handling, generated cuts or columns, and deterministic stopping behavior.

## Do Not Do

Do not build a general decomposition framework before small examples work. Do not hide external solver calls inside native decomposition algorithms.

## Acceptance Criteria

Decomposition examples expose the master-subproblem structure and remain optional layers above the core modeling and LP interfaces.
