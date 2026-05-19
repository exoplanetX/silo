from dataclasses import dataclass, field

from silo.core.status import SolverStatus


@dataclass(frozen=True)
class Solution:
    status: SolverStatus
    objective_value: float | None = None
    primal_values: dict[str, float] = field(default_factory=dict)
    dual_values: dict[str, float] = field(default_factory=dict)
    reduced_costs: dict[str, float] = field(default_factory=dict)
    message: str = ""
