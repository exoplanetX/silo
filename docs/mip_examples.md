# MIP JSON Examples

## Purpose

The files under `examples/mip/` are checked-in JSON models for the native branch-and-bound Python API and `silo mip-solve` CLI. They provide small deterministic regression examples for the current supported MIP scope.

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

## How to Run from CLI

```bash
silo mip-solve examples/mip/binary_knapsack.json
```

Use [MIP Solve CLI](mip_solve_cli.md) for command options and exit-code behavior.

## Examples

- `binary_knapsack.json`: binary knapsack with expected objective `22`.
- `binary_choice.json`: two binary alternatives with expected objective `1`.
- `integer_allocation.json`: bounded nonnegative integer allocation with expected objective `7`.
- `mixed_binary_integer.json`: mixed binary and bounded integer model with expected objective `11`.
- `mixed_continuous_integer.json`: bounded integer plus compatible continuous variable with expected objective `11`.
- `infeasible_binary.json`: infeasible binary model.

## Current CLI Status

MIP examples are exposed through `silo mip-solve`. `silo solve` remains the continuous LP solve path and does not silently route MIP models to branch-and-bound.

## Limitations

The current MIP path has no cuts, heuristics, callbacks, branch-and-cut, minimization, general lower bounds, unbounded integer variables, MIP presolve, or detailed node-count JSON. It is a small deterministic reference implementation intended for early Phase 5 tests and examples.
