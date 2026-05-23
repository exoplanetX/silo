import pytest

from silo.core.enums import ConstraintSense
from silo.cuts import (
    CutActivityState,
    CutCandidate,
    CutMetadata,
    CutPool,
    CutPoolAddResult,
    CutValidityScope,
)


def _cut(
    coefficients: dict[str, float],
    *,
    rhs: float = 1.0,
    source: str = "toy_separator",
    cut_id: str | None = None,
    scope: CutValidityScope = CutValidityScope.GLOBAL,
    node_id: int | None = None,
) -> CutCandidate:
    return CutCandidate(
        coefficients=coefficients,
        sense=ConstraintSense.LE,
        rhs=rhs,
        metadata=CutMetadata(
            source=source,
            cut_id=cut_id,
            scope=scope,
            node_id=node_id,
        ),
    )


def test_add_unique_cut_accepts_and_stores_in_insertion_order() -> None:
    pool = CutPool()
    original = _cut({"y": 2.0, "x": 1.0}, cut_id="c0")

    result = pool.add(original)

    assert isinstance(result, CutPoolAddResult)
    assert result.added is True
    assert result.duplicate_of is None
    assert result.cut.metadata.state == CutActivityState.ACCEPTED
    assert original.metadata.state == CutActivityState.CANDIDATE
    assert pool.cuts == (result.cut,)
    assert result.cut.coefficients == (("x", 1.0), ("y", 2.0))


def test_duplicate_cut_is_reported_without_appending() -> None:
    pool = CutPool()
    first = pool.add(_cut({"x": 1.0, "y": 2.0}, cut_id="c0")).cut
    duplicate = _cut(
        {"y": 2.0, "x": 1.0},
        source="other_separator",
        cut_id="other-id",
    )

    result = pool.add(duplicate)

    assert result.added is False
    assert result.cut.metadata.state == CutActivityState.DUPLICATE
    assert result.duplicate_of == first
    assert pool.cuts == (first,)


def test_duplicate_detection_can_use_explicit_variable_order() -> None:
    pool = CutPool(variable_order=("y", "x"))
    first = pool.add(_cut({"x": 1.0, "y": 2.0})).cut
    duplicate = _cut({"y": 2.0, "x": 1.0}, source="other_separator")

    result = pool.add(duplicate)

    assert result.added is False
    assert result.duplicate_of == first


def test_active_cuts_for_node_includes_global_and_matching_node_local() -> None:
    pool = CutPool()
    global_cut = pool.add(_cut({"x": 1.0}, cut_id="global")).cut
    node_three_cut = pool.add(
        _cut(
            {"y": 1.0},
            cut_id="node-3",
            scope=CutValidityScope.NODE_LOCAL,
            node_id=3,
        )
    ).cut
    pool.add(
        _cut(
            {"z": 1.0},
            cut_id="node-4",
            scope=CutValidityScope.NODE_LOCAL,
            node_id=4,
        )
    )

    active = pool.active_cuts_for_node(3)

    assert [cut.canonical_key() for cut in active] == [
        global_cut.canonical_key(),
        node_three_cut.canonical_key(),
    ]
    assert [cut.metadata.state for cut in active] == [
        CutActivityState.ACTIVE,
        CutActivityState.ACTIVE,
    ]
    assert [cut.metadata.state for cut in pool.cuts] == [
        CutActivityState.ACCEPTED,
        CutActivityState.ACCEPTED,
        CutActivityState.ACCEPTED,
    ]


def test_clear_expired_node_local_cuts_keeps_global_and_active_scope() -> None:
    pool = CutPool()
    global_cut = pool.add(_cut({"x": 1.0}, cut_id="global")).cut
    expired_node_cut = pool.add(
        _cut(
            {"y": 1.0},
            cut_id="node-1",
            scope=CutValidityScope.NODE_LOCAL,
            node_id=1,
        )
    ).cut
    active_node_cut = pool.add(
        _cut(
            {"z": 1.0},
            cut_id="node-2",
            scope=CutValidityScope.NODE_LOCAL,
            node_id=2,
        )
    ).cut

    expired = pool.clear_expired_node_local_cuts(active_node_ids={2})

    assert [cut.canonical_key() for cut in expired] == [expired_node_cut.canonical_key()]
    assert expired[0].metadata.state == CutActivityState.EXPIRED
    assert pool.cuts == (global_cut, active_node_cut)


def test_rejects_non_cut_candidate_instances() -> None:
    pool = CutPool()

    with pytest.raises(TypeError, match="CutCandidate instances"):
        pool.add(object())  # type: ignore[arg-type]


def test_rejects_node_local_cut_without_node_id() -> None:
    pool = CutPool()

    with pytest.raises(ValueError, match="node-local cut must include a node id"):
        pool.add(_cut({"x": 1.0}, scope=CutValidityScope.NODE_LOCAL))


def test_rejects_global_cut_with_node_id() -> None:
    pool = CutPool()

    with pytest.raises(ValueError, match="global cut must not include a node id"):
        pool.add(_cut({"x": 1.0}, node_id=1))


def test_rejects_duplicate_initial_cuts() -> None:
    cut = _cut({"x": 1.0})

    with pytest.raises(ValueError, match="duplicate cuts"):
        CutPool(cuts=(cut, cut))


def test_public_exports_from_silo_cuts() -> None:
    pool = CutPool()

    assert isinstance(pool, CutPool)
    assert CutPoolAddResult(cut=_cut({"x": 1.0}), added=True)
