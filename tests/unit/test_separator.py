from dataclasses import FrozenInstanceError, dataclass
from math import inf

import pytest

from silo.core.enums import ConstraintSense
from silo.cuts import (
    CutCandidate,
    CutMetadata,
    CutPool,
    NoOpSeparator,
    Separator,
    SeparatorContext,
    separate_cuts,
)


def _cut(variable_name: str, rhs: float) -> CutCandidate:
    return CutCandidate(
        coefficients={variable_name: 1.0},
        sense=ConstraintSense.LE,
        rhs=rhs,
        metadata=CutMetadata(source="test_separator"),
    )


@dataclass(frozen=True)
class _DeterministicSeparator:
    candidates: tuple[CutCandidate, ...]
    name: str = "deterministic"

    def separate(self, context: SeparatorContext) -> tuple[CutCandidate, ...]:
        assert isinstance(context, SeparatorContext)
        return self.candidates


@dataclass(frozen=True)
class _InvalidSeparator:
    name: str = "invalid"

    def separate(self, context: SeparatorContext) -> tuple[object, ...]:
        assert isinstance(context, SeparatorContext)
        return (object(),)


def test_noop_separator_satisfies_protocol_and_returns_empty_tuple() -> None:
    separator = NoOpSeparator()
    context = SeparatorContext(variable_names=("x",), relaxation_values={"x": 0.5})

    assert isinstance(separator, Separator)
    assert separator.separate(context) == ()
    assert separate_cuts(separator, context) == ()


def test_noop_separator_does_not_mutate_cut_pool() -> None:
    pool = CutPool()
    accepted_cut = pool.add(_cut("x", 1.0)).cut
    context = SeparatorContext(variable_names=("x",), cut_pool=pool)

    assert NoOpSeparator().separate(context) == ()
    assert pool.cuts == (accepted_cut,)


def test_separator_context_is_immutable_at_dataclass_boundary() -> None:
    context = SeparatorContext(variable_names=("x",))

    with pytest.raises(FrozenInstanceError):
        context.node_id = 1


def test_separator_context_defensively_copies_mappings() -> None:
    relaxation_values = {"x": 0.5}
    metadata = {"phase": "test"}
    context = SeparatorContext(
        variable_names=("x",),
        relaxation_values=relaxation_values,
        metadata=metadata,
    )

    relaxation_values["x"] = 9.0
    metadata["phase"] = "mutated"

    assert context.relaxation_values["x"] == 0.5
    assert context.metadata["phase"] == "test"
    with pytest.raises(TypeError):
        context.relaxation_values["x"] = 1.0


def test_separator_context_normalizes_variable_names() -> None:
    names = ["y", "x"]
    context = SeparatorContext(variable_names=names)
    names.append("z")

    assert context.variable_names == ("y", "x")


def test_separator_context_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="node id must be nonnegative"):
        SeparatorContext(node_id=-1)

    with pytest.raises(ValueError, match="duplicates"):
        SeparatorContext(variable_names=("x", "x"))

    with pytest.raises(ValueError, match="unknown variable"):
        SeparatorContext(variable_names=("x",), relaxation_values={"y": 1.0})

    with pytest.raises(ValueError, match="must be finite"):
        SeparatorContext(variable_names=("x",), relaxation_values={"x": inf})

    with pytest.raises(TypeError, match="CutPool"):
        SeparatorContext(cut_pool=object())  # type: ignore[arg-type]


def test_separator_runner_preserves_candidate_order() -> None:
    first = _cut("x", 1.0)
    second = _cut("y", 2.0)
    separator = _DeterministicSeparator(candidates=(first, second))
    context = SeparatorContext(variable_names=("x", "y"))

    assert isinstance(separator, Separator)
    assert separate_cuts(separator, context) == (first, second)


def test_separator_runner_rejects_non_cut_candidate_outputs() -> None:
    context = SeparatorContext(variable_names=("x",))

    with pytest.raises(TypeError, match="CutCandidate"):
        separate_cuts(_InvalidSeparator(), context)


def test_noop_separator_rejects_invalid_context() -> None:
    with pytest.raises(TypeError, match="SeparatorContext"):
        NoOpSeparator().separate(object())  # type: ignore[arg-type]


def test_noop_separator_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        NoOpSeparator(name=" ")


def test_public_exports_from_silo_cuts() -> None:
    context = SeparatorContext(variable_names=("x",))

    assert NoOpSeparator().separate(context) == ()
    assert separate_cuts(NoOpSeparator(), context) == ()
