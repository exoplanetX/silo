from dataclasses import dataclass, field

from silo.core.constraint import Constraint
from silo.core.enums import OptimizationSense, VariableType
from silo.core.objective import Objective
from silo.core.variable import Variable


@dataclass
class Model:
    name: str = "model"
    variables: list[Variable] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    objective: Objective = field(default_factory=Objective)

    def add_variable(self, variable: Variable) -> None:
        if any(v.name == variable.name for v in self.variables):
            raise ValueError(f"Duplicate variable name: {variable.name}")
        self.variables.append(variable)

    def add_constraint(self, constraint: Constraint) -> None:
        if any(c.name == constraint.name for c in self.constraints):
            raise ValueError(f"Duplicate constraint name: {constraint.name}")
        self.constraints.append(constraint)

    def set_objective(self, objective: Objective) -> None:
        self.objective = objective

    def variable_names(self) -> list[str]:
        return [v.name for v in self.variables]

    def validate(self) -> None:
        variable_names = self.variable_names()
        variable_name_set = set(variable_names)
        if len(variable_names) != len(variable_name_set):
            duplicates = _duplicates(variable_names)
            raise ValueError(f"Duplicate variable name: {duplicates[0]}")

        constraint_names = [constraint.name for constraint in self.constraints]
        if len(constraint_names) != len(set(constraint_names)):
            duplicates = _duplicates(constraint_names)
            raise ValueError(f"Duplicate constraint name: {duplicates[0]}")

        for variable in self.variables:
            if not variable.name:
                raise ValueError("Variable name must not be empty.")
            variable.bounds.validate()
            if variable.var_type == VariableType.BINARY and (
                variable.bounds.lower < 0.0 or variable.bounds.upper > 1.0
            ):
                raise ValueError(
                    f"Binary variable bounds must stay within [0, 1]: {variable.name}"
                )
            if variable.var_type not in VariableType:
                raise ValueError(f"Invalid variable type for {variable.name}: {variable.var_type}")

        for constraint in self.constraints:
            if not constraint.name:
                raise ValueError("Constraint name must not be empty.")
            for variable_name in constraint.coefficients:
                if variable_name not in variable_name_set:
                    raise ValueError(
                        f"Unknown variable in constraint {constraint.name}: {variable_name}"
                    )

        for variable_name in self.objective.coefficients:
            if variable_name not in variable_name_set:
                raise ValueError(f"Unknown variable in objective: {variable_name}")

        if self.objective.sense not in OptimizationSense:
            raise ValueError(f"Invalid objective sense: {self.objective.sense}")


def _duplicates(names: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for name in names:
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    return duplicates
