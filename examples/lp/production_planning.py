from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable


def build_model() -> Model:
    model = Model(name="production")
    model.add_variable(Variable(name="x1", bounds=Bounds(lower=0.0)))
    model.add_variable(Variable(name="x2", bounds=Bounds(lower=0.0)))

    model.add_constraint(
        Constraint(
            name="labor",
            coefficients={"x1": 1.0, "x2": 2.0},
            sense=ConstraintSense.LE,
            rhs=8.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="material",
            coefficients={"x1": 3.0, "x2": 2.0},
            sense=ConstraintSense.LE,
            rhs=12.0,
        )
    )

    model.set_objective(
        Objective(
            coefficients={"x1": 3.0, "x2": 5.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )
    return model


if __name__ == "__main__":
    m = build_model()
    print(m)
