from collections.abc import Callable
from dataclasses import dataclass, field

import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.cuts import (
    CallbackEvent,
    CallbackHook,
    CutCandidate,
    NoOpCallback,
    NoOpSeparator,
    SeparatorContext,
)
from silo.mip.branch_and_bound import BranchAndBoundResult, BranchAndBoundSolver


@dataclass
class _RecordingCallback:
    name: str = "recording"
    events: list[CallbackEvent] = field(default_factory=list)

    def on_event(self, event: CallbackEvent) -> None:
        self.events.append(event)


@dataclass
class _RecordingNoOpSeparator:
    name: str = "recording_noop"
    contexts: list[SeparatorContext] = field(default_factory=list)

    def separate(self, context: SeparatorContext) -> tuple[CutCandidate, ...]:
        self.contexts.append(context)
        return ()


@pytest.mark.parametrize(
    "model_factory",
    [
        pytest.param(lambda: _binary_choice_model(), id="binary-choice"),
        pytest.param(lambda: _single_fractional_binary_model(), id="fractional-binary"),
        pytest.param(lambda: _single_bounded_integer_model(), id="bounded-integer"),
    ],
)
def test_explicit_noop_components_match_default_branch_and_bound(
    model_factory: Callable[[], Model],
) -> None:
    default_result = BranchAndBoundSolver().solve_with_details(model_factory())
    noop_result = BranchAndBoundSolver(
        separator=NoOpSeparator(),
        callbacks=(NoOpCallback(),),
    ).solve_with_details(model_factory())

    _assert_same_observable_result(default_result, noop_result)


def test_readonly_callbacks_observe_deterministic_hook_order() -> None:
    callback = _RecordingCallback()
    separator = _RecordingNoOpSeparator()

    result = BranchAndBoundSolver(
        separator=separator,
        callbacks=(callback,),
    ).solve_with_details(_single_fractional_binary_model())

    assert result.solution.status == SolverStatus.OPTIMAL
    assert [event.hook for event in callback.events] == [
        CallbackHook.BEFORE_NODE_SOLVE,
        CallbackHook.AFTER_LP_RELAXATION,
        CallbackHook.AFTER_CANDIDATE_CUT_SEPARATION,
        CallbackHook.AFTER_CUT_POOL_UPDATE,
        CallbackHook.AFTER_CHILD_CREATION,
        CallbackHook.BEFORE_NODE_SOLVE,
        CallbackHook.AFTER_LP_RELAXATION,
        CallbackHook.AFTER_CANDIDATE_CUT_SEPARATION,
        CallbackHook.AFTER_CUT_POOL_UPDATE,
        CallbackHook.AFTER_INCUMBENT_UPDATE,
        CallbackHook.AFTER_NODE_PRUNE,
        CallbackHook.BEFORE_NODE_SOLVE,
        CallbackHook.AFTER_LP_RELAXATION,
        CallbackHook.AFTER_NODE_PRUNE,
        CallbackHook.SOLVE_COMPLETE,
    ]
    assert [event.node_id for event in callback.events if event.node_id is not None] == [
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
    ]
    assert [context.node_id for context in separator.contexts] == [0, 1]
    assert all(
        context.cut_pool is not None and len(context.cut_pool) == 0
        for context in separator.contexts
    )


def test_noop_components_preserve_log_order_and_prune_reasons() -> None:
    default_result = BranchAndBoundSolver().solve_with_details(_single_fractional_binary_model())
    noop_result = BranchAndBoundSolver(
        separator=NoOpSeparator(),
        callbacks=(NoOpCallback(),),
    ).solve_with_details(_single_fractional_binary_model())

    assert [entry.node_id for entry in noop_result.log] == [0, 1, 2]
    assert _log_signature(noop_result) == _log_signature(default_result)


def test_branch_and_bound_rejects_invalid_cut_callback_components() -> None:
    with pytest.raises(TypeError, match="Separator protocol"):
        BranchAndBoundSolver(separator=object())  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="CutCallback protocol"):
        BranchAndBoundSolver(callbacks=(object(),))  # type: ignore[arg-type]


def _assert_same_observable_result(
    default_result: BranchAndBoundResult,
    noop_result: BranchAndBoundResult,
) -> None:
    assert noop_result.solution.status == default_result.solution.status
    assert noop_result.solution.objective_value == default_result.solution.objective_value
    assert noop_result.solution.primal_values == default_result.solution.primal_values
    assert noop_result.nodes_processed == default_result.nodes_processed
    assert noop_result.nodes_created == default_result.nodes_created
    assert noop_result.nodes_pruned == default_result.nodes_pruned
    assert len(noop_result.log) == len(default_result.log)
    assert [entry.node_id for entry in noop_result.log] == [
        entry.node_id for entry in default_result.log
    ]
    assert [entry.prune_reason for entry in noop_result.log] == [
        entry.prune_reason for entry in default_result.log
    ]
    assert [entry.branching_variable for entry in noop_result.log] == [
        entry.branching_variable for entry in default_result.log
    ]


def _log_signature(result: BranchAndBoundResult) -> tuple[tuple[int, str, str | None], ...]:
    return tuple(
        (entry.node_id, entry.prune_reason.value, entry.branching_variable)
        for entry in result.log
    )


def _binary_choice_model() -> Model:
    model = Model(name="choice")
    _add_binary_variable(model, "x")
    _add_binary_variable(model, "y")
    model.add_constraint(
        Constraint(
            name="choice",
            coefficients={"x": 1.0, "y": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 1.0, "y": 1.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _single_fractional_binary_model() -> Model:
    model = Model(name="single_fractional")
    _add_binary_variable(model, "x")
    model.add_constraint(
        Constraint(
            name="half_capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=0.5,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model


def _single_bounded_integer_model() -> Model:
    model = Model(name="single_integer")
    _add_integer_variable(model, "x", 3.0)
    model.add_constraint(
        Constraint(
            name="row_limit",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=2.5,
        )
    )
    model.set_objective(Objective(coefficients={"x": 3.0}, sense=OptimizationSense.MAXIMIZE))
    return model


def _add_binary_variable(model: Model, name: str) -> None:
    model.add_variable(
        Variable(
            name=name,
            bounds=Bounds(lower=0.0, upper=1.0),
            var_type=VariableType.BINARY,
        )
    )


def _add_integer_variable(model: Model, name: str, upper: float) -> None:
    model.add_variable(
        Variable(
            name=name,
            bounds=Bounds(lower=0.0, upper=upper),
            var_type=VariableType.INTEGER,
        )
    )
