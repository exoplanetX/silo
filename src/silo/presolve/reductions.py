from dataclasses import dataclass
from enum import Enum


class ReductionType(str, Enum):
    EMPTY_ROW = "empty_row"
    EMPTY_COLUMN = "empty_column"
    FIXED_VARIABLE = "fixed_variable"
    BOUND_TIGHTENING = "bound_tightening"
    SCALING_DIAGNOSTIC = "scaling_diagnostic"
    NO_OP = "no_op"


ReductionData = tuple[tuple[str, object], ...]


def reduction_data(**items: object) -> ReductionData:
    return tuple(sorted(items.items()))


@dataclass(frozen=True)
class ReductionRecord:
    reduction_type: ReductionType
    target: str
    description: str
    data: ReductionData = ()
