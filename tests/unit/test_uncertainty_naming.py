from pathlib import Path

import pytest

import silo.uncertainty as uncertainty
from silo.uncertainty.naming import (
    NONANTICIPATIVITY_DELIMITER,
    NONANTICIPATIVITY_PREFIX,
    SCENARIO_COMPONENT_DELIMITER,
    nonanticipativity_constraint_name,
    scenario_constraint_name,
    scenario_variable_name,
)


def test_scenario_variable_name_uses_documented_convention() -> None:
    assert scenario_variable_name("x", "high") == "x__s::high"


def test_scenario_constraint_name_uses_documented_convention() -> None:
    assert scenario_constraint_name("capacity", "low") == "capacity__s::low"


def test_nonanticipativity_constraint_name_uses_documented_convention() -> None:
    assert nonanticipativity_constraint_name("x", "high") == "na::x::high"


def test_naming_helpers_trim_surrounding_whitespace() -> None:
    assert scenario_variable_name(" x ", " high ") == "x__s::high"
    assert scenario_constraint_name(" row ", " low ") == "row__s::low"
    assert nonanticipativity_constraint_name(" y ", " base ") == "na::y::base"


@pytest.mark.parametrize(
    "helper",
    [
        scenario_variable_name,
        scenario_constraint_name,
        nonanticipativity_constraint_name,
    ],
)
def test_naming_helpers_reject_nonstring_labels(helper: object) -> None:
    with pytest.raises(TypeError, match="must be a string"):
        helper(1, "base")

    with pytest.raises(TypeError, match="must be a string"):
        helper("x", object())


@pytest.mark.parametrize(
    "helper",
    [
        scenario_variable_name,
        scenario_constraint_name,
        nonanticipativity_constraint_name,
    ],
)
def test_naming_helpers_reject_empty_labels(helper: object) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        helper("", "base")

    with pytest.raises(ValueError, match="must not be empty"):
        helper("x", " ")


@pytest.mark.parametrize(
    "helper",
    [
        scenario_variable_name,
        scenario_constraint_name,
    ],
)
def test_scenario_component_helpers_reject_ambiguous_delimiter(
    helper: object,
) -> None:
    with pytest.raises(ValueError, match="delimiter"):
        helper(f"x{SCENARIO_COMPONENT_DELIMITER}copy", "base")

    with pytest.raises(ValueError, match="delimiter"):
        helper("x", f"base{SCENARIO_COMPONENT_DELIMITER}copy")


def test_nonanticipativity_helper_rejects_ambiguous_delimiter() -> None:
    with pytest.raises(ValueError, match="delimiter"):
        nonanticipativity_constraint_name(
            f"x{NONANTICIPATIVITY_DELIMITER}copy",
            "base",
        )

    with pytest.raises(ValueError, match="delimiter"):
        nonanticipativity_constraint_name(
            "x",
            f"base{NONANTICIPATIVITY_DELIMITER}copy",
        )


def test_naming_constants_are_explicit() -> None:
    assert SCENARIO_COMPONENT_DELIMITER == "__s::"
    assert NONANTICIPATIVITY_PREFIX == "na::"
    assert NONANTICIPATIVITY_DELIMITER == "::"


def test_uncertainty_package_exports_remain_finite_scenario_only() -> None:
    assert uncertainty.__all__ == [
        "DEFAULT_PROBABILITY_TOLERANCE",
        "Scenario",
        "ScenarioSet",
    ]
    assert not hasattr(uncertainty, "scenario_variable_name")
    assert not hasattr(uncertainty, "nonanticipativity_constraint_name")


def test_naming_module_has_no_solver_or_transformation_integration() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "uncertainty" / "naming.py").read_text(
        encoding="utf-8"
    )
    forbidden_patterns = (
        "silo.core",
        "silo.modeling",
        "silo.lp",
        "silo.mip",
        "silo.presolve",
        "silo.cuts",
        "silo.decomposition",
        "silo.interfaces",
        "build_deterministic_equivalent",
        "Model(",
        "LPSolver",
        "BranchAndBoundSolver",
        "Presolver",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source
