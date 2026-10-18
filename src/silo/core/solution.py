from dataclasses import dataclass, field

from silo.core.status import SolverStatus


@dataclass(frozen=True)
class Solution:
    """Solver result. Optimal LP duals use original row names/signs.

    For maximization: LE multipliers >= 0, GE <= 0, EQ unrestricted;
    reduced costs are c - A.T*y. See docs/lp_duality.md for fixed bounds.
    MIP and nonoptimal statuses do not carry LP dual optimality evidence.
    """

    status: SolverStatus
    objective_value: float | None = None
    primal_values: dict[str, float] = field(default_factory=dict)
    slack_values: dict[str, float] = field(default_factory=dict)
    dual_values: dict[str, float] = field(default_factory=dict)
    reduced_costs: dict[str, float] = field(default_factory=dict)
    basis_status: dict[str, str] = field(default_factory=dict)
    message: str = ""
