"""Exact unscaled tableau proof view of a verified Phase-II numeric basis.

The original model and effective valid box rebuild the equations with Fraction;
the numeric QR tableau or scaled integer columns are never fraction-rounded.
"""

from dataclasses import dataclass
from fractions import Fraction as F
from math import inf

from silo.modeling.matrix_ops import row_support
from silo.utils.rational import ProofBudget, ProofLimitError, exact_solve


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


def exact_basis_candidates(result, budget, basis_limit=80):
    """Propose unscaled exact primal/row-dual candidates from the numeric basis.

    Reuses existing proof-equation reconstruction, not the floating tableau.
    It does not establish optimality, and never runs a second LP algorithm.
    """
    if result._lp is None:
        return None
    norm, native, _ = result._lp
    if native.status != "optimal" or native.matrix is None or len(native.basis) > basis_limit:
        return None
    if any(key[0] == "artificial" for key in native.column_keys):
        return None
    try:
        with budget.workspace(proof_workspace_cells(norm, native)):
            basis, rhs, _, _, flips = _exact_basis_data(norm, native, budget)
            basic = exact_solve(basis, rhs, budget=budget)
            point = {
                name: budget.guard(F(float(offset)))
                for name, offset in zip(norm.data.names, norm.offset, strict=True)
            }
            for column, value in zip(native.basis, basic, strict=True):
                budget.guard(value)
                key = native.column_keys[column]
                if key[0] == "variable":
                    _, name, direction = key
                    point[name] = budget.guard(point[name] + direction * value)
            names = {name: i for i, name in enumerate(norm.data.names)}
            costs = [
                budget.guard(F(float(norm.data.c[names[key[1]]])) * key[2] * norm.data.sign)
                if key[0] == "variable"
                else F(0)
                for key in (native.column_keys[j] for j in native.basis)
            ]
            multipliers = exact_solve(list(zip(*basis, strict=True)), costs, budget=budget)
            duals = dict.fromkeys(norm.data.row_names, F(0))
            for key, flip, value in zip(native.row_keys, flips, multipliers, strict=True):
                if key[0] == "row":
                    duals[key[1]] = budget.guard(duals[key[1]] + flip * value * norm.data.sign)
            return point, duals
    except ProofLimitError:
        raise
    except (ValueError, OverflowError, ZeroDivisionError):
        return None


def proof_workspace_cells(norm, native, full=False):
    """Dimension/nnz-only conservative count, before any Fraction container."""
    d = norm.data
    n, m, q, p = len(d.names), len(d.row_names), len(native.row_keys), len(native.column_keys)
    if full:
        return q * n + q * p + p * n + 4 * q * q + 8 * q + 4 * p + 3 * n + 3 * m
    rows = {name: i for i, name in enumerate(d.row_names)}
    count = sum(
        len(row_support(d.a, rows[key[1]])[0]) if key[0] == "row" else 1 for key in native.row_keys
    )
    return count + 4 * q * q + 8 * q + 3 * n + 3 * m


def _raw_equations(norm, native, budget):
    d = norm.data
    names = {name: i for i, name in enumerate(d.names)}
    rows = {name: i for i, name in enumerate(d.row_names)}
    positions = {key: i for i, key in enumerate(norm.row_keys)}
    coefficients, bounds, senses, flips = [], [], [], []
    offset = [budget.guard(F(float(value))) for value in norm.offset]
    for key in native.row_keys:
        budget.charge()
        kind, name, side = key
        if kind == "bound":
            i = names[name]
            row = {i: F(1)}
            bound = budget.guard(F(float(norm.upper[i])))
        else:
            i = rows[name]
            indices, values = row_support(d.a, i)
            row = {
                int(j): budget.guard(F(float(value)))
                for j, value in zip(indices, values, strict=True)
            }
            bound = budget.guard(F(float(d.row_upper[i] if side == "upper" else d.row_lower[i])))
        coefficients.append(row)
        bounds.append(bound)
        senses.append(1 if side == "upper" else -1 if side == "lower" else 0)
        flips.append(-1 if norm.rhs[positions[key]] < 0 else 1)
    rhs = [
        budget.guard(flip * (bound - sum((a * offset[j] for j, a in row.items()), F(0))))
        for row, bound, flip in zip(coefficients, bounds, flips, strict=True)
    ]
    return coefficients, bounds, senses, flips, rhs, offset


def _exact_basis_data(norm, native, budget):
    """Rebuild only selected original rows and B, without a q-by-p tableau."""
    coefficients, bounds, senses, flips, rhs, _ = _raw_equations(norm, native, budget)
    names = {name: i for i, name in enumerate(norm.data.names)}
    keys = [native.column_keys[j] for j in native.basis]
    if len(keys) != len(rhs):
        raise ValueError("Exact basis shape mismatch.")
    basis = []
    for r, row in enumerate(coefficients):
        values = []
        for key in keys:
            if key[0] == "variable":
                value = flips[r] * row.get(names[key[1]], F(0)) * key[2]
            elif key[1] != native.row_keys[r]:
                value = F(0)
            else:
                value = F(1) if key[0] == "artificial" else F(flips[r] * senses[r])
            values.append(budget.guard(value))
        basis.append(values)
    return basis, rhs, coefficients, bounds, flips


def _exact_standard_data(norm, native, original_integer, budget=None):
    """Bounded full GMI workspace; its caller owns the live reservation."""
    budget = ProofBudget() if budget is None else budget
    d = norm.data
    names, n = {name: i for i, name in enumerate(d.names)}, len(d.names)
    assert budget.live_cells >= proof_workspace_cells(norm, native, full=True)
    coefficients, bounds, senses, flips, rhs, offset = _raw_equations(norm, native, budget)
    column_count = len(native.column_keys)
    matrix = [[F(0)] * column_count for _ in bounds]
    coordinates, integer_tags = [], []
    for j, key in enumerate(native.column_keys):
        budget.charge()
        if key[0] == "variable":
            _, name, direction = key
            i = names[name]
            for r, row in enumerate(coefficients):
                matrix[r][j] = flips[r] * row.get(i, F(0)) * direction
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
            expr = tuple(-sign * coefficients[r].get(i, F(0)) for i in range(n))
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
        with budget.workspace(proof_workspace_cells(norm, native, full=True)):
            return _tableau_rows_reserved(norm, native, original_integer, row_limit, budget)
    except (ValueError, OverflowError, ZeroDivisionError):
        return ()


def _tableau_rows_reserved(norm, native, original_integer, row_limit, budget):
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
        weights = exact_solve(list(map(list, zip(*basic_matrix, strict=True))), unit, budget=budget)
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
                    for name, lo, hi in zip(norm.data.names, norm.lower, norm.upper, strict=True)
                ),
            )
        )
        if len(answer) >= row_limit:
            break
    return tuple(answer)


def exact_basis_farkas(
    norm, native, activity, basis_limit=160, operation_limit=2000000, deadline=inf
):
    """Recover an exact witness when small-denominator dual guessing fails."""
    if native.matrix is None or len(native.basis) > basis_limit:
        return None
    try:
        budget = ProofBudget(operation_limit, deadline)
        with budget.workspace(proof_workspace_cells(norm, native)):
            return _basis_farkas_reserved(norm, native, activity, budget)
    except (ValueError, OverflowError, ZeroDivisionError):
        return None


def _basis_farkas_reserved(norm, native, activity, budget):
    from silo.lp.verification import exact_farkas

    d, keys = norm.data, native.column_keys
    basic, rhs, coefficients, _, flips = _exact_basis_data(norm, native, budget)
    basis = list(native.basis)
    basic_rhs = [F(0)] * len(basis)
    if any(k[0] == "artificial" for k in keys):
        for r, j in enumerate(basis):
            if keys[j][0] == "artificial":
                source = norm.row_keys.index(keys[j][1])
                basic_rhs[r] = -F(float(norm.row_scale[source]))
    else:
        values = exact_solve(basic, rhs, budget=budget)
        negative = next((i for i, value in enumerate(values) if value < 0), None)
        if negative is None:
            return None
        basic_rhs[negative] = F(1)
    weights = exact_solve(list(map(list, zip(*basic, strict=True))), basic_rhs, budget=budget)
    yl, yu = [F(0)] * len(d.row_names), [F(0)] * len(d.row_names)
    zl, zu = [F(0)] * len(d.names), [F(0)] * len(d.names)
    normal = [F(0)] * len(d.names)
    origins = dict(zip(norm.row_keys, norm.origins, strict=True))
    for r, key in enumerate(native.row_keys):
        kind, i, side = origins[key]
        lam = budget.guard(flips[r] * weights[r])
        if kind == "bound":
            zu[i] += lam
        elif side == "lower":
            yl[i] -= lam
        elif side == "upper":
            yu[i] += lam
        else:
            yl[i] += max(-lam, 0)
            yu[i] += max(lam, 0)
        for j, coefficient in coefficients[r].items():
            normal[j] = budget.guard(normal[j] + lam * coefficient)
    for i, direction in norm.column_origins:
        value = budget.guard(direction * normal[i])
        if norm.lower[i] != -inf:
            zl[i] += value
        elif norm.upper[i] != inf:
            zu[i] += value
    for i in range(len(d.names)):
        if norm.lower[i] == norm.upper[i]:
            zl[i], zu[i] = max(normal[i], 0), max(-normal[i], 0)
    del normal
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
