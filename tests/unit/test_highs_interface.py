"""Optional external comparisons; native algorithms remain independent of SciPy."""

import ast
import json
from math import inf
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solve_types import SolveOptions, SolveResult
from silo.core.variable import Variable
from silo.interfaces import highs
from silo.io import model_from_dict


def general_model(maximize=False):
    payload = {
        "name": "comparison",
        "sense": "minimize",
        "variables": [
            {"name": "x", "lower": -2, "upper": 4},
            {"name": "y", "lower": None},
            {"name": "z", "lower": 3, "upper": 3},
            {"name": "u", "lower": None, "upper": 2},
        ],
        "constraints": [
            {"name": "range", "coefficients": {"x": 1, "y": 1}, "lower": 1, "upper": 3}
        ],
        "objective": {"coefficients": {"x": 1, "y": 2, "z": 5, "u": -1}, "constant": 7},
    }
    if maximize:
        payload["sense"] = "maximize"
        payload["objective"]["constant"] *= -1
        payload["objective"]["coefficients"] = {
            n: -c for n, c in payload["objective"]["coefficients"].items()
        }
    return model_from_dict(payload)


@pytest.mark.parametrize("maximize", [False, True])
def test_lp_adapter_maps_original_ranges_bounds_and_constant(monkeypatch, maximize):
    captured = {}

    def linprog(cost, **kwargs):
        captured.update(cost=cost, **kwargs)
        return SimpleNamespace(status=0, message="optimal", x=[4, -3, 3, 2], fun=11, nit=2)

    monkeypatch.setattr(
        highs,
        "_scipy_modules",
        lambda: (SimpleNamespace(__version__="test"), SimpleNamespace(linprog=linprog)),
    )
    result = highs.solve_with_highs(general_model(maximize))
    assert result.status == "optimal"
    assert result.objective_value == (-18 if maximize else 18)
    assert result.original_primal_valid
    assert result.dual_bound == result.objective_value
    assert result.absolute_gap == result.relative_gap == 0
    assert captured["bounds"] == [(-2, 4), (None, None), (3, 3), (None, 2)]
    np.testing.assert_array_equal(captured["A_ub"], [[1, 1, 0, 0], [-1, -1, 0, 0]])
    np.testing.assert_array_equal(captured["b_ub"], [3, -1])
    np.testing.assert_array_equal(captured["cost"], [1, 2, 5, -1])
    assert captured["method"] == "highs" and result.external_algorithm_count == 1
    json.dumps(result.to_dict(), allow_nan=False)


def test_milp_maximize_bound_constant_and_gap_use_original_direction(monkeypatch):
    captured = {}

    def milp(cost, **kwargs):
        captured.update(cost=cost, **kwargs)
        return SimpleNamespace(
            status=1,
            message="node limit",
            x=[3],
            fun=-6,
            mip_dual_bound=-8,
            mip_gap=1 / 3,
            mip_node_count=4,
        )

    optimize = SimpleNamespace(milp=milp, Bounds=lambda lb, ub: SimpleNamespace(lb=lb, ub=ub))
    monkeypatch.setattr(
        highs, "_scipy_modules", lambda: (SimpleNamespace(__version__="test"), optimize)
    )
    model = model_from_dict(
        {
            "sense": "maximize",
            "variables": [{"name": "x", "upper": 4, "type": "integer"}],
            "objective": {"coefficients": {"x": 2}, "constant": 5},
        }
    )
    result = highs.solve_with_highs(model, SolveOptions(node_limit=4))
    assert result.status == "limit" and result.original_primal_valid
    assert result.primal_bound == 11 and result.dual_bound == 13
    assert result.absolute_gap == 2 and result.relative_gap == pytest.approx(2 / 13)
    assert result.backend_relative_gap == pytest.approx(1 / 3)
    np.testing.assert_array_equal(captured["integrality"], [1])
    assert captured["options"]["node_limit"] == 4


def test_optional_scipy_absence_is_structured_and_explicit(monkeypatch):
    def absent():
        raise ImportError("scipy is not installed")

    monkeypatch.setattr(highs, "_scipy_modules", absent)
    assert highs.highs_availability()["available"] is False
    result = highs.solve_with_highs(general_model())
    assert result.available is False and result.status == "unavailable"
    assert result.termination_reason == "optional_dependency_missing"
    assert result.external_algorithm_count == 0 and not result.has_primal_solution


def test_limit_without_primal_never_publishes_a_finite_gap(monkeypatch):
    raw = SimpleNamespace(status=1, message="time limit", x=None, fun=None, nit=0)
    optimize = SimpleNamespace(linprog=lambda *args, **kwargs: raw)
    monkeypatch.setattr(
        highs, "_scipy_modules", lambda: (SimpleNamespace(__version__="test"), optimize)
    )
    result = highs.solve_with_highs(general_model(), SolveOptions(time_limit=0))
    assert result.status == "limit" and not result.has_primal_solution
    assert result.absolute_gap is None and result.relative_gap is None


def test_external_success_with_infeasible_primal_is_rejected(monkeypatch):
    raw = SimpleNamespace(status=0, message="optimal", x=[2], fun=2, nit=0)
    optimize = SimpleNamespace(linprog=lambda *args, **kwargs: raw)
    monkeypatch.setattr(
        highs, "_scipy_modules", lambda: (SimpleNamespace(__version__="test"), optimize)
    )
    model = Model(variables=[Variable("x", Bounds(0, 1))], objective=Objective({"x": 1}))
    result = highs.solve_with_highs(model)
    assert result.status == "numerical_failure" and not result.has_primal_solution
    assert result.termination_reason == "original_primal_failed"


def test_comparison_consumes_a_precomputed_native_result(monkeypatch):
    model = general_model()
    native = SolveResult(
        "optimal", "verified", objective_value=18, primal_values={"x": 4, "y": -3, "z": 3, "u": 2}
    )
    external = highs.HighsComparisonResult(
        "optimal",
        "verified",
        objective_value=18,
        primal_values=native.primal_values,
        original_primal_valid=True,
        external_algorithm_count=1,
    )
    monkeypatch.setattr(highs, "solve_with_highs", lambda *args, **kwargs: external)
    result = highs.compare_with_highs(model, native)
    assert result["optimal_comparison_passed"]
    assert result["external_algorithm_count"] == 1
    assert result["evidence_stream"] == "scipy_highs"
    native.primal_values = {"x": 0, "y": 0, "z": 3, "u": 2}
    assert not highs.compare_with_highs(model, native)["optimal_comparison_passed"]


@pytest.mark.parametrize("maximize", [False, True])
def test_real_optional_highs_general_lp(maximize):
    pytest.importorskip("scipy.optimize")
    result = highs.solve_with_highs(general_model(maximize))
    assert result.status == "optimal", result
    assert result.objective_value == pytest.approx(-18 if maximize else 18)
    assert result.original_primal_valid and result.external_algorithm_count == 1


def test_real_optional_highs_mixed_negative_bounds_and_binary_domain():
    pytest.importorskip("scipy.optimize")
    model = model_from_dict(
        {
            "variables": [
                {"name": "i", "lower": -2, "upper": 1, "type": "integer"},
                {"name": "b", "upper": 1, "type": "binary"},
                {"name": "f", "upper": 4},
            ],
            "constraints": [
                {"name": "d", "coefficients": {"i": 1, "b": 1, "f": 1}, "sense": ">=", "rhs": 1.5},
                {"name": "l", "coefficients": {"f": 1, "b": -2}, "rhs": 1},
            ],
            "objective": {"coefficients": {"i": 2, "b": 3, "f": 0.5}, "constant": -2},
        }
    )
    result = highs.solve_with_highs(model)
    assert result.status == "optimal", result
    assert result.objective_value == pytest.approx(-1.75)
    assert result.dual_bound == pytest.approx(-1.75)
    assert result.original_primal_valid


@pytest.mark.parametrize("integer", [False, True])
@pytest.mark.parametrize("status", ["infeasible", "unbounded"])
def test_real_optional_highs_nonoptimal_statuses(integer, status):
    pytest.importorskip("scipy.optimize")
    if status == "infeasible":
        model = model_from_dict(
            {
                "variables": [
                    {
                        "name": "x",
                        "lower": 0,
                        "upper": 1,
                        "type": "integer" if integer else "continuous",
                    }
                ],
                "constraints": [{"name": "bad", "coefficients": {"x": 1}, "sense": ">=", "rhs": 2}],
            }
        )
    else:
        model = Model(
            variables=[
                Variable(
                    "x",
                    Bounds(0, inf),
                    VariableType.INTEGER if integer else VariableType.CONTINUOUS,
                )
            ],
            objective=Objective({"x": -1}),
        )
    result = highs.solve_with_highs(model)
    assert result.status == status, result
    assert result.absolute_gap is None and result.relative_gap is None


def test_native_layers_never_import_scipy_or_the_external_adapter():
    root = Path(__file__).resolve().parents[2] / "src/silo"
    for layer in (
        "core",
        "modeling",
        "presolve",
        "lp",
        "mip",
        "cuts",
        "decomposition",
        "uncertainty",
    ):
        for path in (root / layer).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports = [
                node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
            ]
            imports += [
                alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            ]
            assert not any(
                name.startswith(("scipy", "silo.interfaces.highs")) for name in imports
            ), path


def _no_backend_stub(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid input entered the external algorithm")

    optimize = SimpleNamespace(
        linprog=forbidden, milp=forbidden, Bounds=forbidden, LinearConstraint=forbidden
    )
    monkeypatch.setattr(
        highs, "_scipy_modules", lambda: (SimpleNamespace(__version__="test"), optimize)
    )


@pytest.mark.parametrize("value", [float("nan"), inf, -inf])
def test_empty_model_nonfinite_constant_is_rejected_before_optimality(monkeypatch, value):
    _no_backend_stub(monkeypatch)
    model = Model(objective=Objective({}, constant=value))
    result = highs.solve_with_highs(model)
    assert result.status == "invalid_model"
    assert not result.has_primal_solution and result.objective_value is None
    assert result.external_algorithm_count == 0
    json.dumps(result.to_dict(), allow_nan=False)


@pytest.mark.parametrize("value", [float("nan"), inf, -inf])
@pytest.mark.parametrize("location", ["cost", "row_coefficient", "legacy_rhs"])
def test_nonfinite_raw_data_never_enters_highs(monkeypatch, value, location):
    _no_backend_stub(monkeypatch)
    model = Model(variables=[Variable("x", Bounds(0, 1))])
    if location == "cost":
        model.set_objective(Objective({"x": value}))
    else:
        model.add_constraint(
            Constraint(
                "r",
                {"x": value if location == "row_coefficient" else 1},
                rhs=value if location == "legacy_rhs" else 1,
            )
        )
    result = highs.solve_with_highs(model)
    assert result.status == "invalid_model"
    assert not result.has_primal_solution and result.external_algorithm_count == 0


@pytest.mark.parametrize("location", ["constant", "cost", "row_coefficient", "bound", "row_side"])
def test_inexact_large_integer_conversion_matches_native_rejection(monkeypatch, location):
    _no_backend_stub(monkeypatch)
    value = 2**60 + 1
    model = Model() if location == "constant" else Model(variables=[Variable("x", Bounds(0, 1))])
    if location == "constant":
        model.set_objective(Objective({}, constant=value))
    elif location == "cost":
        model.set_objective(Objective({"x": value}))
    elif location == "row_coefficient":
        model.add_constraint(Constraint("r", {"x": value}, rhs=1))
    elif location == "bound":
        model.variables[0] = Variable("x", Bounds(0, value))
    else:
        model.add_constraint(Constraint("r", {"x": 1}, lower_bound=value))
    result = highs.solve_with_highs(model)
    assert result.status == "numerical_failure"
    assert "exactly representable" in result.backend_message
    assert not result.has_primal_solution and result.external_algorithm_count == 0


def test_exactly_representable_large_integer_constant_remains_supported(monkeypatch):
    _no_backend_stub(monkeypatch)
    result = highs.solve_with_highs(Model(objective=Objective({}, constant=2**60)))
    assert result.status == "optimal" and result.objective_value == 2**60
    assert result.has_primal_solution and result.external_algorithm_count == 0


def _integer_ray_model():
    return Model(
        variables=[Variable("x", Bounds(0, inf), VariableType.INTEGER)],
        objective=Objective({"x": -1}),
    )


def _mock_milp(monkeypatch, milp):
    optimize = SimpleNamespace(milp=milp, Bounds=lambda lb, ub: SimpleNamespace(lb=lb, ub=ub))
    monkeypatch.setattr(
        highs, "_scipy_modules", lambda: (SimpleNamespace(__version__="test"), optimize)
    )


def test_ambiguous_mip_presolve_retry_uses_only_remaining_time_and_nodes(monkeypatch):
    clock, calls = [0.0], []
    monkeypatch.setattr(highs, "perf_counter", lambda: clock[0])

    def milp(cost, **kwargs):
        calls.append(dict(kwargs["options"]))
        if len(calls) == 1:
            clock[0] = 4
            return SimpleNamespace(
                status=4, message="Infeasible or unbounded", x=None, fun=None, mip_node_count=2
            )
        clock[0] = 6
        return SimpleNamespace(status=3, message="Unbounded", x=None, fun=None, mip_node_count=1)

    _mock_milp(monkeypatch, milp)
    result = highs.solve_with_highs(_integer_ray_model(), SolveOptions(time_limit=10, node_limit=5))
    assert result.status == "unbounded" and result.backend_status == 3
    assert len(calls) == 2 and calls[0]["presolve"] is True and calls[1]["presolve"] is False
    assert calls[0]["time_limit"] == 10 and calls[1]["time_limit"] == 6
    assert calls[0]["node_limit"] == 5 and calls[1]["node_limit"] == 3
    assert result.nodes == 3 and result.elapsed_seconds == 6
    assert result.external_algorithm_count == 1 and result.diagnostics["backend_calls"] == 2
    assert result.diagnostics["ambiguous_presolve_resolved"]


@pytest.mark.parametrize("presolve", [False, True])
def test_ambiguous_backend_result_is_never_relabelled_unbounded(monkeypatch, presolve):
    calls = []

    def milp(cost, **kwargs):
        calls.append(kwargs["options"])
        return SimpleNamespace(status=4, message="Unbounded or infeasible", x=None, fun=None)

    _mock_milp(monkeypatch, milp)
    result = highs.solve_with_highs(_integer_ray_model(), SolveOptions(presolve=presolve))
    assert result.status == "numerical_failure" and result.backend_status == 4
    assert len(calls) == (2 if presolve else 1)
    assert result.diagnostics["ambiguous_presolve_resolved"] is False


@pytest.mark.parametrize("budget", ["time_limit", "node_limit"])
def test_ambiguous_retry_stops_at_exhausted_shared_budget(monkeypatch, budget):
    calls, clock = [], [0.0]
    monkeypatch.setattr(highs, "perf_counter", lambda: clock[0])

    def milp(cost, **kwargs):
        calls.append(kwargs["options"])
        clock[0] = 2
        return SimpleNamespace(
            status=4, message="Infeasible or unbounded", x=None, fun=None, mip_node_count=5
        )

    _mock_milp(monkeypatch, milp)
    options = SolveOptions(time_limit=1 if budget == "time_limit" else inf, node_limit=5)
    result = highs.solve_with_highs(_integer_ray_model(), options)
    assert result.status == "limit" and result.termination_reason == budget
    assert result.backend_status == 4 and len(calls) == 1
    assert result.relative_gap is None and result.absolute_gap is None


def test_nonambiguous_numeric_failure_is_not_retried(monkeypatch):
    calls = []

    def milp(cost, **kwargs):
        calls.append(kwargs["options"])
        return SimpleNamespace(status=4, message="Numerical failure", x=None, fun=None)

    _mock_milp(monkeypatch, milp)
    result = highs.solve_with_highs(_integer_ray_model())
    assert result.status == "numerical_failure" and len(calls) == 1
