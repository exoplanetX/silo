from dataclasses import dataclass
from math import isinf

from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.lp.simplex.basis import Basis
from silo.utils.numerics import DEFAULT_TOLERANCE

COLUMN_ORIGINAL = "original"
COLUMN_SLACK = "slack"
COLUMN_SURPLUS = "surplus"
COLUMN_ARTIFICIAL = "artificial"


@dataclass(frozen=True)
class StandardColumn:
    name: str
    role: str
    original_name: str | None = None
    source_constraint: str | None = None


@dataclass(frozen=True)
class NormalizedConstraintRow:
    name: str
    coefficients: tuple[float, ...]
    sense: ConstraintSense
    rhs: float


@dataclass(frozen=True)
class StandardFormProblem:
    name: str
    columns: tuple[StandardColumn, ...]
    row_names: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    rhs: tuple[float, ...]
    objective_coefficients: tuple[float, ...]
    objective_constant: float
    initial_basis: Basis
    artificial_columns: tuple[int, ...]
    original_variable_count: int


def build_standard_form(model: Model) -> StandardFormProblem:
    _validate_supported_lp(model)
    original_names = tuple(model.variable_names())
    original_count = len(original_names)
    columns = [
        StandardColumn(
            name=name,
            role=COLUMN_ORIGINAL,
            original_name=name,
        )
        for name in original_names
    ]
    rows: list[list[float]] = []
    rhs_values: list[float] = []
    row_names: list[str] = []
    basic_columns: list[int] = []
    artificial_columns: list[int] = []

    for normalized_row in _normalize_rows(model, original_names):
        row = list(normalized_row.coefficients)
        row.extend(0.0 for _ in range(len(columns) - original_count))

        if normalized_row.sense == ConstraintSense.LE:
            slack_column = _append_column(
                columns=columns,
                rows=rows,
                name=f"slack_{normalized_row.name}",
                role=COLUMN_SLACK,
                source_constraint=normalized_row.name,
            )
            row.append(1.0)
            basic_columns.append(slack_column)
        elif normalized_row.sense == ConstraintSense.GE:
            _append_column(
                columns=columns,
                rows=rows,
                name=f"surplus_{normalized_row.name}",
                role=COLUMN_SURPLUS,
                source_constraint=normalized_row.name,
            )
            row.append(-1.0)
            artificial_column = _append_column(
                columns=columns,
                rows=rows,
                name=f"artificial_{normalized_row.name}",
                role=COLUMN_ARTIFICIAL,
                source_constraint=normalized_row.name,
            )
            row.append(1.0)
            artificial_columns.append(artificial_column)
            basic_columns.append(artificial_column)
        else:
            artificial_column = _append_column(
                columns=columns,
                rows=rows,
                name=f"artificial_{normalized_row.name}",
                role=COLUMN_ARTIFICIAL,
                source_constraint=normalized_row.name,
            )
            row.append(1.0)
            artificial_columns.append(artificial_column)
            basic_columns.append(artificial_column)

        row_names.append(normalized_row.name)
        rhs_values.append(normalized_row.rhs)
        rows.append([_clean_zero(value) for value in row])

    objective_coefficients = [
        model.objective.coefficients.get(column.name, 0.0)
        if column.role == COLUMN_ORIGINAL
        else 0.0
        for column in columns
    ]
    basic_set = set(basic_columns)
    initial_basis = Basis(
        basic_columns=tuple(basic_columns),
        nonbasic_columns=tuple(
            column_index
            for column_index in range(len(columns))
            if column_index not in basic_set
        ),
    )
    initial_basis.validate(column_count=len(columns), row_count=len(rows))

    return StandardFormProblem(
        name=model.name,
        columns=tuple(columns),
        row_names=tuple(row_names),
        matrix=tuple(tuple(row) for row in rows),
        rhs=tuple(rhs_values),
        objective_coefficients=tuple(_clean_zero(value) for value in objective_coefficients),
        objective_constant=_clean_zero(model.objective.constant),
        initial_basis=initial_basis,
        artificial_columns=tuple(artificial_columns),
        original_variable_count=original_count,
    )


def _validate_supported_lp(model: Model) -> None:
    model.validate()
    if model.objective.sense != OptimizationSense.MAXIMIZE:
        raise ValueError("Standard form builder supports only maximization models.")

    for variable in model.variables:
        if variable.var_type != VariableType.CONTINUOUS:
            raise ValueError("Standard form builder supports only continuous variables.")
        if abs(variable.bounds.lower) > DEFAULT_TOLERANCE:
            raise ValueError("Standard form builder supports only variables with lower bound 0.")
        if not isinf(variable.bounds.upper):
            raise ValueError("Standard form builder does not support finite variable upper bounds.")


def _normalize_rows(
    model: Model,
    original_names: tuple[str, ...],
) -> list[NormalizedConstraintRow]:
    normalized_rows: list[NormalizedConstraintRow] = []
    for constraint in model.constraints:
        coefficients = [constraint.coefficients.get(name, 0.0) for name in original_names]
        sense = constraint.sense
        rhs = constraint.rhs

        if rhs < -DEFAULT_TOLERANCE:
            coefficients = [-coefficient for coefficient in coefficients]
            rhs = -rhs
            sense = _flip_sense(sense)
        elif abs(rhs) <= DEFAULT_TOLERANCE:
            rhs = 0.0

        normalized_rows.append(
            NormalizedConstraintRow(
                name=constraint.name,
                coefficients=tuple(_clean_zero(coefficient) for coefficient in coefficients),
                sense=sense,
                rhs=_clean_zero(rhs),
            )
        )
    return normalized_rows


def _flip_sense(sense: ConstraintSense) -> ConstraintSense:
    if sense == ConstraintSense.LE:
        return ConstraintSense.GE
    if sense == ConstraintSense.GE:
        return ConstraintSense.LE
    return ConstraintSense.EQ


def _append_column(
    columns: list[StandardColumn],
    rows: list[list[float]],
    name: str,
    role: str,
    source_constraint: str,
) -> int:
    column_index = len(columns)
    columns.append(
        StandardColumn(
            name=name,
            role=role,
            source_constraint=source_constraint,
        )
    )
    for row in rows:
        row.append(0.0)
    return column_index


def _clean_zero(value: float) -> float:
    return 0.0 if abs(value) <= DEFAULT_TOLERANCE else value
