import json
from pathlib import Path
from typing import Any

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable


def read_json_model(path: str | Path) -> Model:
    payload: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    model = Model(name=payload.get("name", "model"))
    for item in payload.get("variables", []):
        upper = item.get("upper")
        model.add_variable(
            Variable(
                name=item["name"],
                bounds=Bounds(
                    lower=item.get("lower", 0.0),
                    upper=float("inf") if upper is None else upper,
                ),
                var_type=VariableType(item.get("type", VariableType.CONTINUOUS.value)),
            )
        )
    objective = payload.get("objective", {})
    model.set_objective(
        Objective(
            coefficients=objective.get("coefficients", {}),
            sense=OptimizationSense(payload.get("sense", OptimizationSense.MINIMIZE.value)),
            constant=objective.get("constant", 0.0),
        )
    )
    for item in payload.get("constraints", []):
        model.add_constraint(
            Constraint(
                name=item["name"],
                coefficients=item.get("coefficients", {}),
                sense=ConstraintSense(item.get("sense", ConstraintSense.LE.value)),
                rhs=item.get("rhs", 0.0),
            )
        )
    return model
