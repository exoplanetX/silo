import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable


def read_json_model(path: str | Path) -> Model:
    payload = _read_payload(path)
    model = Model(name=str(payload.get("name", "model")))

    variables = _optional_sequence(payload, "variables")
    for item in variables:
        variable_payload = _mapping(item, "variable")
        upper = variable_payload.get("upper")
        model.add_variable(
            Variable(
                name=_required_string(variable_payload, "name", "variable"),
                bounds=Bounds(
                    lower=_optional_float(variable_payload, "lower", 0.0),
                    upper=float("inf") if upper is None else _float(upper, "variable.upper"),
                ),
                var_type=_enum(
                    VariableType,
                    variable_payload.get("type", VariableType.CONTINUOUS.value),
                    "variable.type",
                ),
            )
        )

    objective = _mapping(payload.get("objective", {}), "objective")
    model.set_objective(
        Objective(
            coefficients=_coefficients(objective.get("coefficients", {}), "objective.coefficients"),
            sense=_enum(
                OptimizationSense,
                payload.get("sense", OptimizationSense.MINIMIZE.value),
                "sense",
            ),
            constant=_optional_float(objective, "constant", 0.0),
        )
    )

    constraints = _optional_sequence(payload, "constraints")
    for item in constraints:
        constraint_payload = _mapping(item, "constraint")
        model.add_constraint(
            Constraint(
                name=_required_string(constraint_payload, "name", "constraint"),
                coefficients=_coefficients(
                    constraint_payload.get("coefficients", {}),
                    "constraint.coefficients",
                ),
                sense=_enum(
                    ConstraintSense,
                    constraint_payload.get("sense", ConstraintSense.LE.value),
                    "constraint.sense",
                ),
                rhs=_optional_float(constraint_payload, "rhs", 0.0),
            )
        )
    model.validate()
    return model


def _read_payload(path: str | Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON model file: {path}") from exc
    return _mapping(payload, "model")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Invalid {label}: expected object")
    return value


def _optional_sequence(payload: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = payload.get(key, [])
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError(f"Invalid {key}: expected list")
    return value


def _required_string(payload: Mapping[str, Any], key: str, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"Invalid {label}.{key}: expected string")
    return value


def _optional_float(payload: Mapping[str, Any], key: str, default: float) -> float:
    if key not in payload:
        return default
    return _float(payload[key], key)


def _float(value: Any, label: str) -> float:
    if not isinstance(value, int | float):
        raise ValueError(f"Invalid {label}: expected number")
    return float(value)


def _coefficients(value: Any, label: str) -> dict[str, float]:
    coefficient_payload = _mapping(value, label)
    coefficients: dict[str, float] = {}
    for name, coefficient in coefficient_payload.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"Invalid {label}: variable names must be nonempty strings")
        coefficients[name] = _float(coefficient, f"{label}.{name}")
    return coefficients


def _enum(enum_type: type[Any], value: Any, label: str) -> Any:
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {label}: {value}") from exc
