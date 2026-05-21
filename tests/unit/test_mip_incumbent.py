from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.mip.incumbent import Incumbent


def test_empty_incumbent_has_no_solution() -> None:
    incumbent = Incumbent()

    assert not incumbent.has_solution()
    assert incumbent.objective_value is None


def test_optimal_candidate_updates_empty_incumbent() -> None:
    candidate = Solution(status=SolverStatus.OPTIMAL, objective_value=10.0)

    updated = Incumbent().update(candidate)

    assert updated.has_solution()
    assert updated.solution is candidate
    assert updated.objective_value == 10.0


def test_lower_objective_candidate_does_not_update() -> None:
    incumbent = Incumbent(solution=Solution(status=SolverStatus.OPTIMAL, objective_value=10.0))
    candidate = Solution(status=SolverStatus.OPTIMAL, objective_value=9.0)

    assert incumbent.update(candidate) is incumbent


def test_equal_objective_within_tolerance_does_not_update() -> None:
    incumbent = Incumbent(solution=Solution(status=SolverStatus.OPTIMAL, objective_value=10.0))
    candidate = Solution(status=SolverStatus.OPTIMAL, objective_value=10.0 + 5e-10)

    assert incumbent.update(candidate, tolerance=1e-9) is incumbent


def test_non_optimal_candidate_does_not_update_empty_incumbent() -> None:
    candidate = Solution(status=SolverStatus.INFEASIBLE, objective_value=100.0)
    incumbent = Incumbent()

    assert not incumbent.is_better(candidate)
    assert incumbent.update(candidate) is incumbent


def test_candidate_without_objective_does_not_update_empty_incumbent() -> None:
    candidate = Solution(status=SolverStatus.OPTIMAL, objective_value=None)
    incumbent = Incumbent()

    assert not incumbent.is_better(candidate)
    assert incumbent.update(candidate) is incumbent


def test_update_returns_new_incumbent_when_improved() -> None:
    incumbent = Incumbent(solution=Solution(status=SolverStatus.OPTIMAL, objective_value=10.0))
    candidate = Solution(status=SolverStatus.OPTIMAL, objective_value=11.0)

    updated = incumbent.update(candidate)

    assert updated is not incumbent
    assert updated.solution is candidate
