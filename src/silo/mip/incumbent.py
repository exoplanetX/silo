from dataclasses import dataclass

from silo.core.solution import Solution
from silo.core.status import SolverStatus


@dataclass(frozen=True)
class Incumbent:
    solution: Solution | None = None

    def has_solution(self) -> bool:
        return self.solution is not None

    @property
    def objective_value(self) -> float | None:
        if self.solution is None:
            return None
        return self.solution.objective_value

    def is_better(self, candidate: Solution, tolerance: float = 1e-9) -> bool:
        if candidate.status != SolverStatus.OPTIMAL:
            return False
        if candidate.objective_value is None:
            return False
        if self.objective_value is None:
            return True
        return candidate.objective_value > self.objective_value + tolerance

    def update(self, candidate: Solution, tolerance: float = 1e-9) -> "Incumbent":
        if self.is_better(candidate, tolerance=tolerance):
            return Incumbent(solution=candidate)
        return self
