from dataclasses import dataclass, field

from silo.core.constraint import Constraint
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
