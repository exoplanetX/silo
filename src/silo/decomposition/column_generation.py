from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus


class ColumnGenerationSolver:
    def solve(self, model: Model) -> Solution:
        return Solution(
            status=SolverStatus.NOT_SOLVED,
            message="Column generation is not implemented yet.",
        )
