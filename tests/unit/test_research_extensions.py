"""Public MIP policies must preserve feasibility, proof bounds and ownership."""

import json
from dataclasses import FrozenInstanceError
from math import inf
from pathlib import Path

import pytest

from silo import SolveOptions, SolveResult, solve
from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.mip.research import ResearchExtensions
from silo.mip.research_example import policy_model_payload, run_example


def branching_model():
    return Model(
        "branching",
        [Variable("x", Bounds(0, 3), "integer"), Variable("y", Bounds(0, 4))],
        [Constraint("cover", {"x": 2, "y": 1}, ">=", 3)],
        Objective({"x": 1, "y": 1}),
    )


def test_installed_policy_example_matches_frozen_truth():
    result = run_example()
    assert result["status"] == "optimal" and result["objective"] == -8.5
    assert result["diagnostics"]["research_calls"] >= 3
    assert result["trace"][-1]["event"] == "terminated"
    integration = json.loads(
        (Path(__file__).resolve().parents[2] / "tests/fixtures/prototype_manifest.json").read_text()
    )["integrations"]["mip_policy"]
    assert policy_model_payload() == integration["model"]
    assert result["input_sha256"] == integration["input_sha256"]
    assert result["policy_invocations"]["node_selector"] > 0
    assert result["policy_invocations"]["branch_rule"] == 0  # integral frozen root
    json.dumps(result, allow_nan=False)
    assert result["trace"][0]["dual_bound_kind"] == "negative_infinity"


def test_replacement_branch_node_and_heuristic_paths_are_real_and_deterministic():
    def run():
        calls = []

        def branch(context):
            calls.append(("branch", context.node, context.fractional))
            return context.fractional[0]

        def select(context):
            choice = max(context.open_nodes, key=lambda n: n.number).number
            calls.append(("node", choice))
            return choice

        def heuristic(context):
            calls.append(("heuristic", context.node))
            return {"x": 2, "y": 0}

        result = solve(
            branching_model(),
            SolveOptions(presolve=False, cuts=False, heuristics=False),
            extensions=ResearchExtensions(
                branch_rule=branch, node_selector=select, heuristic=heuristic
            ),
        )
        return result, calls

    first, calls = run()
    second, other = run()
    assert first.status == second.status == "optimal" and first.objective_value == 2
    assert calls == other and any(item[0] == "branch" for item in calls)
    assert any(item[0] == "heuristic" for item in calls)


def test_context_is_a_deep_readonly_snapshot_and_includes_active_bound():
    captured = []

    def observer(context):
        captured.append(context)
        with pytest.raises(TypeError):
            context.lower["x"] = 99
        with pytest.raises(FrozenInstanceError):
            context.event = "changed"
        if context.event == "node_selected":
            assert context.dual_bound == -inf or context.dual_bound <= 2

    result = solve(branching_model(), extensions=ResearchExtensions(observer=observer))
    assert result.status == "optimal"
    assert captured[0].lower["x"] == 0


@pytest.mark.parametrize(
    "hook,callback",
    [
        ("node_selector", lambda c: 999),
        ("branch_rule", lambda c: "absent"),
        ("heuristic", lambda c: {"x": 0, "y": 0}),
        ("heuristic", lambda c: {"x": 2}),
        ("separator", lambda c: [999]),
        ("observer", lambda c: (_ for _ in ()).throw(ValueError("policy failed"))),
    ],
)
def test_invalid_research_action_keeps_a_valid_frontier(hook, callback):
    result = solve(
        branching_model(),
        SolveOptions(presolve=False, cuts=hook == "separator", heuristics=False),
        extensions=ResearchExtensions(**{hook: callback}),
    )
    assert result.status == "limit" and result.termination_reason == "invalid_research_action"
    assert result.diagnostics["open_nodes"] >= 1
    assert result.dual_bound <= 2
    assert result.diagnostics["research_error"]


def test_separator_can_select_only_verified_cuts_or_decline():
    seen = []

    def separate(context):
        seen.extend(context.cuts)
        with pytest.raises(TypeError):
            context.cuts[0].coefficients["x"] = -1
        return [0]

    result = solve(
        branching_model(),
        SolveOptions(presolve=False),
        extensions=ResearchExtensions(separator=separate),
    )
    assert result.status == "optimal" and result.objective_value == pytest.approx(2)
    assert seen and result.diagnostics["cuts_added"] > 0
    declined = solve(
        branching_model(),
        SolveOptions(presolve=False),
        extensions=ResearchExtensions(separator=lambda c: []),
    )
    assert declined.status == "optimal" and declined.diagnostics["cuts_added"] == 0


def test_callback_budget_stops_before_mutating_the_tree():
    result = solve(
        branching_model(), extensions=ResearchExtensions(observer=lambda c: None, call_limit=0)
    )
    assert result.status == "limit" and result.termination_reason == "research_call_limit"
    assert result.nodes == 0 and result.diagnostics["open_nodes"] == 1
    assert result.dual_bound == -inf


def test_callback_deadline_failure_preserves_verified_relaxation(monkeypatch):
    import silo.mip.research as research

    ticks = iter([0, inf])
    monkeypatch.setattr(research, "perf_counter", lambda: next(ticks, inf))
    result = solve(
        branching_model(),
        SolveOptions(time_limit=10),
        extensions=ResearchExtensions(node_selector=lambda c: c.open_nodes[0].number),
    )
    assert result.status == "limit" and result.termination_reason == "time_limit"
    assert result.diagnostics["open_nodes"] == 1 and result.diagnostics["lp_calls"] == 0


def test_lp_extension_domain_and_extension_argument_are_explicit():
    with pytest.raises(TypeError, match="ResearchExtensions"):
        solve(branching_model(), extensions={})
    result = solve(Model(), extensions=ResearchExtensions())
    assert result.status == "unsupported"
    with pytest.raises(ValueError):
        ResearchExtensions(call_limit=-1)


@pytest.mark.parametrize("event", ["relaxation", "terminated"])
def test_terminal_observer_failure_retains_primary_lp_failure(monkeypatch, event):
    import silo.lp.general as lp

    monkeypatch.setattr(
        lp,
        "solve_lp_data",
        lambda *args, **kwargs: SolveResult("numerical_failure", "controlled_lp_failure"),
    )

    def observer(context):
        if context.event == event:
            raise RuntimeError("secondary observer failure")

    result = solve(branching_model(), extensions=ResearchExtensions(observer=observer))
    assert result.status == "numerical_failure"
    assert result.termination_reason == "controlled_lp_failure"
    assert result.dual_bound == -inf and result.relative_gap is None
    assert result.diagnostics["open_nodes"] == 1
    assert "secondary observer failure" in result.diagnostics["research_error"]
