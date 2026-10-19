"""Immutable append-only basis identities and full-row feasibility checks.

No simplex runner or RMP dependency. All numerical checks use the existing
absolute tolerance; this is a conservative reuse gate, not exact LP solving.
"""

from copy import deepcopy
from dataclasses import dataclass, replace
from math import fsum, isfinite

import numpy as np

from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.lp.simplex.basis import Basis
from silo.lp.simplex.standard_form import (
    COLUMN_ARTIFICIAL,
    COLUMN_ORIGINAL,
    COLUMN_SLACK,
    COLUMN_SURPLUS,
    StandardFormProblem,
    build_standard_form,
)
from silo.utils.numerics import DEFAULT_TOLERANCE

ColumnKey = tuple[str, str]


@dataclass(frozen=True)
class VariableIdentity:
    name: str
    var_type: VariableType
    lower: float
    upper: float
    cost: float


@dataclass(frozen=True)
class RowIdentity:
    name: str
    sense: ConstraintSense
    rhs: float
    coefficients: tuple[float, ...]

    def __post_init__(self):
        object.__setattr__(self, 'coefficients', tuple(self.coefficients))


@dataclass(frozen=True)
class ModelIdentity:
    variables: tuple[VariableIdentity, ...]
    rows: tuple[RowIdentity, ...]
    sense: OptimizationSense
    constant: float

    def __post_init__(self):
        object.__setattr__(self, 'variables', tuple(self.variables))
        object.__setattr__(self, 'rows', tuple(self.rows))


@dataclass(frozen=True)
class RevisedBasisSnapshot:
    basis_keys: tuple[ColumnKey, ...]
    row_names: tuple[str, ...]
    column_keys: tuple[ColumnKey, ...]
    model_identity: ModelIdentity

    def __post_init__(self):
        for name in ('basis_keys', 'column_keys'):
            object.__setattr__(self, name, tuple(tuple(k) for k in getattr(self, name)))
        object.__setattr__(self, 'row_names', tuple(self.row_names))


def capture_identity(model: Model) -> ModelIdentity:
    model.validate()
    names = model.variable_names()
    values = [model.objective.constant, *model.objective.coefficients.values()]
    for row in model.constraints:
        values.extend((row.rhs, *row.coefficients.values()))
    if not all(isfinite(value) for value in values):
        raise ValueError('Nonfinite original model data.')
    return ModelIdentity(
        tuple(VariableIdentity(v.name, v.var_type, v.bounds.lower, v.bounds.upper,
                               model.objective.coefficients.get(v.name, 0))
              for v in model.variables),
        tuple(RowIdentity(r.name, r.sense, r.rhs,
                          tuple(r.coefficients.get(n, 0) for n in names))
              for r in model.constraints),
        model.objective.sense, model.objective.constant,
    )


def column_keys(problem: StandardFormProblem) -> tuple[ColumnKey, ...]:
    keys = []
    for column in problem.columns:
        if column.role == COLUMN_ORIGINAL:
            if column.original_name != column.name or column.source_constraint is not None:
                raise ValueError('Invalid original column role/name/source.')
            key = (COLUMN_ORIGINAL, column.original_name)
        elif column.role in (COLUMN_SLACK, COLUMN_SURPLUS):
            if (column.original_name is not None
                    or column.source_constraint not in problem.row_names):
                raise ValueError('Invalid structural column role/source.')
            key = (column.role, column.source_constraint)
        else:
            raise ValueError('Artificial or unknown column role is not reusable.')
        keys.append(key)
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate semantic column keys.')
    return tuple(keys)


def _without_artificials(problem: StandardFormProblem) -> StandardFormProblem:
    count = len(problem.columns)
    if (len(problem.matrix) != len(problem.row_names)
            or len(problem.rhs) != len(problem.row_names)
            or any(len(row) != count for row in problem.matrix)
            or len(problem.objective_coefficients) != count
            or any(type(j) is not int or not 0 <= j < count for j in problem.artificial_columns)):
        raise ValueError('Invalid fresh matrix/column coordinates.')
    artificial = set(problem.artificial_columns)
    if (len(artificial) != len(problem.artificial_columns)
            or artificial != {j for j, c in enumerate(problem.columns)
                              if c.role == COLUMN_ARTIFICIAL}):
        raise ValueError('Invalid fresh artificial-column inventory.')
    kept = [j for j in range(len(problem.columns)) if j not in artificial]
    return replace(problem, columns=tuple(problem.columns[j] for j in kept),
                   matrix=tuple(tuple(row[j] for j in kept) for row in problem.matrix),
                   objective_coefficients=tuple(problem.objective_coefficients[j] for j in kept),
                   artificial_columns=())


def map_snapshot(
    model: Model, identity: ModelIdentity, fresh: StandardFormProblem,
    snapshot: RevisedBasisSnapshot,
) -> tuple[StandardFormProblem, Basis]:
    if not isinstance(snapshot, RevisedBasisSnapshot):
        raise ValueError('Invalid snapshot type.')
    old = snapshot.model_identity
    if not isinstance(old, ModelIdentity):
        raise ValueError('Invalid snapshot model identity.')
    count = len(old.variables)
    if (identity.variables[:count] != old.variables or len(identity.variables) < count
            or identity.sense != old.sense or identity.constant != old.constant
            or len(identity.rows) != len(old.rows)):
        raise ValueError('Incompatible old variables, objective or row inventory.')
    for current, previous in zip(identity.rows, old.rows, strict=True):
        if (not isinstance(previous, RowIdentity)
                or (current.name, current.sense, current.rhs, current.coefficients[:count])
                != (previous.name, previous.sense, previous.rhs, previous.coefficients)):
            raise ValueError('Incompatible original row order/data or old coefficients.')
    rows = tuple(r.name for r in identity.rows)
    if snapshot.row_names != rows or fresh.row_names != rows:
        raise ValueError('Snapshot must retain every original row in order.')
    problem = _without_artificials(fresh)
    keys = column_keys(problem)
    old_names = {v.name for v in old.variables}
    expected_old = tuple(k for k in keys if k[0] != COLUMN_ORIGINAL or k[1] in old_names)
    if snapshot.column_keys != expected_old:
        raise ValueError('Snapshot semantic column inventory disagrees with the original model.')
    if (len(snapshot.basis_keys) != len(rows)
            or len(set(snapshot.basis_keys)) != len(snapshot.basis_keys)
            or any(k not in expected_old for k in snapshot.basis_keys)):
        raise ValueError('Invalid or duplicate basic semantic keys.')
    positions = {key: j for j, key in enumerate(keys)}
    basic = tuple(positions[key] for key in snapshot.basis_keys)
    basis = Basis(basic, tuple(j for j in range(len(keys)) if j not in basic))
    problem = replace(problem, initial_basis=basis)
    validate_basis_point(model, problem, basis)
    return problem, basis


def validate_basis_point(model: Model, problem: StandardFormProblem, basis: Basis) -> None:
    """Validate raw basis solution and independently recompute original rows."""
    if not isinstance(basis, Basis) or any(
        type(j) is not int for j in (*basis.basic_columns, *basis.nonbasic_columns)
    ):
        raise ValueError('Invalid basis coordinates.')
    rows, columns = len(problem.row_names), len(problem.columns)
    basis.validate(column_count=columns, row_count=rows)
    if (len(problem.matrix) != rows or len(problem.rhs) != rows
            or any(len(row) != columns for row in problem.matrix)):
        raise ValueError('Invalid matrix dimensions.')
    try:
        matrix = np.asarray(problem.matrix, dtype=float).reshape(rows, columns)
        rhs = np.asarray(problem.rhs, dtype=float)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f'Invalid numerical basis coordinates: {exc}') from exc
    try:
        if not np.all(np.isfinite(matrix)) or not np.all(np.isfinite(rhs)):
            raise ValueError('Nonfinite basis matrix/RHS.')
        b = matrix[:, list(basis.basic_columns)]
        raw = np.linalg.solve(b, rhs)
    except np.linalg.LinAlgError as exc:
        raise ValueError(f'Basis solve failed: {exc}') from exc
    if (not np.all(np.isfinite(raw)) or np.any(raw < -DEFAULT_TOLERANCE)
            or not np.all(np.isfinite(b @ raw - rhs))
            or np.any(np.abs(b @ raw - rhs) > DEFAULT_TOLERANCE)):
        raise ValueError('Raw standard-form basis point is not feasible/finite.')
    point = np.zeros(columns)
    point[list(basis.basic_columns)] = raw
    keys = column_keys(problem)
    original = {key[1]: float(point[j]) for j, key in enumerate(keys) if key[0] == COLUMN_ORIGINAL}
    if set(original) != set(model.variable_names()):
        raise ValueError('Incomplete original point coordinates.')
    for v in model.variables:
        value = original[v.name]
        if (value < v.bounds.lower - DEFAULT_TOLERANCE
                or value > v.bounds.upper + DEFAULT_TOLERANCE):
            raise ValueError(f'Original point violates bound {v.name!r}.')
    for row in model.constraints:
        residual = fsum(a * original[n] for n, a in row.coefficients.items()) - row.rhs
        if (not isfinite(residual) or (row.sense == ConstraintSense.LE
                                      and residual > DEFAULT_TOLERANCE)
                or (row.sense == ConstraintSense.GE and residual < -DEFAULT_TOLERANCE)
                or (row.sense == ConstraintSense.EQ and abs(residual) > DEFAULT_TOLERANCE)):
            raise ValueError(f'Original point violates row {row.name!r}.')


def make_snapshot(
    model: Model, identity: ModelIdentity, problem: StandardFormProblem | None, basis: Basis | None,
) -> RevisedBasisSnapshot:
    """Caller has checked OPTIMAL evidence; qualify its actual final metadata."""
    if not isinstance(problem, StandardFormProblem) or not isinstance(basis, Basis):
        raise ValueError('Final standard-form problem/basis is unavailable.')
    if problem.row_names != tuple(r.name for r in identity.rows):
        raise ValueError('Final problem deleted/reordered original rows; snapshot unavailable.')
    if problem.artificial_columns:
        raise ValueError('Final problem still contains artificial columns.')
    keys = column_keys(problem)
    expected = _without_artificials(build_standard_form(deepcopy(model)))
    if (problem.columns != expected.columns or problem.matrix != expected.matrix
            or problem.rhs != expected.rhs
            or problem.original_variable_count != expected.original_variable_count
            or problem.objective_coefficients != expected.objective_coefficients
            or problem.objective_constant != expected.objective_constant):
        raise ValueError('Final metadata disagrees with the full original standard form.')
    validate_basis_point(model, problem, basis)
    return RevisedBasisSnapshot(tuple(keys[j] for j in basis.basic_columns), problem.row_names,
                                keys, identity)
