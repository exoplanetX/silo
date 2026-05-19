from silo.core.model import Model
from silo.core.status import SolverStatus
from silo.lp.simplex.tableau import TableauSimplexSolver


def test_tableau_simplex_placeholder_returns_not_solved() -> None:
    solver = TableauSimplexSolver()
    solution = solver.solve(Model(name="empty"))
    assert solution.status == SolverStatus.NOT_SOLVED
