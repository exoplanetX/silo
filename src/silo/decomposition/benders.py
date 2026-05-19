from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus


class BendersSolver:
    def solve(self, model: Model) -> Solution:
        return Solution(status=SolverStatus.NOT_SOLVED, message="Benders is not implemented yet.")
