"""The legacy JSON model schema and its general-bound extension."""

import json
from collections.abc import Mapping, Sequence
from math import inf, isfinite
from pathlib import Path
from typing import Any

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable


def read_json_model(path: str | Path) -> Model:
    """Read a model, rejecting nonstandard numbers and unrecognized metadata."""
    try:
        payload = json.loads(
            Path(path).read_text(encoding="utf-8"),
            parse_constant=_invalid_json_constant,
            object_pairs_hook=_unique_object,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid JSON model file: {path}") from exc
    return model_from_dict(payload)


def model_from_dict(payload: Mapping[str, Any]) -> Model:
    """Construct a model from JSON-compatible data without silently dropping fields.

    Explicit ``lower``/``upper`` sides take precedence over legacy ``sense``/``rhs``.
    An omitted or null interval side is unbounded; two null sides make a free
    row. All supplied fields are validated, including inactive legacy fields.
    Variable lower/upper nulls denote minus/plus infinity.
    """
    payload = _mapping(payload, "model")
    _known_keys(payload, {"name", "sense", "variables", "objective", "constraints"}, "model")
    name = payload.get("name", "model")
    if not isinstance(name, str) or not name:
        raise ValueError("Invalid model.name: expected nonempty string")
    model = Model(name=name)

    for item in _optional_sequence(payload, "variables"):
        variable_payload = _mapping(item, "variable")
        _known_keys(variable_payload, {"name", "lower", "upper", "type"}, "variable")
        model.add_variable(
            Variable(
                name=_required_string(variable_payload, "name", "variable"),
                bounds=Bounds(
                    lower=_bound(variable_payload.get("lower", 0.0), -inf, "variable.lower"),
                    upper=_bound(variable_payload.get("upper"), inf, "variable.upper"),
                ),
                var_type=_enum(
                    VariableType,
                    variable_payload.get("type", VariableType.CONTINUOUS.value),
                    "variable.type",
                ),
            )
        )

    objective = _mapping(payload.get("objective", {}), "objective")
    _known_keys(objective, {"coefficients", "constant"}, "objective")
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

    for item in _optional_sequence(payload, "constraints"):
        row = _mapping(item, "constraint")
        _known_keys(
            row, {"name", "coefficients", "sense", "rhs", "lower", "upper"}, "constraint"
        )
        name = _required_string(row, "name", "constraint")
        coefficients = _coefficients(row.get("coefficients", {}), "constraint.coefficients")
        sense = _enum(
            ConstraintSense, row.get("sense", ConstraintSense.LE.value), "constraint.sense"
        )
        rhs = _optional_float(row, "rhs", 0.0)
        if "lower" in row or "upper" in row:
            lower = _bound(row.get("lower"), -inf, "constraint.lower")
            upper = _bound(row.get("upper"), inf, "constraint.upper")
            constraint = Constraint(
                name, coefficients, sense, rhs, lower_bound=lower, upper_bound=upper
            )
        else:
            constraint = Constraint(
                name=name,
                coefficients=coefficients,
                sense=sense,
                rhs=rhs,
            )
        model.add_constraint(constraint)
    model.validate()
    return model


def model_to_dict(model: Model) -> dict[str, Any]:
    """Return standard-JSON-compatible data, preserving legacy row syntax where used."""
    model.validate()
    variables = [
        {
            "name": variable.name,
            "lower": _json_bound(variable.bounds.lower, -inf, "variable.lower"),
            "upper": _json_bound(variable.bounds.upper, inf, "variable.upper"),
            "type": variable.var_type.value,
        }
        for variable in model.variables
    ]
    constraints: list[dict[str, Any]] = []
    for constraint in model.constraints:
        row: dict[str, Any] = {
            "name": constraint.name,
            "coefficients": _coefficients(constraint.coefficients, "constraint.coefficients"),
        }
        if constraint.lower_bound is None and constraint.upper_bound is None:
            row.update(sense=constraint.sense.value, rhs=_float(constraint.rhs, "constraint.rhs"))
        else:
            lower, upper = constraint.row_bounds
            row.update(
                lower=_json_bound(lower, -inf, "constraint.lower"),
                upper=_json_bound(upper, inf, "constraint.upper"),
            )
        constraints.append(row)
    return {
        "name": model.name,
        "sense": model.objective.sense.value,
        "variables": variables,
        "objective": {
            "coefficients": _coefficients(model.objective.coefficients, "objective.coefficients"),
            "constant": _float(model.objective.constant, "objective.constant"),
        },
        "constraints": constraints,
    }


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Invalid {label}: expected object")
    return value


def _known_keys(payload: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = [str(key) for key in payload if key not in allowed]
    if unknown:
        raise ValueError(f"Invalid {label}: unknown field {unknown[0]}")


def _optional_sequence(payload: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = payload.get(key, [])
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise ValueError(f"Invalid {key}: expected list")
    return value


def _required_string(payload: Mapping[str, Any], key: str, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Invalid {label}.{key}: expected nonempty string")
    return value


def _optional_float(payload: Mapping[str, Any], key: str, default: float) -> float:
    return default if key not in payload else _float(payload[key], key)


def _float(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"Invalid {label}: expected number")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"Invalid {label}: expected finite number") from exc
    if not isfinite(result):
        raise ValueError(f"Invalid {label}: expected finite number")
    return result


def _bound(value: Any, missing: float, label: str) -> float:
    return missing if value is None else _float(value, label)


def _json_bound(value: float, missing: float, label: str) -> float | None:
    return None if value == missing else _float(value, label)


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
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {label}: {value}") from exc


def _invalid_json_constant(value: str) -> Any:
    raise ValueError(f"Nonstandard JSON number: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result
