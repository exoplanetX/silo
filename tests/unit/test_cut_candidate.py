from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from silo.core.enums import ConstraintSense
from silo.cuts import CutActivityState, CutCandidate, CutMetadata, CutValidityScope


def test_valid_global_cut_candidate_construction() -> None:
    metadata = CutMetadata(source="toy_separator", cut_id="c0", message="violated")
    cut = CutCandidate(
        coefficients={"y": 2, "x": 1.5},
        sense="<=",
        rhs=3,
        metadata=metadata,
    )

    assert cut.coefficients == (("x", 1.5), ("y", 2.0))
    assert cut.sense == ConstraintSense.LE
    assert cut.rhs == 3.0
    assert cut.metadata == metadata


def test_valid_node_local_metadata_construction() -> None:
    metadata = CutMetadata(
        source="node_separator",
        scope="node_local",
        node_id=7,
        tolerance=1e-7,
        state="active",
    )

    assert metadata.scope == CutValidityScope.NODE_LOCAL
    assert metadata.node_id == 7
    assert metadata.tolerance == 1e-7
    assert metadata.state == CutActivityState.ACTIVE


def test_metadata_is_immutable() -> None:
    metadata = CutMetadata(source="separator")

    with pytest.raises(FrozenInstanceError):
        metadata.source = "other"


def test_cut_candidate_is_immutable() -> None:
    cut = CutCandidate({"x": 1.0}, ConstraintSense.LE, 1.0, CutMetadata(source="s"))

    with pytest.raises(FrozenInstanceError):
        cut.rhs = 2.0


def test_coefficients_are_copied_and_normalized() -> None:
    coefficients = {"b": 2.0, "a": 1.0}
    cut = CutCandidate(coefficients, ConstraintSense.GE, 3.0, CutMetadata(source="s"))
    coefficients["a"] = 99.0

    assert cut.coefficients == (("a", 1.0), ("b", 2.0))


def test_rejects_empty_coefficient_map() -> None:
    with pytest.raises(ValueError, match="coefficients must not be empty"):
        CutCandidate({}, ConstraintSense.LE, 1.0, CutMetadata(source="s"))


def test_rejects_empty_variable_name() -> None:
    with pytest.raises(ValueError, match="variable names must not be empty"):
        CutCandidate({"": 1.0}, ConstraintSense.LE, 1.0, CutMetadata(source="s"))


@pytest.mark.parametrize("coefficient", [inf, -inf, nan])
def test_rejects_nonfinite_coefficients(coefficient: float) -> None:
    with pytest.raises(ValueError, match="coefficients must be finite"):
        CutCandidate({"x": coefficient}, ConstraintSense.LE, 1.0, CutMetadata(source="s"))


def test_rejects_all_zero_coefficient_vector() -> None:
    with pytest.raises(ValueError, match="must contain a nonzero value"):
        CutCandidate({"x": 0.0, "y": 0.0}, ConstraintSense.LE, 1.0, CutMetadata(source="s"))


@pytest.mark.parametrize("rhs", [inf, -inf, nan])
def test_rejects_nonfinite_rhs(rhs: float) -> None:
    with pytest.raises(ValueError, match="RHS must be finite"):
        CutCandidate({"x": 1.0}, ConstraintSense.LE, rhs, CutMetadata(source="s"))


def test_rejects_empty_source_separator_name() -> None:
    with pytest.raises(ValueError, match="source must not be empty"):
        CutMetadata(source=" ")


@pytest.mark.parametrize("tolerance", [0.0, -1.0, inf, nan])
def test_rejects_nonpositive_or_nonfinite_tolerance(tolerance: float) -> None:
    with pytest.raises(ValueError, match="tolerance must be positive and finite"):
        CutMetadata(source="s", tolerance=tolerance)


def test_rejects_negative_node_id() -> None:
    with pytest.raises(ValueError, match="node id must be nonnegative"):
        CutMetadata(source="s", node_id=-1)


def test_canonical_key_is_independent_of_input_order() -> None:
    first = CutCandidate(
        {"x": 1.0, "y": 2.0},
        ConstraintSense.LE,
        4.0,
        CutMetadata(source="s"),
    )
    second = CutCandidate(
        {"y": 2.0, "x": 1.0},
        ConstraintSense.LE,
        4.0,
        CutMetadata(source="other"),
    )

    assert first.canonical_key() == second.canonical_key()


def test_canonical_key_respects_explicit_variable_order() -> None:
    cut = CutCandidate(
        {"x": 1.0, "y": 2.0, "z": 3.0},
        ConstraintSense.LE,
        4.0,
        CutMetadata(source="s"),
    )

    assert cut.canonical_key(variable_order=("z", "x")) == (
        "cut",
        (("z", 3.0), ("x", 1.0), ("y", 2.0)),
        "<=",
        4.0,
        "global",
        None,
    )


def test_public_exports_from_silo_cuts() -> None:
    assert CutActivityState.CANDIDATE.value == "candidate"
    assert CutValidityScope.GLOBAL.value == "global"
    assert CutCandidate({"x": 1.0}, ConstraintSense.LE, 1.0, CutMetadata(source="s"))
