from silo.lp.base import LPSolver
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

SOLVER_FACTORIES: dict[str, type[LPSolver]] = {
    "tableau": TableauSimplexSolver,
    "revised": RevisedSimplexSolver,
}


def available_solver_names() -> tuple[str, ...]:
    return tuple(SOLVER_FACTORIES)


def create_solver(name: str) -> LPSolver:
    return SOLVER_FACTORIES[name]()
