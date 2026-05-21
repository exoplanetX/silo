# MIP CLI Exposure Design Note

## 1. Purpose

SILO now has a small native branch-and-bound path for mixed-integer models through the Python API. Users can read a JSON model with binary or bounded nonnegative integer variables and solve it with `BranchAndBoundSolver`. That is enough for deterministic examples and regression tests, but it is not yet exposed as a public command-line workflow.

The design question is how to expose MIP solving without changing the meaning of the existing LP-oriented CLI. Today, these commands have a narrow and useful meaning:

```bash
silo solve MODEL_PATH
silo solve MODEL_PATH --solver tableau
silo solve MODEL_PATH --solver revised
```

They load a JSON model and solve it with an LP backend. The `--solver` flag selects an LP simplex backend, not a modeling class and not a MIP algorithm. If MIP support is added casually to the same surface, users may not be able to tell whether they are selecting an LP algorithm, a MIP algorithm, or an internal relaxation backend.

The purpose of this note is to set a conservative first CLI boundary. The first public MIP command should make the modeling class explicit, preserve existing `silo solve` behavior, and leave room for later MIP diagnostics without expanding the solution schema too early.

## 2. Current CLI Boundary

The current public CLI has three main solver-facing commands:

```text
silo solve       -> LP solve using tableau or revised backend
silo compare     -> compare LP tableau and revised backends
silo presolve    -> presolve and scaling diagnostics
```

The `solve` command reads a JSON model and sends it to one LP backend. Its solver choices are:

```text
tableau
revised
```

Both are LP simplex implementations. The default remains `tableau`, while `revised` is available for basis-oriented workflows and backend comparison. The `compare` command is also LP-specific: it runs compatible LP backends and reports whether their public solution fields agree. The `presolve` command reports conservative LP-oriented reductions and diagnostics; solve-time presolve is opt-in through `silo solve --presolve`.

MIP branch-and-bound is different. It solves a MIP by repeatedly solving LP relaxations, but it is not itself an LP backend. It may use tableau or revised simplex internally, yet the branch-and-bound layer owns node selection, branching, incumbent handling, pruning, and final MIP status mapping. Therefore, the MIP command line should not describe branch-and-bound as just another `--solver` value beside `tableau` and `revised`.

## 3. Why MIP Needs an Explicit CLI Boundary

A command such as:

```bash
silo solve examples/mip/binary_knapsack.json
```

is ambiguous under the current design. The command name says "solve", but the implemented behavior means "solve as a continuous LP with the selected LP backend". A MIP JSON model contains binary or integer variable declarations. LP backends currently reject those variables because they are not continuous LP variables in the supported LP path. By contrast, `BranchAndBoundSolver` can solve the same model if its variables are inside the supported MIP class.

This distinction is not cosmetic. LP solve and MIP solve have different algorithmic contracts, different failure modes, and different options. In the LP path, `--solver revised` means "use the revised simplex backend." In a MIP path, a revised simplex backend would only solve node relaxations; it would not replace branch-and-bound. If the CLI hides that difference, users may infer that `revised` is a MIP solver or that `branch-and-bound` is an LP backend.

The first rule should therefore be:

```text
LP solve and MIP solve are different command paths.
```

Later versions may add a unified command after careful model-class detection and documentation. The first public MIP exposure should instead choose clarity over elegance.

## 4. Candidate Command Designs

### Option A: `silo mip-solve MODEL_PATH`

Example:

```bash
silo mip-solve examples/mip/binary_knapsack.json
```

This option creates a new top-level command for MIP solving. Its main advantage is that it separates the modeling class from the existing LP command. Users can see that `silo solve` remains the LP workflow, while `silo mip-solve` invokes branch-and-bound. It also avoids overloading `--solver`: the MIP command can use a different flag, such as `--lp-solver`, for the internal LP relaxation backend.

The command is simple to document and test. It fits the current command style, which uses direct top-level verbs such as `solve`, `compare`, and `presolve`. The main downside is that it adds another top-level command. It is also slightly less elegant than a unified `solve` command. For the current project stage, that tradeoff is acceptable because semantic clarity is more important than a compact command surface.

### Option B: `silo solve MODEL_PATH --mip`

Example:

```bash
silo solve examples/mip/binary_knapsack.json --mip
```

This option keeps one `solve` command and requires an explicit flag for MIP routing. It is easy to type and makes the modeling class visible when the flag is present. However, it makes the existing command more complex. A user who forgets `--mip` would still get LP-path behavior or an LP validation error. The command also has unclear interactions with existing flags. For example, `silo solve MODEL_PATH --mip --solver revised` could be read as selecting a MIP solver, an LP relaxation backend, or both.

The flag also raises questions about `--presolve`. Current solve-time presolve is LP-oriented. If `--mip` appears on the same command, users may expect `--presolve` to be a MIP presolve, which is not implemented. This option should wait until the project has a stronger unified solve design.

### Option C: `silo solve MODEL_PATH --solver branch-and-bound`

Example:

```bash
silo solve examples/mip/binary_knapsack.json --solver branch-and-bound
```

This option reuses the existing `--solver` concept, but that is also its main problem. Today, `--solver` means LP backend and accepts `tableau` or `revised`. Branch-and-bound is a MIP algorithm that still needs an LP backend for relaxations. Placing it beside LP backends would mix two levels of the solver stack in one option.

This design should be rejected for the first version. It obscures the dependency direction and makes future flags harder to name. If branch-and-bound is selected through `--solver`, the CLI still needs another flag for the relaxation backend, and users may not understand why two solver flags exist.

### Option D: `silo mip MODEL_PATH` or `silo mip solve MODEL_PATH`

Examples:

```bash
silo mip examples/mip/binary_knapsack.json
silo mip solve examples/mip/binary_knapsack.json
```

A MIP namespace could scale well if SILO later adds `mip inspect`, `mip relax`, `mip compare`, or node-log diagnostics. The nested form `silo mip solve` is especially clean for a larger CLI.

The drawback is that the current argparse structure is intentionally simple. Introducing nested subcommands now may add structure before there are enough MIP commands to justify it. The shorter `silo mip MODEL_PATH` also makes "mip" both a noun and a command, which is less explicit than `mip-solve`. This option may become attractive later, but it is more CLI architecture than the first exposure needs.

## 5. Recommended First Command

The recommended first command is:

```bash
silo mip-solve MODEL_PATH
```

For example:

```bash
silo mip-solve examples/mip/binary_knapsack.json
```

and, when writing output:

```bash
silo mip-solve examples/mip/binary_knapsack.json --output outputs/knapsack_solution.json
```

This command is explicit, preserves existing `silo solve` behavior, and keeps LP backend selection separate from MIP algorithm selection. It also matches the current simple command style. The name says what the command does without implying that MIP models are automatically routed through the LP solve command.

The first implementation should keep branch-and-bound as the only MIP algorithm. There is no need for a `--mip-solver` flag until there are multiple MIP algorithms. The command should document that it supports the same small class currently supported by the Python API: maximization models with binary variables, bounded nonnegative integer variables, and compatible continuous variables.

## 6. First-Version Flags

The first version should support only a small set of flags:

```text
--output / -o
--lp-solver tableau|revised
--node-limit N
```

`--output` should mirror the existing `silo solve` behavior. If it is omitted, solution JSON is printed to stdout. If it is present, SILO writes the solution JSON to the requested path.

`--lp-solver` should select the LP relaxation backend used inside branch-and-bound:

```bash
silo mip-solve examples/mip/binary_knapsack.json --lp-solver tableau
silo mip-solve examples/mip/binary_knapsack.json --lp-solver revised
```

The default should be `tableau`, matching the current LP solve default and the early educational backend. This flag should not be named `--solver` in the first MIP command because `--solver` already means LP backend in `silo solve`. The longer name is deliberate: it tells users that tableau and revised are relaxation solvers, not MIP algorithms.

`--node-limit` should expose the existing branch-and-bound limit:

```bash
silo mip-solve examples/mip/binary_knapsack.json --node-limit 1000
```

The default should match `BranchAndBoundSolver`. The CLI should validate it as a nonnegative integer. A zero limit should be accepted if the Python API accepts it, and should return the solver's corresponding limit status rather than being treated as an argparse error.

## 7. Output JSON and Exit Codes

The first MIP CLI should reuse the existing solution JSON schema:

```text
status
objective_value
primal_values
slack_values
dual_values
reduced_costs
basis_status
message
```

For MIP solutions, these fields should normally be populated:

```text
status
objective_value
primal_values
message
```

The LP-specific fields may remain empty:

```text
slack_values
dual_values
reduced_costs
basis_status
```

The first version should not add node counts, best bounds, gaps, or node logs to the public solution JSON. Those are useful diagnostics, but adding them to the default schema would widen the public contract. If detailed MIP output is needed later, it should be designed through a separate `--details` or `--log` option.

Exit codes should mirror `silo solve`:

```text
0 = status optimal
1 = non-optimal status or read/write error
2 = argparse usage error
```

An infeasible MIP should return a valid solution JSON with status `infeasible` and exit code `1`, consistent with the current LP solve convention for non-optimal statuses.

## 8. Relationship to Presolve and LP Backends

MIP presolve is not implemented. LP presolve is separate and should not be implied by the first MIP command. Therefore, the first `mip-solve` command should not support:

```text
--presolve
```

unless a later design note defines how MIP presolve should behave, how original variable recovery should work across branch-and-bound, and how diagnostics should be reported.

The first MIP CLI may support LP backend selection through `--lp-solver` because branch-and-bound solves LP relaxations. This does not mean tableau or revised simplex are MIP solvers. They remain LP backends. The MIP algorithm is branch-and-bound, and the first command should keep that implicit because there is only one MIP algorithm in the native path.

This boundary also protects dependency direction. The MIP layer may depend on LP relaxations, but LP commands should not depend on MIP routing. The existing LP command should continue to reject unsupported integer or binary variables rather than silently dispatching to MIP.

## 9. Documentation and Examples

Future CLI documentation should reference the checked-in MIP examples:

```text
examples/mip/binary_knapsack.json
examples/mip/binary_choice.json
examples/mip/integer_allocation.json
examples/mip/mixed_binary_integer.json
examples/mip/mixed_continuous_integer.json
examples/mip/infeasible_binary.json
```

Planned command examples are:

```bash
silo mip-solve examples/mip/binary_knapsack.json
silo mip-solve examples/mip/integer_allocation.json --lp-solver revised
silo mip-solve examples/mip/infeasible_binary.json
```

Until the command is implemented, user-facing docs must describe these as planned examples or design recommendations. The existing Python API example remains the executable path:

```python
from silo.io.json_reader import read_json_model
from silo.mip.branch_and_bound import BranchAndBoundSolver

model = read_json_model("examples/mip/binary_knapsack.json")
solution = BranchAndBoundSolver().solve(model)
```

## 10. Testing Strategy

The future implementation should add CLI regression tests without weakening the existing Python API tests. Required cases include:

```text
mip-solve binary_knapsack -> optimal 22
mip-solve integer_allocation -> optimal 7
mip-solve mixed_binary_integer -> optimal 11
mip-solve mixed_continuous_integer -> optimal 11
mip-solve infeasible_binary -> infeasible exit code 1
--lp-solver revised works on selected examples
--output writes solution JSON
--node-limit 0 returns iteration_limit
missing path returns exit code 1
invalid lp solver rejected by argparse
default silo solve behavior unchanged
```

The regression suite should also assert that:

```bash
silo solve examples/mip/binary_knapsack.json
```

does not silently route to MIP. If a later design changes that behavior, it should do so explicitly and update the tests and documentation in the same task.

## 11. Implementation Phases

The future MIP CLI work should be split into small phases:

```text
Phase 5G: MIP CLI naming and exposure design note
Phase 5H: implement silo mip-solve command
Phase 5I: add MIP CLI documentation and examples
Phase 5J: MIP CLI regression matrix
```

Phase 5H should add only the minimal command, flags, output behavior, and tests. Phase 5I can then promote planned examples into implemented user documentation. Phase 5J should broaden the matrix across console-script invocation, `python -m silo.cli.main`, LP backend choices, output files, non-optimal statuses, and unchanged LP command behavior.

## 12. Out of Scope

The first MIP CLI exposure should not include:

```text
unified solve auto-detection
silo solve automatically dispatching to MIP
MIP presolve
MIP compare
MIP backend comparison
cuts
heuristics
callbacks
branch-and-cut
best-bound search
performance benchmarking
node-log JSON output
detailed MIP result JSON
parallel solving
commercial solver comparisons
```

It should also avoid schema changes. The current JSON model schema already represents integer and binary variables, and the current solution JSON schema is sufficient for first CLI output. The first CLI task should be a narrow exposure of an existing Python capability, not a redesign of SILO's public model or solution formats.
