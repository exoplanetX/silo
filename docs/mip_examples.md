# MIP JSON Examples

## Purpose

The files under `examples/mip/` are checked-in JSON models for the native branch-and-bound Python API. They provide small deterministic regression examples before SILO exposes any user-facing MIP CLI command.

## Current Solver Scope

The current branch-and-bound solver supports maximization models with linear constraints, binary variables, bounded nonnegative integer variables, and optional compatible continuous variables. Continuous variables must have lower bound `0` and no finite upper bound. Integer variables must have lower bound `0` and a finite integer-valued upper bound.

## How to Run from Python

```python
from silo.io.json_reader import read_json_model
from silo.mip.branch_and_bound import BranchAndBoundSolver

model = read_json_model("examples/mip/binary_knapsack.json")
solution = BranchAndBoundSolver().solve(model)
print(solution.status, solution.objective_value)
```

Use `solve_with_details(model)` when tests or diagnostics need node counts, incumbent value, best bound, or node logs.

## Examples

- `binary_knapsack.json`: binary knapsack with expected objective `22`.
- `binary_choice.json`: two binary alternatives with expected objective `1`.
- `integer_allocation.json`: bounded nonnegative integer allocation with expected objective `7`.
- `mixed_binary_integer.json`: mixed binary and bounded integer model with expected objective `11`.
- `mixed_continuous_integer.json`: bounded integer plus compatible continuous variable with expected objective `11`.
- `infeasible_binary.json`: infeasible binary model.

## Current CLI Status

MIP examples are not yet exposed through a dedicated CLI command. `silo solve` currently uses LP backends and is not the MIP interface. Do not use `silo solve examples/mip/...` as a MIP solve command.

## Limitations

The current MIP path has no cuts, heuristics, callbacks, branch-and-cut, minimization, general lower bounds, unbounded integer variables, or MIP CLI. It is a small deterministic reference implementation intended for early Phase 5 tests and examples.
