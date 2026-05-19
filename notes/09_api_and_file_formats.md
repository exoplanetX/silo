# API and File Formats

SILO should expose two stable entry points: a Python API and simple file-based input. The Python API is the primary interface for learning and experimentation. JSON fixtures are useful for tests because they are readable, deterministic, and easy to inspect.

The early JSON format should stay close to the core model: variables, bounds, variable types, objective sense, objective coefficients, constraints, row senses, and right-hand sides. It should avoid advanced solver options until the solver has meaningful algorithms.

Solution output should also be explicit. A solution file should include status, objective value, primal values, dual values, reduced costs, and a message. Missing values should be represented plainly rather than inferred by readers.

Later, SILO may read standard formats such as MPS or LP. Those formats are useful, but they add parsing complexity. The first priority is a small internal format that supports tests, examples, and CLI smoke checks.
