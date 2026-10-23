"""Frozen F3/F4 semantic-number regressions; exactly one public solve per run."""

import json
from decimal import Decimal
from math import inf, nextafter
from pathlib import Path
from sys import float_info
from time import perf_counter

import pytest

from silo import solve
from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.io import model_to_mps, parse_mps

_FROZEN = json.loads(
    (
        Path(__file__).resolve().parents[1] / "fixtures" / "prototype_revision_manifest.json"
    ).read_text(encoding="utf-8")
)["mps"]
_TOKENS = _FROZEN["equivalent_tokens"]
_INTEGER = _FROZEN["large_integer"]
_FIELDS = [*_FROZEN["fields"], "objective", "constant"]


@pytest.fixture(scope="module", autouse=True)
def accounting():
    start = perf_counter()
    counter = {"public_solve_calls": 0}
    yield counter
    print(
        f"\nR1_MPS_PUBLIC_SOLVE_CALLS={counter['public_solve_calls']} "
        f"R1_MPS_MODULE_SECONDS={perf_counter() - start:.9f}"
    )


def _text(field, token):
    objective = token if field == "objective" else "1"
    coefficient = token if field == "coefficient" else "1"
    rhs = token if field == "rhs" else "0"
    constant_rhs = token if field == "constant" else "0"
    bounds = {"lower": f" LI b x {token}\n PL b x\n", "upper": f" UI b x {token}\n"}.get(field, "")
    return (
        f"NAME numeric\nROWS\n N obj\n L r\nCOLUMNS\n"
        f" x obj {objective} r {coefficient}\nRHS\n rhs r {rhs} obj {constant_rhs}\n"
        + ("BOUNDS\n" + bounds if bounds else "")
        + "ENDATA\n"
    )


def _value(model, field):
    return {
        "coefficient": model.constraints[0].coefficients["x"],
        "rhs": model.constraints[0].row_bounds[1],
        "lower": model.variables[0].bounds.lower,
        "upper": model.variables[0].bounds.upper,
        "objective": model.objective.coefficients["x"],
        "constant": -model.objective.constant,
    }[field]


@pytest.mark.parametrize("field", _FIELDS)
@pytest.mark.parametrize("token", _TOKENS)
@pytest.mark.parametrize("sign", ["", "-"])
def test_frozen_equal_integer_spellings_keep_exact_value_before_native_conversion(
    field, token, sign
):
    model = parse_mps(_text(field, sign + token))
    value = _value(model, field)
    assert type(value) is int
    assert value == (-_INTEGER if sign else _INTEGER)
    assert Decimal(value) == Decimal(sign + token)
    assert _value(parse_mps(model_to_mps(model)), field) == value


def test_existing_public_input_conversion_rejects_unrepresentable_integer_lower(accounting):
    text = (
        "NAME lattice\nROWS\n N obj\nCOLUMNS\n x obj 1\n"
        f"BOUNDS\n LI bnd x {_INTEGER}.0\n PL bnd x\nENDATA\n"
    )
    model = parse_mps(text)
    assert model.variables[0].bounds.lower == _INTEGER
    accounting["public_solve_calls"] += 1
    start = perf_counter()
    result = solve(model)
    elapsed = perf_counter() - start
    print(f"\nR1_MPS_SINGLE_PUBLIC_SOLVE_SECONDS={elapsed:.9f}")
    assert result.status == "numerical_failure" and result.termination_reason == "input_conversion"
    assert not result.has_primal_solution


def _ranged(kind, rhs, width):
    return (
        f"NAME ranged\nROWS\n N obj\n {kind} r\nCOLUMNS\n x obj 1 r 1\n"
        f"RHS\n rhs r {rhs}\nRANGES\n rng r {width}\nENDATA\n"
    )


@pytest.mark.parametrize("kind", ["L", "G", "E"])
@pytest.mark.parametrize("sign", [-1, 1])
@pytest.mark.parametrize("suffix", ["", ".0", ".000"])
def test_derived_range_integer_uses_mathematical_value_independent_of_rhs_exponent(
    kind, sign, suffix
):
    upper_anchored = kind == "L" or (kind == "E" and sign < 0)
    rhs = str(_INTEGER + 1 if upper_anchored else _INTEGER - 1) + suffix
    model = parse_mps(_ranged(kind, rhs, str(sign) + ".0"))
    side = model.constraints[0].row_bounds[0 if upper_anchored else 1]
    assert type(side) is int and side == _INTEGER


@pytest.mark.parametrize("kind", _FROZEN["range_underflow"]["row_types"])
@pytest.mark.parametrize("sign", _FROZEN["range_underflow"]["range_signs"])
def test_frozen_nonzero_derived_range_endpoint_underflow_rejected(kind, sign):
    case = _FROZEN["range_underflow"]
    positive_rhs = kind == "L" or (kind == "E" and sign < 0)
    rhs = ("" if positive_rhs else "-") + case["rhs_magnitude"]
    width = ("-" if sign < 0 else "") + case["width"]
    assert float(Decimal(rhs)) != 0 and float(Decimal(width)) != 0
    # The lost endpoint is exactly +/-1e-400; neither direct input underflows.
    assert Decimal(case["derived_magnitude"]) != 0
    assert float(Decimal(case["derived_magnitude"])) == 0
    text = _ranged(kind, rhs, width).replace("x obj 1 r 1\n", "x obj 1 r 1e-300\n")
    text = text.replace("ENDATA\n", "BOUNDS\n BV b x\nENDATA\n")
    with pytest.raises(ValueError, match="underflows"):
        parse_mps(text)


@pytest.mark.parametrize("field", _FIELDS)
@pytest.mark.parametrize("token", ["1e-400", "-1e-400", "1e309", "-1e309"])
def test_direct_nonzero_underflow_and_overflow_rejected_in_every_numeric_field(field, token):
    with pytest.raises(ValueError, match="underflows|finite numeric"):
        parse_mps(_text(field, token))


@pytest.mark.parametrize("width", ["1e-400", "-1e-400", "1e10000", "-1e10000"])
def test_direct_range_scale_rejected_before_derivation(width):
    with pytest.raises(ValueError, match="representable model-bound scale"):
        parse_mps(_ranged("L", "1", width))


@pytest.mark.parametrize("kind", ["L", "G", "E"])
@pytest.mark.parametrize("sign", [-1, 1])
def test_derived_range_endpoint_overflow_rejected(kind, sign):
    rhs = "-1e308" if kind == "L" or (kind == "E" and sign < 0) else "1e308"
    with pytest.raises(ValueError, match="finite number"):
        parse_mps(_ranged(kind, rhs, ("-" if sign < 0 else "") + "1e308"))


@pytest.mark.parametrize(
    "value", [1e308, -1e308, float_info.max, -float_info.max, 2**53 + 2.0, 1e20]
)
def test_writer_uses_actual_exact_integer_of_representable_large_float_in_all_fields(value):
    for field in _FIELDS:
        model = parse_mps(_text(field, str(int(value))))
        parsed = _value(model, field)
        assert type(parsed) is float and parsed == value
        text = model_to_mps(model)
        assert str(int(value)) in text or str(-int(value)) in text
        result = parse_mps(text)
        assert type(_value(result, field)) is float and _value(result, field) == value


@pytest.mark.parametrize(
    "lower,upper",
    [
        (-1e308, 1e308),
        (-float_info.max, float_info.max),
        (nextafter(1e308, 0), 1e308),
        (-0.1, 0.2),
        (1e-300, 1e308),
        (-5e-324, 5e-324),
        (0, 5e-324),
        (5e-324, 1e308),
    ],
)
def test_ranged_float_roundtrip_preserves_actual_large_and_subnormal_endpoints(lower, upper):
    original = Model(
        name="range_float",
        constraints=[
            Constraint("r", lower_bound=lower, upper_bound=upper),
        ],
    )
    text = model_to_mps(original)
    row = parse_mps(text).constraints[0]
    assert row.row_bounds == (lower, upper)
    assert model_to_mps(parse_mps(text)) == text


@pytest.mark.parametrize("token", ["0.1", "9007199254740993.5", "1e-300", "5e-324", "-5e-324"])
def test_ordinary_noninteger_decimals_retain_documented_float64_semantics(token):
    model = parse_mps(_text("coefficient", token))
    assert type(model.constraints[0].coefficients["x"]) is float
    assert model.constraints[0].coefficients["x"] == float(Decimal(token))


def test_writer_roundtrips_existing_float_bounds_objective_coefficients_and_constant():
    value = 1e308
    model = Model(
        name="large_float",
        variables=[Variable("x", Bounds(-value, value), VariableType.INTEGER)],
        constraints=[Constraint("r", {"x": value}, lower_bound=-value, upper_bound=value)],
        objective=Objective({"x": -value}, constant=value),
    )
    parsed = parse_mps(model_to_mps(model))
    assert parsed.variables[0].bounds == Bounds(-value, value)
    assert parsed.variables[0].var_type == VariableType.INTEGER
    assert parsed.objective == model.objective
    assert parsed.constraints[0].coefficients == {"x": value}
    assert parsed.constraints[0].row_bounds == (-value, value)
    assert type(parsed.variables[0].bounds.lower) is float
    assert type(parsed.objective.coefficients["x"]) is float
    assert parsed.variables[0].bounds.upper != inf
