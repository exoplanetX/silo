from pathlib import Path

import silo.uncertainty as uncertainty
from silo.cli.main import build_parser
from silo.core.solution import Solution
from silo.uncertainty import Scenario, ScenarioSet


def test_uncertainty_package_exports_only_finite_scenario_boundary() -> None:
    assert uncertainty.__all__ == [
        "DEFAULT_PROBABILITY_TOLERANCE",
        "Scenario",
        "ScenarioSet",
    ]
    assert uncertainty.Scenario is Scenario
    assert uncertainty.ScenarioSet is ScenarioSet


def test_uncertainty_package_does_not_expose_transformation_placeholders() -> None:
    transformation_names = {
        "StochasticModel",
        "RobustModel",
        "UncertaintySet",
        "build_deterministic_equivalent",
    }

    assert transformation_names.isdisjoint(uncertainty.__all__)
    for name in transformation_names:
        assert not hasattr(uncertainty, name)


def test_uncertainty_records_can_be_imported_without_solver_layers() -> None:
    scenario_set = ScenarioSet((Scenario("base"),))

    assert scenario_set.scenario_ids == ("base",)


def test_public_solution_schema_has_no_uncertainty_run_fields() -> None:
    assert "scenarios" not in Solution.__dataclass_fields__
    assert "scenario_ids" not in Solution.__dataclass_fields__
    assert "deterministic_equivalent" not in Solution.__dataclass_fields__
    assert "uncertainty_metadata" not in Solution.__dataclass_fields__


def test_public_cli_has_no_uncertainty_command() -> None:
    parser = build_parser()
    command_action = next(action for action in parser._actions if action.dest == "command")

    assert "uncertainty" not in command_action.choices
    assert "stochastic" not in command_action.choices
    assert "robust" not in command_action.choices


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


def test_uncertainty_modules_do_not_import_solver_layers() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    uncertainty_dir = repo_root / "src" / "silo" / "uncertainty"
    forbidden_patterns = (
        "silo.lp",
        "silo.mip",
        "silo.presolve",
        "silo.cuts",
        "silo.decomposition",
        "silo.interfaces",
        "LPSolver",
        "BranchAndBoundSolver",
        "Presolver",
    )

    for path in uncertainty_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert pattern not in text
