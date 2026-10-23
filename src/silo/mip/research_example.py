"""External research policy using only the public extension API."""

import hashlib
import json

from silo import SolveOptions, solve
from silo.io import model_from_dict
from silo.mip.research import ResearchExtensions


def policy_model_payload():
    """Exact JSON input identity, including names and integer numeric syntax."""
    return {
        "name": "frozen",
        "sense": "minimize",
        "variables": [
            {"name": f"x{i}", "lower": 0, "upper": 1, "type": "binary"} for i in range(4)
        ],
        "constraints": [
            {"name": "p", "coefficients": {"x0": 1, "x1": 1}, "sense": "=", "rhs": 1},
            {"name": "q", "coefficients": {"x2": 1, "x3": 1}, "sense": "=", "rhs": 1},
            {"name": "c", "coefficients": {"x0": 2, "x2": 2}, "sense": "<=", "rhs": 3},
        ],
        "objective": {"coefficients": {f"x{i}": -(i + 2) for i in range(4)}, "constant": -0.5},
    }


def digest(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def run_example():
    """Frozen small_milp(10): explicit two-choice capacities, optimum -8.5."""
    payload = policy_model_payload()
    integration = {
        "model": payload,
        "node_limit": 1000,
        "oracle_kind": "integer_enumeration_vertices",
    }
    model = model_from_dict(payload)
    trace = []

    def observer(context):
        trace.append(
            {
                "event": context.event,
                "node": context.node,
                "primal_bound": context.primal_bound,
                "dual_bound": context.dual_bound,
                "iterations": context.iterations,
                "elapsed_seconds": context.elapsed_seconds,
            }
        )

    extensions = ResearchExtensions(
        branch_rule=lambda context: min(context.fractional),
        node_selector=lambda context: max(context.open_nodes, key=lambda n: n.number).number,
        observer=observer,
    )
    result = solve(model, SolveOptions(node_limit=1000), extensions=extensions)
    return {
        "status": result.status,
        "objective": result.objective_value,
        "primal_values": result.primal_values,
        "nodes": result.nodes,
        "iterations": result.iterations,
        "trace": trace,
        "reason": result.termination_reason,
        "parameters": {"node_limit": 1000},
        "input_identity": "prototype_manifest.integrations.mip_policy",
        "input_sha256": digest(integration),
        "model_sha256": digest(payload),
        "policy_invocations": {
            name: sum(item["hook"] == name for item in result.diagnostics["research_trace"])
            for name in ("branch_rule", "node_selector", "observer")
        },
        "diagnostics": result.diagnostics,
    }
