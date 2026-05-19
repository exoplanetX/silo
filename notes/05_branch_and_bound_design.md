# Branch-and-Bound Design

Branch-and-bound should be implemented as a state machine over nodes, not as a deeply nested script. Each node represents a relaxation of a subset of the feasible region. The solver processes nodes until none remain or a termination limit is reached.

The basic node lifecycle is: apply local bounds, solve LP relaxation, classify the result, prune or branch, and update global search state. The solver should record enough information to explain why a node was pruned. This is useful for tests and for diagnosing incorrect optimality claims.

Branching should be deterministic at first. A simple rule can select the first fractional integer variable by model order. Node selection should also be deterministic, such as depth-first search. More advanced rules can be added later only after the simple behavior is tested.

The MIP layer should not depend on external solvers except through controlled interfaces. Native branch-and-bound should call the project LP interface. External solvers may be used in tests for comparison, but they should not define the internal architecture.
