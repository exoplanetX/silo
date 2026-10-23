"""General linear data and reversible affine normalization.

No solver is imported here. Row identity is stored explicitly, independently of
names and column positions. The canonical objective is MAX -s*f, with z >= 0.
"""

from dataclasses import dataclass
from math import ceil, floor, isfinite

import numpy as np

from silo.core.enums import OptimizationSense, VariableType
from silo.core.model import Model


@dataclass
class LinearData:
    names: tuple[str, ...]
    row_names: tuple[str, ...]
    a: np.ndarray
    c: np.ndarray
    constant: float
    sign: int
    lower: np.ndarray
    upper: np.ndarray
    row_lower: np.ndarray
    row_upper: np.ndarray
    integer: np.ndarray


def linear_data(model: Model, max_cells: int = 2_000_000) -> LinearData:
    model.validate()
    for value in [
        model.objective.constant,
        *model.objective.coefficients.values(),
        *[a for r in model.constraints for a in r.coefficients.values()],
    ]:
        if not isfinite(value):
            raise ValueError("Coefficients and objective constant must be finite.")
        if isinstance(value, int) and int(float(value)) != value:
            raise FloatingPointError("Integer coefficient is not exactly representable in float64.")
    for r in model.constraints:
        if r.lower_bound is None and r.upper_bound is None and not isfinite(r.rhs):
            raise ValueError(
                "Legacy row RHS must be finite; use explicit sides for missing bounds."
            )
    for value in [
        *[b for v in model.variables for b in (v.bounds.lower, v.bounds.upper)],
        *[b for r in model.constraints for b in r.row_bounds],
    ]:
        if isinstance(value, int) and int(float(value)) != value:
            raise FloatingPointError(
                "Integer bound/row side is not exactly representable in float64."
            )
    n, m = len(model.variables), len(model.constraints)
    if (m + n) * (3 * n + 2 * m + 1) > max_cells:
        raise MemoryError("Dense reference workspace exceeds max_dense_cells.")
    names = tuple(model.variable_names())
    a = np.array(
        [[r.coefficients.get(k, 0.0) for k in names] for r in model.constraints], dtype=float
    ).reshape(m, n)
    return LinearData(
        names,
        tuple(r.name for r in model.constraints),
        a,
        np.array([model.objective.coefficients.get(k, 0.0) for k in names], dtype=float),
        model.objective.constant,
        1 if model.objective.sense == OptimizationSense.MINIMIZE else -1,
        np.array([v.bounds.lower for v in model.variables], dtype=float),
        np.array([v.bounds.upper for v in model.variables], dtype=float),
        np.array([r.row_bounds[0] for r in model.constraints], dtype=float),
        np.array([r.row_bounds[1] for r in model.constraints], dtype=float),
        np.array([v.var_type != VariableType.CONTINUOUS for v in model.variables], dtype=bool),
    )


def integer_bounds(data: LinearData) -> tuple[np.ndarray, np.ndarray]:
    lower, upper = data.lower.copy(), data.upper.copy()
    for j in np.flatnonzero(data.integer):
        if isfinite(lower[j]):
            lower[j] = ceil(lower[j])
        if isfinite(upper[j]):
            upper[j] = floor(upper[j])
    return lower, upper


@dataclass
class Normalization:
    data: LinearData
    offset: np.ndarray
    transform: np.ndarray
    matrix: np.ndarray
    rhs: np.ndarray
    senses: tuple[str, ...]
    costs: np.ndarray
    origins: tuple[tuple[str, int, str], ...]
    column_origins: tuple[tuple[int, int], ...]
    row_scale: np.ndarray
    col_scale: np.ndarray
    lower: np.ndarray
    upper: np.ndarray

    @property
    def row_keys(self):
        return tuple(
            (kind, self.data.row_names[i] if kind == "row" else self.data.names[i], side)
            for kind, i, side in self.origins
        )

    def point(self, z):
        return self.offset + self.transform @ (self.col_scale * z)

    def ray(self, dz):
        return self.transform @ (self.col_scale * dz)

    def multipliers(self, row_dual, reduced, objective=True):
        """Canonical MAX dual -> effective original-side minimization multipliers."""
        d = self.data
        yl, yu = np.zeros(len(d.row_names)), np.zeros(len(d.row_names))
        zl, zu = np.zeros(len(d.names)), np.zeros(len(d.names))
        for (kind, i, side), lam in zip(self.origins, self.row_scale * row_dual, strict=True):
            if kind == "bound":
                zu[i] += lam
            elif side == "lower":
                yl[i] -= lam
            elif side == "upper":
                yu[i] += lam
            else:
                yl[i] += max(-lam, 0.0)
                yu[i] += max(lam, 0.0)
        rc = reduced / self.col_scale
        for j, (i, _direction) in enumerate(self.column_origins):
            if isfinite(self.lower[i]):
                zl[i] -= rc[j]
            elif isfinite(self.upper[i]):
                zu[i] -= rc[j]
        h = (d.sign * d.c if objective else np.zeros(len(d.names))) + d.a.T @ (yu - yl)
        for i in range(len(d.names)):
            if self.lower[i] == self.upper[i]:
                zl[i], zu[i] = max(h[i], 0.0), max(-h[i], 0.0)
        return yl, yu, zl, zu


def normalize(data, lower, upper, scaling=True, redundant=None):
    """Affine coordinate map, original row sides and supplementary upper rows."""
    n = len(data.names)
    offset = np.zeros(n)
    columns, col_origins, upper_rows = [], [], []
    for i in range(n):
        if lower[i] == upper[i]:
            offset[i] = lower[i]
            continue
        directions = (1,)
        if isfinite(lower[i]):
            offset[i] = lower[i]
            if isfinite(upper[i]):
                upper_rows.append((i, len(columns), upper[i] - lower[i]))
        elif isfinite(upper[i]):
            offset[i], directions = upper[i], (-1,)
        else:
            directions = (1, -1)
        for direction in directions:
            v = np.zeros(n)
            v[i] = direction
            columns.append(v)
            col_origins.append((i, direction))
    t = np.array(columns).T if columns else np.empty((n, 0))
    at = data.a @ t
    shift = data.a @ offset
    rows, rhs, senses, origins = [], [], [], []
    for i in range(len(data.row_names)):
        if redundant is not None and redundant[i]:
            continue
        lo, hi = data.row_lower[i], data.row_upper[i]
        if lo == hi:
            rows.append(at[i])
            rhs.append(lo - shift[i])
            senses.append("=")
            origins.append(("row", i, "equal"))
        else:
            for bound, sense, side in ((lo, ">=", "lower"), (hi, "<=", "upper")):
                if isfinite(bound):
                    rows.append(at[i])
                    rhs.append(bound - shift[i])
                    senses.append(sense)
                    origins.append(("row", i, side))
    for i, col, bound in upper_rows:
        v = np.zeros(t.shape[1])
        v[col] = 1.0
        rows.append(v)
        rhs.append(bound)
        senses.append("<=")
        origins.append(("bound", i, "upper"))
    a = np.array(rows, dtype=float).reshape(len(rows), t.shape[1])
    b = np.array(rhs, dtype=float)
    c = -data.sign * (t.T @ data.c)
    rscale, cscale = np.ones(len(rows)), np.ones(t.shape[1])
    if scaling and a.size:
        norms = np.max(np.abs(a), axis=1)
        rscale = 1.0 / np.where(norms > 0, norms, 1.0)
        a = rscale[:, None] * a
        b = rscale * b
        norms = np.max(np.abs(a), axis=0)
        cscale = 1.0 / np.where(norms > 0, norms, 1.0)
        a = a * cscale
        c = c * cscale
    if not all(np.isfinite(v).all() for v in (offset, t, a, b, c, rscale, cscale)):
        raise FloatingPointError("Nonfinite affine normalization/scaling.")
    return Normalization(
        data,
        offset,
        t,
        a,
        b,
        tuple(senses),
        c,
        tuple(origins),
        tuple(col_origins),
        rscale,
        cscale,
        lower,
        upper,
    )
