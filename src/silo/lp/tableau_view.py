"""Exact unscaled tableau proof view of a verified Phase-II numeric basis.

The original model and effective valid box rebuild the equations with Fraction;
the numeric QR tableau or scaled integer columns are never fraction-rounded.
"""

from dataclasses import dataclass
from fractions import Fraction as F
from math import inf

from silo.utils.rational import ProofBudget, exact_solve


@dataclass(frozen=True)
class AffineCoordinate:
    key: tuple
    constant: F
    coefficients: tuple[F, ...]
    integer: bool


@dataclass(frozen=True)
class GmiTableauRow:
    basic_key: tuple
    rhs: F
    coefficients: tuple[F, ...]
    coordinates: tuple[AffineCoordinate | None, ...]
    basic_integer: bool
    provenance: tuple
    basis_keys: tuple = ()
    effective_box: tuple = ()


def _exact_standard_data(norm, native, original_integer, budget=None):
    budget = ProofBudget() if budget is None else budget
    d = norm.data
    names, n = {name: i for i, name in enumerate(d.names)}, len(d.names)
    rows = {name: i for i, name in enumerate(d.row_names)}
    norm_keys = {key: i for i, key in enumerate(norm.row_keys)}
    offset = list(map(lambda v: F(float(v)), norm.offset))
    coefficients, bounds, senses, flips = [], [], [], []
    for key in native.row_keys:
        budget.charge()
        kind, name, side = key
        ni = norm_keys[key]
        if kind == "bound":
            i = names[name]
            a = [F(int(j == i)) for j in range(n)]
            bound = F(float(norm.upper[i]))
        else:
            i = rows[name]
            a = [F(float(v)) for v in d.a[i]]
            bound = F(float(d.row_upper[i] if side == "upper" else d.row_lower[i]))
        flip = -1 if norm.rhs[ni] < 0 else 1
        coefficients.append(a)
        bounds.append(bound)
        senses.append(1 if side == "upper" else -1 if side == "lower" else 0)
        flips.append(flip)
    column_count = len(native.column_keys)
    matrix = [[F(0)] * column_count for _ in bounds]
    rhs = [
        flip * (bound - sum(a * o for a, o in zip(row, offset, strict=True)))
        for row, bound, flip in zip(coefficients, bounds, flips, strict=True)
    ]
    coordinates, integer_tags = [], []
    for j, key in enumerate(native.column_keys):
        budget.charge()
        if key[0] == "variable":
            _, name, direction = key
            i = names[name]
            for r, row in enumerate(coefficients):
                matrix[r][j] = flips[r] * row[i] * direction
            integer = bool(original_integer[i] and offset[i].denominator == 1)
            expr = [F(0)] * n
            expr[i] = F(direction)
            unique = sum(v[0] == i for v in norm.column_origins) == 1
            coordinates.append(
                AffineCoordinate(key, -offset[i] * direction, tuple(expr), integer)
                if unique
                else None
            )
            integer_tags.append(integer)
        else:
            source = key[1]
            if source not in native.row_keys:
                coordinates.append(None)
                integer_tags.append(False)
                continue
            r = native.row_keys.index(source)
            if key[0] == "artificial":
                matrix[r][j] = F(1)
                coordinates.append(None)
                integer_tags.append(False)
                continue
            sign = senses[r]
            matrix[r][j] = flips[r] * sign
            expr = tuple(-sign * a for a in coefficients[r])
            constant = sign * bounds[r]
            integer = constant.denominator == 1 and all(
                not a or (original_integer[i] and a.denominator == 1) for i, a in enumerate(expr)
            )
            coordinates.append(AffineCoordinate(key, constant, expr, integer))
            integer_tags.append(integer)
    return matrix, rhs, coordinates, integer_tags, flips


def exact_tableau_rows(
    norm,
    native,
    original_integer,
    row_limit=3,
    basis_limit=80,
    operation_limit=2000000,
    deadline=inf,
    budget=None,
):
    if len(original_integer) != len(norm.data.names):
        return ()
    if native.status != "optimal" or native.matrix is None or len(native.basis) > basis_limit:
        return ()
    if any(k[0] == "artificial" for k in native.column_keys):
        return ()
    try:
        budget = ProofBudget(operation_limit, deadline) if budget is None else budget
        matrix, rhs, coordinates, integer_tags, _ = _exact_standard_data(
            norm, native, original_integer, budget
        )
        column_count = len(native.column_keys)
        basis = list(native.basis)
        basic_matrix = [[row[j] for j in basis] for row in matrix]
        basic_values = exact_solve(basic_matrix, rhs, budget=budget)
        if any(v < 0 for v in basic_values):
            return ()
        nonbasic = [j for j in range(column_count) if j not in set(basis)]
        answer = []
        for r, j in enumerate(basis):
            if not integer_tags[j] or basic_values[r].denominator == 1:
                continue
            unit = [F(int(i == r)) for i in range(len(basis))]
            weights = exact_solve(
                list(map(list, zip(*basic_matrix, strict=True))), unit, budget=budget
            )
            abar = tuple(sum(w * matrix[i][col] for i, w in enumerate(weights)) for col in nonbasic)
            answer.append(
                GmiTableauRow(
                    native.column_keys[j],
                    basic_values[r],
                    abar,
                    tuple(coordinates[col] for col in nonbasic),
                    True,
                    (
                        "original_binary_equations",
                        "unscaled_integer_lattice",
                        "effective_node_box",
                        tuple(native.row_keys),
                    ),
                    tuple(native.column_keys[j] for j in native.basis),
                    tuple(
                        (name, str(lo), str(hi))
                        for name, lo, hi in zip(
                            norm.data.names, norm.lower, norm.upper, strict=True
                        )
                    ),
                )
            )
            if len(answer) >= row_limit:
                break
        return tuple(answer)
    except (ValueError, OverflowError, ZeroDivisionError):
        return ()


def exact_basis_farkas(
    norm, native, activity, basis_limit=160, operation_limit=2000000, deadline=inf
):
    """Recover an exact witness when small-denominator dual guessing fails."""
    from silo.lp.verification import exact_farkas

    if native.matrix is None or len(native.basis) > basis_limit:
        return None
    d, keys = norm.data, native.column_keys
    try:
        budget = ProofBudget(operation_limit, deadline)
        matrix, rhs, _, _, flips = _exact_standard_data(
            norm, native, [False] * len(d.names), budget
        )
        basis = list(native.basis)
        basic = [[row[j] for j in basis] for row in matrix]
        basic_rhs = [F(0)] * len(basis)
        if any(k[0] == "artificial" for k in keys):
            for r, j in enumerate(basis):
                if keys[j][0] == "artificial":
                    source = norm.row_keys.index(keys[j][1])
                    basic_rhs[r] = -F(float(norm.row_scale[source]))
        else:
            values = exact_solve(basic, rhs, budget=budget)
            negative = next((i for i, v in enumerate(values) if v < 0), None)
            if negative is None:
                return None
            basic_rhs[negative] = F(1)
        weights = exact_solve(list(map(list, zip(*basic, strict=True))), basic_rhs, budget=budget)
        yl, yu = [F(0)] * len(d.row_names), [F(0)] * len(d.row_names)
        zl, zu = [F(0)] * len(d.names), [F(0)] * len(d.names)
        for r, key in enumerate(native.row_keys):
            origin = norm.origins[norm.row_keys.index(key)]
            kind, i, side = origin
            lam = flips[r] * weights[r]
            if kind == "bound":
                zu[i] += lam
            elif side == "lower":
                yl[i] -= lam
            elif side == "upper":
                yu[i] += lam
            else:
                yl[i] += max(-lam, 0)
                yu[i] += max(lam, 0)
        for j, (i, _direction) in enumerate(norm.column_origins):
            value = sum(weights[r] * matrix[r][j] for r in range(len(rhs)))
            if norm.lower[i] != -float("inf"):
                zl[i] += value
            elif norm.upper[i] != float("inf"):
                zu[i] += value
        for i in range(len(d.names)):
            if norm.lower[i] == norm.upper[i]:
                value = sum(F(float(d.a[r, i])) * (yu[r] - yl[r]) for r in range(len(yl)))
                zl[i], zu[i] = max(value, 0), max(-value, 0)
        for entry in reversed(activity.history):
            target = zl if entry.side == "lower" else zu
            mu = target[entry.variable]
            target[entry.variable] = F(0)
            coefficient = abs(F(float(d.a[entry.row, entry.variable])))
            (yl if entry.row_side == "lower" else yu)[entry.row] += mu / coefficient
            for j, side, _weight in entry.others:
                (zl if side == "lower" else zu)[j] += (
                    mu * abs(F(float(d.a[entry.row, j]))) / coefficient
                )
        return exact_farkas(d, (yl, yu, zl, zu))
    except (ValueError, OverflowError, ZeroDivisionError):
        return None
