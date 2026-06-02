from __future__ import annotations

SCENARIO_COMPONENT_DELIMITER = "__s::"
NONANTICIPATIVITY_PREFIX = "na::"
NONANTICIPATIVITY_DELIMITER = "::"

__all__ = [
    "NONANTICIPATIVITY_DELIMITER",
    "NONANTICIPATIVITY_PREFIX",
    "SCENARIO_COMPONENT_DELIMITER",
    "nonanticipativity_constraint_name",
    "scenario_constraint_name",
    "scenario_variable_name",
]


def scenario_variable_name(base_name: str, scenario_id: str) -> str:
    """Return the deterministic variable name for a scenario-specific copy."""

    return _scenario_component_name(base_name, scenario_id)


def scenario_constraint_name(base_name: str, scenario_id: str) -> str:
    """Return the deterministic constraint name for a scenario-specific copy."""

    return _scenario_component_name(base_name, scenario_id)


def nonanticipativity_constraint_name(base_variable_name: str, scenario_id: str) -> str:
    """Return the deterministic nonanticipativity constraint name."""

    base = _normalize_unambiguous_name(
        base_variable_name,
        "base variable name",
        NONANTICIPATIVITY_DELIMITER,
    )
    scenario = _normalize_unambiguous_name(
        scenario_id,
        "scenario id",
        NONANTICIPATIVITY_DELIMITER,
    )
    return (
        f"{NONANTICIPATIVITY_PREFIX}"
        f"{base}{NONANTICIPATIVITY_DELIMITER}{scenario}"
    )


def _scenario_component_name(base_name: str, scenario_id: str) -> str:
    base = _normalize_unambiguous_name(
        base_name,
        "base name",
        SCENARIO_COMPONENT_DELIMITER,
    )
    scenario = _normalize_unambiguous_name(
        scenario_id,
        "scenario id",
        SCENARIO_COMPONENT_DELIMITER,
    )
    return f"{base}{SCENARIO_COMPONENT_DELIMITER}{scenario}"


def _normalize_unambiguous_name(value: str, label: str, forbidden_delimiter: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    if forbidden_delimiter in normalized:
        raise ValueError(
            f"{label} must not contain delimiter {forbidden_delimiter!r}."
        )
    return normalized
