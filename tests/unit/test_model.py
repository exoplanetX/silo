import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable


def test_add_variable() -> None:
    model = Model(name="test")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=0.0)))
    assert model.variable_names() == ["x"]


def test_duplicate_variable_raises() -> None:
    model = Model(name="test")
    model.add_variable(Variable(name="x"))
    with pytest.raises(ValueError, match="Duplicate variable name"):
        model.add_variable(Variable(name="x"))


def test_invalid_bounds_raises() -> None:
    with pytest.raises(ValueError, match="Invalid bounds"):
        Variable(name="x", bounds=Bounds(lower=2.0, upper=1.0))


def test_duplicate_constraint_raises() -> None:
    model = Model(name="test")
    model.add_constraint(Constraint(name="capacity"))
    with pytest.raises(ValueError, match="Duplicate constraint name"):
        model.add_constraint(Constraint(name="capacity"))


def test_validate_unknown_constraint_variable_raises() -> None:
    model = Model(name="test")
    model.add_variable(Variable(name="x"))
    model.add_constraint(Constraint(name="row", coefficients={"y": 1.0}))

    with pytest.raises(ValueError, match="Unknown variable in constraint row: y"):
        model.validate()


def test_validate_unknown_objective_variable_raises() -> None:
    model = Model(name="test")
    model.add_variable(Variable(name="x"))
    model.set_objective(Objective(coefficients={"y": 1.0}))

    with pytest.raises(ValueError, match="Unknown variable in objective: y"):
        model.validate()


def test_validate_binary_bounds_raises() -> None:
    model = Model(name="test")
    model.add_variable(
        Variable(
            name="z",
            bounds=Bounds(lower=0.0, upper=2.0),
            var_type=VariableType.BINARY,
        )
    )

    with pytest.raises(ValueError, match=r"Binary variable bounds must stay within \[0, 1\]"):
        model.validate()
