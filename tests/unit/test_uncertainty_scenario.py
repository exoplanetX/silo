from dataclasses import FrozenInstanceError
from math import inf, nan
from pathlib import Path

import pytest

from silo.uncertainty import DEFAULT_PROBABILITY_TOLERANCE, Scenario, ScenarioSet


def test_scenario_construction_normalizes_values_and_copies_inputs() -> None:
    objective_coefficients = {" y ": 2, "x": 1.5}
    rhs_values = {" demand ": 10}
    constraint_coefficients = {" capacity ": {"z": 3, " a ": 1.0}}
    parameters = {" price ": 4}
    metadata = {" z ": 2, "a": "alpha"}

    scenario = Scenario(
        " high ",
        probability=0.25,
        objective_coefficients=objective_coefficients,
        rhs_values=rhs_values,
        constraint_coefficients=constraint_coefficients,
        parameters=parameters,
        metadata=metadata,
        message="high demand",
    )
    objective_coefficients["x"] = 99.0
    rhs_values["demand"] = 99.0
    constraint_coefficients[" capacity "][" a "] = 99.0
    parameters[" price "] = 99.0
    metadata[" z "] = 99

    assert scenario.name == "high"
    assert scenario.scenario_id == "high"
    assert scenario.probability == 0.25
    assert scenario.objective_coefficients == (("x", 1.5), ("y", 2.0))
    assert scenario.rhs_values == (("demand", 10.0),)
    assert scenario.constraint_coefficients == (
        ("capacity", (("a", 1.0), ("z", 3.0))),
    )
    assert scenario.parameters == (("price", 4.0),)
    assert scenario.metadata == (("a", "alpha"), ("z", 2))
    assert scenario.message == "high demand"


def test_scenario_is_immutable() -> None:
    scenario = Scenario("base")

    with pytest.raises(FrozenInstanceError):
        scenario.probability = 0.5


@pytest.mark.parametrize("scenario_id", ["", " "])
def test_rejects_invalid_scenario_ids(scenario_id: str) -> None:
    with pytest.raises(ValueError, match="scenario id"):
        Scenario(scenario_id)


def test_rejects_nonstring_scenario_ids() -> None:
    with pytest.raises(TypeError, match="scenario id"):
        Scenario(123)


@pytest.mark.parametrize("probability", [inf, -inf, nan])
def test_rejects_nonfinite_probabilities(probability: float) -> None:
    with pytest.raises(ValueError, match="probability"):
        Scenario("bad", probability=probability)


def test_rejects_negative_probabilities() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        Scenario("bad", probability=-0.1)


def test_individual_scenario_accepts_zero_probability() -> None:
    scenario = Scenario("zero", probability=0.0)

    assert scenario.probability == 0.0


def test_scenario_collection_rejects_zero_total_probability() -> None:
    with pytest.raises(ValueError, match="probability total"):
        ScenarioSet((Scenario("zero", probability=0.0),))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"objective_coefficients": {"": 1.0}},
        {"objective_coefficients": {"x": inf}},
        {"rhs_values": {"": 1.0}},
        {"rhs_values": {"row": nan}},
        {"constraint_coefficients": {"": {"x": 1.0}}},
        {"constraint_coefficients": {"row": {"": 1.0}}},
        {"constraint_coefficients": {"row": {"x": -inf}}},
        {"parameters": {"": 1.0}},
        {"parameters": {"theta": inf}},
    ],
)
def test_rejects_invalid_scenario_override_data(kwargs: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        Scenario("bad", **kwargs)


def test_rejects_invalid_metadata_keys_and_values() -> None:
    with pytest.raises(ValueError, match="metadata key"):
        Scenario("bad", metadata={"": 1})

    with pytest.raises(ValueError, match="metadata float"):
        Scenario("bad", metadata={"value": inf})

    with pytest.raises(TypeError, match="metadata values"):
        Scenario("bad", metadata={"value": object()})


def test_rejects_invalid_message_values() -> None:
    with pytest.raises(TypeError, match="message"):
        Scenario("bad", message=object())


def test_scenario_set_orders_scenarios_deterministically() -> None:
    scenario_set = ScenarioSet(
        (
            Scenario("high", probability=0.3),
            Scenario("low", probability=0.7),
        )
    )

    assert scenario_set.scenario_ids == ("high", "low")
    assert scenario_set.probability_total == pytest.approx(1.0)
    assert scenario_set.probability_tolerance == DEFAULT_PROBABILITY_TOLERANCE


def test_scenario_set_rejects_duplicate_ids_after_normalization() -> None:
    with pytest.raises(ValueError, match="unique"):
        ScenarioSet((Scenario("base", 0.5), Scenario(" base ", 0.5)))


def test_scenario_set_rejects_probability_sums_outside_tolerance() -> None:
    with pytest.raises(ValueError, match="sum to one"):
        ScenarioSet((Scenario("a", 0.5), Scenario("b", 0.4)))


def test_scenario_set_accepts_probability_sums_within_tolerance() -> None:
    scenario_set = ScenarioSet(
        (
            Scenario("a", 0.5),
            Scenario("b", 0.5 + (DEFAULT_PROBABILITY_TOLERANCE / 2.0)),
        )
    )

    assert scenario_set.scenario_ids == ("a", "b")


@pytest.mark.parametrize("probability_tolerance", [0.0, -1.0, inf, nan])
def test_scenario_set_rejects_invalid_probability_tolerances(
    probability_tolerance: float,
) -> None:
    with pytest.raises(ValueError, match="probability tolerance"):
        ScenarioSet((Scenario("base"),), probability_tolerance=probability_tolerance)


def test_scenario_set_rejects_boolean_probability_tolerance() -> None:
    with pytest.raises(TypeError, match="probability tolerance"):
        ScenarioSet((Scenario("base"),), probability_tolerance=True)


def test_scenario_set_rejects_invalid_scenario_sequences() -> None:
    with pytest.raises(TypeError, match="sequence"):
        ScenarioSet(Scenario("base"))

    with pytest.raises(TypeError, match="Scenario records"):
        ScenarioSet(("base",))

    with pytest.raises(ValueError, match="at least one"):
        ScenarioSet(())


def test_public_uncertainty_exports_are_available() -> None:
    scenario = Scenario("base")
    scenario_set = ScenarioSet((scenario,))

    assert Scenario
    assert ScenarioSet
    assert DEFAULT_PROBABILITY_TOLERANCE == 1e-9
    assert scenario_set.scenarios == (scenario,)


def test_lower_layers_still_do_not_import_uncertainty() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    lower_layer_packages = (
        "core",
        "modeling",
        "presolve",
        "lp",
        "mip",
        "cuts",
        "decomposition",
    )

    for package in lower_layer_packages:
        for path in (repo_root / "src" / "silo" / package).rglob("*.py"):
            text = path.read_text(encoding="utf-8")

            assert "silo.uncertainty" not in text
            assert "from silo import uncertainty" not in text
