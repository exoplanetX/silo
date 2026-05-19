from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable


def build_model() -> Model:
    model = Model(name="knapsack")
    for name in ("item_1", "item_2", "item_3"):
        model.add_variable(
            Variable(
                name=name,
                bounds=Bounds(lower=0.0, upper=1.0),
                var_type=VariableType.BINARY,
            )
        )
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"item_1": 1.0, "item_2": 2.0, "item_3": 3.0},
            sense=ConstraintSense.LE,
            rhs=5.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"item_1": 6.0, "item_2": 10.0, "item_3": 12.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )
    return model


if __name__ == "__main__":
    print(build_model())
