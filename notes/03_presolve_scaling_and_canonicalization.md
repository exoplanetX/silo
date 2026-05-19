# Presolve, Scaling, and Canonicalization

Canonicalization converts user-facing model objects into the conventions expected by solver algorithms. Presolve changes the model to make it smaller or numerically safer. Scaling changes numerical representation. These steps are related but should not be conflated.

In early SILO phases, canonicalization should remain deterministic and conservative. The model should preserve variable order, constraint order, objective sense, row senses, bounds, and coefficient values in a predictable representation. This makes tests easy to read and helps identify convention errors before simplex implementation begins.

Presolve should start with reversible transformations: fixed-variable elimination, bound tightening, redundant-row detection for simple cases, and empty-row checks. Every transformation should record enough information to reconstruct original-space solutions. A presolve pass that improves speed but loses traceability would violate the project purpose.

Scaling should first be diagnostic. The project can report large coefficient ranges, zero rows, or ill-conditioned toy examples before applying automatic scaling. Numerical transformations should be introduced only with tests that explain how primal values, dual values, and objective values are mapped back to the original model.
