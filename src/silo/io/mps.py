"""Strict, deterministic I/O for the documented SILO free-MPS subset.

No format guessing or external solver is used. See ``docs/mps_format.md`` for
the accepted records, integer defaults, and deliberate format restrictions.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, localcontext
from math import inf, isfinite
from pathlib import Path
from typing import NoReturn

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable

_SECTIONS = ("NAME", "OBJSENSE", "ROWS", "COLUMNS", "RHS", "RANGES", "BOUNDS", "ENDATA")
_VALUE_BOUNDS = {"LO", "UP", "FX", "LI", "UI"}
_EMPTY_BOUNDS = {"FR", "MI", "PL", "BV"}
_NUMERIC = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?", re.ASCII)


def read_mps_model(path: str | Path) -> Model:
    """Read an uncompressed UTF-8 free-MPS model."""
    return parse_mps(Path(path).read_text(encoding="utf-8"))


def parse_mps(text: str) -> Model:
    """Parse one model; malformed, fixed-column and unsupported data raise ValueError."""
    if not isinstance(text, str):
        raise ValueError("Invalid MPS: expected text")
    parser = _MPSParser()
    for number, line in enumerate(text.splitlines(), 1):
        parser.read_line(line, number)
    try:
        return parser.model()
    except ValueError as exc:
        if str(exc).startswith("MPS line "):
            raise
        parser.fail(str(exc))


def write_mps_model(model: Model, path: str | Path) -> None:
    """Write a model in the deterministic free-MPS profile accepted by this reader."""
    output = model_to_mps(model)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")


def model_to_mps(model: Model) -> str:
    """Serialize general linear bounds, integrality, objective sense and constant."""
    model.validate()
    _name(model.name, "model name")
    for variable in model.variables:
        _name(variable.name, "variable name")
        _valid_bounds(variable.bounds.lower, variable.bounds.upper, variable.name)
    for row in model.constraints:
        _name(row.name, "row name")
    objective_name = _fresh_name("__obj__", {row.name for row in model.constraints})
    lines = [
        f"NAME {model.name}",
        "OBJSENSE",
        " MAX" if model.objective.sense == OptimizationSense.MAXIMIZE else " MIN",
        "ROWS",
        f" N {objective_name}",
    ]
    row_data: list[tuple[Constraint, str, float, str | None]] = []
    for row in model.constraints:
        kind, rhs, width = _row_encoding(row)
        row_data.append((row, kind, rhs, width))
        lines.append(f" {kind} {row.name}")

    lines.append("COLUMNS")
    integer_section = False
    marker_count = 0
    reserved_names = set(model.variable_names()) | {row.name for row in model.constraints}
    for variable in model.variables:
        integer = variable.var_type != VariableType.CONTINUOUS
        if integer != integer_section:
            marker = _fresh_name(f"__mark_{marker_count}__", reserved_names)
            reserved_names.add(marker)
            lines.append(f" {marker} 'MARKER' '{'INTORG' if integer else 'INTEND'}'")
            marker_count += 1
            integer_section = integer
        entries: list[tuple[str, float]] = []
        coefficient = _finite(model.objective.coefficients.get(variable.name, 0.0), "objective")
        if coefficient != 0.0:
            entries.append((objective_name, coefficient))
        for row in model.constraints:
            coefficient = _finite(row.coefficients.get(variable.name, 0.0), row.name)
            if coefficient != 0.0:
                entries.append((row.name, coefficient))
        if not entries:
            entries.append((objective_name, 0.0))
        lines.extend(f" {variable.name} {row_name} {_number(value)}" for row_name, value in entries)
    if integer_section:
        marker = _fresh_name(f"__mark_{marker_count}__", reserved_names)
        lines.append(f" {marker} 'MARKER' 'INTEND'")

    lines.append("RHS")
    constant = _finite(model.objective.constant, "objective constant")
    if constant != 0.0:
        lines.append(f" RHS1 {objective_name} {_number(-constant)}")
    for row, kind, rhs, _ in row_data:
        if kind != "N":
            lines.append(f" RHS1 {row.name} {_number(rhs)}")
    ranges = [(row.name, width) for row, _, _, width in row_data if width is not None]
    if ranges:
        lines.append("RANGES")
        lines.extend(f" RNG1 {name} {width}" for name, width in ranges)
    if model.variables:
        lines.append("BOUNDS")
        for variable in model.variables:
            lines.extend(_bound_records(variable))
    lines.append("ENDATA")
    return "\n".join(lines) + "\n"


@dataclass
class _Column:
    integer_marker: bool = False
    lower: float = 0.0
    upper: float = inf
    var_type: VariableType = VariableType.CONTINUOUS
    bound_sides: set[str] = field(default_factory=set)
    binary_record: bool = False


@dataclass
class _MPSParser:
    section: str = ""
    seen_sections: set[str] = field(default_factory=set)
    name: str = "model"
    sense: OptimizationSense = OptimizationSense.MINIMIZE
    sense_seen: bool = False
    objective_name: str | None = None
    rows: dict[str, str] = field(default_factory=dict)
    columns: dict[str, _Column] = field(default_factory=dict)
    coefficients: dict[tuple[str, str], float] = field(default_factory=dict)
    rhs: dict[str, Decimal] = field(default_factory=dict)
    ranges: dict[str, Decimal] = field(default_factory=dict)
    vector_names: dict[str, str] = field(default_factory=dict)
    integer_section: bool = False
    last_column: str | None = None
    line_number: int = 0

    def read_line(self, line: str, number: int) -> None:
        self.line_number = number
        if not line.strip() or line.lstrip().startswith("*"):
            return
        tokens = line.split()
        if self.section == "ENDATA":
            self.fail("data after ENDATA")
        if not line[0].isspace() and tokens[0].upper() in _SECTIONS:
            self.header(tokens)
            return
        if self.section == "OBJSENSE":
            self.objective_sense(tokens)
            return
        if not self.section:
            self.fail("NAME must be the first record")
        if not line[0].isspace():
            self.fail(f"unsupported section or unindented data record: {tokens[0]}")
        if _fixed_record(line, self.section):
            self.fail("fixed-column MPS is unsupported; use free token records")
        if self.section == "ROWS":
            self.row(tokens)
        elif self.section == "COLUMNS":
            self.column(tokens)
        elif self.section in {"RHS", "RANGES"}:
            self.vector(tokens)
        elif self.section == "BOUNDS":
            self.bound(tokens)
        else:
            self.fail(f"unexpected data in {self.section}")

    def header(self, tokens: list[str]) -> None:
        section = tokens[0].upper()
        if section in self.seen_sections:
            self.fail(f"duplicate {section} section")
        if self.section and _SECTIONS.index(section) <= _SECTIONS.index(self.section):
            self.fail(f"out-of-order {section} section")
        if not self.section and section != "NAME":
            self.fail("NAME must be the first record")
        if self.section == "OBJSENSE" and not self.sense_seen:
            self.fail("OBJSENSE requires MIN or MAX")
        if self.integer_section and section != "COLUMNS":
            self.fail("INTORG has no matching INTEND")
        if section in {"NAME", "OBJSENSE"}:
            if len(tokens) > 2:
                self.fail(f"malformed {section} record")
        elif len(tokens) != 1:
            self.fail(f"malformed {section} header")
        self.section = section
        self.seen_sections.add(section)
        if section == "NAME" and len(tokens) == 2:
            self.name = self.checked_name(tokens[1], "model name")
        elif section == "OBJSENSE" and len(tokens) == 2:
            self.objective_sense(tokens[1:])
        if section == "COLUMNS" and self.objective_name is None:
            self.fail("ROWS requires an N objective row")

    def objective_sense(self, tokens: list[str]) -> None:
        if self.sense_seen or len(tokens) != 1 or tokens[0].upper() not in {"MIN", "MAX"}:
            self.fail("OBJSENSE requires exactly one MIN or MAX")
        self.sense = (
            OptimizationSense.MINIMIZE if tokens[0].upper() == "MIN" else OptimizationSense.MAXIMIZE
        )
        self.sense_seen = True

    def row(self, tokens: list[str]) -> None:
        if len(tokens) != 2 or tokens[0].upper() not in {"N", "L", "G", "E"}:
            self.fail("malformed ROWS record; expected N/L/G/E and a row name")
        name = self.checked_name(tokens[1], "row name")
        if name in self.rows:
            self.fail(f"duplicate row: {name}")
        kind = tokens[0].upper()
        if kind == "N" and self.objective_name is None:
            self.objective_name = name
        self.rows[name] = kind

    def column(self, tokens: list[str]) -> None:
        if len(tokens) == 3 and tokens[1] == "'MARKER'":
            self.checked_name(tokens[0], "marker name")
            marker = tokens[2]
            if marker == "'INTORG'" and not self.integer_section:
                self.integer_section = True
            elif marker == "'INTEND'" and self.integer_section:
                self.integer_section = False
            else:
                self.fail("malformed, nested or unmatched INTORG/INTEND marker")
            self.last_column = None
            return
        if len(tokens) not in {3, 5}:
            self.fail("malformed COLUMNS record; expected column and one or two row/value pairs")
        name = self.checked_name(tokens[0], "variable name")
        if name in self.columns and name != self.last_column:
            self.fail(f"non-contiguous column records: {name}")
        if name not in self.columns:
            self.columns[name] = _Column(
                integer_marker=self.integer_section,
                upper=1.0 if self.integer_section else inf,
                var_type=VariableType.INTEGER if self.integer_section else VariableType.CONTINUOUS,
            )
        if self.columns[name].integer_marker != self.integer_section:
            self.fail(f"inconsistent integer marker for column: {name}")
        self.last_column = name
        for position in range(1, len(tokens), 2):
            row = tokens[position]
            if row not in self.rows:
                self.fail(f"unknown row in COLUMNS: {row}")
            key = (name, row)
            if key in self.coefficients:
                self.fail(f"duplicate coefficient for column {name}, row {row}")
            self.coefficients[key] = self.value(tokens[position + 1])

    def vector(self, tokens: list[str]) -> None:
        if len(tokens) not in {3, 5}:
            self.fail(f"malformed {self.section} record")
        name = self.checked_name(tokens[0], f"{self.section} set name")
        self.vector_name(name)
        target = self.rhs if self.section == "RHS" else self.ranges
        for position in range(1, len(tokens), 2):
            row = tokens[position]
            if row not in self.rows:
                self.fail(f"unknown row in {self.section}: {row}")
            if self.rows[row] == "N" and (self.section == "RANGES" or row != self.objective_name):
                self.fail(f"{self.section} data on free/objective row is unsupported: {row}")
            if row in target:
                self.fail(f"duplicate {self.section} value for row: {row}")
            value = self.decimal_value(tokens[position + 1])
            if self.section == "RHS":
                self.value(tokens[position + 1])
            elif value and (value.adjusted() > 308 or float(value) == 0.0):
                self.fail("range is outside the representable model-bound scale")
            target[row] = value

    def bound(self, tokens: list[str]) -> None:
        if not tokens or tokens[0].upper() not in _VALUE_BOUNDS | _EMPTY_BOUNDS:
            self.fail(f"unsupported bound type: {tokens[0] if tokens else ''}")
        kind = tokens[0].upper()
        expected = 4 if kind in _VALUE_BOUNDS else 3
        if len(tokens) != expected:
            self.fail(f"malformed {kind} bound record")
        self.vector_name(self.checked_name(tokens[1], "BOUNDS set name"))
        name = tokens[2]
        if name not in self.columns:
            self.fail(f"unknown variable in BOUNDS: {name}")
        column = self.columns[name]
        value = self.value(tokens[3]) if kind in _VALUE_BOUNDS else 0.0
        if kind == "BV":
            if column.binary_record or column.bound_sides:
                self.fail(f"BV must precede other bounds for variable: {name}")
            column.lower, column.upper = 0.0, 1.0
            column.var_type = VariableType.BINARY
            column.binary_record = True
            return
        sides = (
            {"lower", "upper"}
            if kind in {"FX", "FR"}
            else {"lower"}
            if kind in {"LO", "LI", "MI"}
            else {"upper"}
        )
        if column.bound_sides & sides:
            self.fail(f"duplicate bound side for variable: {name}")
        column.bound_sides.update(sides)
        if kind in {"LI", "UI"} and column.var_type != VariableType.BINARY:
            column.var_type = VariableType.INTEGER
        if kind in {"LO", "LI", "FX"}:
            column.lower = value
        if kind in {"UP", "UI", "FX"}:
            column.upper = value
            if value < 0.0 and "lower" not in column.bound_sides and not column.binary_record:
                column.lower = -inf
        if kind in {"FR", "MI"}:
            column.lower = -inf
        if kind in {"FR", "PL"}:
            column.upper = inf

    def vector_name(self, name: str) -> None:
        if self.section in self.vector_names and self.vector_names[self.section] != name:
            self.fail(f"multiple {self.section} sets are unsupported")
        self.vector_names[self.section] = name

    def model(self) -> Model:
        for required in ("NAME", "ROWS", "COLUMNS", "ENDATA"):
            if required not in self.seen_sections:
                self.fail(f"missing {required} section")
        if self.objective_name is None:
            self.fail("ROWS requires an N objective row")
        model = Model(name=self.name)
        for name, column in self.columns.items():
            _valid_bounds(column.lower, column.upper, name)
            model.add_variable(Variable(name, Bounds(column.lower, column.upper), column.var_type))
        objective_coefficients = self.row_coefficients(self.objective_name)
        model.set_objective(
            Objective(
                objective_coefficients,
                self.sense,
                -_decimal_number(
                    self.rhs.get(self.objective_name, Decimal(0)), "objective constant"
                ),
            )
        )
        for name, kind in self.rows.items():
            if name == self.objective_name:
                continue
            rhs_decimal = self.rhs.get(name, Decimal(0))
            rhs = _decimal_number(rhs_decimal, "RHS")
            lower, upper = _row_bounds(kind, rhs_decimal, self.ranges.get(name))
            _valid_bounds(lower, upper, name)
            sense = {
                "N": ConstraintSense.LE,
                "L": ConstraintSense.LE,
                "G": ConstraintSense.GE,
                "E": ConstraintSense.EQ,
            }[kind]
            model.add_constraint(
                Constraint(
                    name,
                    self.row_coefficients(name),
                    sense,
                    rhs,
                    lower_bound=lower,
                    upper_bound=upper,
                )
            )
        model.validate()
        return model

    def row_coefficients(self, row: str) -> dict[str, float]:
        return {
            name: self.coefficients[(name, row)]
            for name in self.columns
            if self.coefficients.get((name, row), 0.0) != 0.0
        }

    def checked_name(self, token: str, label: str) -> str:
        try:
            return _name(token, label)
        except ValueError as exc:
            self.fail(str(exc))
        raise AssertionError("unreachable")

    def value(self, token: str) -> float:
        decimal = self.decimal_value(token)
        try:
            return _decimal_number(decimal, "MPS value")
        except ValueError as exc:
            self.fail(f"invalid finite numeric value: {token}: {exc}")

    def decimal_value(self, token: str) -> Decimal:
        if _NUMERIC.fullmatch(token) is None:
            self.fail(f"invalid finite numeric value: {token}")
        try:
            value = Decimal(token.replace("D", "E").replace("d", "e"))
        except InvalidOperation:
            self.fail(f"invalid finite numeric value: {token}")
        if not value.is_finite():
            self.fail(f"invalid finite numeric value: {token}")
        return value if value != 0 else Decimal(0)

    def fail(self, message: str) -> NoReturn:
        raise ValueError(f"MPS line {self.line_number}: {message}")


def _row_bounds(kind: str, rhs: Decimal, width: Decimal | None) -> tuple[float, float]:
    rhs_float = _decimal_number(rhs, "RHS value")
    if kind == "N":
        return -inf, inf
    if width is None:
        return {"L": (-inf, rhs_float), "G": (rhs_float, inf), "E": (rhs_float, rhs_float)}[kind]
    if kind == "L":
        other = _decimal_add(rhs, width.copy_abs().copy_negate())
        return _decimal_number(other, "ranged lower bound"), rhs_float
    if kind == "G":
        return rhs_float, _decimal_number(_decimal_add(rhs, width.copy_abs()), "ranged upper bound")
    other = _decimal_number(_decimal_add(rhs, width), "ranged bound")
    return (rhs_float, other) if width >= 0 else (other, rhs_float)


def _row_encoding(row: Constraint) -> tuple[str, float, str | None]:
    lower, upper = row.row_bounds
    _valid_bounds(lower, upper, row.name)
    if lower == -inf and upper == inf:
        return "N", 0.0, None
    if lower == upper:
        return "E", lower, None
    if upper == inf:
        return "G", lower, None
    if lower == -inf:
        return "L", upper, None
    # Use exactly the Decimal spellings emitted for each endpoint. In particular,
    # an integer-valued float such as 1e308 is emitted as its actual exact integer,
    # not repr's distinct mathematical integer 10**308. Range reconstruction must
    # use that same value, including when the intermediate width exceeds float64.
    width = _decimal_add(Decimal(_number(upper)), Decimal(_number(lower)).copy_negate())
    text = format(width, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "L", upper, text


def _decimal_add(left: Decimal, right: Decimal) -> Decimal:
    # Bounds are native floats, but an MPS range can be wider than a float.
    # Preserve all input decimal digits through side reconstruction before the
    # final float conversion; this also prevents subtractive endpoint loss.
    digits = len(left.as_tuple().digits) + len(right.as_tuple().digits)
    span = abs(left.adjusted() - right.adjusted()) if left and right else 0
    with localcontext() as context:
        context.prec = max(1100, digits + span + 2)
        return left + right


def _bound_records(variable: Variable) -> list[str]:
    name, lower, upper = variable.name, variable.bounds.lower, variable.bounds.upper
    result: list[str] = []
    if variable.var_type == VariableType.BINARY:
        result.append(f" BV BND1 {name}")
        if lower == upper:
            result.append(f" FX BND1 {name} {_number(lower)}")
        else:
            if lower != 0.0:
                result.append(f" LO BND1 {name} {_number(lower)}")
            if upper != 1.0:
                result.append(f" UP BND1 {name} {_number(upper)}")
        return result
    if lower == upper:
        return [f" FX BND1 {name} {_number(lower)}"]
    if lower == -inf and upper == inf and variable.var_type == VariableType.CONTINUOUS:
        return [f" FR BND1 {name}"]
    integer = variable.var_type == VariableType.INTEGER
    if lower == -inf:
        result.append(f" MI BND1 {name}")
    elif lower != 0.0 or integer:
        result.append(f" {'LI' if integer else 'LO'} BND1 {name} {_number(lower)}")
    if upper == inf:
        if integer:
            result.append(f" PL BND1 {name}")
    else:
        result.append(f" {'UI' if integer else 'UP'} BND1 {name} {_number(upper)}")
    return result


def _finite(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"Invalid {label}: expected finite number")
    original = value
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid {label}: expected finite number") from exc
    if not isfinite(value):
        raise ValueError(f"Invalid {label}: expected finite number")
    return original if isinstance(original, int) and int(value) != original else value


def _decimal_number(value: Decimal, label: str) -> int | float:
    """One semantic gate for direct tokens and exactly derived Decimal sides.

    Noninteger decimals use finite float64 rounding. Mathematical integers whose
    value would change are retained as ints for the native input_conversion gate;
    trailing zeros or scientific notation do not change this decision. Nonzero
    underflow is rejected here so derived bounds cannot silently become zero.
    """
    number = _finite(float(value), label)
    if number == 0.0 and value != 0:
        raise ValueError(
            f"Invalid {label}: nonzero decimal underflows the model float representation"
        )
    if value == value.to_integral_value() and Decimal.from_float(number) != value:
        return int(value)
    return number


def _valid_bounds(lower: float, upper: float, name: str) -> None:
    if lower == inf or upper == -inf or lower != lower or upper != upper or lower > upper:
        raise ValueError(f"Invalid bounds for {name}: lower={lower}, upper={upper}")


def _number(value: float) -> str:
    value = _finite(value, "MPS value")
    # Every binary64 float above 2**53 is itself an integer. Its shortest decimal
    # spelling may denote a different exact integer, which the reader must protect.
    # Emit the actual integer instead of weakening that protection on round-trip.
    return str(int(value)) if isinstance(value, int) or value.is_integer() else repr(value)


def _name(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or any(char.isspace() or char in "*'$\"" or ord(char) < 32 for char in value)
    ):
        raise ValueError(f"Invalid {label}: expected an unquoted token without whitespace")
    return value


def _fresh_name(base: str, used: set[str]) -> str:
    candidate = base
    suffix = 1
    while candidate in used:
        candidate = f"{base}{suffix}"
        suffix += 1
    return candidate


def _fixed_record(line: str, section: str) -> bool:
    """Reserve traditional fixed-field whitespace layouts for rejected fixed input."""
    if "\t" in line:
        return False
    if section == "ROWS":
        return (
            len(line) >= 5
            and line[0] == " "
            and line[1] in "NLEG"
            and line[2:4] == "  "
            and bool(line[4:12].strip())
            and len(line[4:12].split()) == 1
            and not line[12:].strip()
        )
    if section in {"COLUMNS", "RHS", "RANGES"}:
        fields = (line[4:12], line[14:22], line[24:36], line[39:47], line[49:61])
        gaps = (line[:4], line[12:14], line[22:24], line[36:39], line[47:49], line[61:])
        marker = (
            section == "COLUMNS"
            and not line[:4].strip()
            and bool(line[4:12].strip())
            and line[14:22] == "'MARKER'"
            and line[39:47] in {"'INTORG'", "'INTEND'"}
            and not (line[12:14] + line[22:39] + line[47:]).strip()
        )
        return (
            marker
            or len(line) >= 25
            and all(not gap.strip() for gap in gaps)
            and all(fields[index].strip() for index in (0, 1, 2))
            and all(len(part.split()) <= 1 for part in fields)
        )
    if section == "BOUNDS":
        fields = (line[1:3], line[4:12], line[14:22], line[24:36])
        gaps = (line[:1], line[3:4], line[12:14], line[22:24], line[36:])
        return (
            len(line) >= 15
            and all(not gap.strip() for gap in gaps)
            and all(fields[index].strip() for index in (0, 1, 2))
            and all(len(part.split()) <= 1 for part in fields)
        )
    return False
