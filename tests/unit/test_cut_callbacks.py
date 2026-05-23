from dataclasses import FrozenInstanceError, dataclass
from math import inf

import pytest

from silo.cuts import (
    CallbackEvent,
    CallbackHook,
    CutCallback,
    NoOpCallback,
    dispatch_callback_events,
)


@dataclass
class _RecordingCallback:
    name: str
    records: list[tuple[str, CallbackHook]]

    def on_event(self, event: CallbackEvent) -> None:
        self.records.append((self.name, event.hook))


@dataclass(frozen=True)
class _ControlSignalCallback:
    name: str = "control"

    def on_event(self, event: CallbackEvent) -> str:
        assert isinstance(event, CallbackEvent)
        return "stop"


def test_callback_hooks_cover_phase6_design_points() -> None:
    assert {hook.value for hook in CallbackHook} == {
        "before_node_solve",
        "after_lp_relaxation",
        "after_candidate_cut_separation",
        "after_cut_pool_update",
        "after_incumbent_update",
        "after_node_prune",
        "after_child_creation",
        "solve_complete",
    }


def test_callback_event_normalizes_hook_and_stores_observation_fields() -> None:
    event = CallbackEvent(
        hook="after_lp_relaxation",
        node_id=3,
        depth=1,
        parent_id=0,
        lp_status="optimal",
        lp_objective=10.5,
        prune_reason="bound",
        branching_variable="x",
        incumbent_objective=8.0,
        cut_count=2,
        cut_ids=("c0", "c1"),
        solver_status="running",
        diagnostics={"lp_iterations": 4},
    )

    assert event.hook == CallbackHook.AFTER_LP_RELAXATION
    assert event.node_id == 3
    assert event.depth == 1
    assert event.parent_id == 0
    assert event.cut_ids == ("c0", "c1")
    assert event.diagnostics["lp_iterations"] == 4


def test_callback_event_is_immutable_at_dataclass_boundary() -> None:
    event = CallbackEvent(hook=CallbackHook.BEFORE_NODE_SOLVE)

    with pytest.raises(FrozenInstanceError):
        event.node_id = 1


def test_callback_event_defensively_copies_cut_ids_and_diagnostics() -> None:
    cut_ids = ["c0"]
    diagnostics = {"node_count": 1}
    event = CallbackEvent(
        hook=CallbackHook.AFTER_CUT_POOL_UPDATE,
        cut_ids=cut_ids,
        diagnostics=diagnostics,
    )

    cut_ids.append("c1")
    diagnostics["node_count"] = 2

    assert event.cut_ids == ("c0",)
    assert event.diagnostics["node_count"] == 1
    with pytest.raises(TypeError):
        event.diagnostics["node_count"] = 3


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        ("node_id", -1, "node id must be nonnegative"),
        ("depth", -1, "depth must be nonnegative"),
        ("parent_id", -1, "parent id must be nonnegative"),
        ("cut_count", -1, "cut count must be nonnegative"),
        ("lp_objective", inf, "LP objective must be finite"),
        ("incumbent_objective", inf, "incumbent objective must be finite"),
        ("lp_status", " ", "LP status must not be empty"),
        ("prune_reason", " ", "prune reason must not be empty"),
        ("branching_variable", " ", "branching variable must not be empty"),
        ("solver_status", " ", "solver status must not be empty"),
    ],
)
def test_callback_event_rejects_invalid_fields(
    field_name: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        CallbackEvent(hook=CallbackHook.BEFORE_NODE_SOLVE, **{field_name: value})


def test_callback_event_rejects_invalid_cut_ids() -> None:
    with pytest.raises(TypeError, match="cut ids"):
        CallbackEvent(hook=CallbackHook.AFTER_CUT_POOL_UPDATE, cut_ids="c0")

    with pytest.raises(ValueError, match="cut ids must not contain empty"):
        CallbackEvent(hook=CallbackHook.AFTER_CUT_POOL_UPDATE, cut_ids=("c0", " "))


def test_noop_callback_satisfies_protocol_and_returns_none() -> None:
    callback = NoOpCallback()
    event = CallbackEvent(hook=CallbackHook.BEFORE_NODE_SOLVE)

    assert isinstance(callback, CutCallback)
    assert callback.on_event(event) is None


def test_noop_callback_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        NoOpCallback(name=" ")

    with pytest.raises(TypeError, match="CallbackEvent"):
        NoOpCallback().on_event(object())  # type: ignore[arg-type]


def test_dispatch_with_noop_callbacks_preserves_event_order() -> None:
    events = (
        CallbackEvent(hook=CallbackHook.BEFORE_NODE_SOLVE, node_id=0),
        CallbackEvent(hook=CallbackHook.AFTER_LP_RELAXATION, node_id=0),
        CallbackEvent(hook=CallbackHook.SOLVE_COMPLETE),
    )

    dispatched = dispatch_callback_events(
        callbacks=(NoOpCallback(name="first"), NoOpCallback(name="second")),
        events=events,
    )

    assert dispatched == events
    assert [event.hook for event in dispatched] == [
        CallbackHook.BEFORE_NODE_SOLVE,
        CallbackHook.AFTER_LP_RELAXATION,
        CallbackHook.SOLVE_COMPLETE,
    ]


def test_dispatch_preserves_callback_order_within_each_event() -> None:
    records: list[tuple[str, CallbackHook]] = []
    callbacks = (
        _RecordingCallback(name="first", records=records),
        _RecordingCallback(name="second", records=records),
    )
    events = (
        CallbackEvent(hook=CallbackHook.BEFORE_NODE_SOLVE, node_id=0),
        CallbackEvent(hook=CallbackHook.AFTER_NODE_PRUNE, node_id=0),
    )

    dispatch_callback_events(callbacks=callbacks, events=events)

    assert records == [
        ("first", CallbackHook.BEFORE_NODE_SOLVE),
        ("second", CallbackHook.BEFORE_NODE_SOLVE),
        ("first", CallbackHook.AFTER_NODE_PRUNE),
        ("second", CallbackHook.AFTER_NODE_PRUNE),
    ]


def test_dispatch_rejects_invalid_callback_inputs() -> None:
    event = CallbackEvent(hook=CallbackHook.BEFORE_NODE_SOLVE)

    with pytest.raises(TypeError, match="CutCallback"):
        dispatch_callback_events(callbacks=(object(),), events=(event,))


def test_dispatch_rejects_invalid_event_inputs() -> None:
    with pytest.raises(TypeError, match="CallbackEvent"):
        dispatch_callback_events(callbacks=(NoOpCallback(),), events=(object(),))  # type: ignore[arg-type]


def test_dispatch_rejects_callback_control_signals() -> None:
    event = CallbackEvent(hook=CallbackHook.BEFORE_NODE_SOLVE)

    with pytest.raises(TypeError, match="control signals"):
        dispatch_callback_events(callbacks=(_ControlSignalCallback(),), events=(event,))


def test_public_exports_from_silo_cuts() -> None:
    event = CallbackEvent(hook=CallbackHook.SOLVE_COMPLETE)

    assert NoOpCallback().on_event(event) is None
    assert dispatch_callback_events(callbacks=(NoOpCallback(),), events=(event,)) == (event,)
