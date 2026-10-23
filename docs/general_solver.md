# Unified general-form solver

Use `from silo import solve, SolveOptions`; call `solve(model, options)` for
`min/max c0+c'x`, `row_lower <= Ax <= row_upper`, and variable intervals.
Continuous, integer and binary variables are supported. Infinity represents a
missing side; coefficients and constants must be finite. Unrepresentable integer
conversion returns `numerical_failure/input_conversion` before changing the lattice.

```python
from silo import SolveOptions, solve
from silo.io import model_from_dict

model = model_from_dict({
    "name": "mixed", "sense": "minimize",
    "variables": [{"name": "x", "lower": 0, "upper": 3, "type": "integer"},
                  {"name": "y", "lower": 0, "upper": 4}],
    "constraints": [{"name": "d", "coefficients": {"x": 2, "y": 1}, "lower": 3}],
    "objective": {"coefficients": {"x": 1, "y": 1}},
})
result = solve(model, SolveOptions(time_limit=60, node_limit=100000))
assert result.status == "optimal" and abs(result.objective_value - 2) < 1e-7
```

Python results retain an immutable `basis` snapshot for LP reoptimization.
`LPSession` owns its model and supports RHS, row/variable bounds, rows and columns.
JSON schema2 includes primal/dual bounds, signed infinity kinds, gap and the
separate termination reason. Limit results may contain a verified incumbent.
Unresolved unbounded MILP relaxations retain an infinite bound and no finite gap.
LP row duals/side multipliers apply to the original continuous problem; MILP
results expose tree bounds rather than LP shadow prices.

| Control | Default | Meaning |
|---|---|---|
| `time_limit`, `node_limit`, `lp_iteration_limit` | infinity,100000,10000 | Shared search wall, processed nodes, LP pivot budget |
| `relative_gap`, `absolute_gap` | 0,0 | Positive values enable early gap termination |
| `presolve`, `scaling`, `cuts`, `heuristics` | all True | Actual native mechanisms, with counters |
| `node_strategy`, `lp_method` | best_bound,auto | DFS alternative; primal/dual eligible warm bases |
| primal/dual/integrality tolerances | 1e-7 each | Separate original feasibility, stationarity and integer checks |
| pivot/complementarity/objective tolerances | 1e-10,1e-7,1e-7 | Separate numerical decisions |
| `max_dense_cells` | 2000000 | Conservative preallocation size gate |
| `cut_round_limit`, `cuts_per_round`, `cut_depth_limit` | 2,3,2 | Bounded local GMI loop |
| `proof_operation_limit`, `integer_ray_proof_limit` | 2000000,1000000 | Exact proof work and integer-ray multiplier caps |

`relative_gap=abs(P-D)/max(1,abs(P),abs(D))`; the normalized search uses
`F=s*f`, s=+1 for min/-1 for max, and translates bounds back on output.
The [frozen mathematical contract](prototype_model_contract.md) defines KKT and
residual conventions. [Numeric details](numeric_engine.md), [MIP](branch_and_cut.md)
and [research interfaces](research_api.md) document the algorithm boundaries.

CLI: `silo optimize model.json` or `python -m silo optimize model.mps`.
Flags include `--time-limit`, `--node-limit`, `--lp-iteration-limit`,
`--relative-gap`, `--absolute-gap`, `--node-strategy`, `--lp-method`,
`--no-presolve`, `--no-scaling`, `--no-cuts`, `--no-heuristics`, `--output`.
Exit codes: optimal0, infeasible2, unbounded3, limit4, numerical_failure5,
invalid_model6, unsupported7, file-output error1.

The prototype uses dense NumPy QR and Python reference algorithms. Frozen inputs
bound the measured domain; they give no arbitrary-instance time guarantee or
industrial-performance claim. Native code never calls SciPy or another solver.
