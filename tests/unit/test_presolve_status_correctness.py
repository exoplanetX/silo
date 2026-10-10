import pytest

from silo.cli.main import _solve_model
from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.presolve import Presolver, PresolveStatus


def _model(rows: list[Constraint], fixed_x: bool = False) -> Model:
    return Model(
        name="empty_column_status",
        variables=[Variable("x", bounds=Bounds(0.0, 0.0) if fixed_x else Bounds()),
                   Variable("y")],
        constraints=rows,
        objective=Objective({"y": 1.0}, OptimizationSense.MAXIMIZE),
    )


@pytest.mark.parametrize("backend", ["tableau", "revised"])
@pytest.mark.parametrize("use_presolve", [False, True])
def test_infeasible_nonempty_rows_take_precedence_over_improving_column(
    backend: str, use_presolve: bool,
) -> None:
    model = _model([
        Constraint("upper", {"x": 1.0}, ConstraintSense.LE, 0.0),
        Constraint("lower", {"x": 1.0}, ConstraintSense.GE, 1.0),
    ])
    assert _solve_model(model, backend, use_presolve).status == SolverStatus.INFEASIBLE


def test_presolve_defers_unbounded_candidate_without_feasible_point() -> None:
    model = _model([Constraint("lower", {"x": 1.0}, ConstraintSense.GE, 1.0)])
    result = Presolver().run(model)
    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert result.model is model
    assert result.diagnostics.warnings[0].code == "empty_column_unbounded"


@pytest.mark.parametrize("backend", ["tableau", "revised"])
def test_deferred_candidate_still_solves_as_truly_unbounded(backend: str) -> None:
    model = _model([Constraint("lower", {"x": 1.0}, ConstraintSense.GE, 1.0)])
    assert _solve_model(model, backend, True).status == SolverStatus.UNBOUNDED


def test_certified_feasible_background_keeps_unbounded_diagnostic() -> None:
    model = _model([Constraint("upper", {"x": 1.0}, ConstraintSense.LE, 1.0)])
    assert Presolver().run(model).diagnostics.status == PresolveStatus.UNBOUNDED


@pytest.mark.parametrize("backend", ["tableau", "revised"])
def test_fixed_variable_contradiction_is_exposed_before_unbounded_return(backend: str) -> None:
    model = _model([Constraint("lower", {"x": 1.0}, ConstraintSense.GE, 1.0)], fixed_x=True)
    assert Presolver().run(model).diagnostics.status == PresolveStatus.INFEASIBLE
    assert _solve_model(model, backend, True).status == SolverStatus.INFEASIBLE
