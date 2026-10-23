from math import inf

import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.io import model_to_mps, parse_mps, read_mps_model, write_mps_model


def _model_signature(model: Model):
    return (
        model.name,
        [(v.name, v.bounds, v.var_type) for v in model.variables],
        model.objective,
        [(r.name, r.coefficients, r.row_bounds) for r in model.constraints],
    )


@pytest.mark.parametrize("sense", [OptimizationSense.MINIMIZE, OptimizationSense.MAXIMIZE])
def test_mps_general_model_round_trip(sense, tmp_path) -> None:
    model = Model(name="general")
    for variable in [
        Variable("free", Bounds(-inf, inf)),
        Variable("upper", Bounds(-inf, -2)),
        Variable("fixed", Bounds(3, 3)),
        Variable("integer", Bounds(-4, inf), VariableType.INTEGER),
        Variable("integer_free", Bounds(-inf, inf), VariableType.INTEGER),
        Variable("integer_upper", Bounds(-inf, 8), VariableType.INTEGER),
        Variable("integer_fixed", Bounds(-2, -2), VariableType.INTEGER),
        Variable("binary", Bounds(0, 1), VariableType.BINARY),
        Variable("binary_fixed", Bounds(1, 1), VariableType.BINARY),
        Variable("binary_tight", Bounds(0.25, 0.75), VariableType.BINARY),
        Variable("isolated"),
    ]:
        model.add_variable(variable)
    model.set_objective(Objective({"free": 2, "integer": -1}, sense, 7.5))
    for constraint in [
        Constraint("range", {"free": 1, "integer": -2}, lower_bound=-1, upper_bound=4),
        Constraint("equal", {"upper": 1}, ConstraintSense.EQ, -2),
        Constraint("lower", {"fixed": 1}, ConstraintSense.GE, 2),
        Constraint("upper", {"binary": 1}, ConstraintSense.LE, 1),
        Constraint("free_row", {"isolated": 1}, lower_bound=-inf, upper_bound=inf),
        Constraint("__obj__", {"free": -1}, ConstraintSense.LE, 8),
        Constraint("empty", {}, ConstraintSense.LE, 5),
    ]:
        model.add_constraint(constraint)
    encoded = model_to_mps(model)
    assert "'INTORG'" in encoded and "'INTEND'" in encoded
    assert "PL BND1 integer" in encoded
    assert "RHS1 __obj__1 -7.5" in encoded
    assert _model_signature(parse_mps(encoded)) == _model_signature(model)
    assert model_to_mps(parse_mps(encoded)) == encoded
    path = tmp_path / "nested" / "model.mps"
    write_mps_model(model, path)
    assert _model_signature(read_mps_model(path)) == _model_signature(model)


@pytest.mark.parametrize(
    "kind,width,expected",
    [
        ("L", "3", (7, 10)), ("L", "-3", (7, 10)),
        ("G", "3", (10, 13)), ("G", "-3", (10, 13)),
        ("E", "3", (10, 13)), ("E", "-3", (7, 10)),
        ("E", "0", (10, 10)),
    ],
)
def test_mps_signed_ranges(kind, width, expected) -> None:
    text = (
        f"NAME ranges\nROWS\n N obj\n {kind} r\nCOLUMNS\n x obj 1 r 2\n"
        f"RHS\n rhs r 10\nRANGES\n rng r {width}\nENDATA\n"
    )
    assert parse_mps(text).constraints[0].row_bounds == expected


def test_mps_defaults_and_fortran_exponents() -> None:
    text = "NAME defaults\nROWS\n N obj\n G r\nCOLUMNS\n x obj 1D+0 r 2d0\nENDATA\n"
    model = parse_mps(text)
    assert model.variables[0].bounds == Bounds(0, inf)
    assert model.objective == Objective({"x": 1}, OptimizationSense.MINIMIZE, 0)
    assert model.constraints[0].row_bounds == (0, inf)
    assert model.constraints[0].coefficients == {"x": 2}


def test_mps_integer_markers_have_explicit_binary_range_default() -> None:
    text = (
        "NAME integer\nROWS\n N obj\nCOLUMNS\n m0 'MARKER' 'INTORG'\n"
        " x obj 1\n m1 'MARKER' 'INTEND'\nENDATA\n"
    )
    model = parse_mps(text)
    assert model.variables[0].var_type == VariableType.INTEGER
    assert model.variables[0].bounds == Bounds(0, 1)


@pytest.mark.parametrize(
    "records,expected,var_type",
    [
        (" LO b x -2\n UP b x 4\n", (-2, 4), VariableType.CONTINUOUS),
        (" FX b x 3\n", (3, 3), VariableType.CONTINUOUS),
        (" FR b x\n", (-inf, inf), VariableType.CONTINUOUS),
        (" MI b x\n UP b x -2\n", (-inf, -2), VariableType.CONTINUOUS),
        (" UP b x -2\n", (-inf, -2), VariableType.CONTINUOUS),
        (" LO b x 2\n PL b x\n", (2, inf), VariableType.CONTINUOUS),
        (" BV b x\n", (0, 1), VariableType.BINARY),
        (" LI b x -3\n UI b x 7\n", (-3, 7), VariableType.INTEGER),
        (" LI b x -3\n", (-3, inf), VariableType.INTEGER),
        (" UI b x 7\n", (0, 7), VariableType.INTEGER),
    ],
)
def test_mps_bound_types(records, expected, var_type) -> None:
    text = "NAME bounds\nROWS\n N obj\nCOLUMNS\n x obj 1\nBOUNDS\n" + records + "ENDATA\n"
    model = parse_mps(text)
    assert model.variables[0].bounds == Bounds(*expected)
    assert model.variables[0].var_type == var_type


def _base(extra: str = "") -> str:
    return "NAME bad\nROWS\n N obj\n L r\nCOLUMNS\n x obj 1 r 2\n" + extra + "ENDATA\n"


@pytest.mark.parametrize(
    "text,match",
    [
        (_base("RHS\n a r 1\n b obj 2\n"), "multiple RHS sets"),
        (_base("RANGES\n a r 1\n b r 2\n"), "multiple RANGES sets"),
        (_base("BOUNDS\n LO a x 0\n UP b x 1\n"), "multiple BOUNDS sets"),
        (_base("BOUNDS\n SC b x 2\n"), "unsupported bound type"),
        (_base("SOS\n"), "unsupported section"),
        (_base("QUADOBJ\n x x 2\n"), "unsupported section"),
        (_base("BOUNDS\n FR b x 0\n"), "malformed FR"),
        (_base("BOUNDS\n LO b unknown 0\n"), "unknown variable"),
        (_base("RHS\n rhs unknown 1\n"), "unknown row"),
        (_base("RHS\n rhs r nan\n"), "finite numeric"),
        (_base().replace("x obj 1 r 2", "x obj 1_000 r 2"), "finite numeric"),
        (_base().replace("x obj 1 r 2", "x obj 1e-10000 r 2"), "underflows"),
        (_base("BOUNDS\n UP b x inf\n"), "finite numeric"),
        (_base("RHS\n rhs r 1 extra\n"), "malformed RHS"),
        (_base("BOUNDS\n LO b x 1\n LI b x 2\n"), "duplicate bound side"),
        (_base(" x r 3\n"), "duplicate coefficient"),
        (_base("RANGES\n rng obj 2\n"), "free/objective row"),
        (_base("RANGES\n rng r 1e10000\n"), "representable model-bound scale"),
        (_base("RHS\n rhs r 1\nRHS\n"), "duplicate RHS"),
        (_base().removesuffix("ENDATA\n"), "missing ENDATA"),
        (_base() + " x r 1\n", "data after ENDATA"),
        (_base(" m0 'MARKER' 'INTORG'\n"), "matching INTEND"),
        (_base(" m0 'MARKER' 'INTEND'\n"), "unmatched INTORG/INTEND"),
        (_base("COLUMNS\n"), "duplicate COLUMNS"),
        (_base("OBJSENSE\n MAX\n"), "out-of-order"),
        ("NAME bad\nROWS\n L r\nCOLUMNS\nENDATA\n", "N objective"),
        (_base().replace("x obj 1 r 2", "x obj 1 r 2 extra"), "malformed COLUMNS"),
    ],
)
def test_mps_rejects_malformed_unknown_or_ambiguous_records(text, match) -> None:
    with pytest.raises(ValueError, match=match):
        parse_mps(text)


@pytest.mark.parametrize(
    "text",
    [
        "NAME fixed\nROWS\n N  OBJ\nCOLUMNS\nENDATA\n",
        _base().replace(" x obj 1 r 2", "    x         obj                  1"),
        _base("BOUNDS\n UP b         x                    2\n"),
        _base().replace(" x obj 1 r 2", "              obj                  1"),
        _base("    MARK0000  'MARKER'                 'INTORG'\n"),
    ],
)
def test_mps_rejects_fixed_column_layout_and_name_continuation(text) -> None:
    with pytest.raises(ValueError):
        parse_mps(text)


def test_mps_preserves_empty_model_and_nonobjective_free_rows() -> None:
    model = Model(name="empty")
    model.add_constraint(Constraint("free", lower_bound=-inf, upper_bound=inf))
    model.set_objective(Objective(constant=5))
    assert _model_signature(parse_mps(model_to_mps(model))) == _model_signature(model)


def test_mps_inline_sense_comments_and_objective_rhs() -> None:
    model = parse_mps(
        "* comment\nNAME max_constant\nOBJSENSE MAX\nROWS\n N obj\nCOLUMNS\n"
        " x obj 2\nRHS\n rhs obj 4\nENDATA\n* trailing comment\n"
    )
    assert model.objective == Objective({"x": 2}, OptimizationSense.MAXIMIZE, -4)


@pytest.mark.parametrize("name", ["has space", "quoted'name", "comment*name", ""])
def test_mps_writer_rejects_names_outside_token_profile(name) -> None:
    with pytest.raises(ValueError):
        model_to_mps(Model(name=name))


@pytest.mark.parametrize("lower,upper", [(-0.1, 0.2), (-1e-100, 1e100), (-1e308, 1e308)])
def test_mps_ranged_row_round_trip_preserves_float_endpoints(lower, upper) -> None:
    model = Model(name="decimal_range")
    model.add_constraint(Constraint("r", lower_bound=lower, upper_bound=upper))
    assert parse_mps(model_to_mps(model)).constraints[0].row_bounds == (lower, upper)
