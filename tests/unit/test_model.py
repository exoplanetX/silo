import pytest

from silo.core.bounds import Bounds
from silo.core.model import Model
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
