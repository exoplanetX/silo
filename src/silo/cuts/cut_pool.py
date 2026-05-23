from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from silo.cuts.candidate import (
    CutActivityState,
    CutCandidate,
    CutMetadata,
    CutValidityScope,
)

CutKey = tuple[str, tuple[tuple[str, float], ...], str, float, str, int | None]


@dataclass(frozen=True)
class CutPoolAddResult:
    cut: CutCandidate
    added: bool
    duplicate_of: CutCandidate | None = None


def _copy_with_state(cut: CutCandidate, state: CutActivityState) -> CutCandidate:
    metadata = CutMetadata(
        source=cut.metadata.source,
        scope=cut.metadata.scope,
        cut_id=cut.metadata.cut_id,
        node_id=cut.metadata.node_id,
        tolerance=cut.metadata.tolerance,
        message=cut.metadata.message,
        state=state,
    )
    return CutCandidate(
        coefficients=dict(cut.coefficients),
        sense=cut.sense,
        rhs=cut.rhs,
        metadata=metadata,
    )


@dataclass
class CutPool:
    cuts: tuple[CutCandidate, ...] = field(default_factory=tuple)
    variable_order: tuple[str, ...] | None = None
    _key_index: dict[CutKey, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.variable_order is not None:
            variable_order = tuple(self.variable_order)
            if any(not variable_name for variable_name in variable_order):
                raise ValueError("Cut-pool variable order must not contain empty names.")
            if len(set(variable_order)) != len(variable_order):
                raise ValueError("Cut-pool variable order must not contain duplicates.")
            self.variable_order = variable_order

        self.cuts = tuple(self.cuts)
        self._key_index = {}
        for index, cut in enumerate(self.cuts):
            self._validate_cut(cut)
            key = self._canonical_key(cut)
            if key in self._key_index:
                raise ValueError("Cut pool cannot be initialized with duplicate cuts.")
            self._key_index[key] = index

    def __iter__(self) -> Iterator[CutCandidate]:
        return iter(self.cuts)

    def __len__(self) -> int:
        return len(self.cuts)

    def add(self, cut: CutCandidate) -> CutPoolAddResult:
        return self.add_candidate(cut)

    def add_candidate(self, cut: CutCandidate) -> CutPoolAddResult:
        self._validate_cut(cut)
        key = self._canonical_key(cut)
        duplicate_index = self._key_index.get(key)
        if duplicate_index is not None:
            return CutPoolAddResult(
                cut=_copy_with_state(cut, CutActivityState.DUPLICATE),
                added=False,
                duplicate_of=self.cuts[duplicate_index],
            )

        accepted_cut = _copy_with_state(cut, CutActivityState.ACCEPTED)
        self.cuts = (*self.cuts, accepted_cut)
        self._key_index[key] = len(self.cuts) - 1
        return CutPoolAddResult(cut=accepted_cut, added=True)

    def active_cuts_for_node(self, node_id: int) -> tuple[CutCandidate, ...]:
        if node_id < 0:
            raise ValueError("Cut-pool node id must be nonnegative.")

        active: list[CutCandidate] = []
        for cut in self.cuts:
            if cut.metadata.state not in {
                CutActivityState.ACCEPTED,
                CutActivityState.ACTIVE,
            }:
                continue
            if cut.metadata.scope == CutValidityScope.GLOBAL:
                active.append(_copy_with_state(cut, CutActivityState.ACTIVE))
            elif (
                cut.metadata.scope == CutValidityScope.NODE_LOCAL
                and cut.metadata.node_id == node_id
            ):
                active.append(_copy_with_state(cut, CutActivityState.ACTIVE))
        return tuple(active)

    def clear_expired_node_local_cuts(
        self,
        active_node_ids: Iterable[int],
    ) -> tuple[CutCandidate, ...]:
        active_nodes = set(active_node_ids)
        if any(node_id < 0 for node_id in active_nodes):
            raise ValueError("Cut-pool active node ids must be nonnegative.")

        kept: list[CutCandidate] = []
        expired: list[CutCandidate] = []
        for cut in self.cuts:
            if (
                cut.metadata.scope == CutValidityScope.NODE_LOCAL
                and cut.metadata.node_id not in active_nodes
            ):
                expired.append(_copy_with_state(cut, CutActivityState.EXPIRED))
            else:
                kept.append(cut)

        self.cuts = tuple(kept)
        self._rebuild_index()
        return tuple(expired)

    def _canonical_key(self, cut: CutCandidate) -> CutKey:
        return cut.canonical_key(variable_order=self.variable_order)

    def _rebuild_index(self) -> None:
        self._key_index = {
            self._canonical_key(cut): index for index, cut in enumerate(self.cuts)
        }

    @staticmethod
    def _validate_cut(cut: CutCandidate) -> None:
        if not isinstance(cut, CutCandidate):
            raise TypeError("CutPool accepts CutCandidate instances only.")
        if cut.metadata.scope == CutValidityScope.GLOBAL and cut.metadata.node_id is not None:
            raise ValueError("A global cut must not include a node id.")
        if cut.metadata.scope == CutValidityScope.NODE_LOCAL and cut.metadata.node_id is None:
            raise ValueError("A node-local cut must include a node id.")
