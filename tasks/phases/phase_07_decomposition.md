# Phase 7: Decomposition Layer

## Goal

Add educational master-subproblem abstractions for decomposition methods after the LP and MIP layers have stable interfaces.

Phase 7A records the decomposition boundary design in `notes/19_decomposition_boundary_design.md`; it is design-only and includes no implementation.

Phase 7B upgrades the existing decomposition placeholder modules with immutable master/subproblem context and result records plus validation tests; it does not implement Benders or column-generation solve loops.

Phase 7C adds immutable decomposition method, termination-reason, iteration-log, and run-summary records with validation tests; it does not implement Benders or column-generation solve loops or call LP/MIP solvers.

Phase 7D adds boundary smoke tests confirming placeholder Benders and column-generation solvers remain no-op `not_solved` boundaries while decomposition logging records stay separate from public `Solution` schemas and lower layers do not import decomposition.

Phase 7E adds immutable Benders cut type and candidate records with validation and deterministic canonical-key tests; it does not implement Benders cut generation, solve loops, LP/MIP solver calls, or cut materialization.

Phase 7F adds immutable column candidate records with validation, deterministic canonical-key tests, and reduced-cost convention tests; it does not implement pricing logic, column-generation solve loops, or LP/MIP solver calls.

Phase 7G adds a no-op decomposition driver boundary that records one deterministic iteration in a run summary; it does not accept models, call LP/MIP solvers, or implement Benders/column-generation solve loops.

Phase 7H adds a toy fixture-only Benders-style driver with deterministic no-cut, duplicate-cut, and iteration-limit stopping tests; it does not implement a general Benders solver, call LP/MIP solvers, or materialize cuts.

Phase 7I adds a toy fixture-only column-generation-style driver with deterministic no-improving-column, duplicate-column, and iteration-limit stopping tests; it does not implement general column generation, branch-and-price, restricted-master solves, or LP/MIP solver calls.

Phase 7J adds checked-in educational examples for the existing toy Benders and toy column-generation drivers; it does not modify solver source code, tests, CLI behavior, JSON schemas, or LP/MIP behavior.

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
