"""Test-only original-input specifications and independent reference calculations."""

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import isfinite

import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.variable import Variable

# All fixture numbers are integers or exact terminating decimal strings.
Number = int | str
Row = tuple[tuple[Number, ...], str, Number]
TOL = 1e-7


@dataclass(frozen=True)
class Case:
    name: str
    objective: tuple[Number, ...]
    rows: tuple[Row, ...]
    status: str
    value: Number | None = None
    constant: Number = 0
    upper: tuple[int, ...] | None = None


def make_model(case: Case) -> Model:
    names = [f"x{i}" for i in range(len(case.objective))]
    variables = [Variable(name) for name in names]
    if case.upper is not None:
        variables = [
            Variable(name, Bounds(0, upper), VariableType.INTEGER)
            for name, upper in zip(names, case.upper, strict=True)
        ]
    return Model(
        name=case.name,
        variables=variables,
        constraints=[
            Constraint(
                f"r{i}", dict(zip(names, map(float, coefficients), strict=True)),
                ConstraintSense(sense), float(rhs),
            )
            for i, (coefficients, sense, rhs) in enumerate(case.rows)
        ],
        objective=Objective(
            dict(zip(names, map(float, case.objective), strict=True)),
            OptimizationSense.MAXIMIZE, float(case.constant),
        ),
    )


def enumerate_integer_optimum(case: Case) -> tuple[str, Fraction | None]:
    """Exhaust the ORIGINAL finite domain, without SILO relaxation/branching code."""
    assert case.upper is not None
    best = None
    for point in product(*(range(upper + 1) for upper in case.upper)):
        feasible = True
        for coefficients, sense, rhs in case.rows:
            lhs = sum(Fraction(a) * x for a, x in zip(coefficients, point, strict=True))
            bound = Fraction(rhs)
            feasible &= {"<=": lhs <= bound, ">=": lhs >= bound, "=": lhs == bound}[sense]
        if feasible:
            value = Fraction(case.constant) + sum(
                Fraction(c) * x for c, x in zip(case.objective, point, strict=True)
            )
            best = value if best is None else max(best, value)
    return ("infeasible", None) if best is None else ("optimal", best)


def check_solution(case: Case, solution: Solution, status: str, value) -> None:
    """Check original coordinates/rows; do not reuse solver feasibility helpers."""
    assert solution.status.value == status
    if status != "optimal":
        assert solution.objective_value is None
        return
    names = [f"x{i}" for i in range(len(case.objective))]
    assert set(solution.primal_values) == set(names)
    point = [solution.primal_values[name] for name in names]
    assert all(isfinite(x) and x >= -TOL for x in point)
    if case.upper is not None:
        for x, upper in zip(point, case.upper, strict=True):
            assert x <= upper + TOL
            assert abs(x - round(x)) <= TOL
    for coefficients, sense, rhs in case.rows:
        lhs = sum(float(a) * x for a, x in zip(coefficients, point, strict=True))
        if sense == "<=":
            assert lhs <= float(rhs) + TOL
        elif sense == ">=":
            assert lhs >= float(rhs) - TOL
        else:
            assert abs(lhs - float(rhs)) <= TOL
    reconstructed = float(case.constant) + sum(
        float(c) * x for c, x in zip(case.objective, point, strict=True)
    )
    assert isfinite(solution.objective_value)
    assert solution.objective_value == pytest.approx(float(value), rel=0, abs=TOL)
    assert reconstructed == pytest.approx(solution.objective_value, rel=0, abs=TOL)


LP_CASES = (
    # Intersection x+y=4, 2x+y=5 gives (1,3), value 9.
    Case("intersection", (3, 2), (((1, 1), "<=", 4), ((2, 1), "<=", 5)), "optimal", 9),
    Case("equality", (1, 2), (((1, 1), "=", 3),), "optimal", 6),
    Case("negative-rhs", (1,), (((-1,), ">=", -3), ((-1,), "<=", -1)), "optimal", 3),
    Case("phase-one", (-1, -2), (((1, 1), ">=", 2),), "optimal", -2),
    Case("redundancy", (1, 1), (((1, 1), "<=", 2), ((2, 2), "<=", 4),
                               ((1, 0), "<=", 2)), "optimal", 2),
    Case("degenerate-origin", (-1, -1), (((1, 1), "<=", 0),), "optimal", 0),
    Case("constant", (2,), (((1,), "<=", 3),), "optimal", 13, constant=7),
    Case("zero-objective", (0,), (((1,), ">=", 2),), "optimal", 7, constant=7),
    Case("rowless-bounded-objective", (-1,), (), "optimal", 4, constant=4),
    Case("conflicting-rows", (1,), (((1,), "<=", 0), ((1,), ">=", 1)), "infeasible"),
    Case("empty-row-infeasible", (1,), (((0,), "=", 1),), "infeasible"),
    Case("rowless-unbounded", (1,), (), "unbounded"),
    Case("coupled-ray", (1, 1), (((1, -1), "=", 0),), "unbounded"),
    Case("empty-column-infeasible", (0, 1), (((1, 0), "<=", 0),
                                            ((1, 0), ">=", 1)), "infeasible"),
    Case("empty-column-feasible", (0, 1), (((1, 0), ">=", 1),), "unbounded"),
    Case("fractional-coefficients", ("0.5", "0.25"),
         ((("0.5", "0.25"), "<=", "1.25"), ((1, 0), "<=", 2)), "optimal", "1.25"),
    Case("fractional-negative-rhs", (-1,),
         ((("-0.5",), "<=", "-0.25"), ((1,), "<=", 2)), "optimal", "-0.5"),
)

MIP_CASES = (
    Case("knapsack", (3, 2), (((2, 1), "<=", 3),), "optimal", 5, upper=(1, 1)),
    Case("fractional-root", (1, 1), (((2, 2), "<=", 3),), "optimal", 1, upper=(2, 2)),
    Case("parity-infeasible", (1, 1), (((2, 2), "=", 3),), "infeasible", upper=(2, 2)),
    Case("integer-upper", (2, -1), (), "optimal", 6, upper=(3, 2)),
    Case("negative-rhs-integer", (1,), (((-1,), ">=", -2),), "optimal", 2, upper=(4,)),
    Case("general-equality", (3, 1), (((1, 1), "=", 3),), "optimal", 9, upper=(3, 3)),
    Case("minimum-cover", (-2, -1), (((2, 1), ">=", 3),), "optimal", -3, upper=(2, 2)),
    Case("integer-constant", (1,), (((2,), "<=", 3),), "optimal", 8,
         constant=7, upper=(3,)),
    Case("integer-zero", (0, 0), (((1, 1), ">=", 1),), "optimal", 5,
         constant=5, upper=(1, 1)),
    Case("three-variable", (4, 3, 2), (((3, 2, 1), "<=", 4),), "optimal", 6,
         upper=(1, 1, 1)),
)
