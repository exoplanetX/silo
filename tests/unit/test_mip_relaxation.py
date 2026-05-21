from math import inf

import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.lp.simplex.standard_form import build_standard_form
from silo.mip.relaxation import BranchingConstraint, build_lp_relaxation


def test_relaxes_binary_variables_with_explicit_upper_bound_rows() -> None:
    model = _binary_choice_model()

    relaxation = build_lp_relaxation(model)

    assert relaxation.model.name == "choice_lp_relaxation"
    assert [variable.name for variable in relaxation.model.variables] == ["x", "y"]
    assert [variable.var_type for variable in relaxation.model.variables] == [
        VariableType.CONTINUOUS,
        VariableType.CONTINUOUS,
    ]
    assert [variable.bounds.upper for variable in relaxation.model.variables] == [inf, inf]
    assert relaxation.bound_row_names == ("__mip_bound_x_upper", "__mip_bound_y_upper")
    assert relaxation.branching_row_names == ()
    assert [constraint.name for constraint in relaxation.model.constraints] == [
        "choice",
        "__mip_bound_x_upper",
        "__mip_bound_y_upper",
    ]
    assert relaxation.model.constraints[1].coefficients == {"x": 1.0}
    assert relaxation.model.constraints[1].sense == ConstraintSense.LE
    assert relaxation.model.constraints[1].rhs == 1.0
    assert relaxation.model.objective == model.objective


def test_relaxes_bounded_integer_variables_with_explicit_upper_bound_rows() -> None:
    model = _bounded_integer_model()

    relaxation = build_lp_relaxation(model)

    assert [variable.var_type for variable in relaxation.model.variables] == [
        VariableType.CONTINUOUS,
        VariableType.CONTINUOUS,
    ]
    assert relaxation.bound_row_names == ("__mip_bound_x_upper", "__mip_bound_y_upper")
    assert relaxation.model.constraints[1].rhs == 2.0
    assert relaxation.model.constraints[2].rhs == 3.0


def test_preserves_original_constraints_and_objective_without_mutating_model() -> None:
    model = _bounded_integer_model()
    original_variable_types = [variable.var_type for variable in model.variables]
    original_constraint_names = [constraint.name for constraint in model.constraints]

    relaxation = build_lp_relaxation(model)

    assert [variable.var_type for variable in model.variables] == original_variable_types
    assert [constraint.name for constraint in model.constraints] == original_constraint_names
    assert relaxation.model.constraints[0] == model.constraints[0]
    assert relaxation.model.constraints[0].coefficients is not model.constraints[0].coefficients
    assert relaxation.model.objective == model.objective
    assert relaxation.model.objective.coefficients is not model.objective.coefficients


def test_branching_constraints_are_appended_as_generated_rows() -> None:
    model = _bounded_integer_model()

    relaxation = build_lp_relaxation(
        model,
        branching_constraints=(
            BranchingConstraint("x", ConstraintSense.LE, 1.0),
            BranchingConstraint("y", ConstraintSense.GE, 2.0),
        ),
    )

    assert relaxation.branching_row_names == (
        "__mip_branch_0_x_le",
        "__mip_branch_1_y_ge",
    )
    assert [constraint.name for constraint in relaxation.model.constraints] == [
        "capacity",
        "__mip_bound_x_upper",
        "__mip_bound_y_upper",
        "__mip_branch_0_x_le",
        "__mip_branch_1_y_ge",
    ]
    assert relaxation.model.constraints[3] == Constraint(
        name="__mip_branch_0_x_le",
        coefficients={"x": 1.0},
        sense=ConstraintSense.LE,
        rhs=1.0,
    )
    assert relaxation.model.constraints[4] == Constraint(
        name="__mip_branch_1_y_ge",
        coefficients={"y": 1.0},
        sense=ConstraintSense.GE,
        rhs=2.0,
    )


def test_relaxation_can_be_passed_to_standard_form_builder() -> None:
    model = _binary_choice_model()

    relaxation = build_lp_relaxation(
        model,
        branching_constraints=(BranchingConstraint("x", ConstraintSense.LE, 0.0),),
    )
    standard_form = build_standard_form(relaxation.model)

    assert standard_form.row_names == (
        "choice",
        "__mip_bound_x_upper",
        "__mip_bound_y_upper",
        "__mip_branch_0_x_le",
    )
    assert standard_form.objective_coefficients[:2] == (1.0, 1.0)


def test_rejects_minimization_model() -> None:
    model = _binary_choice_model()
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MINIMIZE))

    with pytest.raises(ValueError, match="maximization"):
        build_lp_relaxation(model)


def test_rejects_nonzero_lower_bound() -> None:
    model = _bounded_integer_model()
    model.variables[0] = Variable(
        name="x",
        bounds=Bounds(lower=1.0, upper=2.0),
        var_type=VariableType.INTEGER,
    )

    with pytest.raises(ValueError, match="lower bound 0"):
        build_lp_relaxation(model)


def test_rejects_continuous_variable_with_finite_upper_bound() -> None:
    model = _binary_choice_model()
    model.add_variable(Variable(name="z", bounds=Bounds(lower=0.0, upper=4.0)))
    model.set_objective(
        Objective(
            coefficients={"x": 1.0, "y": 1.0, "z": 1.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )

    with pytest.raises(ValueError, match="finite upper bounds on continuous variable z"):
        build_lp_relaxation(model)


def test_rejects_binary_variable_without_full_binary_bounds() -> None:
    model = _binary_choice_model()
    model.variables[0] = Variable(
        name="x",
        bounds=Bounds(lower=0.0, upper=0.5),
        var_type=VariableType.BINARY,
    )

    with pytest.raises(ValueError, match=r"binary variable bounds \[0, 1\]"):
        build_lp_relaxation(model)


def test_rejects_unbounded_integer_variable() -> None:
    model = _bounded_integer_model()
    model.variables[0] = Variable(name="x", var_type=VariableType.INTEGER)

    with pytest.raises(ValueError, match="finite upper bound for integer variable x"):
        build_lp_relaxation(model)


def test_rejects_branching_on_unknown_variable() -> None:
    model = _bounded_integer_model()

    with pytest.raises(ValueError, match="Unknown branching variable: z"):
        build_lp_relaxation(
            model,
            branching_constraints=(BranchingConstraint("z", ConstraintSense.LE, 1.0),),
        )


def test_rejects_branching_on_continuous_variable() -> None:
    model = _bounded_integer_model()
    model.add_variable(Variable(name="z"))

    with pytest.raises(ValueError, match="integer or binary variables: z"):
        build_lp_relaxation(
            model,
            branching_constraints=(BranchingConstraint("z", ConstraintSense.LE, 1.0),),
        )


def test_rejects_invalid_branching_sense() -> None:
    model = _bounded_integer_model()

    with pytest.raises(ValueError, match="must use <= or >= senses"):
        build_lp_relaxation(
            model,
            branching_constraints=(BranchingConstraint("x", ConstraintSense.EQ, 1.0),),
        )


def test_rejects_reserved_generated_row_prefix() -> None:
    model = _binary_choice_model()
    model.add_constraint(
        Constraint(
            name="__mip_user_row",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )

    with pytest.raises(ValueError, match="reserved MIP relaxation prefix"):
        build_lp_relaxation(model)


def _binary_choice_model() -> Model:
    model = Model(name="choice")
    model.add_variable(
        Variable(
            name="x",
            bounds=Bounds(lower=0.0, upper=1.0),
            var_type=VariableType.BINARY,
        )
    )
    model.add_variable(
        Variable(
            name="y",
            bounds=Bounds(lower=0.0, upper=1.0),
            var_type=VariableType.BINARY,
        )
    )
    model.add_constraint(
        Constraint(
            name="choice",
            coefficients={"x": 1.0, "y": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 1.0, "y": 1.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _bounded_integer_model() -> Model:
    model = Model(name="bounded_integer")
    model.add_variable(
        Variable(
            name="x",
            bounds=Bounds(lower=0.0, upper=2.0),
            var_type=VariableType.INTEGER,
        )
    )
    model.add_variable(
        Variable(
            name="y",
            bounds=Bounds(lower=0.0, upper=3.0),
            var_type=VariableType.INTEGER,
        )
    )
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 2.0, "y": 1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 3.0, "y": 2.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model
