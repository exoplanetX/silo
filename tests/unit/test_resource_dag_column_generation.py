"""Reference examples, real resource caps and bounded fault/lifecycle checks."""

from dataclasses import FrozenInstanceError, replace
from math import inf, nan, nextafter

import pytest

from silo.core.enums import ConstraintSense as S
from silo.core.status import SolverStatus as T
from silo.decomposition import (
    DagArc,
    DagColumnGenerationProblem,
    DagMasterRow,
    DagPricingProblem,
    DagPricingResult,
    ResourceDagColumnGenerationIteration,
    ResourceDagColumnGenerationResult,
    ResourceDagPricingProblem,
    ResourceDagPricingResult,
    solve_dag_column_generation,
)
from silo.decomposition import (
    DagColumnGenerationStatus as C,
)
from silo.decomposition import (
    ResourceDagPricingStatus as P,
)
from silo.decomposition import resource_dag_column_generation as cg
from silo.decomposition.restricted_master import RestrictedMasterProblem, RestrictedMasterResult
from silo.lp.simplex import revised as rv
from silo.lp.simplex.tableau import TableauSimplexSolver


def hand():
    graph = DagPricingProblem(("s", "u", "t"), (
        DagArc("a", "s", "u", 4), DagArc("b", "s", "u", 1, {"R": 1}),
        DagArc("c", "s", "u", 6, {"R": 2}), DagArc("d", "s", "u", -10, {"R": 0.5}),
        DagArc("z", "u", "t", 0)), "s", "t", ("conv", "R"),
        base_coefficients={"conv": 1})
    problem = DagColumnGenerationProblem(graph, (DagMasterRow("conv", S.EQ, 1),
        DagMasterRow("R", S.EQ, 0.5)), "conv", (("a", "z"), ("c", "z")))
    resources = ResourceDagPricingProblem(graph, (2,), {
        "a": (0,), "b": (1,), "c": (0,), "d": (2,), "z": (1,)})
    return problem, resources


def single():
    graph = DagPricingProblem(("s", "t"), (DagArc("e", "s", "t", 1),),
                              "s", "t", ("conv",), base_coefficients={"conv": 1})
    problem = DagColumnGenerationProblem(graph, (DagMasterRow("conv", S.EQ, 1),),
                                         "conv", (("e",),))
    return problem, ResourceDagPricingProblem(graph, (0,), {"e": (0,)})


def empty_bounds(record):
    assert record.numerical_upper_bound is record.dual_objective is record.rho is None
    assert record.numerical_lower_bound is record.numerical_gap is record.accepted_path is None
    assert record.objective_gap is record.roundoff_allowance is None


def watch_masters(monkeypatch):
    owners = []

    class ObservedMaster(RestrictedMasterProblem):
        def __init__(self, model):
            super().__init__(model)
            self.cold_calls = self.optin_calls = 0
            self.outcomes, self.columns = [], []
            owners.append(self)

        def solve(self, solver=None):
            self.cold_calls += 1
            return super().solve(solver)

        def solve_reoptimized(self, solver=None):
            self.optin_calls += 1
            outcome = super().solve_reoptimized(solver)
            self.outcomes.append(outcome)
            return outcome

        def add_column(self, **kwargs):
            self.columns.append(kwargs)
            return super().add_column(**kwargs)

    monkeypatch.setattr(cg, "RestrictedMasterProblem", ObservedMaster)
    return owners


class ObservedSolver(rv.RevisedSimplexSolver):
    def __init__(self):
        super().__init__()
        self.round = self.cold_calls = 0
        self.in_cold = False
        self.snapshots = []

    def reoptimize(self, model, snapshot=None):
        self.round += 1
        self.snapshots.append(snapshot)
        return super().reoptimize(model, snapshot)

    def solve_with_details(self, model, basis=None):
        self.cold_calls += 1
        self.in_cold = True
        try:
            return super().solve_with_details(model, basis)
        finally:
            self.in_cold = False


@pytest.mark.parametrize("mode", ("revised", "tableau", "reuse"))
def test_literal_two_round_example_and_original_duals(mode):
    problem, resources = hand()
    solver = TableauSimplexSolver() if mode == "tableau" else rv.RevisedSimplexSolver()
    result = cg.solve_resource_dag_column_generation(problem, resources, solver=solver,
                                                     reoptimize_rmp=mode == "reuse")
    assert isinstance(result, ResourceDagColumnGenerationResult)
    assert result.status == C.TOLERANCE_REACHED
    assert [r.master_result.objective_value for r in result.iterations] == [4.5, 2.5]
    assert [dict(r.master_result.dual_values) for r in result.iterations] == [
        {"conv": 4, "R": 1}, {"conv": 4, "R": -3}]
    assert [r.rho for r in result.iterations] == [-4, 0]
    assert result.iterations[0].accepted_path == ("b", "z")
    assert result.last_valid_master.primal_values == {"path_0": 0.5, "path_1": 0, "path_2": 0.5}
    assert ("d", "z") not in result.column_paths.values()


def test_real_warm_phase_two_public_entry_counts_and_fresh_owner(monkeypatch):
    owners = watch_masters(monkeypatch)
    solver = ObservedSolver()
    events, prices = [], []
    run, price = rv._run_primal_revised_simplex, cg.price_resource_dag

    def observe(**kw):
        events.append((solver.round, solver.in_cold, kw["phase_name"]))
        return run(**kw)

    def observe_price(*args, **kwargs):
        prices.append((args, kwargs))
        return price(*args, **kwargs)

    monkeypatch.setattr(rv, "_run_primal_revised_simplex", observe)
    monkeypatch.setattr(cg, "price_resource_dag", observe_price)
    problem, resources = hand()
    first = cg.solve_resource_dag_column_generation(problem, resources, solver=solver,
        reoptimize_rmp=True, pricing_state_limit=6, pricing_transition_limit=7)
    assert first.status == C.TOLERANCE_REACHED
    assert [event for event in events if event[0] == 2] == [(2, False, "Phase II")]
    assert owners[0].cold_calls == 0 and owners[0].optin_calls == 2
    assert [r.rmp_reoptimization.used_warm_start for r in first.iterations] == [False, True]
    assert solver.cold_calls == 1
    for record, outcome, (args, kwargs) in zip(first.iterations, owners[0].outcomes,
                                              prices, strict=True):
        assert record.master_result is outcome.result
        assert record.rmp_reoptimization is outcome
        assert args[0] is resources and args[1] is outcome.result.dual_values
        assert kwargs == {"tolerance": 1e-9, "state_limit": 6, "transition_limit": 7}
    second = cg.solve_resource_dag_column_generation(problem, resources, solver=solver,
                                                     reoptimize_rmp=True)
    assert second.status == C.TOLERANCE_REACHED
    assert len(owners) == 2 and owners[0] is not owners[1]
    assert solver.snapshots[0] is solver.snapshots[2] is None and solver.cold_calls == 2
    assert all(r.rmp_reoptimization is o for r, o in zip(
        second.iterations, owners[1].outcomes, strict=True))


def test_default_calls_only_public_cold_rmp_once_per_round(monkeypatch):
    owners = watch_masters(monkeypatch)
    result = cg.solve_resource_dag_column_generation(*hand())
    assert result.status == C.TOLERANCE_REACHED
    assert owners[0].cold_calls == 2 and owners[0].optin_calls == 0
    assert all(r.rmp_reoptimization is None for r in result.iterations)


@pytest.mark.parametrize("both_fail", (False, True))
def test_warm_failure_uses_only_rmp_internal_cold_fallback(monkeypatch, both_fail):
    owners = watch_masters(monkeypatch)
    solver, events, prices = ObservedSolver(), [], []
    run, price = rv._run_primal_revised_simplex, cg.price_resource_dag

    def injected(**kw):
        if solver.round == 2 and (not solver.in_cold or both_fail):
            events.append("cold" if solver.in_cold else "warm")
            return rv.RevisedRunResult(T.NUMERICAL_ISSUE, kw["basis"], message="injected failure")
        return run(**kw)

    def counted(*args, **kwargs):
        prices.append(args[1])
        return price(*args, **kwargs)

    monkeypatch.setattr(rv, "_run_primal_revised_simplex", injected)
    monkeypatch.setattr(cg, "price_resource_dag", counted)
    result = cg.solve_resource_dag_column_generation(*hand(), solver=solver, reoptimize_rmp=True)
    assert owners[0].cold_calls == 0 and owners[0].optin_calls == 2
    assert events == (["warm", "cold"] if both_fail else ["warm"])
    assert solver.cold_calls == 2
    failed = result.iterations[-1]
    assert failed.master_result is failed.rmp_reoptimization.result
    assert failed.rmp_reoptimization.cold_solve_count == 1
    assert failed.rmp_reoptimization.fallback_reason
    if both_fail:
        assert result.status == C.MASTER_FAILURE and len(prices) == 1
        assert result.last_valid_master is result.iterations[0].master_result
        assert result.column_set_iteration == result.last_valid_master_iteration == 1
        assert len(result.column_paths) == 2 and len(failed.column_paths) == 3
        assert failed.pricing_result is None
        empty_bounds(failed)
    else:
        assert result.status == C.TOLERANCE_REACHED and len(prices) == 2
        assert not failed.rmp_reoptimization.used_warm_start
        assert prices[-1] is failed.master_result.dual_values


@pytest.mark.parametrize("kwargs", [
    {"reoptimize_rmp": 1}, {"reoptimize_rmp": "true"},
    {"reoptimize_rmp": True, "solver": TableauSimplexSolver()},
    {"iteration_limit": True}, {"iteration_limit": 0}, {"iteration_limit": 1.5},
    {"tolerance": 0}, {"tolerance": nan}, {"tolerance": inf},
    {"pricing_state_limit": 0}, {"pricing_state_limit": True}, {"pricing_state_limit": 1.5},
    {"pricing_transition_limit": -1}, {"pricing_transition_limit": False},
    {"pricing_transition_limit": inf},
])
def test_invalid_parameters_rejected_before_any_work(monkeypatch, kwargs):
    def forbidden(*args, **kw):
        raise AssertionError("No RMP, pricing or numeric reconstruction allowed")

    monkeypatch.setattr(cg, "RestrictedMasterProblem", forbidden)
    monkeypatch.setattr(cg, "price_resource_dag", forbidden)
    monkeypatch.setattr(cg, "_reconstruct", forbidden)
    with pytest.raises((TypeError, ValueError)):
        cg.solve_resource_dag_column_generation(*hand(), **kwargs)


def test_input_types_and_same_graph_identity(monkeypatch):
    problem, resources = hand()

    def forbidden(*args, **kwargs):
        raise AssertionError("Inputs must fail before RMP/pricing")

    monkeypatch.setattr(cg, "RestrictedMasterProblem", forbidden)
    monkeypatch.setattr(cg, "price_resource_dag", forbidden)
    for p, r in ((None, resources), (problem, None),
                 (problem, replace(resources, graph=replace(problem.graph)))):
        with pytest.raises((TypeError, ValueError)):
            cg.solve_resource_dag_column_generation(p, r)


def test_all_seed_resources_checked_before_numeric_reconstruction(monkeypatch):
    problem, resources = hand()
    problem = replace(problem, seed_paths=(("a", "z"), ("d", "z")))

    def forbidden(*args, **kwargs):
        raise AssertionError("All seeds must be resource-checked first")

    for name in ("RestrictedMasterProblem", "price_resource_dag", "_reconstruct"):
        monkeypatch.setattr(cg, name, forbidden)
    with pytest.raises(ValueError, match="resource"):
        cg.solve_resource_dag_column_generation(problem, resources)


@pytest.mark.parametrize("kwargs,status,counts", [
    ({"pricing_state_limit": 5}, P.STATE_LIMIT, (5, 6)),
    ({"pricing_transition_limit": 5}, P.TRANSITION_LIMIT, (5, 5)),
])
def test_real_cap_after_a_sink_is_pricing_failure_not_convergence(kwargs, status, counts):
    result = cg.solve_resource_dag_column_generation(*hand(), reoptimize_rmp=True, **kwargs)
    assert result.status == C.PRICING_FAILURE and result.failure_iteration == 1
    failed = result.iterations[0]
    empty_bounds(failed)
    assert failed.pricing_result.status == status
    assert (failed.pricing_result.states_discovered,
            failed.pricing_result.transitions_checked) == counts
    assert failed.pricing_result.arc_ids == () and failed.pricing_result.resource_usage is None
    assert failed.pricing_result.is_improving is None
    assert result.last_valid_master is failed.master_result is failed.rmp_reoptimization.result
    assert result.column_paths == failed.column_paths


@pytest.mark.parametrize("status", (P.NO_PATH, P.NUMERICAL_ISSUE,
                                   P.STATE_LIMIT, P.TRANSITION_LIMIT))
def test_nonoptimal_price_preserves_its_diagnostic_and_empty_bounds(monkeypatch, status):
    diagnostic = ResourceDagPricingResult(status, states_discovered=3, message="synthetic")
    monkeypatch.setattr(cg, "price_resource_dag", lambda *args, **kwargs: diagnostic)
    result = cg.solve_resource_dag_column_generation(*hand())
    assert result.status == C.PRICING_FAILURE
    assert result.iterations[-1].pricing_result is diagnostic
    empty_bounds(result.iterations[-1])


@pytest.mark.parametrize("change", [
    {"resource_usage": None}, {"resource_usage": ()}, {"resource_usage": (True,)},
    {"resource_usage": (2.0,)}, {"resource_usage": (-1,)}, {"resource_usage": (1,)},
    {"arc_ids": ("unknown",)}, {"cost": 100}, {"reduced_cost": nan},
    {"row_coefficients": {"conv": 1}}, {"is_improving": False},
])
def test_invalid_candidate_never_enters_master(monkeypatch, change):
    owners, price = watch_masters(monkeypatch), cg.price_resource_dag
    monkeypatch.setattr(cg, "price_resource_dag",
                        lambda *args, **kwargs: replace(price(*args, **kwargs), **change))
    result = cg.solve_resource_dag_column_generation(*hand())
    assert result.status == C.NUMERICAL_ISSUE and not owners[0].columns
    empty_bounds(result.iterations[-1])


def test_forged_resource_infeasible_path_rejected_after_column_check(monkeypatch):
    bad = ResourceDagPricingResult(P.OPTIMAL, ("d", "z"), -10, {"R": 0.5, "conv": 1},
                                   -14.5, True, (3,))
    monkeypatch.setattr(cg, "price_resource_dag", lambda *args, **kwargs: bad)
    result = cg.solve_resource_dag_column_generation(*hand())
    assert result.status == C.NUMERICAL_ISSUE and "resource" in result.message
    empty_bounds(result.iterations[-1])


@pytest.mark.parametrize("bad", [None, object(), DagPricingResult("optimal"),
                                ResourceDagPricingResult("optimal")])
def test_wrong_result_record_or_status_is_numerical_failure(monkeypatch, bad):
    monkeypatch.setattr(cg, "price_resource_dag", lambda *args, **kwargs: bad)
    result = cg.solve_resource_dag_column_generation(*hand())
    assert result.status == C.NUMERICAL_ISSUE
    assert result.iterations[-1].pricing_result is None
    empty_bounds(result.iterations[-1])


def test_tolerance_close_fields_are_not_used_as_master_columns(monkeypatch):
    owners, price = watch_masters(monkeypatch), cg.price_resource_dag

    def drift(*args, **kwargs):
        result = price(*args, **kwargs)
        return replace(result, cost=result.cost + 5e-10,
                       row_coefficients={row: value + 5e-10
                                         for row, value in result.row_coefficients.items()})

    monkeypatch.setattr(cg, "price_resource_dag", drift)
    result = cg.solve_resource_dag_column_generation(*hand())
    assert result.status == C.TOLERANCE_REACHED
    assert owners[0].columns == [{"name": "path_2", "cost": 1,
                                  "row_coefficients": {"conv": 1, "R": 1}}]
    assert result.last_valid_master.objective_value == 2.5


@pytest.mark.parametrize("status", (T.INFEASIBLE, T.NUMERICAL_ISSUE, T.ITERATION_LIMIT))
def test_first_master_failure_has_no_price_or_valid_master(monkeypatch, status):
    monkeypatch.setattr(RestrictedMasterProblem, "solve", lambda *args, **kwargs:
                        RestrictedMasterResult(status, message="synthetic"))

    def forbidden(*args, **kwargs):
        raise AssertionError("Failed master must not trigger pricing")

    monkeypatch.setattr(cg, "price_resource_dag", forbidden)
    result = cg.solve_resource_dag_column_generation(*hand())
    assert result.status == C.MASTER_FAILURE and result.failure_iteration == 1
    assert result.last_valid_master is None and result.last_valid_master_iteration is None
    assert result.column_set_iteration == 1 and len(result.column_paths) == 2
    assert result.iterations[0].pricing_result is None
    empty_bounds(result.iterations[0])


def test_later_price_failure_keeps_current_solved_registry_and_outcome(monkeypatch):
    original, calls = cg.price_resource_dag, []

    def fail_second(*args, **kwargs):
        calls.append(args[1])
        return original(*args, **kwargs) if len(calls) == 1 else ResourceDagPricingResult(P.NO_PATH)

    monkeypatch.setattr(cg, "price_resource_dag", fail_second)
    result = cg.solve_resource_dag_column_generation(*hand(), reoptimize_rmp=True)
    assert result.status == C.PRICING_FAILURE and len(calls) == 2
    failed = result.iterations[-1]
    assert result.last_valid_master is failed.master_result is failed.rmp_reoptimization.result
    assert result.column_paths == failed.column_paths and len(result.column_paths) == 3
    assert result.last_valid_master_iteration == result.column_set_iteration == 2
    empty_bounds(failed)


def test_iteration_limit_does_not_append_an_unsolved_column():
    result = cg.solve_resource_dag_column_generation(*hand(), iteration_limit=1,
                                                     reoptimize_rmp=True)
    assert result.status == C.ITERATION_LIMIT and len(result.column_paths) == 2
    assert result.iterations[0].accepted_path is None and result.iterations[0].rho == -4
    assert result.last_valid_master_iteration == result.column_set_iteration == 1


def test_synthetic_existing_negative_column_is_rejected(monkeypatch):
    wrong = RestrictedMasterResult(T.OPTIMAL, 1, {"path_0": 1}, {"conv": 2}, {"path_0": -1})
    monkeypatch.setattr(RestrictedMasterProblem, "solve", lambda *args, **kwargs: wrong)
    result = cg.solve_resource_dag_column_generation(*single())
    assert result.status == C.NUMERICAL_ISSUE and "existing" in result.message
    empty_bounds(result.iterations[0])


def test_seed_numeric_overflow_returns_no_solved_history(monkeypatch):
    graph = DagPricingProblem(("s", "u", "t"), (DagArc("a", "s", "u", 1e308),
        DagArc("z", "u", "t", 1e308)), "s", "t", ("conv",),
        base_coefficients={"conv": 1})
    problem = DagColumnGenerationProblem(graph, (DagMasterRow("conv", S.EQ, 1),),
                                         "conv", (("a", "z"),))
    resources = ResourceDagPricingProblem(graph, (), {"a": (), "z": ()})

    def forbidden(*args, **kwargs):
        raise AssertionError("Numeric seed failure precedes RMP construction")

    monkeypatch.setattr(cg, "RestrictedMasterProblem", forbidden)
    result = cg.solve_resource_dag_column_generation(problem, resources)
    assert result.status == C.NUMERICAL_ISSUE and result.iterations == ()
    assert result.last_valid_master is result.column_set_iteration is None
    assert result.column_paths == {} and result.failure_iteration == 1


@pytest.mark.parametrize("failed_round", (1, 2))
def test_synthetic_master_objective_failure_keeps_only_earlier_valid_evidence(monkeypatch,
                                                                          failed_round):
    original, calls = cg._master_objectives, []

    def fail(*args):
        calls.append(1)
        if len(calls) == failed_round:
            raise cg._NumericalFailure("synthetic objective validation failure")
        return original(*args)

    monkeypatch.setattr(cg, "_master_objectives", fail)
    result = cg.solve_resource_dag_column_generation(*hand(), reoptimize_rmp=True)
    assert result.status == C.NUMERICAL_ISSUE and result.failure_iteration == failed_round
    failed = result.iterations[-1]
    assert failed.master_result is failed.rmp_reoptimization.result
    assert failed.pricing_result is None
    empty_bounds(failed)
    if failed_round == 1:
        assert result.last_valid_master is None and result.column_set_iteration == 1
    else:
        assert result.last_valid_master is result.iterations[0].master_result
        assert result.column_set_iteration == result.last_valid_master_iteration == 1
        assert len(result.column_paths) == 2 and len(failed.column_paths) == 3


def test_zero_resources_agree_with_ordinary_reference_and_double_resources_bind():
    problem, resource = hand()
    zero = ResourceDagPricingProblem(problem.graph, (), {arc: () for arc in resource.arc_resources})
    ordinary = solve_dag_column_generation(problem)
    reduced = cg.solve_resource_dag_column_generation(problem, zero)
    assert reduced.status == ordinary.status
    assert reduced.column_paths == ordinary.column_paths
    assert reduced.last_valid_master == ordinary.last_valid_master
    two = ResourceDagPricingProblem(problem.graph, (2, 1), {
        "a": (0, 0), "b": (1, 1), "c": (0, 0), "d": (2, 0), "z": (1, 1)})
    result = cg.solve_resource_dag_column_generation(problem, two)
    assert result.status == C.TOLERANCE_REACHED
    assert result.last_valid_master.objective_value == 4.5  # b fails only the second resource.
    assert result.iterations[0].pricing_result.resource_usage == (1, 1)


@pytest.mark.parametrize("sense,sign", [(S.LE, 1), (S.GE, -1), (S.GE, 1), (S.LE, -1)])
def test_inequality_original_min_dual_sign_and_row_flip(sense, sign):
    graph = DagPricingProblem(("s", "t"), (
        DagArc("seed", "s", "t", 2), DagArc("cheap", "s", "t", 0, {"R": sign}),
        DagArc("other", "s", "t", 1)), "s", "t", ("conv", "R"),
        base_coefficients={"conv": 1})
    problem = DagColumnGenerationProblem(graph, (DagMasterRow("conv", S.EQ, 1),
        DagMasterRow("R", sense, 0)), "conv", (("seed",),))
    resources = ResourceDagPricingProblem(graph, (0,), {arc.arc_id: (0,) for arc in graph.arcs})
    result = cg.solve_resource_dag_column_generation(problem, resources)
    assert result.status == C.TOLERANCE_REACHED
    restrictive = (sense == S.LE and sign == 1) or (sense == S.GE and sign == -1)
    assert result.last_valid_master.objective_value == (1 if restrictive else 0)
    for record in result.iterations:
        pi = record.master_result.dual_values["R"]
        assert pi <= 1e-9 if sense == S.LE else pi >= -1e-9


@pytest.mark.parametrize("constant", [2**60, -(2**60)])
def test_large_common_constant_preserves_local_gap(constant):
    problem, resources = hand()
    result = cg.solve_resource_dag_column_generation(replace(problem, objective_constant=constant),
                                                     resources)
    assert result.status == C.TOLERANCE_REACHED
    assert result.iterations[0].numerical_gap == 0
    assert result.iterations[0].objective_gap == 4
    assert result.iterations[-1].objective_gap == 0


@pytest.mark.parametrize("weight,constant,status", [
    (nextafter(1, 0), 0, C.TOLERANCE_REACHED), (1 - 5e-10, 2**60, C.NUMERICAL_ISSUE),
])
def test_synthetic_signed_gap_uses_local_allowance_not_global_constant(monkeypatch, weight,
                                                                    constant, status):
    problem, resources = single()
    snapshot = RestrictedMasterResult(T.OPTIMAL, float(constant + weight),
                                      {"path_0": weight}, {"conv": 1}, {"path_0": 0})
    monkeypatch.setattr(RestrictedMasterProblem, "solve", lambda *args, **kwargs: snapshot)
    result = cg.solve_resource_dag_column_generation(replace(problem, objective_constant=constant),
                                                     resources)
    assert result.status == status
    record = result.iterations[-1]
    if status == C.TOLERANCE_REACHED:
        assert record.objective_gap < 0
        assert -record.objective_gap <= record.roundoff_allowance <= 1e-9
    else:
        empty_bounds(record)


def test_history_and_exported_records_are_immutable_snapshots():
    result = cg.solve_resource_dag_column_generation(*hand(), reoptimize_rmp=True)
    first, second = result.iterations
    assert isinstance(first, ResourceDagColumnGenerationIteration)
    assert len(first.column_paths) == 2 and len(second.column_paths) == 3
    with pytest.raises(TypeError):
        first.column_paths["new"] = ("b", "z")
    with pytest.raises(FrozenInstanceError):
        first.accepted_path = ("d", "z")
    with pytest.raises(TypeError):
        first.pricing_result.row_coefficients["R"] = 0
    with pytest.raises(FrozenInstanceError):
        first.rmp_reoptimization.cold_solve_count = 10
