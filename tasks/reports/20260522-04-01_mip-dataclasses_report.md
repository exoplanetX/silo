# MIP Search Dataclasses Report

## Summary

Added Phase 5C internal MIP search dataclasses and pure helper functions. This task did not implement branch-and-bound solving, did not solve LP relaxations, and did not change CLI behavior, JSON schemas, tableau simplex, revised simplex, or presolve behavior.

## Public Objects Added

- `BranchingConstraint`
- `MIPNode`
- `root_node()`
- `make_child_node()`
- `NodeIdGenerator`
- `SearchTree`
- `PruneReason`
- `NodeLogEntry`

`Node` remains an alias for `MIPNode`, and `BranchingConstraint` remains import-compatible from `silo.mip.relaxation`.

## Branching Helpers

Added `DEFAULT_INTEGER_TOLERANCE`, `is_integral_value()`, `fractional_part()`, `choose_branching_variable()`, and `branch_on_value()`. Branching-variable selection follows the Phase 5 design rule: first fractional integer variable in original model order. Branching constraints use deterministic floor/ceil rows.

## Incumbent Semantics

Updated `Incumbent` into an immutable maximization helper. It accepts only optimal candidates with non-null objective values, updates empty incumbents, compares improvements using tolerance, and returns a new incumbent only when a candidate improves the current value.

## Node Logging

Added `PruneReason` and immutable `NodeLogEntry` in `src/silo/mip/logging.py`. The log entry stores only simple node-processing metadata and does not introduce a logging framework or file output.

## Files Changed

- `src/silo/mip/node.py`
- `src/silo/mip/branching.py`
- `src/silo/mip/incumbent.py`
- `src/silo/mip/node_selection.py`
- `src/silo/mip/tree.py`
- `src/silo/mip/logging.py`
- `src/silo/mip/relaxation.py`
- `src/silo/mip/__init__.py`
- `tests/unit/test_mip_node.py`
- `tests/unit/test_mip_branching.py`
- `tests/unit/test_mip_incumbent.py`
- `tests/unit/test_mip_node_selection.py`
- `tests/unit/test_mip_logging.py`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/codex/20260522-04-01_mip-dataclasses.md`
- `tasks/reports/20260522-04-01_mip-dataclasses_report.md`

## Tests Added

Added deterministic unit tests for node creation and immutability, child construction, branching helpers, incumbent update semantics, depth-first node selection, node id generation, node logging, prune reason enum values, and relaxation compatibility.

## Tests Run

- `pytest tests/unit/test_mip_node.py tests/unit/test_mip_branching.py tests/unit/test_mip_incumbent.py tests/unit/test_mip_node_selection.py tests/unit/test_mip_logging.py tests/unit/test_mip_relaxation.py`
- `python -m pip install -e ".[dev]"`
- `pytest tests/unit/test_mip_node.py tests/unit/test_mip_branching.py tests/unit/test_mip_incumbent.py tests/unit/test_mip_node_selection.py`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json`
- `silo compare examples/json/production.json`
- `git diff --check`

## Results

All checks passed. The full test suite reports 351 passing tests. `python scripts/check_quality.py` also reports 351 passing tests and all checks passed. Module and console CLI smoke commands returned expected help, version, solve, and compare outputs.

## Notes for Next Task

Phase 5D: implement pure depth-first branch-and-bound for binary variables.
