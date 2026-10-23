"""Public immutable options and versioned result data, independent of solver layers."""

from dataclasses import dataclass, field
from math import inf, isfinite


@dataclass(frozen=True)
class SolveOptions:
    time_limit: float = inf
    node_limit: int = 100000
    lp_iteration_limit: int = 10000
    relative_gap: float = 0.0
    absolute_gap: float = 0.0
    presolve: bool = True
    scaling: bool = True
    cuts: bool = True
    heuristics: bool = True
    node_strategy: str = "best_bound"
    lp_method: str = "auto"
    primal_tolerance: float = 1e-7
    dual_tolerance: float = 1e-7
    integrality_tolerance: float = 1e-7
    pivot_tolerance: float = 1e-10
    max_dense_cells: int = 2000000
    cut_round_limit: int = 2
    cuts_per_round: int = 3
    integer_ray_proof_limit: int = 1000000

    def __post_init__(self):
        for name in ("time_limit", "relative_gap", "absolute_gap"):
            value = getattr(self, name)
            if isinstance(value, bool) or value < 0 or value != value:
                raise ValueError(f"{name} must be nonnegative.")
            if name != "time_limit" and not isfinite(value):
                raise ValueError(f"{name} must be finite.")
        for name in (
            "node_limit",
            "lp_iteration_limit",
            "max_dense_cells",
            "cut_round_limit",
            "cuts_per_round",
            "integer_ray_proof_limit",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer.")
        for name in (
            "primal_tolerance",
            "dual_tolerance",
            "integrality_tolerance",
            "pivot_tolerance",
        ):
            value = getattr(self, name)
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite.")
        for name in ("presolve", "scaling", "cuts", "heuristics"):
            if type(getattr(self, name)) is not bool:
                raise ValueError(f"{name} must be boolean.")
        if self.node_strategy not in ("best_bound", "dfs"):
            raise ValueError("node_strategy must be best_bound or dfs.")
        if self.lp_method not in ("auto", "primal", "dual"):
            raise ValueError("lp_method must be auto, primal or dual.")


@dataclass
class SolveResult:
    status: str
    termination_reason: str
    objective_value: float | None = None
    primal_values: dict[str, float] = field(default_factory=dict)
    row_activities: dict[str, float] = field(default_factory=dict)
    row_slacks: dict = field(default_factory=dict)
    dual_values: dict[str, float] = field(default_factory=dict)
    reduced_costs: dict[str, float] = field(default_factory=dict)
    side_multipliers: dict = field(default_factory=dict)
    primal_bound: float | None = None
    dual_bound: float | None = None
    absolute_gap: float | None = None
    relative_gap: float | None = None
    iterations: int = 0
    nodes: int = 0
    elapsed_seconds: float = 0.0
    optimality: dict = field(default_factory=dict)
    witness: dict | None = None
    diagnostics: dict = field(default_factory=dict)
    basis: object | None = None
    _lp: object = field(default=None, repr=False)

    @property
    def has_primal_solution(self):
        return self.objective_value is not None

    def to_dict(self):
        def clean(value):
            if isinstance(value, dict):
                return {k: clean(v) for k, v in value.items()}
            if isinstance(value, list | tuple):
                return [clean(v) for v in value]
            if isinstance(value, float) and not isfinite(value):
                return None
            return value

        data = {k: v for k, v in vars(self).items() if not k.startswith("_") and k != "basis"}
        return clean(
            {
                "schema_version": 2,
                "has_primal_solution": self.has_primal_solution,
                "dual_bound_is_infinite": self.dual_bound is not None
                and not isfinite(self.dual_bound),
                **data,
            }
        )
