import pytest

from silo.core.status import SolverStatus
from silo.mip.logging import NodeLogEntry, PruneReason


def test_node_log_entry_defaults_to_not_pruned() -> None:
    entry = NodeLogEntry(node_id=0, depth=0, lp_status=SolverStatus.OPTIMAL)

    assert entry.prune_reason == PruneReason.NOT_PRUNED
    assert entry.lp_objective is None
    assert entry.branching_variable is None
    assert entry.incumbent_value is None
    assert entry.message == ""


def test_node_log_entry_stores_fields() -> None:
    entry = NodeLogEntry(
        node_id=3,
        depth=2,
        lp_status=SolverStatus.INFEASIBLE,
        lp_objective=12.0,
        prune_reason=PruneReason.LP_INFEASIBLE,
        branching_variable="x",
        incumbent_value=10.0,
        message="pruned",
    )

    assert entry.node_id == 3
    assert entry.depth == 2
    assert entry.lp_status == SolverStatus.INFEASIBLE
    assert entry.lp_objective == 12.0
    assert entry.prune_reason == PruneReason.LP_INFEASIBLE
    assert entry.branching_variable == "x"
    assert entry.incumbent_value == 10.0
    assert entry.message == "pruned"


def test_node_log_entry_rejects_negative_node_id() -> None:
    with pytest.raises(ValueError, match="id must be nonnegative"):
        NodeLogEntry(node_id=-1, depth=0, lp_status=SolverStatus.OPTIMAL)


def test_node_log_entry_rejects_negative_depth() -> None:
    with pytest.raises(ValueError, match="depth must be nonnegative"):
        NodeLogEntry(node_id=0, depth=-1, lp_status=SolverStatus.OPTIMAL)


def test_prune_reason_values_are_stable() -> None:
    assert PruneReason.LP_INFEASIBLE.value == "lp_infeasible"
    assert PruneReason.BOUND_DOMINATED.value == "bound_dominated"
    assert PruneReason.INTEGER_FEASIBLE.value == "integer_feasible"
    assert PruneReason.UNBOUNDED.value == "unbounded"
    assert PruneReason.ERROR.value == "error"
    assert PruneReason.NOT_PRUNED.value == "not_pruned"


def test_node_log_entry_normalizes_enum_values() -> None:
    entry = NodeLogEntry(node_id=0, depth=0, lp_status="optimal", prune_reason="error")

    assert entry.lp_status == SolverStatus.OPTIMAL
    assert entry.prune_reason == PruneReason.ERROR
