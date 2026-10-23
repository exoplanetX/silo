from dataclasses import FrozenInstanceError
from fractions import Fraction
from math import inf, nan
from pathlib import Path

import pytest

from silo import solve
from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solve_types import SolveOptions
from silo.core.variable import Variable
from silo.decomposition import RestrictedMasterProblem
from silo.decomposition import general_master as implementation
from silo.decomposition.general_master import (
    FiniteColumnPricer,
    GeneralRestrictedMaster,
    MasterColumn,
    PricingContext,
    PricingResult,
    column_generation,
    covering_example,
    covering_input_payload,
)


def _model(pool, rows, initial=None, constant=0):
    selected = tuple(pool) if initial is None else tuple(c for c in pool if c.name in initial)
    return Model(
        name="test_general_master",
        variables=[Variable(c.name) for c in selected],
        constraints=[
            Constraint(
                name,
                {c.name: c.row_coefficients.get(name, 0) for c in selected},
                lower_bound=lower,
                upper_bound=upper,
            )
            for name, lower, upper in rows
        ],
        objective=Objective({c.name: c.cost for c in selected}, constant=constant),
    )


def _cover():
    pool = (
        MasterColumn("a", 3, {"r": 1}),
        MasterColumn("b", 2, {"s": 1}),
        MasterColumn("ab", 4, {"r": 1, "s": 1}),
        MasterColumn("aa", 1, {"r": 2}),
    )
    return pool, (("r", 1, inf), ("s", 1, inf))


def _run(pool, rows, initial=(), constant=0, **kwargs):
    options = kwargs.pop("options", SolveOptions(presolve=False))
    master = GeneralRestrictedMaster(_model(pool, rows, initial, constant), options)
    result = column_generation(master, FiniteColumnPricer(pool), **kwargs)
    return result, master


@pytest.mark.parametrize("presolve", [False, True])
@pytest.mark.parametrize("scaling", [False, True])
def test_fixed_covering_example_matches_analytic_and_full_column_lp(presolve, scaling):
    options = SolveOptions(presolve=presolve, scaling=scaling)
    result = covering_example(options)
    pool, rows = _cover()
    full = solve(_model(pool, rows), options)
    assert result.status == full.status == "optimal"
    assert result.objective_value == pytest.approx(2.5)
    assert result.objective_value == pytest.approx(full.objective_value)
    assert result.primal_values["double_a"] == pytest.approx(0.5)
    assert result.primal_values["b"] == pytest.approx(1)
    assert result.pool_size == 4 and result.pricing_complete
    assert result.phase1_objective == pytest.approx(0)
    assert result.iterations == len(result.trace) <= 20
    assert result.trace[-1].termination_reason == "finite_pool_optimal"
    assert result.trace[-1].pricing_reduced_costs.keys() == {"a", "b", "ab", "double_a"}
    assert all(not name.startswith("__cg_art_") for name in result.primal_values)
    if not presolve:
        assert any(step.basis_reused for step in result.trace if step.added_columns == ())


def test_partitioning_equality_and_constant_need_no_implicit_convex_combination():
    pool = (MasterColumn("unit", 3, {"partition": 1}),)
    result, master = _run(pool, (("partition", 2, 2),), initial=("unit",), constant=7)
    assert result.status == "optimal"
    assert result.primal_values["unit"] == pytest.approx(2)
    assert result.objective_value == pytest.approx(13)
    assert [row.name for row in master.model.constraints] == ["partition"]
    assert master.model.constraints[0].row_bounds == (2, 2)


def test_general_mixed_rows_and_negative_coefficients_match_full_lp():
    pool = (
        MasterColumn("a", 3, {"range": 1, "eq": 1, "cap": 1, "free": 999}),
        MasterColumn("b", 1, {"range": -1, "eq": 1, "cap": 1}),
        MasterColumn("c", 2, {"range": 2, "eq": 1}),
    )
    rows = (("range", 1, 3), ("eq", 2, 2), ("cap", -inf, 4), ("free", -inf, inf))
    result, master = _run(pool, rows, initial=("a", "b"))
    full = solve(_model(pool, rows), SolveOptions(presolve=False))
    assert result.status == full.status == "optimal"
    assert result.objective_value == pytest.approx(full.objective_value)
    assert result.objective_value == pytest.approx(3)
    assert result.primal_values["b"] == pytest.approx(1)
    assert result.primal_values["c"] == pytest.approx(1)
    assert [row.row_bounds for row in master.model.constraints] == [row[1:] for row in rows]
    last = result.trace[-1]
    for column in pool:
        expected = column.cost - sum(
            value * last.dual_values[name] for name, value in column.row_coefficients.items()
        )
        assert last.pricing_reduced_costs[column.name] == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    "rows,coefficients,objective",
    [
        ((("r", 2, inf),), {"r": 1}, 4),
        ((("r", -inf, -2),), {"r": -1}, 4),
        ((("r", -3, -3),), {"r": -1}, 6),
        ((("r", 2, 4),), {"r": 1}, 4),
    ],
)
def test_phase1_restores_empty_initial_master_for_each_side(rows, coefficients, objective):
    pool = (MasterColumn("real", 2, coefficients),)
    result, master = _run(pool, rows)
    assert result.status == "optimal"
    assert result.objective_value == pytest.approx(objective)
    assert result.trace[0].phase == "phase1"
    assert result.trace[0].objective > 0
    assert result.trace[0].added_columns == ("real",)
    assert any(step.basis_reused for step in result.trace if step.phase == "phase1")
    assert master.model.variable_names() == ["real"]
    assert result.phase1_objective == pytest.approx(0)


def test_phase1_explicit_per_side_artificials_then_clean_original_model(monkeypatch):
    pool = (MasterColumn("real", 2, {"range": 1, "eq": 1}),)
    rows = (("range", 1, 3), ("eq", 2, 2), ("free", -inf, inf))
    snapshots = []
    original_solve = implementation.LPSession.solve

    def observed(session, model=None):
        snapshots.append(session.model if model is None else model)
        return original_solve(session, model)

    monkeypatch.setattr(implementation.LPSession, "solve", observed)
    result, _ = _run(pool, rows, initial=("real",))
    assert result.status == "optimal" and result.objective_value == pytest.approx(4)
    auxiliary = snapshots[0]
    arts = set(auxiliary.variable_names()) - {"real"}
    assert len(arts) == 4 and len(auxiliary.constraints) == 4
    assert auxiliary.objective.coefficients.get("real", 0) == 0
    assert auxiliary.objective.constant == 0
    assert all(auxiliary.objective.coefficients[name] == 1 for name in arts)
    for row in auxiliary.constraints:
        present = set(row.coefficients) & arts
        assert len(present) == 1
        assert row.coefficients[present.pop()] == (1 if row.sense == ConstraintSense.GE else -1)
    cleaned = snapshots[-1]
    assert cleaned.variable_names() == ["real"]
    assert [row.name for row in cleaned.constraints] == ["range", "eq", "free"]
    assert cleaned.objective.coefficients == {"real": 2}
    assert any(
        step.termination_reason == "phase1_feasible_remove_artificials" for step in result.trace
    )


@pytest.mark.parametrize("pool", [(), (MasterColumn("bad", 1, {"r": -1}),)])
def test_positive_phase1_with_complete_pool_has_exact_farkas(pool):
    result, _ = _run(pool, (("r", 1, inf),), initial=tuple(c.name for c in pool))
    assert result.status == "infeasible"
    assert result.termination_reason == "finite_pool_infeasible"
    assert result.objective_value is None and not result.has_primal_solution
    assert result.phase1_objective == pytest.approx(1)
    assert result.pricing_complete
    assert result.witness["kind"] == "finite_pool_farkas"
    assert Fraction(result.witness["separation"]) > 0
    assert all(Fraction(value) <= 0 for value in result.witness["column_products"].values())
    assert all(step.phase == "phase1" for step in result.trace)


class _EmptyHeuristic:
    def price(self, context):
        return PricingResult(complete=True)


@pytest.mark.parametrize("feasible", [False, True])
def test_heuristic_self_claimed_completeness_never_proves_optimal_or_infeasible(feasible):
    pool = (MasterColumn("a", 1, {"r": 1}),)
    model = _model(pool, (("r", 1, inf),), initial=("a",) if feasible else ())
    master = GeneralRestrictedMaster(model)
    result = column_generation(master, _EmptyHeuristic())
    assert result.status == "limit" and result.termination_reason == "incomplete_pricing"
    assert result.pricing_complete is False and result.pool_size is None
    assert result.trace[-1].phase == ("phase2" if feasible else "phase1")
    assert result.has_primal_solution is feasible
    assert result.witness is None


def test_finite_subclass_lying_price_is_heuristic():
    class Liar(FiniteColumnPricer):
        def price(self, context):
            return PricingResult(complete=True)

    pool, rows = _cover()
    master = GeneralRestrictedMaster(_model(pool, rows, ("a", "b")))
    result = column_generation(master, Liar(pool))
    assert result.status == "limit" and result.termination_reason == "incomplete_pricing"
    assert result.objective_value == pytest.approx(5)


def test_driver_verifies_finite_enumeration_instead_of_trusting_price(monkeypatch):
    monkeypatch.setattr(FiniteColumnPricer, "price", lambda self, ctx: PricingResult(complete=True))
    pool, rows = _cover()
    result, _ = _run(pool, rows, initial=("a", "b"))
    assert result.status == "optimal" and result.objective_value == pytest.approx(2.5)
    assert any(step.added_columns == ("aa",) for step in result.trace)


def test_heuristic_can_add_a_column_but_cannot_claim_full_optimality():
    pool, rows = _cover()

    class UsefulHeuristic:
        def price(self, context):
            return PricingResult((pool[-1],), complete=True)

    master = GeneralRestrictedMaster(_model(pool, rows, ("a", "b")), SolveOptions(presolve=False))
    result = column_generation(master, UsefulHeuristic())
    assert result.status == "limit" and result.termination_reason == "incomplete_pricing"
    assert result.objective_value == pytest.approx(2.5)
    assert any(step.added_columns == ("aa",) for step in result.trace)


def test_append_column_uses_same_public_basis_and_warm_reoptimization():
    pool, rows = _cover()
    model = _model(pool, rows, ("a", "b"), constant=7)
    master = GeneralRestrictedMaster(model, SolveOptions(presolve=False))
    first = master.solve()
    basis = master.basis
    assert first.status == "optimal" and first.objective_value == pytest.approx(12)
    assert basis is not None
    master.add_column("aa", 1, {"r": 2})
    assert master.basis is basis
    after = master.solve()
    assert after.objective_value == pytest.approx(9.5)
    assert after.diagnostics["warm_starts"] == 1
    assert after.diagnostics["cold_starts"] == 0
    assert len(master.history) == 2
    assert first.primal_values == {"a": pytest.approx(1), "b": pytest.approx(1)}


def test_models_columns_context_and_pool_are_owned_snapshots():
    coefficients = {"r": 1}
    column = MasterColumn("a", 3, coefficients)
    coefficients["r"] = 99
    assert column.row_coefficients["r"] == 1
    with pytest.raises(TypeError):
        column.row_coefficients["r"] = 99
    pool = [column]
    pricer = FiniteColumnPricer(pool)
    pool.clear()
    assert len(pricer.columns) == 1
    with pytest.raises(FrozenInstanceError):
        pricer.columns = ()
    model = _model(pricer.columns, (("r", 2, inf),))
    master = GeneralRestrictedMaster(model)
    model.constraints.clear()
    exported = master.model
    exported.objective.coefficients["a"] = 99
    exported.constraints.clear()
    assert master.solve().objective_value == pytest.approx(6)
    history = master.history
    history[0]["objective"] = 99
    assert master.history[0]["objective"] == pytest.approx(6)
    dual = {"r": 3}
    context = PricingContext("phase2", dual, (), 1e-7, inf)
    dual["r"] = 99
    assert context.reduced_cost(column) == 0
    with pytest.raises(TypeError):
        context.dual_values["r"] = 99


def test_reduced_cost_uses_binary_values_instead_of_decimal_reconstruction():
    column = MasterColumn("a", 0.3, {"r": 3})
    context = PricingContext("phase2", {"r": 0.1}, (), 1e-20, inf)
    exact = Fraction(0.3) - 3 * Fraction(0.1)
    assert exact < 0
    assert Fraction(context.reduced_cost(column)) == exact
    assert FiniteColumnPricer((column,)).price(context).columns == (column,)


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "a"},
        {"name": ""},
        {"cost": nan},
        {"cost": inf},
        {"cost": 2**60 + 1},
        {"row_coefficients": {"missing": 1}},
        {"row_coefficients": {"r": nan}},
        {"row_coefficients": {"r": -inf}},
        {"row_coefficients": []},
    ],
)
def test_invalid_add_column_is_atomic(changes):
    pool, rows = _cover()
    master = GeneralRestrictedMaster(_model(pool, rows, ("a", "b")))
    arguments = {"name": "new", "cost": 1, "row_coefficients": {"r": 2}}
    arguments.update(changes)
    with pytest.raises((ValueError, TypeError)):
        master.add_column(**arguments)
    assert master.model.variable_names() == ["a", "b"]
    assert master.solve().objective_value == pytest.approx(5)


@pytest.mark.parametrize(
    "variable",
    [
        Variable("a", Bounds(-1, inf)),
        Variable("a", Bounds(0, 3)),
        Variable("a", var_type=VariableType.INTEGER),
    ],
)
def test_master_rejects_out_of_domain_columns(variable):
    with pytest.raises(ValueError):
        GeneralRestrictedMaster(Model(variables=[variable]))


def test_master_rejects_nonfinite_constant_and_maximization():
    with pytest.raises(ValueError, match="finite"):
        GeneralRestrictedMaster(Model(objective=Objective(constant=nan)))
    with pytest.raises(ValueError, match="minimization"):
        GeneralRestrictedMaster(Model(objective=Objective(sense=OptimizationSense.MAXIMIZE)))


@pytest.mark.parametrize(
    "pool",
    [
        (),
        (MasterColumn("a", 99, {"r": 1}),),
        (MasterColumn("a", 1, {"r": 99}),),
        (MasterColumn("a", 1, {"r": 1, "unknown": 1}),),
    ],
)
def test_complete_pool_identity_is_validated_against_initial_master(pool):
    model = _model((MasterColumn("a", 1, {"r": 1}),), (("r", 1, inf),))
    master = GeneralRestrictedMaster(model)
    with pytest.raises(ValueError):
        column_generation(master, FiniteColumnPricer(pool))
    assert not master.history


def test_duplicate_pool_names_rejected():
    with pytest.raises(ValueError, match="unique"):
        FiniteColumnPricer((MasterColumn("a", 1), MasterColumn("a", 2)))


def test_bad_pricing_is_explicit_and_does_not_change_original_model():
    class BadPricer:
        def price(self, context):
            return PricingResult((MasterColumn("new", 1, {"unknown": 1}),), complete=True)

    pool, rows = _cover()
    master = GeneralRestrictedMaster(_model(pool, rows, ("a", "b")))
    result = column_generation(master, BadPricer())
    assert result.status == "invalid_model" and result.termination_reason == "invalid_pricing"
    assert master.model.variable_names() == ["a", "b"]
    assert "pricing_error" in result.trace[-1].lp_diagnostics


def test_unbounded_restricted_master_implies_unbounded_full_pool():
    pool = (MasterColumn("negative", -1), MasterColumn("unused", 2))
    result, _ = _run(pool, (), initial=("negative",))
    assert result.status == "unbounded"
    assert result.witness is not None
    assert result.objective_value == pytest.approx(0)
    assert result.trace[-1].phase == "phase2"


@pytest.mark.parametrize(
    "options,reason",
    [
        (SolveOptions(time_limit=0), "time_limit"),
        (SolveOptions(lp_iteration_limit=0), "lp_iteration_limit"),
    ],
)
def test_zero_shared_budgets_do_not_start_lp(options, reason):
    pool, rows = _cover()
    result, master = _run(pool, rows, initial=("a", "b"), options=options)
    assert result.status == "limit" and result.termination_reason == reason
    assert result.iterations == 0 and not result.trace and not master.history


def test_round_limit_counts_phase1_and_retains_only_real_feasible_point():
    pool, rows = _cover()
    result, master = _run(pool, rows, initial=("a", "b"), max_iterations=1)
    assert result.status == "limit" and result.termination_reason == "cg_iteration_limit"
    assert result.iterations == 1 and result.trace[0].phase == "phase1"
    assert result.objective_value == pytest.approx(5)
    assert set(result.primal_values) == {"a", "b"}
    assert not master.history


def test_round_limit_after_unsolved_addition_clears_top_duals_but_keeps_trace_and_point():
    pool, rows = _cover()
    pool = (*pool[:-1], MasterColumn("double_a", pool[-1].cost, pool[-1].row_coefficients))
    result, master = _run(pool, rows, initial=("a", "b"), max_iterations=2)
    assert result.status == "limit" and result.termination_reason == "cg_iteration_limit"
    assert master.model.variable_names() == ["a", "b", "double_a"]
    assert result.dual_values == {} and result.dual_bound is None
    assert result.objective_value == pytest.approx(5)
    assert result.primal_values == {
        "a": pytest.approx(1),
        "b": pytest.approx(1),
        "double_a": 0,
    }
    step = result.trace[-1]
    assert step.column_names == ("a", "b")
    assert step.dual_values == {"r": pytest.approx(3), "s": pytest.approx(2)}
    assert step.added_columns == ("double_a",)
    assert step.pricing_reduced_costs["double_a"] < 0


def test_pricing_runtime_error_returns_failure_with_existing_primal_and_trace():
    class FailingPricer:
        def price(self, context):
            raise RuntimeError("pricing failed on purpose")

    pool, rows = _cover()
    master = GeneralRestrictedMaster(_model(pool, rows, ("a", "b")))
    result = column_generation(master, FailingPricer())
    assert result.status == "numerical_failure"
    assert result.termination_reason == "pricing_error"
    assert result.objective_value == pytest.approx(5)
    assert len(result.trace) == 2 and result.trace[-1].termination_reason == "pricing_error"
    assert result.trace[-1].lp_diagnostics["pricing_error"] == (
        "RuntimeError: pricing failed on purpose"
    )
    assert master.model.variable_names() == ["a", "b"]


@pytest.mark.parametrize("exception", [KeyboardInterrupt, SystemExit])
def test_pricing_process_control_exceptions_propagate(exception):
    class InterruptingPricer:
        def price(self, context):
            raise exception()

    with pytest.raises(exception):
        column_generation(GeneralRestrictedMaster(Model()), InterruptingPricer())


@pytest.mark.parametrize("limit", [-1, 21, True, 1.5])
def test_max_rounds_cannot_exceed_frozen_twenty(limit):
    with pytest.raises(ValueError, match="20"):
        column_generation(
            GeneralRestrictedMaster(Model()), FiniteColumnPricer(()), max_iterations=limit
        )


def test_remaining_time_and_pivots_shared_between_all_phase_solves(monkeypatch):
    clock = {"now": 0.0}
    calls, results = [], []
    original_solve = GeneralRestrictedMaster.solve
    monkeypatch.setattr(implementation, "perf_counter", lambda: clock["now"])

    def observed(master, options=None):
        calls.append(options)
        clock["now"] += 1
        result = original_solve(master, options)
        results.append(result)
        return result

    monkeypatch.setattr(GeneralRestrictedMaster, "solve", observed)
    pool, rows = _cover()
    result, _ = _run(
        pool,
        rows,
        initial=("a", "b"),
        options=SolveOptions(presolve=False, time_limit=10, lp_iteration_limit=100),
    )
    assert result.status == "optimal"
    assert len(calls) == result.iterations == 3
    assert [call.time_limit for call in calls] == [10, 9, 8]
    used = 0
    for call, lp in zip(calls, results, strict=True):
        assert call.lp_iteration_limit == 100 - used
        used += lp.iterations
    assert used == result.lp_iterations


def test_slow_heuristic_response_rejected_before_adding_column(monkeypatch):
    clock = {"now": 0.0}
    monkeypatch.setattr(implementation, "perf_counter", lambda: clock["now"])
    pool, rows = _cover()

    class SlowPricer:
        def price(self, context):
            assert 0 < context.remaining_seconds <= 1
            clock["now"] += 2
            return PricingResult((pool[-1],), complete=True)

    master = GeneralRestrictedMaster(_model(pool, rows, ("a", "b")))
    result = column_generation(master, SlowPricer(), options=SolveOptions(time_limit=1))
    assert result.status == "limit" and result.termination_reason == "time_limit"
    assert master.model.variable_names() == ["a", "b"]
    assert result.objective_value == pytest.approx(5)


def test_legacy_restricted_master_retains_its_api_and_explicit_interval_rejection():
    legacy = Model(
        variables=[Variable("a")],
        constraints=[Constraint("r", {"a": 1}, ConstraintSense.EQ, 2)],
        objective=Objective({"a": 3}, constant=7),
    )
    assert RestrictedMasterProblem(legacy).solve().objective_value == pytest.approx(13)
    assert GeneralRestrictedMaster(legacy).solve().objective_value == pytest.approx(13)
    ranged = _model((MasterColumn("a", 3, {"r": 1}),), (("r", 2, 3),))
    with pytest.raises(ValueError, match="general restricted master"):
        RestrictedMasterProblem(ranged)
    assert GeneralRestrictedMaster(ranged).solve().objective_value == pytest.approx(6)


def test_result_trace_serializes_public_information_without_basis_internals():
    import json

    result = covering_example()
    encoded = json.loads(json.dumps(result.to_dict(), allow_nan=False))
    assert encoded["status"] == "optimal" and encoded["objective_value"] == pytest.approx(2.5)
    assert encoded["has_primal_solution"] is True
    assert encoded["primal_bound"] == encoded["dual_bound"] == pytest.approx(2.5)
    assert encoded["parameters"]["max_iterations"] == 20
    assert all(
        {
            "phase",
            "objective",
            "pricing_reduced_costs",
            "basis_reused",
            "elapsed_seconds",
            "termination_reason",
            "column_names",
            "added_columns",
        }
        <= set(step)
        for step in encoded["trace"]
    )
    with pytest.raises(TypeError):
        result.primal_values["made_up"] = 1


def test_covering_example_uses_exact_frozen_integration_payload_and_hash():
    import hashlib
    import json

    manifest = json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "prototype_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    frozen = dict(manifest["integrations"]["finite_cg"])
    expected_hash = frozen.pop("input_sha256")
    result = covering_example()
    assert result.input_identity == "prototype_manifest.integrations.finite_cg"
    assert result.input_payload == covering_input_payload() == frozen
    computed = hashlib.sha256(
        json.dumps(
            result.input_payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()
    assert result.input_sha256 == computed == expected_hash
    assert result.objective_value == pytest.approx(frozen["expected_objective"])
