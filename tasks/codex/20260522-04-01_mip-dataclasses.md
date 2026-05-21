# Codex Task 20260522-04-01: Add MIP Search Dataclasses

## Task Metadata

Task file:

```text
tasks/codex/20260522-04-01_mip-dataclasses.md
```

Execution report file:

```text
tasks/reports/20260522-04-01_mip-dataclasses_report.md
```

Recommended local commit message:

```text
Add MIP search dataclasses
```

Repository:

```text
https://github.com/exoplanetX/silo
```

Important workflow rule:

Create a local commit after all checks pass. Do **not** push to GitHub unless the user explicitly asks you to push in the Codex session.

------

## 1. Background

SILO has entered Phase 5: MIP Branch-and-Bound.

The previous Phase 5B task implemented the MIP-to-LP relaxation builder:

```text
src/silo/mip/relaxation.py
```

The builder already provides:

```text
BranchingConstraint
MIPRelaxation
build_lp_relaxation(model, branching_constraints=...)
```

The relaxation builder converts supported MIP models into continuous LP relaxations by:

```text
binary variable -> continuous variable + generated x <= 1 row
bounded nonnegative integer variable -> continuous variable + generated x <= U row
node-local branching constraints -> generated branching rows
```

The next step is not to implement branch-and-bound search yet. The next step is to introduce the internal dataclasses needed for the search layer:

```text
MIPNode
NodeLogEntry
PruneReason
Incumbent
branching helpers
node stack / depth-first selection helpers
```

This task is Phase 5C only.

------

## 2. Goal

Add deterministic MIP search dataclasses and small pure helper functions needed by the future branch-and-bound solver.

This task should provide:

1. immutable MIP node representation;
2. deterministic branching-child construction;
3. fractional-variable detection helpers;
4. incumbent representation and update helpers;
5. node log / prune reason records;
6. depth-first node stack helper behavior;
7. unit tests for all of the above.

This task should not solve any MIP.

------

## 3. Save This Task File

Create:

```text
tasks/codex/20260522-04-01_mip-dataclasses.md
```

Save this full task prompt into that file.

Do not edit, rename, delete, or move any existing files under:

```text
tasks/codex/
```

This task may only add the new task file above.

------

## 4. Allowed Files to Modify or Add

You may modify existing MIP placeholder files:

```text
src/silo/mip/node.py
src/silo/mip/branching.py
src/silo/mip/incumbent.py
src/silo/mip/node_selection.py
src/silo/mip/tree.py
src/silo/mip/__init__.py
```

You may add:

```text
src/silo/mip/logging.py
tests/unit/test_mip_node.py
tests/unit/test_mip_branching.py
tests/unit/test_mip_incumbent.py
tests/unit/test_mip_node_selection.py
tasks/reports/20260522-04-01_mip-dataclasses_report.md
```

You may update:

```text
tasks/phases/phase_05_branch_and_bound.md
notes/15_branch_and_bound_design.md
```

only if needed to align names.

You may update `src/silo/mip/relaxation.py` only if needed to avoid duplicated `BranchingConstraint` definitions or to re-export/move it safely. If you move `BranchingConstraint`, preserve backward compatibility for imports from `silo.mip.relaxation`.

Do not modify tableau simplex.

Do not modify revised simplex.

Do not modify presolve.

Do not modify CLI behavior.

Do not implement branch-and-bound search.

------

## 5. Do Not Do

Do not implement `BranchAndBoundSolver.solve()`.

Do not solve LP relaxations in this task.

Do not call tableau or revised simplex from MIP code in this task.

Do not implement a branch-and-bound loop.

Do not implement pruning logic that depends on solving nodes.

Do not add cuts.

Do not add heuristics.

Do not add callbacks.

Do not add branch-and-cut.

Do not add MIP CLI commands.

Do not change JSON model schema.

Do not change solution JSON schema.

Do not add external solver calls.

Do not add runtime dependencies.

Do not change the Apache-2.0 `LICENSE`.

Do not modify existing files under `tasks/codex/`.

Do not force push.

Do not push unless explicitly instructed by the user.

------

## 6. BranchingConstraint Compatibility

`BranchingConstraint` already exists in:

```text
src/silo/mip/relaxation.py
```

Do not create a second incompatible `BranchingConstraint`.

Choose one of these approaches:

### Preferred approach

Move `BranchingConstraint` to:

```text
src/silo/mip/node.py
```

or:

```text
src/silo/mip/branching.py
```

Then import it in `relaxation.py`.

Keep backward compatibility by re-exporting it from `relaxation.py`, so existing code such as:

```python
from silo.mip.relaxation import BranchingConstraint
```

still works.

### Alternative approach

Leave `BranchingConstraint` in `relaxation.py` and import it from there in `node.py` and `branching.py`.

This is acceptable if it avoids unnecessary refactoring.

Whichever approach is chosen, add tests to ensure the relaxation builder still accepts branching constraints.

------

## 7. MIPNode Requirements

Create or replace the current placeholder `Node` with a clearer immutable node representation.

Recommended:

```python
@dataclass(frozen=True)
class MIPNode:
    id: int
    depth: int
    branching_constraints: tuple[BranchingConstraint, ...] = ()
    parent_id: int | None = None
```

Requirements:

1. `id` must be nonnegative.
2. `depth` must be nonnegative.
3. `parent_id` may be `None` for root.
4. root node should be easy to create.
5. child nodes should preserve parent constraints plus one new branching constraint.
6. node is immutable.
7. branching constraints are stored as tuples.

Add a helper:

```python
def root_node() -> MIPNode:
    ...
```

or:

```python
MIPNode.root()
```

Recommended root:

```text
id = 0
depth = 0
parent_id = None
branching_constraints = ()
```

Do not delete a `Node` alias if existing imports use it. If helpful, keep:

```python
Node = MIPNode
```

for compatibility.

------

## 8. Child Node Construction

Add helper function:

```python
def make_child_node(
    parent: MIPNode,
    node_id: int,
    branching_constraint: BranchingConstraint,
) -> MIPNode:
    ...
```

Expected behavior:

```text
child.id = node_id
child.depth = parent.depth + 1
child.parent_id = parent.id
child.branching_constraints = parent.branching_constraints + (branching_constraint,)
```

Validate that child id is nonnegative and not equal to parent id if simple.

Do not create children based on LP values yet; that belongs in branching helpers below.

------

## 9. Fractionality and Branching Helpers

Update or create:

```text
src/silo/mip/branching.py
```

Keep helpers pure and deterministic.

Define integer tolerance:

```python
DEFAULT_INTEGER_TOLERANCE = 1e-6
```

or place it in a suitable module if already present.

Add helpers:

```python
def is_integral_value(value: float, tolerance: float = DEFAULT_INTEGER_TOLERANCE) -> bool:
    ...

def fractional_part(value: float) -> float:
    ...

def choose_branching_variable(
    variable_names: tuple[str, ...],
    integer_variable_names: tuple[str, ...],
    values: dict[str, float],
    tolerance: float = DEFAULT_INTEGER_TOLERANCE,
) -> str | None:
    ...
```

Expected branching variable rule:

```text
first fractional integer variable in model variable order
```

Input convention:

- `variable_names` is original model variable order;
- `integer_variable_names` includes binary and integer variables;
- `values` maps variable names to LP relaxation primal values.

If a variable is missing from `values`, treat missing value as `0.0` or raise `ValueError`. Prefer raising `ValueError` because missing values indicate a broken relaxation result.

Add helper:

```python
def branch_on_value(variable_name: str, value: float) -> tuple[BranchingConstraint, BranchingConstraint]:
    ...
```

Expected:

```text
left child constraint:  variable <= floor(value)
right child constraint: variable >= ceil(value)
```

Use `ConstraintSense.LE` and `ConstraintSense.GE`.

For binary variables, this naturally gives:

```text
x <= 0
x >= 1
```

when value is fractional between 0 and 1.

Do not create nodes in this helper; it should only create branching constraints.

------

## 10. Node Selection Requirements

Update:

```text
src/silo/mip/node_selection.py
```

Current placeholder has:

```python
select_depth_first(open_nodes: list[Node]) -> Node | None
```

Make it compatible with `MIPNode`.

Requirements:

1. `select_depth_first(open_nodes)` returns the last node or `None`.
2. Add helper if useful:

```python
def pop_depth_first(open_nodes: list[MIPNode]) -> MIPNode | None:
    ...
```

If you add `pop_depth_first`, it should mutate the list by popping the last node. If you keep only select, tests should clarify it does not mutate.

Keep behavior simple.

Do not implement best-bound selection in this task.

------

## 11. Incumbent Requirements

Update:

```text
src/silo/mip/incumbent.py
```

Current `Incumbent` only stores `Solution | None`.

Implement a small maximization incumbent helper.

Recommended:

```python
@dataclass(frozen=True)
class Incumbent:
    solution: Solution | None = None

    def has_solution(self) -> bool:
        ...

    @property
    def objective_value(self) -> float | None:
        ...

    def is_better(self, candidate: Solution, tolerance: float = 1e-9) -> bool:
        ...

    def update(self, candidate: Solution, tolerance: float = 1e-9) -> "Incumbent":
        ...
```

Behavior:

1. If no incumbent exists, an optimal candidate with objective value is better.
2. Candidate must have `SolverStatus.OPTIMAL`.
3. Candidate objective must not be `None`.
4. For maximization, candidate is better if:

```text
candidate.objective_value > incumbent.objective_value + tolerance
```

1. `update()` returns a new `Incumbent`.
2. If candidate is not better, `update()` returns `self`.

Do not mutate incumbent in place.

Do not implement minimization incumbent logic.

------

## 12. Node Log and Prune Reason

Add:

```text
src/silo/mip/logging.py
```

Define enum:

```python
class PruneReason(str, Enum):
    LP_INFEASIBLE = "lp_infeasible"
    BOUND_DOMINATED = "bound_dominated"
    INTEGER_FEASIBLE = "integer_feasible"
    UNBOUNDED = "unbounded"
    ERROR = "error"
    NOT_PRUNED = "not_pruned"
```

Define:

```python
@dataclass(frozen=True)
class NodeLogEntry:
    node_id: int
    depth: int
    lp_status: SolverStatus
    lp_objective: float | None = None
    prune_reason: PruneReason = PruneReason.NOT_PRUNED
    branching_variable: str | None = None
    incumbent_value: float | None = None
    message: str = ""
```

Requirements:

1. immutable dataclass;
2. validates nonnegative node id and depth if simple;
3. stores simple metadata only;
4. no logging framework;
5. no file output.

------

## 13. Tree / Node ID Helper

If useful, update:

```text
src/silo/mip/tree.py
```

with a tiny helper for deterministic ids:

```python
@dataclass
class NodeIdGenerator:
    next_id: int = 1

    def take(self) -> int:
        ...
```

Expected:

```text
root uses id 0
first generated child id = 1
second generated child id = 2
```

This is optional but useful for future Phase 5D.

Do not implement a full search tree.

------

## 14. Tests Required

Add or update tests.

### 14.1 `tests/unit/test_mip_node.py`

Test:

1. root node fields;
2. invalid negative id/depth rejected;
3. child node construction;
4. child preserves parent constraints plus new constraint;
5. immutability.

### 14.2 `tests/unit/test_mip_branching.py`

Test:

1. `is_integral_value(1.0)` true;
2. values within tolerance true;
3. `1.5` false;
4. choose first fractional integer variable in model order;
5. continuous variables ignored if not in integer set;
6. missing value raises `ValueError`;
7. `branch_on_value("x", 2.7)` creates `x <= 2` and `x >= 3`;
8. binary-like value `0.4` creates `x <= 0` and `x >= 1`.

### 14.3 `tests/unit/test_mip_incumbent.py`

Test:

1. empty incumbent has no solution;
2. optimal candidate updates empty incumbent;
3. lower objective candidate does not update;
4. equal objective within tolerance does not update;
5. candidate with non-optimal status does not update;
6. candidate with `None` objective does not update;
7. update returns a new incumbent when improved.

### 14.4 `tests/unit/test_mip_node_selection.py`

Test:

1. depth-first select returns last node;
2. empty list returns `None`;
3. if `pop_depth_first` exists, it pops last node and mutates list accordingly.

### 14.5 `tests/unit/test_mip_logging.py`

If `logging.py` is added, test:

1. default prune reason is `NOT_PRUNED`;
2. fields stored correctly;
3. invalid negative id/depth rejected if validation is implemented;
4. enum values stable.

### 14.6 Relaxation compatibility

Update or add tests to ensure:

```python
from silo.mip.relaxation import BranchingConstraint
```

still works if `BranchingConstraint` was moved or re-exported.

------

## 15. Documentation Update

Update:

```text
tasks/phases/phase_05_branch_and_bound.md
```

Briefly mark Phase 5C as the MIP search dataclasses step.

Update:

```text
notes/15_branch_and_bound_design.md
```

only if exact dataclass names changed from the design note.

Do not update README unless absolutely necessary.

------

## 16. Execution Report

Create:

```text
tasks/reports/20260522-04-01_mip-dataclasses_report.md
```

The report should include:

```markdown
# MIP Search Dataclasses Report

## Summary

## Public Objects Added

## Branching Helpers

## Incumbent Semantics

## Node Logging

## Files Changed

## Tests Added

## Tests Run

## Results

## Notes for Next Task
```

In "Notes for Next Task", recommend:

```text
Phase 5D: implement pure depth-first branch-and-bound for binary variables.
```

Do not record execution results by editing the issued task file.

------

## 17. Local Checks

Run:

```bash
python -m pip install -e ".[dev]"
pytest tests/unit/test_mip_node.py tests/unit/test_mip_branching.py tests/unit/test_mip_incumbent.py tests/unit/test_mip_node_selection.py
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json
python -m silo.cli.main compare examples/json/production.json
```

If the console script is available, also run:

```bash
silo --help
silo --version
silo solve examples/json/production.json
silo compare examples/json/production.json
```

Also run:

```bash
git diff --check
```

Fix any failures.

------

## 18. Git Requirements

Before committing, inspect:

```bash
git status --short
git diff --stat
```

Commit locally:

```bash
git add .
git commit -m "Add MIP search dataclasses"
```

Do not push unless the user explicitly instructs you to push.

After committing, show:

```bash
git status
git log --oneline -5
```

The expected local state may be ahead of `origin/main` by one commit if the commit has not been pushed.

------

## 19. Acceptance Criteria

This task is complete only if:

1. `tasks/codex/20260522-04-01_mip-dataclasses.md` exists.
2. No existing files under `tasks/codex/` are modified.
3. `MIPNode` or equivalent immutable node dataclass exists.
4. Root node helper exists or root construction is clearly tested.
5. Child node construction helper exists and is tested.
6. Branching helpers detect first fractional integer variable deterministically.
7. Branching helpers create floor/ceil branching constraints.
8. `BranchingConstraint` compatibility with `silo.mip.relaxation` is preserved.
9. `Incumbent` supports immutable maximization update semantics.
10. Node selection depth-first helper is tested.
11. `PruneReason` and `NodeLogEntry` or equivalent logging dataclasses exist.
12. No branch-and-bound search loop is implemented.
13. No LP relaxation solving is added to MIP search code in this task.
14. No CLI behavior is changed.
15. No solver behavior is changed.
16. No JSON model or solution schema changes are made.
17. No external solver dependency or call is introduced.
18. `tasks/reports/20260522-04-01_mip-dataclasses_report.md` exists.
19. `pytest` passes.
20. `python scripts/check_quality.py` passes.
21. CLI help/version/solve/compare commands work.
22. `git diff --check` passes.
23. A local commit is created with message:

```text
Add MIP search dataclasses
```

24. The task is not pushed unless the user explicitly instructs Codex to push.
