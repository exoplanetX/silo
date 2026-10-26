"""Construct once, then independently verify the frozen small acceptance corpus."""

import argparse
import copy
import json
import subprocess
from pathlib import Path

from .oracle import solve
from .runtime import FIXTURE, ROOT, sha, write_new


def variable(name, lower=0, upper=4, typ="continuous"):
    return {"name": name, "lower": lower, "upper": upper, "type": typ}


def row(name, coefficients, lower=None, upper=None):
    return {"name": name, "coefficients": coefficients, "lower": lower, "upper": upper}


def model(name, variables, coefficients, rows=(), sense="minimize", constant=0):
    return {"name": name, "sense": sense, "variables": variables,
            "objective": {"coefficients": coefficients, "constant": constant},
            "constraints": list(rows)}


def corpus():
    p = []
    add = p.append
    add(model("L01", [variable("x")], {"x": 2}, [row("floor", {"x": 1}, 2)], constant=1))
    add(model("L02", [variable("x"), variable("y")], {"x": 2, "y": 3},
              [row("cap", {"x": 1, "y": 1}, upper=4)], "maximize", -2))
    add(model("L03", [variable("x", None, None), variable("y")], {"x": -1, "y": 2},
              [row("link", {"x": 1, "y": -1}, 1, 1), row("floor", {"y": 1}, 1)]))
    add(model("L04", [variable("x", -2, 3), variable("y", -1, 2), variable("t", 2, 2)],
              {"x": 1, "y": -1, "t": 0.5}, sense="maximize", constant=1))
    add(model("L05", [variable("x", -2, 5), variable("y", 0, 3)], {"x": 1, "y": 2},
              [row("band", {"x": 1, "y": 1}, 1, 4)], constant=0.25))
    add(model("L06", [variable("x", None, 3), variable("y", -2, 4)], {"x": -0.5, "y": 0.25},
              [row("link", {"x": 1, "y": 1}, -1)]))
    add(model("L07", [variable("x", 0, 5), variable("zero", -1, 2)], {"x": 1},
              [row("eq", {"x": 2}, 3, 3)], constant=-0.5))
    add(model("L08", [variable("x"), variable("y")], {"x": -1, "y": -1},
              [row("budget", {"x": 2, "y": 1}, upper=5),
               row("budget__lower", {"y": 1}, 0.5, 3)], constant=2))
    add(model("L09", [variable("x", -3, 3)], {"x": -0.125},
              [row("band", {"x": 0.5}, -0.5, 1.25)], "maximize", 0.125))
    add(model("L10", [variable("x"), variable("y")], {"x": 1, "y": 1},
              [row("sum", {"x": 1, "y": 1}, 2, 2)], constant=3))
    add(model("L11", [variable("x", None, None), variable("z", 1, 3)], {"x": 2, "z": -1},
              [row("lower", {"x": 1}, -2), row("upper", {"x": 1}, upper=1)], constant=4))
    add(model("L12", [variable("x", 0.5, 3.5), variable("y", -1, 1)], {"x": -2, "y": 1},
              [row("mix", {"x": 0.5, "y": 0.25}, upper=1.5)], "maximize"))
    add(model("L13", [variable("x"), variable("y"), variable("z")],
              {"x": 1, "y": 2, "z": 3},
              [row("cover", {"x": 1, "y": 1, "z": 1}, 3)], constant=-1))
    add(model("L14", [variable("x", -2, 4), variable("y", -2, 4)], {"x": -1, "y": 0.5},
              [row("interval", {"x": 1, "y": -1}, -1, 2)], "maximize", 0.75))
    add(model("L15", [variable("x", 1, 1), variable("y", None, None)], {"x": 2, "y": -1},
              [row("equal", {"x": 1, "y": 2}, 5, 5)], constant=-3))
    add(model("L16", [variable("x"), variable("z", -2, 2)], {"x": 0, "z": 0},
              [row("nonempty", {"x": 1}, 1, 3)], constant=2.5))
    for i in range(4):
        add(model(f"L{17+i:02}", [variable("x", -2, 4)], {"x": 1},
                  [row("atleast", {"x": 1}, 2+i/4), row("atmost", {"x": 1}, upper=1)]))
    witnesses = {}
    for i in range(4):
        name = f"L{21+i:02}"
        direction = 1 if i % 2 == 0 else -1
        add(model(name, [variable("x", 0 if direction == 1 else None,
                                  None if direction == 1 else 0)], {"x": -direction},
                  [row("halfline", {"x": direction}, 0)], constant=i/4))
        witnesses[name] = {"anchor": {"x": 0}, "ray": {"x": direction}}
    # Four nonintegral relaxation optima with strict integer gaps.
    for i in range(4):
        sense = "maximize" if i % 2 == 0 else "minimize"
        coeff = 1 if sense == "maximize" else -1
        add(model(f"M{i+1:02}", [variable("x", 0, 3, "integer"),
                                 variable("y", 0, 3, "integer"), variable("z", 0, 2)],
                  {"x": coeff, "y": coeff, "z": -coeff},
                  [row("cap", {"x": 2, "y": 2}, upper=5)], sense, i/4))
    add(model("M05", [variable("b", 0, 1, "binary"), variable("y", -1, 2)],
              {"b": -2, "y": 1}, [row("link", {"y": 1, "b": -1}, 0)], constant=0.5))
    add(model("M06", [variable("x", -1, 2, "integer"), variable("b", 0, 1, "binary")],
              {"x": 1, "b": 2}, [row("sum", {"x": 1, "b": 1}, upper=2)], "maximize", -1))
    for i in range(2):
        add(model(f"M{7+i:02}", [variable("x", 0, 2, "integer"), variable("y", -1, 1)],
                  {"x": 1, "y": 1}, [row("fractional", {"x": 1}, 0.5, 0.5)]))
    edits = []
    base = copy.deepcopy(p[1])
    for kind in ("rhs", "bounds", "row", "column"):
        changed = copy.deepcopy(base)
        changed["name"] = "edit_" + kind
        if kind == "rhs":
            changed["constraints"][0]["upper"] = 3
        elif kind == "bounds":
            changed["variables"][1]["upper"] = 1
        elif kind == "row":
            changed["constraints"].append(row("extra", {"y": 1}, upper=1.5))
        else:
            changed["variables"].append(variable("z", 0, 2))
            changed["objective"]["coefficients"]["z"] = 4
            changed["constraints"][0]["coefficients"]["z"] = 1
        edits.append({"kind": kind, "initial": "L02", "modified": changed})
    return {"models": p, "witnesses": witnesses, "edits": edits,
            "resolve_ids": ["L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08",
                            "M01", "M02", "M03", "M04"],
            "external_ids": ["L01", "L02", "L03", "L04", "L05", "L06", "L07", "L08",
                             "M01", "M02", "M03", "M04"],
            "options": {"lp_iteration_limit": 10000, "node_limit": 10000,
                        "cuts": False, "heuristics": False},
            "tolerances": {"primal": 1e-7, "dual": 1e-7, "complementarity": 1e-7,
                           "objective": 1e-7, "integer": 1e-7}}


def verify():
    manifest = json.loads((FIXTURE / "manifest.json").read_text(encoding="utf-8"))
    for relative, digest in manifest["files"].items():
        assert sha(ROOT / relative) == digest, relative
    data = json.loads((FIXTURE / "inputs.json").read_text(encoding="utf-8"))
    truth = json.loads((FIXTURE / "truth.json").read_text(encoding="utf-8"))
    for payload in data["models"] + [e["modified"] for e in data["edits"]]:
        actual = solve(payload, data["witnesses"].get(payload["name"]))
        actual.pop("meter")
        expected = dict(truth[payload["name"]])
        expected.pop("meter")
        assert actual == expected, payload["name"]
    assert sum(truth[f"M{i:02}"]["strict_fractional_gap"] for i in range(1, 5)) == 4
    total = sum(p.stat().st_size for p in FIXTURE.rglob("*") if p.is_file())
    assert total <= 512 * 1024
    print(json.dumps({"frozen_models": 32, "edited_states": 4, "fractional_gap_mips": 4,
                      "fixture_bytes": total, "files": len(manifest["files"]),
                      "actual_silo_requests": 0}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    if args.create:
        data = corpus()
        truth = {p["name"]: solve(p, data["witnesses"].get(p["name"]))
                 for p in data["models"] + [e["modified"] for e in data["edits"]]}
        write_new(FIXTURE / "inputs.json", data)
        write_new(FIXTURE / "truth.json", truth)
        paths = [FIXTURE / "inputs.json", FIXTURE / "truth.json", ROOT / "docs/lp_format.md",
                 Path(__file__).with_name("oracle.py"), Path(__file__).with_name("exact.py")]
        write_new(FIXTURE / "manifest.json", {
            "schema": 1, "issuance": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "files": {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
            "public_requests": 160, "operations": "exact Fraction; no SILO imports",
            "profile": "SILO-LP-1", "post_freeze": "read only"})
    verify()


if __name__ == "__main__":
    main()
