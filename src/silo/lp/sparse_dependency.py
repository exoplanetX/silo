"""Stream an exact row-dependency proof from a floating BTRAN proposal."""

from fractions import Fraction
from math import isfinite

import numpy as np

from silo.modeling.matrix_ops import row_support

DEPENDENCY_DENOMINATOR = 1_000_000


def prove_dependency(norm, matrix, basis, rows, keys, position, witness, budget):
    """Prove redundancy in current unscaled affine coordinates, never by tolerance.

    Only the rational row-weight vector and original-coordinate accumulator are
    retained. Existing proof operations, bit limit, deadline and65536-cell gate
    all apply before constructing Fraction containers. No matrix is densified.
    """
    q, n = len(rows), len(norm.data.names)
    if len(basis) != q or np.shape(witness) != (q,):
        return False
    target = basis[position]
    if keys[target][0] != "artificial":
        return False
    active = {key: i for i, key in enumerate(rows)}
    normalized = {key: i for i, key in enumerate(norm.row_keys)}
    physical = active[keys[target][1]]
    for column in basis:
        if keys[column][0] != "artificial":
            continue
        lo, hi = matrix.indptr[column : column + 2]
        if hi - lo != 1 or matrix.data[lo] != 1:
            return False
        if int(matrix.indices[lo]) != active[keys[column][1]]:
            return False
    scales = np.array([norm.row_scale[normalized[key]] for key in rows])
    if not np.isfinite(witness).all() or not np.isfinite(scales).all() or np.any(scales <= 0):
        return False
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        proposal = scales * witness
        denominator = float(proposal[physical])
        proposal = proposal / denominator
    if not isfinite(denominator) or denominator == 0 or not np.isfinite(proposal).all():
        return False
    names = {name: i for i, name in enumerate(norm.data.names)}
    raw_rows = {name: i for i, name in enumerate(norm.data.row_names)}
    with budget.workspace(2 * q + 2 * n + 32):
        weights = [
            budget.guard(Fraction(float(value)).limit_denominator(DEPENDENCY_DENOMINATOR))
            for value in proposal
        ]
        if weights[physical] != 1:
            return False
        for slot, column in enumerate(basis):
            budget.charge()
            if slot != position and keys[column][0] == "artificial":
                if weights[active[keys[column][1]]]:
                    return False
        normal = [Fraction(0)] * n
        combined_rhs = Fraction(0)
        for i, key in enumerate(rows):
            budget.charge()
            weight = weights[i]
            if not weight:
                continue
            kind, name, side = key
            flip = -1 if norm.rhs[normalized[key]] < 0 else 1
            if kind == "bound":
                original = names[name]
                bound = float(norm.upper[original])
                if not isfinite(bound):
                    return False
                rhs = budget.guard(Fraction(bound) - Fraction(float(norm.offset[original])))
                normal[original] = budget.guard(normal[original] + weight * flip)
            else:
                original = raw_rows[name]
                bound = float(
                    norm.data.row_upper[original]
                    if side == "upper" else norm.data.row_lower[original]
                )
                if not isfinite(bound):
                    return False
                rhs = budget.guard(Fraction(bound))
                indices, values = row_support(norm.data.a, original)
                for column, value in zip(indices, values, strict=True):
                    coefficient = budget.guard(Fraction(float(value)))
                    offset = budget.guard(Fraction(float(norm.offset[column])))
                    rhs = budget.guard(rhs - coefficient * offset)
                    normal[column] = budget.guard(normal[column] + weight * flip * coefficient)
            combined_rhs = budget.guard(combined_rhs + weight * flip * rhs)
        if combined_rhs:
            return False
        for key in keys:
            budget.charge()
            if key[0] == "variable" and normal[names[key[1]]]:
                return False
            if key[0] == "slack" and key[1] in active and weights[active[key[1]]]:
                return False
        return True
