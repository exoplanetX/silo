from dataclasses import dataclass
from enum import Enum

from silo.core.status import SolverStatus


class PruneReason(str, Enum):
    LP_INFEASIBLE = "lp_infeasible"
    BOUND_DOMINATED = "bound_dominated"
    INTEGER_FEASIBLE = "integer_feasible"
    UNBOUNDED = "unbounded"
    ERROR = "error"
    NOT_PRUNED = "not_pruned"


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

    def __post_init__(self) -> None:
        if self.node_id < 0:
            raise ValueError("Node log entry id must be nonnegative.")
        if self.depth < 0:
            raise ValueError("Node log entry depth must be nonnegative.")
        object.__setattr__(self, "lp_status", SolverStatus(self.lp_status))
        object.__setattr__(self, "prune_reason", PruneReason(self.prune_reason))
