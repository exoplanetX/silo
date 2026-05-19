# Simplex Basis and Reoptimization

The simplex method is most useful in a solver architecture when it is understood as a basis method, not merely as a loop over tableau entries. A basis identifies the variables that define the current basic solution. Feasibility and optimality are then checked through the relationship between the basis, the right-hand side, the objective coefficients, and reduced costs.

SILO should first implement tableau simplex because it exposes the algebra directly. After that, the revised simplex layer should introduce explicit basis objects. A basis should record basic and nonbasic variables, and later it should support status labels for lower-bound, upper-bound, basic, and fixed variables. This is necessary for variable bounds, presolve reconstruction, and MIP relaxation solves.

Reoptimization matters because solver layers rarely solve isolated LPs. In branch-and-bound, child nodes differ from their parent by one additional bound. In decomposition, the master problem gains cuts or columns over iterations. A revised simplex implementation can reuse a previous basis as a warm start. SILO should not implement sophisticated factor updates at first, but it should design interfaces that do not prevent them.

Early tests should compare tableau and revised simplex on the same small LPs. Once both solvers agree on objective values, primal solutions, and statuses, revised simplex can become the preferred LP backend for higher layers. Basis-level diagnostics should remain visible in tests because silent basis convention changes can break MIP and decomposition behavior.
