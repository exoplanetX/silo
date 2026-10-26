"""One isolated formal acceptance unit, with a parent-enforced wall timeout."""

import json
import sys
import time
from pathlib import Path


def main():
    from silo import SolveOptions, solve
    from silo.io import model_from_dict, model_to_dict
    from silo.lp.session import LPSession

    from .exact import equivalent
    from .runtime import ROOT, sha, write_new

    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    options = SolveOptions(**request["options"])
    model = model_from_dict(request["payload"])
    calls = Path(sys.argv[2]).with_suffix(".calls.jsonl")

    def called(label, function, *args):
        with calls.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": "entry", "label": label}) + "\n")
        return function(*args)

    if "session" not in request:
        started = time.perf_counter()
        result = called("solve", solve, model, options)
        output = {"results": [{"seconds": time.perf_counter() - started,
                               "payload": model_to_dict(model), "result": result.to_dict()}]}
    else:
        session = LPSession(model, options)
        results = []
        started = time.perf_counter()
        initial = called("session_initial", session.solve)
        results.append({"seconds": time.perf_counter() - started,
                        "payload": model_to_dict(session.model), "result": initial.to_dict()})
        change = request["session"]
        modified = model_from_dict(change["modified"])
        if change["kind"] == "rhs":
            session.change_row_bounds("cap", None, 3)
        elif change["kind"] == "bounds":
            session.change_bounds("y", 0, 1)
        elif change["kind"] == "row":
            session.append_row(modified.constraints[-1])
        else:
            session.append_column(modified.variables[-1], {"cap": 1}, 4)
        # Never solve if the edit did not produce exactly the frozen state.
        equivalent(change["modified"], model_to_dict(session.model))
        started = time.perf_counter()
        result = called("session_modified", session.solve)
        results.append({"seconds": time.perf_counter() - started,
                        "payload": model_to_dict(session.model), "result": result.to_dict()})
        output = {"results": results}
    origin = {}
    for name, module in sorted(sys.modules.items()):
        if (name == "silo" or name.startswith("silo.")) and getattr(module, "__file__", None):
            path = Path(module.__file__).resolve()
            assert path.is_relative_to(ROOT / "src"), (name, path)
            origin[path.relative_to(ROOT).as_posix()] = sha(path)
    output["source_origins"] = origin
    output["public_entries"] = len(calls.read_text(encoding="utf-8").splitlines())
    write_new(sys.argv[2], output)


if __name__ == "__main__":
    main()
