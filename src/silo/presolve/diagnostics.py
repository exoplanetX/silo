from dataclasses import dataclass
from enum import Enum


class PresolveStatus(str, Enum):
    NOT_RUN = "not_run"
    NO_CHANGE = "no_change"
    REDUCED = "reduced"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"


@dataclass(frozen=True)
class PresolveWarning:
    code: str
    message: str
    source: str | None = None


@dataclass(frozen=True)
class PresolveDiagnostics:
    status: PresolveStatus = PresolveStatus.NOT_RUN
    warnings: tuple[PresolveWarning, ...] = ()
    removed_rows: tuple[str, ...] = ()
    removed_variables: tuple[str, ...] = ()
    fixed_variables: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
