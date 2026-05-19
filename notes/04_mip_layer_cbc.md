# MIP Layer: CBC as a Branch-and-Cut Reference

CBC is a useful learning reference for SILO because it presents mixed-integer optimization as an organized branch-and-cut process rather than a single monolithic algorithm. The core idea is simple: solve an LP relaxation, inspect integrality, branch when needed, update bounds and incumbents, and optionally separate cuts. The engineering details become complex, but the conceptual structure is accessible and should guide the SILO MIP layer.

SILO should initially treat MIP as repeated LP relaxation plus tree search. A node carries local bound changes or branching constraints. The LP relaxation returns a status and a relaxation solution. If the relaxation is infeasible, the node is pruned. If the relaxation bound cannot improve the incumbent, the node is pruned. If the relaxation solution is integral, it may update the incumbent. Otherwise, the MIP layer chooses a fractional variable and creates child nodes.

The key objects should be explicit. A `Node` stores local restrictions and depth. An `Incumbent` stores the best known feasible integer solution. A global bound records the best remaining relaxation information. A branching rule chooses the disjunction. A node-selection rule chooses which open node to process next. A cut pool stores globally or locally valid inequalities once cuts are introduced.

The first SILO MIP target should be pure branch-and-bound. Cuts, heuristics, callbacks, conflict analysis, and advanced presolve can wait. A pure branch-and-bound implementation is enough to test the relationship between variable types, LP relaxation, incumbent updates, and deterministic tree traversal. Binary knapsack and tiny integer programs are sufficient early fixtures.

CBC can inspire the later branch-and-cut architecture, but SILO should not import CBC's complexity too early. The goal is to make each layer testable: LP solve, node processing, branching decision, incumbent update, pruning rule, and final status. Once that behavior is clear, cut generation can enter through `cuts.separator` and `cuts.cut_pool` without rewriting the MIP search loop.
