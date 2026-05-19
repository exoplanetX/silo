from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus


class HighsBackend:
    def solve(self, model: Model) -> Solution:
        return Solution(status=SolverStatus.NOT_SOLVED, message="HiGHS backend is not wired yet.")
