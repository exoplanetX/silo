from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.modeling.canonical_form import to_canonical_form


def test_to_canonical_form_uses_model_order() -> None:
    model = Model(name="canonical")
    model.add_variable(Variable(name="x1"))
    model.add_variable(Variable(name="x2"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x2": 2.0, "x1": 1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x1": 3.0, "x2": 5.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )

    canonical = to_canonical_form(model)

    assert canonical.variable_names == ("x1", "x2")
    assert canonical.constraint_names == ("capacity",)
    assert canonical.objective_coefficients == (3.0, 5.0)
    assert canonical.constraint_matrix == ((1.0, 2.0),)
    assert canonical.rhs == (4.0,)
    assert canonical.objective_sense == OptimizationSense.MAXIMIZE
