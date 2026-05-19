from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus


class BranchAndBoundSolver:
    def solve(self, model: Model) -> Solution:
        return Solution(
            status=SolverStatus.NOT_SOLVED,
            message="Branch-and-bound is not implemented yet.",
        )
