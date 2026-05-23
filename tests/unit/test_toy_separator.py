from math import inf, nan

import pytest

from silo.core.enums import ConstraintSense
from silo.cuts import (
    CutCandidate,
    CutValidityScope,
    Separator,
    SeparatorContext,
    ToyUpperBoundSeparator,
    separate_cuts,
)


def test_toy_upper_bound_separator_satisfies_protocol() -> None:
    separator = ToyUpperBoundSeparator(variable_name="x", upper_bound=1.0)

    assert isinstance(separator, Separator)


def test_toy_upper_bound_separator_returns_empty_when_value_is_absent() -> None:
    separator = ToyUpperBoundSeparator(variable_name="x", upper_bound=1.0)
    context = SeparatorContext(variable_names=("x",))

    assert separator.separate(context) == ()


@pytest.mark.parametrize("value", [1.0, 1.0 + 0.5e-9])
def test_toy_upper_bound_separator_returns_empty_within_tolerance(value: float) -> None:
    separator = ToyUpperBoundSeparator(variable_name="x", upper_bound=1.0)
    context = SeparatorContext(variable_names=("x",), relaxation_values={"x": value})

    assert separator.separate(context) == ()


def test_toy_upper_bound_separator_returns_deterministic_global_cut() -> None:
    separator = ToyUpperBoundSeparator(
        variable_name="x",
        upper_bound=1.0,
        name="toy_fixture_bound",
        tolerance=1e-8,
    )
    context = SeparatorContext(variable_names=("x", "y"), relaxation_values={"x": 1.1})

    cuts = separator.separate(context)

    assert len(cuts) == 1
    cut = cuts[0]
    assert isinstance(cut, CutCandidate)
    assert cut.coefficients == (("x", 1.0),)
    assert cut.sense == ConstraintSense.LE
    assert cut.rhs == 1.0
    assert cut.metadata.source == "toy_fixture_bound"
    assert cut.metadata.scope == CutValidityScope.GLOBAL
    assert cut.metadata.cut_id == "toy_fixture_bound:x:upper_bound"
    assert cut.metadata.tolerance == 1e-8
    assert "valid only for fixtures" in cut.metadata.message
    assert cut.canonical_key(variable_order=("y", "x")) == (
        "cut",
        (("x", 1.0),),
        "<=",
        1.0,
        "global",
        None,
    )


def test_toy_upper_bound_separator_has_stable_outputs() -> None:
    separator = ToyUpperBoundSeparator(variable_name="x", upper_bound=1.0)
    context = SeparatorContext(variable_names=("x",), relaxation_values={"x": 2.0})

    first = separate_cuts(separator, context)
    second = separate_cuts(separator, context)

    assert [cut.canonical_key() for cut in first] == [cut.canonical_key() for cut in second]
    assert first[0].metadata.cut_id == second[0].metadata.cut_id


def test_toy_upper_bound_separator_rejects_variable_missing_from_context() -> None:
    separator = ToyUpperBoundSeparator(variable_name="x", upper_bound=1.0)
    context = SeparatorContext(variable_names=("y",), relaxation_values={"y": 2.0})

    with pytest.raises(ValueError, match="variable must be present"):
        separator.separate(context)


def test_toy_upper_bound_separator_rejects_invalid_context() -> None:
    separator = ToyUpperBoundSeparator(variable_name="x", upper_bound=1.0)

    with pytest.raises(TypeError, match="SeparatorContext"):
        separator.separate(object())  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"variable_name": " ", "upper_bound": 1.0}, "variable name must not be empty"),
        ({"variable_name": "x", "upper_bound": inf}, "upper bound must be finite"),
        ({"variable_name": "x", "upper_bound": nan}, "upper bound must be finite"),
        ({"variable_name": "x", "upper_bound": 1.0, "name": " "}, "name must not be empty"),
        (
            {"variable_name": "x", "upper_bound": 1.0, "tolerance": 0.0},
            "tolerance must be positive",
        ),
        (
            {"variable_name": "x", "upper_bound": 1.0, "tolerance": inf},
            "tolerance must be positive",
        ),
    ],
)
def test_toy_upper_bound_separator_rejects_invalid_configuration(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ToyUpperBoundSeparator(**kwargs)  # type: ignore[arg-type]


def test_public_exports_from_silo_cuts() -> None:
    separator = ToyUpperBoundSeparator(variable_name="x", upper_bound=1.0)
    context = SeparatorContext(variable_names=("x",), relaxation_values={"x": 2.0})

    assert len(separate_cuts(separator, context)) == 1
