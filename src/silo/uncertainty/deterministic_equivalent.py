from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

from silo.core.constraint import Constraint
from silo.core.enums import VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.uncertainty.naming import (
    NONANTICIPATIVITY_PREFIX,
    SCENARIO_COMPONENT_DELIMITER,
)
from silo.uncertainty.naming import (
    scenario_constraint_name as make_row_name,
)
from silo.uncertainty.scenario import (
    DEFAULT_PROBABILITY_TOLERANCE,
    MetadataItems,
    MetadataValue,
)
from silo.uncertainty.stochastic_model import StochasticModel

EXPECTED_VALUE_OBJECTIVE = "expected_value"
DEFAULT_DETERMINISTIC_EQUIVALENT_NAMING = (
    f"scenario_component={SCENARIO_COMPONENT_DELIMITER};"
    f"nonanticipativity={NONANTICIPATIVITY_PREFIX}"
    "{base_variable}::{scenario_id}"
)


@dataclass(frozen=True)
class DeterministicEquivalentDiagnostics:
    """Passive deterministic-equivalent diagnostics; it records dimensions only."""

    scenario_ids: Sequence[str]
    generated_variables: int = 0
    generated_constraints: int = 0
    nonanticipativity_constraints: int = 0
    objective_aggregation: str = EXPECTED_VALUE_OBJECTIVE
    probability_total: float = 1.0
    probability_tolerance: float = DEFAULT_PROBABILITY_TOLERANCE
    naming_convention: str = DEFAULT_DETERMINISTIC_EQUIVALENT_NAMING
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_ids", _normalize_scenario_ids(self.scenario_ids))
        object.__setattr__(
            self,
            "generated_variables",
            _normalize_nonnegative_count(
                self.generated_variables,
                "generated variable count",
            ),
        )
        object.__setattr__(
            self,
            "generated_constraints",
            _normalize_nonnegative_count(
                self.generated_constraints,
                "generated constraint count",
            ),
        )
        object.__setattr__(
            self,
            "nonanticipativity_constraints",
            _normalize_nonnegative_count(
                self.nonanticipativity_constraints,
                "nonanticipativity constraint count",
            ),
        )
        object.__setattr__(
            self,
            "objective_aggregation",
            _normalize_nonempty_text(
                self.objective_aggregation,
                "objective aggregation convention",
            ),
        )
        object.__setattr__(
            self,
            "probability_total",
            _normalize_positive_float(self.probability_total, "probability total"),
        )
        object.__setattr__(
            self,
            "probability_tolerance",
            _normalize_positive_float(
                self.probability_tolerance,
                "probability tolerance",
            ),
        )
        object.__setattr__(
            self,
            "naming_convention",
            _normalize_nonempty_text(self.naming_convention, "naming convention"),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def scenario_count(self) -> int:
        return len(self.scenario_ids)


@dataclass(frozen=True)
class DeterministicEquivalentResult:
    """Passive deterministic-equivalent result record."""

    model: Model
    diagnostics: DeterministicEquivalentDiagnostics
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.model, Model):
            raise TypeError("model must be a Model.")
        self.model.validate()
        if not isinstance(self.diagnostics, DeterministicEquivalentDiagnostics):
            raise TypeError("diagnostics must be DeterministicEquivalentDiagnostics.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


def build_deterministic_equivalent(
    model: StochasticModel,
) -> Model | DeterministicEquivalentResult:
    if not isinstance(model, StochasticModel):
        raise TypeError("model must be a StochasticModel.")
    if not _has_transformation_request(model):
        return model.base_model

    _validate_tiny_builder_scope(model)

    base_model = model.base_model
    declared_constraints = set(model.scenario_dependent_constraints)
    generated_constraint_names = _generated_constraint_names(model)
    shared_constraints = [
        _copy_constraint(constraint)
        for constraint in base_model.constraints
        if constraint.name not in declared_constraints
    ]
    scenario_constraints = _build_scenario_constraints(model, generated_constraint_names)
    result_model = Model(
        name=f"{base_model.name}_deterministic_equivalent",
        variables=[_copy_variable(variable) for variable in base_model.variables],
        constraints=[*shared_constraints, *scenario_constraints],
        objective=_build_expected_value_objective(model),
    )
    diagnostics = DeterministicEquivalentDiagnostics(
        scenario_ids=model.scenario_ids,
        generated_variables=0,
        generated_constraints=len(scenario_constraints),
        nonanticipativity_constraints=0,
        probability_total=model.scenarios.probability_total,
        probability_tolerance=model.scenarios.probability_tolerance,
        metadata={"builder": "tiny_objective_rhs"},
        message="Tiny objective/RHS deterministic-equivalent transformation.",
    )
    return DeterministicEquivalentResult(
        model=result_model,
        diagnostics=diagnostics,
        message="Tiny deterministic-equivalent result.",
    )


def _has_transformation_request(model: StochasticModel) -> bool:
    if model.scenario_dependent_variables or model.scenario_dependent_constraints:
        return True
    return any(
        scenario.objective_coefficients
        or scenario.rhs_values
        or scenario.constraint_coefficients
        for scenario in model.scenarios.scenarios
    )


def _validate_tiny_builder_scope(model: StochasticModel) -> None:
    if model.scenario_dependent_variables:
        raise ValueError("scenario-dependent variables are not supported yet.")
    for variable in model.base_model.variables:
        if variable.var_type != VariableType.CONTINUOUS:
            raise ValueError("deterministic equivalents currently support continuous LPs only.")

    variable_names = set(model.base_model.variable_names())
    constraint_names = {constraint.name for constraint in model.base_model.constraints}
    declared_constraints = set(model.scenario_dependent_constraints)

    for scenario in model.scenarios.scenarios:
        objective_overrides = dict(scenario.objective_coefficients)
        rhs_overrides = dict(scenario.rhs_values)
        if scenario.constraint_coefficients:
            raise ValueError("constraint coefficient overrides are not supported yet.")
        for variable_name in objective_overrides:
            if variable_name not in variable_names:
                raise ValueError(f"Unknown objective override variable: {variable_name}")
        for constraint_name in rhs_overrides:
            if constraint_name not in constraint_names:
                raise ValueError(f"Unknown RHS override constraint: {constraint_name}")
            if constraint_name not in declared_constraints:
                raise ValueError(
                    "RHS overrides must target declared scenario-dependent constraints: "
                    f"{constraint_name}"
                )


def _generated_constraint_names(model: StochasticModel) -> dict[tuple[str, str], str]:
    existing_shared_constraints = {
        constraint.name
        for constraint in model.base_model.constraints
        if constraint.name not in model.scenario_dependent_constraints
    }
    generated: dict[tuple[str, str], str] = {}
    seen: set[str] = set(existing_shared_constraints)
    for constraint_name in model.scenario_dependent_constraints:
        for scenario_id in model.scenario_ids:
            generated_name = make_row_name(constraint_name, scenario_id)
            if generated_name in seen:
                raise ValueError(f"Generated constraint name collides: {generated_name}")
            seen.add(generated_name)
            generated[(constraint_name, scenario_id)] = generated_name
    return generated


def _build_scenario_constraints(
    model: StochasticModel,
    generated_names: Mapping[tuple[str, str], str],
) -> list[Constraint]:
    base_constraints = {constraint.name: constraint for constraint in model.base_model.constraints}
    constraints: list[Constraint] = []
    for constraint_name in model.scenario_dependent_constraints:
        base_constraint = base_constraints[constraint_name]
        for scenario in model.scenarios.scenarios:
            rhs_overrides = dict(scenario.rhs_values)
            constraints.append(
                Constraint(
                    name=generated_names[(constraint_name, scenario.name)],
                    coefficients=dict(base_constraint.coefficients),
                    sense=base_constraint.sense,
                    rhs=rhs_overrides.get(constraint_name, base_constraint.rhs),
                )
            )
    return constraints


def _build_expected_value_objective(model: StochasticModel) -> Objective:
    base_coefficients = dict(model.base_model.objective.coefficients)
    coefficients: dict[str, float] = {}
    for variable_name in model.base_model.variable_names():
        expected_coefficient = 0.0
        base_coefficient = float(base_coefficients.get(variable_name, 0.0))
        for scenario in model.scenarios.scenarios:
            objective_overrides = dict(scenario.objective_coefficients)
            expected_coefficient += scenario.probability * float(
                objective_overrides.get(variable_name, base_coefficient)
            )
        if expected_coefficient != 0.0:
            coefficients[variable_name] = expected_coefficient
    return Objective(
        coefficients=coefficients,
        sense=model.base_model.objective.sense,
        constant=model.base_model.objective.constant,
    )


def _copy_variable(variable: Variable) -> Variable:
    return Variable(
        name=variable.name,
        bounds=variable.bounds,
        var_type=variable.var_type,
    )


def _copy_constraint(constraint: Constraint) -> Constraint:
    return Constraint(
        name=constraint.name,
        coefficients=dict(constraint.coefficients),
        sense=constraint.sense,
        rhs=constraint.rhs,
    )


def _normalize_scenario_ids(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("scenario ids must be a sequence of strings.")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        scenario_id = _normalize_nonempty_text(value, "scenario id")
        if scenario_id in seen:
            raise ValueError("scenario ids must be unique.")
        seen.add(scenario_id)
        normalized.append(scenario_id)
    if not normalized:
        raise ValueError("scenario ids must include at least one id.")
    return tuple(sorted(normalized))


def _normalize_nonnegative_count(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer.")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative.")
    return value


def _normalize_positive_float(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric.")
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    if numeric <= 0.0:
        raise ValueError(f"{label} must be positive.")
    return numeric


def _normalize_nonempty_text(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_metadata(values: Mapping[str, MetadataValue]) -> MetadataItems:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping.")

    normalized: list[tuple[str, MetadataValue]] = []
    for key, value in values.items():
        label = _normalize_nonempty_text(key, "metadata key")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("metadata float values must be finite.")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise TypeError("metadata values must be scalar strings, numbers, bools, or None.")
        normalized.append((label, value))
    return tuple(sorted(normalized))
