# Stochastic and Robust Extensions

Stochastic and robust optimization should first be treated as modeling extensions. A stochastic model with finite scenarios can often be transformed into a deterministic equivalent. A robust model can sometimes be converted into a robust counterpart, depending on the uncertainty set and the constraint structure.

SILO should not introduce a separate stochastic solver before deterministic LP and MIP layers are stable. Instead, uncertainty modules should build or transform ordinary model objects. This keeps the solver stack coherent and makes uncertainty behavior testable through canonical forms.

Scenario objects should record names, probabilities, and later scenario-specific data. Robust uncertainty sets should record parameters and assumptions. Deterministic-equivalent builders should be explicit about variable replication, nonanticipativity constraints, and objective weighting.

Early examples should be tiny: a two-scenario production model or a simple budgeted uncertainty bound. The goal is to test transformation logic, not to solve large stochastic programs.
