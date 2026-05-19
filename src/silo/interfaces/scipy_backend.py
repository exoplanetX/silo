from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus


class ScipyBackend:
    def solve(self, model: Model) -> Solution:
        return Solution(status=SolverStatus.NOT_SOLVED, message="SciPy backend is not wired yet.")
