# Branch-and-Bound Design Note

## 1. Purpose

Phase 5 adds the first native mixed-integer layer above SILO's continuous LP foundation. The correct next step is not an industrial MIP solver, but a small, deterministic, educational, pure branch-and-bound implementation that repeatedly solves LP relaxations with the existing native LP backends.

This design note fixes the first MIP scope before code is added. The purpose is to make the mathematical boundary explicit: the MIP layer owns integrality, branching, incumbent management, node selection, pruning, and MIP status interpretation, while the LP layer continues to solve only supported continuous LP relaxations. The branch-and-bound layer must not require new tableau or revised simplex behavior in its first implementation. It should construct LP models that respect the current solver contract.

The first implementation should be readable and testable. It should expose why a node was processed, pruned, branched, or used to update the incumbent. It should not claim performance beyond small deterministic fixtures. Cuts, heuristics, dual simplex reoptimization, advanced presolve, and commercial solver comparisons belong to later phases.

## 2. Current LP and Presolve Boundary

The current LP layer supports continuous maximization LPs with nonnegative variables and linear rows using `<=`, `>=`, and `=` senses. The tableau and revised simplex backends both solve the same supported class, and the CLI can select either backend for `silo solve`. The backends also expose primal values, slacks, reduced costs, and basis status for supported LPs, while dual values remain empty.

The current LP solvers deliberately reject several model features: minimization objectives, nonzero lower bounds, finite variable upper bounds, binary variables, and integer variables. This is the critical boundary for Phase 5. MIP models need binary and integer variables with finite bounds, but the LP relaxation sent to the simplex layer cannot contain those variable types or direct finite upper bounds.

The current presolve layer is conservative and opt-in. It can remove feasible empty rows, diagnose infeasible empty rows and empty columns, eliminate fixed variables, run repeated safe passes, recover fixed variables, recompute original-space slacks, and report scaling diagnostics. It does not run by default in `silo solve`, does not automatically scale, and does not include MIP presolve. Phase 5 should not depend on hidden presolve behavior. If future MIP solve paths use presolve, that should be an explicit later design decision.

Therefore, the first branch-and-bound layer should build each LP relaxation as a continuous maximization model with lower bound 0 and no finite variable upper bounds. Any binary, integer, or branching upper bound must be represented as an ordinary linear constraint row. This keeps the LP relaxation inside the existing simplex contract.

## 3. First Supported MIP Class

The first supported MIP class should be:

```text
maximize c^T x + c0
subject to linear rows with <=, >=, =
           continuous variables x_c >= 0 with no finite upper bounds
           binary variables x_b in {0, 1}
           bounded nonnegative integer variables x_i in {0, 1, ..., U_i}
```

All variables must have lower bound 0 in the first implementation. Continuous variables may not have finite upper bounds. Binary variables use their natural upper bound of 1. Integer variables must have finite upper bounds. This finite upper-bound requirement is stricter than a general MIP solver but appropriate for the first SILO implementation because it avoids ambiguous unbounded tree behavior and creates deterministic small fixtures.

The first implementation should reject minimization, negative lower bounds, nonzero lower bounds, semi-continuous variables, general finite lower bounds, SOS constraints, indicator constraints, quadratic objectives, quadratic constraints, nonlinear expressions, and unbounded general integer variables. It should also reject MIP models whose integer bounds cannot be represented as explicit rows under the current model conventions.

This scope is intentionally narrow. It still covers useful examples such as binary knapsack, binary choice, and bounded nonnegative integer allocation, while preserving a clean path from MIP model to LP relaxation.

## 4. LP Relaxation Construction

The MIP-to-LP relaxation builder should be a separate component, not embedded directly in the branch-and-bound loop. Given an original MIP model and a node, it should produce a new continuous LP model that the tableau or revised simplex backend can solve without further special cases.

For each continuous variable with lower bound 0 and no finite upper bound, the relaxation keeps a continuous variable with the same name, lower bound 0, and infinite upper bound. Objective coefficients are copied unchanged, and the objective constant is preserved.

For each binary variable, the relaxation creates a continuous variable with lower bound 0 and no finite upper bound, then adds an explicit row:

```text
x_j <= 1
```

This row represents the binary upper bound in the LP relaxation. Integrality is not represented in the relaxation; it is enforced only by branching and by integer-feasibility checks.

For each bounded nonnegative integer variable with upper bound `U_j`, the relaxation creates a continuous variable with lower bound 0 and no finite upper bound, then adds:

```text
x_j <= U_j
```

If `U_j` is not finite, the first implementation should reject the model before solving. Later implementations may allow unbounded integer variables if problem rows and branching constraints imply effective bounds, but that requires a stronger unboundedness design.

Node-local branching constraints are added as ordinary rows. For a fractional integer value `v`, the two children are:

```text
left child:  x_j <= floor(v)
right child: x_j >= ceil(v)
```

For binary variables, these become `x_j <= 0` and `x_j >= 1`. The relaxation builder should name generated rows deterministically, for example `__mip_bound_x_j_upper` for original integer upper bounds and `__mip_branch_n7_x_j_le` for branching rows. Generated names should be unlikely to collide with user rows. If a collision is possible, the builder should either reject the model or use a deterministic reserved prefix check.

The builder should not mutate the original model. It should return the relaxation model plus metadata that identifies generated bound rows and node rows. This metadata is useful for tests and future diagnostics.

## 5. Node Representation

The first implementation should use immutable node and branching constraint records. A conceptual structure is:

```python
@dataclass(frozen=True)
class BranchingConstraint:
    variable_name: str
    sense: ConstraintSense
    rhs: float

@dataclass(frozen=True)
class MIPNode:
    id: int
    depth: int
    local_bounds: tuple[BranchingConstraint, ...]
    parent_id: int | None = None
```

The branch-and-bound loop may also maintain evaluated node information:

```text
node id
depth
parent id
local branching constraints
LP relaxation status
LP relaxation objective bound
LP relaxation solution
prune reason
branching variable, if any
```

The immutable `MIPNode` should represent search-tree state before solving. Solver results and prune decisions can live in a separate result record or internal log entry. Keeping the node itself immutable makes deterministic tests easier and avoids accidental mutation when children are generated.

Local branching constraints should be accumulated from the root to the current node. The relaxation builder can simply append each node's constraints to the original model rows after adding integer upper-bound rows. This is less efficient than bound propagation but much clearer for the first version.

## 6. Branching Rule

The first branching rule should be:

```text
branch on the first fractional integer variable in original model variable order
```

Only binary and integer variables are checked for fractionality. Continuous variables are ignored. A value is integer-feasible when:

```text
abs(x_j - round(x_j)) <= integer_tolerance
```

The recommended default tolerance is:

```text
DEFAULT_INTEGER_TOLERANCE = 1e-6
```

This constant should be introduced only when implementation begins. The design intent is to keep integer feasibility separate from simplex feasibility tolerances.

For a fractional value `v`, children are:

```text
left child:  x_j <= floor(v)
right child: x_j >= ceil(v)
```

Tie-breaking is by model variable order. No strong branching, pseudo-cost branching, reliability branching, inference branching, or domain-specific branching should be included in the first implementation.

The child creation order must be documented. A simple convention is to create the left child first and the right child second, then push them onto a depth-first stack in reverse visit order so that the left child is processed before the right child. If implementation chooses the opposite order, tests must encode that choice. The important point is not which side is first, but that the order is stable and documented.

## 7. Node Selection Rule

The first node selection rule should be depth-first search using a stack. Depth-first search is simple, deterministic, and likely to find incumbents quickly on small educational examples. It also avoids introducing a priority queue and best-bound tie-breaking before the core solver loop is tested.

The root node has id `0` and depth `0`. Child ids should increase monotonically in creation order. Open nodes are stored in a stack. The implementation should document whether left or right is visited first and make tests assert the resulting node sequence.

Future node selection rules can include best-bound, breadth-first, hybrid depth-first/best-bound, or user-configurable strategies. These are out of scope for the first version because they add policy choices without improving the first correctness target.

## 8. Incumbent and Bounds

For maximization, the incumbent is the best known integer-feasible solution. If no incumbent exists:

```text
incumbent_value = -infinity
incumbent_solution = None
```

Each feasible LP relaxation gives an upper bound on the best MIP solution in that node's subtree. The global upper bound is the best LP relaxation bound among open or recently processed non-pruned nodes. In a simple first implementation, detailed global bound reporting can be conservative. The main pruning comparison at a node is:

```text
node_lp_bound <= incumbent_value + mip_tolerance
```

If true, the node cannot improve the incumbent and can be pruned by bound.

The MIP gap for maximization can be defined as:

```text
global_upper_bound - incumbent_value
```

If no incumbent exists, the gap is undefined. If no open nodes remain, the global upper bound may be reported as the incumbent value or `None`. The first public `Solution` does not need to include the gap. A detailed branch-and-bound result object can carry it for tests and future diagnostics.

Incumbent updates should store the rounded integer values only if they are within tolerance and preserve continuous values from the LP relaxation. The objective value should remain the LP objective value for the integer-feasible relaxation solution, not a separately rounded recomputation, unless future code adds a verified objective recomputation helper.

## 9. Pruning Logic

At each node, the solver builds the LP relaxation, solves it, and applies pruning in a deterministic order:

```text
1. LP relaxation infeasible -> prune by infeasibility.
2. LP relaxation error or numerical issue -> return or record an error.
3. LP relaxation unbounded -> handle conservatively.
4. LP relaxation bound cannot beat incumbent -> prune by bound.
5. LP relaxation solution is integer-feasible -> update incumbent and prune.
6. Otherwise branch on the first fractional integer variable.
```

For LP infeasibility, the node subtree is infeasible because adding more branching constraints cannot restore feasibility. For bound pruning, the LP relaxation is an upper bound for a maximization subtree, so a bound no better than the incumbent can be discarded.

LP unboundedness is delicate. An unbounded LP relaxation does not always mean the MIP is unbounded if fractional variables or future branching could restrict part of the direction, but in the first supported class all integer variables are explicitly bounded. If all integer variables are bounded and continuous variables are allowed to be unbounded, an unbounded relaxation usually indicates an unbounded continuous improving direction that branching on bounded integer variables cannot remove. The first implementation should still treat this conservatively: either return `UNBOUNDED` only for clearly tested cases where integer variables are already bounded and the LP direction cannot be cut by branching, or return `ERROR` with a clear message for unsupported unbounded MIP interpretation. Primary fixtures should avoid unbounded MIP cases until this behavior is specified by tests.

## 10. Status Mapping and Solution Output

The first MIP layer should reuse existing `SolverStatus` values:

```text
OPTIMAL
INFEASIBLE
UNBOUNDED
ITERATION_LIMIT
NUMERICAL_ISSUE
ERROR
```

`NOT_SOLVED` should remain appropriate only for placeholders or solver objects that have not run. A future node limit, time limit, or iteration limit can map to `ITERATION_LIMIT` before introducing a separate `NODE_LIMIT` status. Introducing new public statuses should be deferred until there is a concrete need and corresponding solution-writer behavior.

The public `Solution` returned by the first MIP solver should include:

```text
status
objective_value
primal_values
message
```

For the first implementation, `slack_values`, `dual_values`, `reduced_costs`, and `basis_status` may remain empty. MIP dual values and reduced costs are not meaningful in the same way as final LP relaxation fields, and exposing them could mislead users. Slack recovery for the incumbent can be added later if a shared helper is introduced.

A more detailed internal or optional result object is recommended:

```python
@dataclass(frozen=True)
class BranchAndBoundResult:
    solution: Solution
    nodes_processed: int
    nodes_pruned: int
    best_bound: float | None
    incumbent_value: float | None
```

The detailed result can also include node logs, prune counts by reason, and selected backend. The public CLI should not be expanded until this result contract is stable.

## 11. Determinism and Logging

Determinism is a first-class requirement. The first implementation should use:

```text
variable order from model.variables
constraint order from model.constraints
node ids increasing in creation order
fixed depth-first stack behavior
fixed child creation and visit order
deterministic generated row names
deterministic integer and MIP tolerances
```

Lightweight development logs should record:

```text
node id
depth
LP status
LP objective bound
incumbent update
prune reason
branching variable
child node ids
```

This does not require a logging framework in the first task. A list of immutable event records or simple internal diagnostics is enough. The design goal is traceability for tests and future documentation, not verbose user-facing output.

## 12. Module Layout

The first implementation should keep MIP responsibilities under `src/silo/mip/` and preserve the dependency direction `core <- modeling <- presolve <- lp <- mip`.

Recommended files:

```text
src/silo/mip/relaxation.py
src/silo/mip/node.py
src/silo/mip/branching.py
src/silo/mip/node_selection.py
src/silo/mip/incumbent.py
src/silo/mip/branch_and_bound.py
tests/unit/test_mip_relaxation.py
tests/unit/test_branch_and_bound.py
```

`relaxation.py` should build continuous LP relaxation models from MIP models and node constraints. It should convert binary and integer upper bounds into explicit rows and reject unsupported variable bounds.

`node.py` should define `MIPNode`, `BranchingConstraint`, and possibly prune reason enums or result records. It should avoid importing LP solver modules.

`branching.py` should choose the first fractional integer variable and create deterministic child constraints.

`node_selection.py` should define the first stack-based depth-first policy. A tiny class or helper functions are enough.

`incumbent.py` should manage incumbent comparison and updates for maximization.

`branch_and_bound.py` should orchestrate the main solver loop, call the relaxation builder, call the selected LP backend, prune, update incumbents, and branch.

## 13. Testing Strategy

Implementation should begin with relaxation-builder tests before the solver loop. Tests should verify that binary and integer variables are converted to continuous LP variables and that finite upper bounds are represented by explicit rows.

First MIP fixtures should include:

Binary knapsack:

```text
maximize 6x1 + 10x2 + 12x3
subject to x1 + 2x2 + 3x3 <= 5
x1, x2, x3 binary
```

Expected optimum: `x2 = 1`, `x3 = 1`, objective `22`.

Simple binary choice:

```text
maximize x + y
subject to x + y <= 1
x, y binary
```

Expected objective: `1`, with deterministic tie behavior based on variable order and node order.

Bounded integer model:

```text
maximize 3x + 2y
subject to 2x + y <= 4
x integer in [0, 2]
y integer in [0, 3]
```

Expected optimum: `x = 1`, `y = 2`, objective `7`.

Infeasible MIP:

```text
x binary
x >= 1
x <= 0
```

Expected status: `INFEASIBLE`.

Deterministic branching test: construct a model whose LP relaxation has two fractional integer variables. The expected first branching variable is the first fractional integer variable in original model order.

Pruning tests should cover LP infeasible prune, bound-dominated prune, integer-feasible incumbent update, and deterministic DFS node order. Error tests should verify rejection of minimization, nonzero lower bounds, continuous finite upper bounds, unbounded integer variables, and unsupported variable types or bounds.

## 14. Implementation Phases

Phase 5 should be split into small tasks:

```text
Phase 5A: branch-and-bound design note.
Phase 5B: MIP-to-LP relaxation builder.
Phase 5C: MIP node, branching constraint, node log, and incumbent dataclasses.
Phase 5D: pure depth-first branch-and-bound for binary variables.
Phase 5E: bounded nonnegative integer variables.
Phase 5F: CLI naming discussion, such as --solver mip or silo mip-solve.
Phase 5G: MIP regression examples and documentation.
```

Phase 5B should come before the solver loop because the LP relaxation boundary is the main technical risk. Phase 5D should initially solve binary-only fixtures. Bounded integer variables can follow once child constraints and integer upper-bound rows are stable. CLI work should be deferred until the Python API and result contract are tested.

## 15. Out of Scope for the First Implementation

The first implementation should exclude branch-and-cut, cut generation, lazy constraints, primal heuristics, strong branching, pseudo-costs, reliability branching, conflict analysis, MIP presolve, automatic scaling, dual simplex reoptimization, warm-started LP relaxations, parallel tree search, advanced node selection, commercial solver comparison, large benchmarks, and performance claims.

It should also avoid changing the JSON model format or solution JSON schema. Existing core model objects already include binary and integer variable types, and the first MIP implementation can use those. If future CLI support needs additional MIP diagnostics, the project should first define a structured result object rather than forcing MIP-specific fields into the generic `Solution` dataclass.
