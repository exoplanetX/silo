import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition import RestrictedMasterProblem
from silo.lp.base import LPSolver
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

TOLERANCE = 1e-9


def _assert_minimum(model, result, expected):
    # Direct MIN weak-duality equations in original coordinates, independent of
    # the production MAX checker; known analytic optima supply the main truth.
    assert result.status == SolverStatus.OPTIMAL
    assert set(result.primal_values) == set(result.reduced_costs) == set(model.variable_names())
    assert set(result.dual_values) == {row.name for row in model.constraints}
    for value in result.primal_values.values():
        assert value >= -TOLERANCE
    for row in model.constraints:
        activity = sum(a * result.primal_values[name] for name, a in row.coefficients.items())
        pi = result.dual_values[row.name]
        if row.sense == ConstraintSense.LE:
            assert activity <= row.rhs + TOLERANCE
            assert pi <= TOLERANCE
        elif row.sense == ConstraintSense.GE:
            assert activity >= row.rhs - TOLERANCE
            assert pi >= -TOLERANCE
        else:
            assert activity == pytest.approx(row.rhs, abs=TOLERANCE, rel=0)
        assert abs(pi * (row.rhs - activity)) <= TOLERANCE
    for name in model.variable_names():
        rc = model.objective.coefficients.get(name, 0) - sum(
            row.coefficients.get(name, 0) * result.dual_values[row.name]
            for row in model.constraints
        )
        assert rc >= -TOLERANCE
        assert result.reduced_costs[name] == pytest.approx(rc, abs=TOLERANCE, rel=0)
        assert abs(result.primal_values[name] * rc) <= TOLERANCE
    primal = model.objective.constant + sum(
        c * result.primal_values[name] for name, c in model.objective.coefficients.items())
    dual = model.objective.constant + sum(row.rhs * result.dual_values[row.name]
                                          for row in model.constraints)
    for value in (result.objective_value, primal, dual):
        assert value == pytest.approx(expected, abs=TOLERANCE, rel=0)


@pytest.mark.parametrize("backend", [RevisedSimplexSolver, TableauSimplexSolver])
@pytest.mark.parametrize("cost,expected", [(7, 14), (10, 17), (12, 17)])
def test_a_columns_start_from_same_initial_rmp_with_analytic_minimum(backend, cost, expected):
    model = Model(
        variables=[Variable("la"), Variable("lb")],
        constraints=[Constraint("a", {"la": 1}, ConstraintSense.EQ, 1),
                     Constraint("b", {"lb": 1}, ConstraintSense.EQ, 1)],
        objective=Objective({"la": 4, "lb": 6}, OptimizationSense.MINIMIZE, constant=7),
    )
    rmp = RestrictedMasterProblem(model)
    initial = rmp.solve(backend())
    _assert_minimum(model, initial, 17)
    assert initial.primal_values == {"la": 1, "lb": 1}
    assert initial.dual_values == {"a": 4, "b": 6}
    assert cost - initial.dual_values["a"] - initial.dual_values["b"] == cost - 10
    rmp.add_column(name="p", cost=cost, row_coefficients={"a": 1, "b": 1})
    # Independent original MIN model used only as an oracle, not shared with the adapter.
    model.variables.append(Variable("p"))
    model.objective.coefficients["p"] = cost
    for row in model.constraints:
        row.coefficients["p"] = 1
    result = rmp.solve(backend())
    _assert_minimum(model, result, expected)
    # Eliminate la,lb: 0<=p<=1, P=17+(cost-10)*p.
    if cost == 7:
        assert result.primal_values == {"la": 0, "lb": 0, "p": 1}
    elif cost == 12:
        assert result.primal_values == {"la": 1, "lb": 1, "p": 0}


@pytest.mark.parametrize("backend", [RevisedSimplexSolver, TableauSimplexSolver])
@pytest.mark.parametrize("row_order", [("a", "b"), ("b", "a")])
@pytest.mark.parametrize("column", [{"a": 1}, {"b": 1}])
def test_b_old_redundancy_does_not_survive_adding_a_column(backend, row_order, column):
    model = Model(variables=[Variable("x")],
                  constraints=[Constraint(name, {"x": 1}, ConstraintSense.EQ, 1)
                               for name in row_order],
                  objective=Objective({"x": 2}, OptimizationSense.MINIMIZE))

    class Spy(LPSolver):
        def __init__(self):
            self.models = []
            self.delegate = backend()

        def solve(self, native):
            self.models.append(native)
            return self.delegate.solve(native)

    spy = Spy()
    rmp = RestrictedMasterProblem(model)
    _assert_minimum(model, rmp.solve(spy), 2)
    # This is a hand-constructed valid old dual; the backend need not choose it.
    assert sum((2 if row.name == "a" else 0) * row.rhs for row in model.constraints) == 2
    if column == {"a": 1}:
        assert 0 - (1 * 2 + 0 * 0) == -2  # Negative old rc, yet no strict improvement.
    rmp.add_column(name="q", cost=0, row_coefficients=column)
    model.variables.append(Variable("q"))
    for row in model.constraints:
        row.coefficients["q"] = column.get(row.name, 0)
    result = rmp.solve(spy)
    _assert_minimum(model, result, 2)
    assert result.primal_values == {"x": 1, "q": 0}
    first, second = spy.models
    assert first is not second
    assert first.variables is not second.variables
    assert first.constraints is not second.constraints
    assert first.variable_names() == ["x"]
    assert second.variable_names() == ["x", "q"]
    assert [row.name for row in first.constraints] == list(row_order)
    assert [row.name for row in second.constraints] == list(row_order)
    assert [(row.sense, row.rhs) for row in second.constraints] == [(ConstraintSense.EQ, 1)] * 2
    assert {row.name: row.coefficients.get("q", 0) for row in second.constraints} == {
        "a": column.get("a", 0), "b": column.get("b", 0)}
    assert all(first.constraints[i].coefficients is not second.constraints[i].coefficients
               for i in range(2))


@pytest.mark.parametrize("backend", [RevisedSimplexSolver, TableauSimplexSolver])
def test_c_mixed_rows_negative_rhs_and_minimum_multiplier_signs(backend):
    model = Model(
        variables=[Variable("x"), Variable("z"), Variable("w")],
        constraints=[
            Constraint("ge", {"x": 1}, ConstraintSense.GE, 1),
            Constraint("le", {"z": 1}, ConstraintSense.LE, 3),
            Constraint("negative_eq", {"w": -1}, ConstraintSense.EQ, -2),
            Constraint("loose", {"x": 1, "z": 1}, ConstraintSense.LE, 5),
        ],
        objective=Objective({"x": 2, "z": -1, "w": 3}, OptimizationSense.MINIMIZE, constant=7),
    )
    result = RestrictedMasterProblem(model).solve(backend())
    _assert_minimum(model, result, 12)
    assert result.primal_values == {"x": 1, "z": 3, "w": 2}
    assert result.dual_values == {"ge": 2, "le": -1, "negative_eq": -3, "loose": 0}
    assert result.reduced_costs == {"x": 0, "z": 0, "w": 0}
