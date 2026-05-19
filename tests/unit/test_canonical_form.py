from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
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
    assert canonical.objective_constant == 0.0
    assert canonical.constraint_matrix == ((1.0, 2.0),)
    assert canonical.rhs == (4.0,)
    assert canonical.objective_sense == OptimizationSense.MAXIMIZE


def test_to_canonical_form_includes_bounds_types_and_constant() -> None:
    model = Model(name="canonical")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=-1.0, upper=3.0)))
    model.add_variable(
        Variable(
            name="z",
            bounds=Bounds(lower=0.0, upper=1.0),
            var_type=VariableType.BINARY,
        )
    )
    model.add_constraint(
        Constraint(
            name="balance",
            coefficients={"x": 2.0},
            sense=ConstraintSense.EQ,
            rhs=2.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"z": 4.0},
            sense=OptimizationSense.MINIMIZE,
            constant=1.5,
        )
    )

    canonical = to_canonical_form(model)

    assert canonical.variable_names == ("x", "z")
    assert canonical.objective_coefficients == (0.0, 4.0)
    assert canonical.objective_constant == 1.5
    assert canonical.constraint_matrix == ((2.0, 0.0),)
    assert canonical.variable_lower_bounds == (-1.0, 0.0)
    assert canonical.variable_upper_bounds == (3.0, 1.0)
    assert canonical.variable_types == (VariableType.CONTINUOUS, VariableType.BINARY)
