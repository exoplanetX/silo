"""Standalone external file reader. No optimization methods and no SILO import."""

import argparse
import importlib.metadata
import json
import math
from pathlib import Path


def main():
    import highspy

    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert importlib.metadata.version("highspy") == "1.15.1"
    requests = json.loads(args.requests.read_text(encoding="utf-8"))
    assert len(requests) == 24
    records = []
    for request in requests:
        reader = highspy.Highs()
        reader.setOptionValue("output_flag", False)
        status = reader.readModel(request["path"])
        assert status == highspy.HighsStatus.kOk, (request, str(status))
        lp = reader.getLp()
        names, row_names = list(lp.col_names_), list(lp.row_names_)
        assert len(names) == lp.num_col_ and len(row_names) == lp.num_row_
        matrix = lp.a_matrix_
        coefficients = [dict() for _ in row_names]
        starts, indexes, values = list(matrix.start_), list(matrix.index_), list(matrix.value_)
        if matrix.format_ == highspy.MatrixFormat.kColwise:
            for j, name in enumerate(names):
                for k in range(starts[j], starts[j + 1]):
                    coefficients[indexes[k]][name] = values[k]
        elif matrix.format_ == highspy.MatrixFormat.kRowwise:
            for i in range(len(row_names)):
                for k in range(starts[i], starts[i + 1]):
                    coefficients[i][names[indexes[k]]] = values[k]
        else:
            raise AssertionError("unknown external matrix representation")

        def bound(value, *, lower):
            if math.isfinite(value):
                return value
            assert value == (-math.inf if lower else math.inf), "invalid external infinite side"
            return None

        integrality = list(lp.integrality_) or [highspy.HighsVarType.kContinuous] * len(names)
        assert all(t in (highspy.HighsVarType.kContinuous, highspy.HighsVarType.kInteger)
                   for t in integrality)
        payload = {
            "name": lp.model_name_,
            "sense": "minimize" if lp.sense_ == highspy.ObjSense.kMinimize else "maximize",
            "variables": [{"name": n, "lower": bound(lp.col_lower_[j], lower=True),
                           "upper": bound(lp.col_upper_[j], lower=False),
                           "type": "continuous" if integrality[j] ==
                           highspy.HighsVarType.kContinuous else "integer"}
                          for j, n in enumerate(names)],
            "objective": {"coefficients": dict(zip(names, list(lp.col_cost_), strict=True)),
                          "constant": lp.offset_},
            "constraints": [{"name": n, "coefficients": coefficients[i],
                             "lower": bound(lp.row_lower_[i], lower=True),
                             "upper": bound(lp.row_upper_[i], lower=False)}
                            for i, n in enumerate(row_names)],
        }
        records.append({"id": request["id"], "format": request["format"],
                        "read_status": str(status), "payload": payload,
                        "raw_matrix": {"format": str(matrix.format_), "start": starts,
                                       "index": indexes, "value": values}})
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump({"highspy": "1.15.1", "reads": 24, "optimization_calls": 0,
                   "records": records}, stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
