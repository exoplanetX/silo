# SILO Development Rules for AI Coding Agents

1. Keep the dependency direction clean:
   core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty

2. The `core` package must not depend on LP, MIP, cuts, decomposition, or uncertainty modules.

3. Native algorithms must not call external solvers.

4. External solvers may only be used in `interfaces/`, examples, or tests for comparison.

5. Prefer clarity, correctness, and deterministic tests over performance in early phases.

6. Do not introduce large datasets, generated outputs, or binary files into git.

7. Every algorithmic module must include small deterministic tests.

8. Keep public APIs minimal and documented.

9. Do not silently change mathematical conventions. Record conventions in notes and docs.

10. Avoid premature optimization. First implement a readable reference version.
