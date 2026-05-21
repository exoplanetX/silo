from collections.abc import Iterable
from dataclasses import dataclass, field
from math import inf, isfinite

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable

GENERATED_ROW_PREFIX = "__mip_"


@dataclass(frozen=True)
class BranchingConstraint:
    variable_name: str
    sense: ConstraintSense
    rhs: float

    def __post_init__(self) -> None:
        if not self.variable_name:
            raise ValueError("Branching constraint variable name must not be empty.")
        object.__setattr__(self, "sense", ConstraintSense(self.sense))
        object.__setattr__(self, "rhs", float(self.rhs))


@dataclass(frozen=True)
class MIPRelaxation:
    model: Model
    bound_row_names: tuple[str, ...] = field(default_factory=tuple)
    branching_row_names: tuple[str, ...] = field(default_factory=tuple)


def build_lp_relaxation(
    model: Model,
    branching_constraints: Iterable[BranchingConstraint] = (),
) -> MIPRelaxation:
    model.validate()
    _validate_supported_objective(model)
    _validate_reserved_row_names(model)

    branch_constraints = tuple(branching_constraints)
    variable_types = {variable.name: variable.var_type for variable in model.variables}
    _validate_branching_constraints(branch_constraints, variable_types)

    relaxation = Model(name=f"{model.name}_lp_relaxation")
    bound_row_names: list[str] = []
    branching_row_names: list[str] = []

    for variable in model.variables:
        relaxation.add_variable(_relax_variable(variable))

    for constraint in model.constraints:
        relaxation.add_constraint(_copy_constraint(constraint))

    for variable in model.variables:
        row = _upper_bound_row(variable)
        if row is not None:
            relaxation.add_constraint(row)
            bound_row_names.append(row.name)

    for index, branch in enumerate(branch_constraints):
        row = _branching_row(index, branch)
        relaxation.add_constraint(row)
        branching_row_names.append(row.name)

    relaxation.set_objective(_copy_objective(model.objective))
    relaxation.validate()
    return MIPRelaxation(
        model=relaxation,
        bound_row_names=tuple(bound_row_names),
        branching_row_names=tuple(branching_row_names),
    )


def _validate_supported_objective(model: Model) -> None:
    if model.objective.sense != OptimizationSense.MAXIMIZE:
        raise ValueError("MIP relaxation supports maximization models only.")


def _validate_reserved_row_names(model: Model) -> None:
    for constraint in model.constraints:
        if constraint.name.startswith(GENERATED_ROW_PREFIX):
            raise ValueError(
                f"Constraint name uses reserved MIP relaxation prefix: {constraint.name}"
            )


def _validate_branching_constraints(
    branching_constraints: tuple[BranchingConstraint, ...],
    variable_types: dict[str, VariableType],
) -> None:
    for branch in branching_constraints:
        if branch.variable_name not in variable_types:
            raise ValueError(f"Unknown branching variable: {branch.variable_name}")
        if variable_types[branch.variable_name] == VariableType.CONTINUOUS:
            raise ValueError(
                f"Branching constraints require integer or binary variables: {branch.variable_name}"
            )
        if branch.sense not in (ConstraintSense.LE, ConstraintSense.GE):
            raise ValueError("Branching constraints must use <= or >= senses.")


def _relax_variable(variable: Variable) -> Variable:
    _validate_variable_bounds(variable)
    return Variable(name=variable.name, bounds=Bounds(lower=0.0, upper=inf))


def _validate_variable_bounds(variable: Variable) -> None:
    if variable.bounds.lower != 0.0:
        raise ValueError(
            f"MIP relaxation requires lower bound 0 for variable {variable.name}."
        )

    if variable.var_type == VariableType.CONTINUOUS:
        if isfinite(variable.bounds.upper):
            raise ValueError(
                f"MIP relaxation does not support finite upper bounds on continuous "
                f"variable {variable.name}."
            )
        return

    if variable.var_type == VariableType.BINARY:
        if variable.bounds.upper != 1.0:
            raise ValueError(
                f"MIP relaxation requires binary variable bounds [0, 1]: {variable.name}"
            )
        return

    if variable.var_type == VariableType.INTEGER:
        if not isfinite(variable.bounds.upper):
            raise ValueError(
                f"MIP relaxation requires a finite upper bound for integer variable "
                f"{variable.name}."
            )
        return

    raise ValueError(f"Unsupported variable type for MIP relaxation: {variable.var_type}")


def _upper_bound_row(variable: Variable) -> Constraint | None:
    if variable.var_type == VariableType.CONTINUOUS:
        return None
    return Constraint(
        name=_bound_row_name(variable.name),
        coefficients={variable.name: 1.0},
        sense=ConstraintSense.LE,
        rhs=float(variable.bounds.upper),
    )


def _branching_row(index: int, branch: BranchingConstraint) -> Constraint:
    return Constraint(
        name=_branching_row_name(index, branch),
        coefficients={branch.variable_name: 1.0},
        sense=branch.sense,
        rhs=branch.rhs,
    )


def _copy_constraint(constraint: Constraint) -> Constraint:
    return Constraint(
        name=constraint.name,
        coefficients=dict(constraint.coefficients),
        sense=constraint.sense,
        rhs=constraint.rhs,
    )


def _copy_objective(objective: Objective) -> Objective:
    return Objective(
        coefficients=dict(objective.coefficients),
        sense=objective.sense,
        constant=objective.constant,
    )


def _bound_row_name(variable_name: str) -> str:
    return f"{GENERATED_ROW_PREFIX}bound_{variable_name}_upper"


def _branching_row_name(index: int, branch: BranchingConstraint) -> str:
    sense_label = "le" if branch.sense == ConstraintSense.LE else "ge"
    return f"{GENERATED_ROW_PREFIX}branch_{index}_{branch.variable_name}_{sense_label}"
