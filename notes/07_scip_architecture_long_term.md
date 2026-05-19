# SCIP Architecture as Long-Term Inspiration

SCIP is valuable as long-term inspiration because it treats a solver as a collection of cooperating plugins: presolvers, separators, branching rules, primal heuristics, pricing routines, constraint handlers, and node selectors. This architecture is powerful because optimization problems vary widely. Different problem structures benefit from different algorithmic components.

SILO should learn from the plugin idea without imitating SCIP's full complexity at the beginning. A project that starts by copying every plugin category would become difficult to understand before it can solve small models. The right sequence is to define stable minimal interfaces first, then introduce plugin-style extension points only when there is a concrete algorithmic need.

Possible future modules include presolvers, separators, branching rules, primal heuristics, pricing, and constraint handlers. Presolvers can simplify models before solving. Separators can generate valid inequalities. Branching rules can choose disjunctions. Primal heuristics can search for feasible integer solutions. Pricing modules can generate variables for column generation. Constraint handlers can represent structured constraints beyond flat linear rows.

The long-term architecture should preserve SILO's educational value. A plugin boundary should make an algorithm easier to test and replace; it should not become an abstract layer with no immediate purpose. Each extension point should come with a small example and deterministic tests. For example, before a general separator registry exists, the project should have at least one simple separator and a test showing how it affects an LP relaxation.

SCIP also shows why solver status, transformation history, and numerical diagnostics are critical. When many components interact, silent convention changes can be damaging. SILO should record conventions in notes and tests before adding complexity.

The guiding principle is staged growth. Start with core model objects and canonicalization. Add tableau simplex. Add revised simplex and basis state. Add presolve. Add branch-and-bound. Add cuts and callbacks. Only then consider broader plugin registries. This allows the architecture to mature from tested needs rather than from decorative abstraction.
