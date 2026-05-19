from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable


def build_model() -> Model:
    model = Model(name="diet")
    model.add_variable(Variable(name="bread"))
    model.add_variable(Variable(name="milk"))
    model.add_constraint(
        Constraint(
            name="calories",
            coefficients={"bread": 100.0, "milk": 150.0},
            sense=ConstraintSense.GE,
            rhs=500.0,
        )
    )
    model.set_objective(Objective(coefficients={"bread": 0.5, "milk": 0.8}))
    return model


if __name__ == "__main__":
    print(build_model())
