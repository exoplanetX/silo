from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.lp.base import LPSolver


class TableauSimplexSolver(LPSolver):
    def solve(self, model: Model) -> Solution:
        return Solution(
            status=SolverStatus.NOT_SOLVED,
            message=(
                "Tableau simplex is not implemented yet. "
                "This placeholder will be completed in Phase 3."
            ),
        )
