from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition import RestrictedMasterProblem, RestrictedMasterResult
from silo.decomposition import restricted_master as implementation
from silo.lp.base import LPSolver
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver


def _initial_model():
    return Model(
        variables=[Variable("la"), Variable("lb")],
        constraints=[Constraint("a", {"la": 1}, ConstraintSense.EQ, 1),
                     Constraint("b", {"lb": 1}, ConstraintSense.EQ, 1)],
        objective=Objective({"la": 4, "lb": 6}, OptimizationSense.MINIMIZE, constant=7),
    )


class SpySolver(LPSolver):
    def __init__(self, delegate=None):
        self.delegate = delegate if delegate is not None else RevisedSimplexSolver()
        self.models = []
        self.solutions = []

    def solve(self, model):
        self.models.append(model)
        solution = self.delegate.solve(model)
        self.solutions.append(solution)
        return solution


class FixedSolver(LPSolver):
    def __init__(self, solution):
        self.solution = solution

    def solve(self, model):
        return self.solution


def _valid_native_solution():
    return Solution(
        status=SolverStatus.OPTIMAL, objective_value=-17,
        primal_values={"la": 1, "lb": 1}, dual_values={"a": -4, "b": -6},
        reduced_costs={"la": 0, "lb": 0},
    )


def _assert_no_optimal_fields(result, status):
    assert result.status == status
    assert result.objective_value is None
    assert result.primal_values == result.dual_values == result.reduced_costs == {}


@pytest.mark.parametrize("backend", [RevisedSimplexSolver, TableauSimplexSolver])
def test_native_objective_constant_duals_and_reduced_costs_are_converted(backend):
    rmp = RestrictedMasterProblem(_initial_model())
    spy = SpySolver(backend())
    initial = rmp.solve(spy)
    assert isinstance(initial, RestrictedMasterResult)
    assert not isinstance(initial, Solution)
    assert initial.objective_value == 17
    assert initial.dual_values == {"a": 4, "b": 6}
    assert spy.models[0].objective == Objective({"la": -4, "lb": -6},
                                              OptimizationSense.MAXIMIZE, -7)
    assert spy.solutions[0].objective_value == -17
    assert spy.solutions[0].dual_values == {"a": -4, "b": -6}
    rmp.add_column(name="p", cost=12, row_coefficients={"a": 1, "b": 1})
    after = rmp.solve(spy)
    assert after.objective_value == 17
    assert after.reduced_costs["p"] == 2
    assert spy.solutions[1].reduced_costs["p"] == -2
    assert dict(after.dual_values) == {k: -v for k, v in spy.solutions[1].dual_values.items()}
    assert initial.primal_values == {"la": 1, "lb": 1}
    assert spy.models[0] is not spy.models[1]


def test_constructor_owns_lists_objective_and_constraint_dictionaries():
    source = _initial_model()
    rmp = RestrictedMasterProblem(source)
    source.objective.coefficients["la"] = 999
    source.constraints[0].coefficients["la"] = 99
    source.variables.clear()
    source.constraints.clear()
    source.objective = Objective({}, OptimizationSense.MAXIMIZE)
    result = rmp.solve()
    assert result.objective_value == 17
    assert result.primal_values == {"la": 1, "lb": 1}
    assert result.dual_values == {"a": 4, "b": 6}


def test_added_mapping_is_copied_and_results_are_immutable_snapshots():
    rmp = RestrictedMasterProblem(_initial_model())
    before = rmp.solve()
    coefficients = {"a": 1, "b": 1}
    rmp.add_column(name="p", cost=7, row_coefficients=coefficients)
    coefficients["a"] = 99
    coefficients.clear()
    after = rmp.solve()
    assert after.objective_value == 14
    assert before.objective_value == 17
    assert before.dual_values == {"a": 4, "b": 6}
    assert "p" not in before.primal_values
    for field in (before.primal_values, before.dual_values, before.reduced_costs):
        with pytest.raises(TypeError):
            field["changed"] = 1
    with pytest.raises(FrozenInstanceError):
        before.objective_value = 0


def test_backend_result_mapping_mutation_does_not_change_returned_snapshot():
    native = _valid_native_solution()
    result = RestrictedMasterProblem(_initial_model()).solve(FixedSolver(native))
    native.primal_values.clear()
    native.dual_values["a"] = 999
    native.reduced_costs["la"] = 999
    assert result.primal_values == {"la": 1, "lb": 1}
    assert result.dual_values == {"a": 4, "b": 6}
    assert result.reduced_costs == {"la": 0, "lb": 0}


@pytest.mark.parametrize("changes", [
    {"name": "la"}, {"name": ""}, {"name": "  "}, {"name": None},
    {"cost": nan}, {"cost": inf}, {"cost": -inf}, {"cost": "bad"},
    {"row_coefficients": {"a": 1, "absent": 2}},
    {"row_coefficients": {"a": 1, "b": nan}},
    {"row_coefficients": {"a": 1, "b": inf}},
    {"row_coefficients": {"a": 1, "b": "bad"}},
    {"row_coefficients": []},
])
def test_invalid_addition_is_atomic(changes):
    rmp = RestrictedMasterProblem(_initial_model())
    arguments = {"name": "p", "cost": 7, "row_coefficients": {"a": 1, "b": 1}}
    arguments.update(changes)
    with pytest.raises((ValueError, TypeError)):
        rmp.add_column(**arguments)
    spy = SpySolver()
    result = rmp.solve(spy)
    assert result.objective_value == 17
    assert spy.models[0].variable_names() == ["la", "lb"]
    assert spy.models[0].constraints == _initial_model().constraints
    rmp.add_column(name="p", cost=7, row_coefficients={"a": 1, "b": 1})
    assert rmp.solve().objective_value == 14


def test_names_are_matched_exactly_and_preserved():
    source = Model(variables=[Variable(" x ")],
                   constraints=[Constraint(" a ", {" x ": 1}, ConstraintSense.EQ, 1)],
                   objective=Objective({" x ": 2}, OptimizationSense.MINIMIZE))
    rmp = RestrictedMasterProblem(source)
    with pytest.raises(ValueError, match="Unknown row"):
        rmp.add_column(name=" q ", cost=3, row_coefficients={"a": 1})
    rmp.add_column(name=" q ", cost=3, row_coefficients={" a ": 1})
    result = rmp.solve()
    assert result.primal_values == {" x ": 1, " q ": 0}
    assert result.dual_values == {" a ": 2}


@pytest.mark.parametrize("coefficients", [{}, {"a": 0}, {"a": 0, "b": 0}])
def test_zero_columns_are_legal(coefficients):
    rmp = RestrictedMasterProblem(_initial_model())
    rmp.add_column(name="zero", cost=2, row_coefficients=coefficients)
    result = rmp.solve()
    assert result.objective_value == 17
    assert result.primal_values["zero"] == 0
    assert result.reduced_costs["zero"] == 2


def test_same_vector_different_name_and_sequential_solves_are_supported():
    rmp = RestrictedMasterProblem(_initial_model())
    rmp.add_column(name="expensive", cost=12, row_coefficients={"a": 1, "b": 1})
    assert rmp.solve().objective_value == 17
    rmp.add_column(name="cheap", cost=7, row_coefficients={"a": 1, "b": 1})
    first, second = rmp.solve(), rmp.solve()
    assert first == second
    assert first.objective_value == 14
    assert first.primal_values["cheap"] == 1
    assert first.primal_values["expensive"] == 0


@pytest.mark.parametrize("bounds,var_type", [
    (Bounds(-inf, inf), VariableType.CONTINUOUS),
    (Bounds(1, inf), VariableType.CONTINUOUS),
    (Bounds(0, 1), VariableType.CONTINUOUS),
    (Bounds(1, 1), VariableType.CONTINUOUS),
    (Bounds(), VariableType.INTEGER), (Bounds(0, 1), VariableType.BINARY),
])
def test_constructor_rejects_unsupported_variable_domains(bounds, var_type):
    model = _initial_model()
    model.variables[0] = Variable("la", bounds, var_type)
    with pytest.raises(ValueError):
        RestrictedMasterProblem(model)


@pytest.mark.parametrize("location", ["cost", "constant", "coefficient", "rhs"])
@pytest.mark.parametrize("bad", [nan, inf, -inf])
def test_constructor_rejects_nonfinite_data(location, bad):
    model = _initial_model()
    if location == "cost":
        model.objective.coefficients["la"] = bad
    elif location == "constant":
        model.objective = replace(model.objective, constant=bad)
    elif location == "coefficient":
        model.constraints[0].coefficients["la"] = bad
    else:
        model.constraints[0] = replace(model.constraints[0], rhs=bad)
    with pytest.raises(ValueError, match="finite"):
        RestrictedMasterProblem(model)


@pytest.mark.parametrize("malformation", ["maximize", "duplicate-variable", "duplicate-row",
                                          "unknown-variable", "blank-variable", "blank-row"])
def test_constructor_rejects_invalid_or_non_min_models(malformation):
    model = _initial_model()
    if malformation == "maximize":
        model.objective = replace(model.objective, sense=OptimizationSense.MAXIMIZE)
    elif malformation == "duplicate-variable":
        model.variables.append(Variable("la"))
    elif malformation == "duplicate-row":
        model.constraints.append(model.constraints[0])
    elif malformation == "unknown-variable":
        model.constraints[0].coefficients["absent"] = 1
    elif malformation == "blank-variable":
        model.variables.append(Variable("  "))
    else:
        model.constraints.append(Constraint(" ", {}, ConstraintSense.EQ, 0))
    with pytest.raises(ValueError):
        RestrictedMasterProblem(model)


@pytest.mark.parametrize("status", [s for s in SolverStatus if s != SolverStatus.OPTIMAL])
def test_nonoptimal_diagnostics_never_publish_or_reuse_optimal_fields(status):
    rmp = RestrictedMasterProblem(_initial_model())
    earlier = rmp.solve()
    diagnostic = replace(_valid_native_solution(), status=status, message="backend diagnostic")
    result = rmp.solve(FixedSolver(diagnostic))
    _assert_no_optimal_fields(result, status)
    assert result.message == "backend diagnostic"
    assert earlier.objective_value == 17


@pytest.mark.parametrize("changes", [
    {"objective_value": -99}, {"objective_value": None}, {"objective_value": nan},
    {"primal_values": {}}, {"dual_values": {}}, {"reduced_costs": {}},
    {"primal_values": {"la": 0, "lb": 1}},
    {"dual_values": {"a": 4, "b": 6}},
    {"primal_values": {"la": inf, "lb": 1}},
    {"dual_values": {"a": -4, "b": nan}},
    {"reduced_costs": {"la": 1, "lb": 0}},
    {"dual_values": {"a": -4, "b": -6, "unexpected": 0}},
])
def test_invalid_optimal_evidence_fails_conservatively(changes):
    solution = replace(_valid_native_solution(), **changes)
    result = RestrictedMasterProblem(_initial_model()).solve(FixedSolver(solution))
    _assert_no_optimal_fields(result, SolverStatus.NUMERICAL_ISSUE)
    assert "optimality" in result.message


def test_every_optimal_result_is_checked_against_full_model(monkeypatch):
    calls = []
    checker = implementation.check_lp_optimality

    def observe(model, solution, tolerance):
        calls.append((model, tolerance))
        return checker(model, solution, tolerance)

    monkeypatch.setattr(implementation, "check_lp_optimality", observe)
    rmp = RestrictedMasterProblem(_initial_model())
    assert rmp.solve().objective_value == 17
    rmp.add_column(name="p", cost=7, row_coefficients={"a": 1, "b": 1})
    assert rmp.solve().objective_value == 14
    assert len(calls) == 2
    assert all(tolerance == 1e-9 for _, tolerance in calls)
    assert all([row.name for row in model.constraints] == ["a", "b"] for model, _ in calls)
    assert calls[0][0].variable_names() == ["la", "lb"]
    assert calls[1][0].variable_names() == ["la", "lb", "p"]


def test_backend_cannot_change_verification_input_or_persistent_rmp():
    class MutatingSolver(LPSolver):
        def solve(self, model):
            model.variables.clear()
            model.constraints.clear()
            model.objective = Objective({}, OptimizationSense.MAXIMIZE)
            return Solution(SolverStatus.OPTIMAL, objective_value=0)

    rmp = RestrictedMasterProblem(_initial_model())
    _assert_no_optimal_fields(rmp.solve(MutatingSolver()), SolverStatus.NUMERICAL_ISSUE)
    assert rmp.solve().objective_value == 17


def test_real_nonoptimal_calls_and_empty_seed_recovery():
    model = Model(constraints=[Constraint("need", {}, ConstraintSense.EQ, 1)],
                  objective=Objective({}, OptimizationSense.MINIMIZE))
    rmp = RestrictedMasterProblem(model)
    _assert_no_optimal_fields(rmp.solve(), SolverStatus.INFEASIBLE)
    rmp.add_column(name="seed", cost=3, row_coefficients={"need": 1})
    assert rmp.solve().objective_value == 3
    _assert_no_optimal_fields(RestrictedMasterProblem(_initial_model()).solve(
        RevisedSimplexSolver(iteration_limit=0)), SolverStatus.ITERATION_LIMIT)
    rmp.add_column(name="unbounded", cost=-1, row_coefficients={})
    _assert_no_optimal_fields(rmp.solve(), SolverStatus.UNBOUNDED)
