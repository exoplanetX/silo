"""Frozen independent counterexamples: objective pruning and full-pool proof."""

import itertools
import json
from fractions import Fraction as F
from pathlib import Path

import pytest

from silo import SolveOptions, solve
from silo.core.constraint import Constraint
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.decomposition.general_master import (
    FiniteColumnPricer,
    GeneralRestrictedMaster,
    MasterColumn,
    column_generation,
)
from silo.io import model_from_dict

MANIFEST = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures/prototype_revision_manifest.json").read_text()
)


def cg(entry):
    payload = entry["model"]
    pool = [MasterColumn(c["name"], c["cost"], c["coefficients"]) for c in payload["pool"]]
    model = Model(
        payload["name"],
        [Variable(n) for n in payload["initial"]],
        [
            Constraint(row["name"], row["coefficients"], row["sense"], row["rhs"])
            for row in payload["rows"]
        ],
        Objective({c.name: c.cost for c in pool if c.name in payload["initial"]}),
    )
    return column_generation(
        GeneralRestrictedMaster(model),
        FiniteColumnPricer(pool),
        options=SolveOptions(**entry["options"]),
        max_iterations=entry.get("round_limit", 20),
    )


def mip_reference(payload):
    values = [
        F(payload["objective"]["constant"])
        + F(payload["objective"]["coefficients"]["x"]) * x
        + F(payload["objective"]["coefficients"]["y"]) * y
        for x, y in itertools.product((0, 1), repeat=2)
        if 2 * x + 3 * y >= 3
    ]
    return (min if payload["sense"] == "minimize" else max)(values)


@pytest.mark.parametrize("entry", MANIFEST["targeted_cases"], ids=lambda entry: entry["id"])
def test_frozen_revision_optimality(entry):
    if entry["kind"].startswith("mip"):
        p = entry["payload"]
        reference = mip_reference(p)
        result = solve(model_from_dict(p), SolveOptions(**entry["options"]))
        assert result.status == entry["expected_status"], result
        sign = 1 if p["sense"] == "minimize" else -1
        if result.dual_bound is not None:
            assert sign * result.dual_bound <= sign * float(reference) + 1e-12 * (
                1 + abs(float(reference))
            )
        if result.objective_value is not None:
            x, y = (result.primal_values[n] for n in ("x", "y"))
            assert x in (0, 1) and y in (0, 1) and 2 * x + 3 * y >= 3
            assert sign * result.objective_value >= sign * float(reference) - 1e-12 * (
                1 + abs(float(reference))
            )
        else:
            assert result.absolute_gap is result.relative_gap is None
        if result.status == "optimal":
            assert abs(result.objective_value - float(reference)) <= 1e-12 * (
                1 + abs(float(reference))
            )
            assert result.primal_values == entry["expected_point"]
        return
    result = cg(entry)
    if entry["kind"] == "cg_limit":
        assert result.status in ("limit", "numerical_failure")
        assert result.dual_bound is None
    elif entry["model"]["expected_status"] == "optimal":
        assert result.status == "optimal", result
        assert result.objective_value == pytest.approx(-10000, abs=1e-8)
        assert result.dual_bound <= -10000 + 1e-8
        proof = result.witness
        assert proof["kind"] == "finite_pool_optimality"
        assert all(F(v) >= 0 for v in proof["reduced_costs"].values())
        assert F(proof["primal_objective"]) == F(proof["dual_objective"])
        assert any("x" in step.added_columns for step in result.trace)
        if not entry["options"]["presolve"]:
            assert any(step.termination_reason == "refine_dual_tolerance" for step in result.trace)
    else:
        assert result.status in ("unbounded", "limit", "numerical_failure")
        assert result.dual_bound is None or result.dual_bound == float("-inf")


@pytest.mark.parametrize("mutation", ["valid", "side", "column", "primal", "gap"])
def test_full_pool_gate_checks_raw_side_all_columns_primal_and_exact_gap(mutation):
    from silo.core.solve_types import SolveResult
    from silo.decomposition.general_master import _full_pool_certificate
    from silo.utils.rational import ProofBudget

    # Upper-only row, min -x at x=1; y=-1 and P=D=-1 are exact.
    model = Model(
        "proof", [Variable("x")], [Constraint("cap", {"x": 1}, "<=", 1)], Objective({"x": -1})
    )
    pool = [MasterColumn("x", -1, {"cap": 1})]
    point, dual = {"x": 1.0}, {"cap": -1.0}
    if mutation == "side":
        dual["cap"] = 1.0  # invalid sign on the absent lower side
    elif mutation == "column":
        pool.append(MasterColumn("missing", -2, {"cap": 1}))
    elif mutation == "primal":
        point["x"] = 2.0
    elif mutation == "gap":
        # Exactly feasible but suboptimal; even a huge objective tolerance cannot certify it.
        point["x"] = 0.5
    result = SolveResult("optimal", "test", primal_values=point, dual_values=dual)
    proof = _full_pool_certificate(
        model, pool, result, SolveOptions(objective_tolerance=1), ProofBudget()
    )
    assert (proof is not None) == (mutation == "valid")
    if proof is not None:
        assert F(proof["primal_objective"]) == F(proof["dual_objective"]) == -1


def test_finite_pool_prices_strict_binary_negative_within_old_tolerance():
    from silo.decomposition.general_master import PricingContext

    column = MasterColumn("tiny", -1e-8, {"cap": 1})
    context = PricingContext("phase2", {"cap": 0}, (), 1e-7, 1)
    assert FiniteColumnPricer([column]).price(context).columns == (column,)


def test_non_dyadic_master_basis_pair_is_checked_on_raw_input():
    model = Model(
        "third", [Variable("x")], [Constraint("need", {"x": 3}, ">=", 1)], Objective({"x": 1})
    )
    result = column_generation(
        GeneralRestrictedMaster(model, SolveOptions(presolve=False)),
        FiniteColumnPricer([MasterColumn("x", 1, {"need": 3})]),
    )
    assert result.status == "optimal"
    proof = result.witness
    assert F(proof["point"]["x"]) == F(1, 3)
    assert F(proof["row_duals"]["need"]) == F(1, 3)
    assert F(proof["primal_objective"]) == F(proof["dual_objective"]) == F(1, 3)
    assert F(result.dual_bound) <= F(1, 3)
    assert F(result.primal_bound) >= F(1, 3)
