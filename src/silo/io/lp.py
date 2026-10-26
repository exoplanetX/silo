"""Strict SILO-LP-1 linear text reader/writer; see docs/lp_format.md."""

import re
from fractions import Fraction
from math import inf, isfinite
from pathlib import Path

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.io.number_codec import numeric, spelling, text_number

_ALIASES = {
    "minimize": "min", "minimum": "min", "min": "min",
    "maximize": "max", "maximum": "max", "max": "max",
    "subject to": "rows", "such that": "rows", "st": "rows", "s.t.": "rows", "s.t": "rows",
    "bounds": "bounds", "bound": "bounds",
    "generals": "integer", "general": "integer", "gen": "integer",
    "integers": "integer", "integer": "integer",
    "binaries": "binary", "binary": "binary", "bin": "binary", "end": "end",
}
_RESERVED = {word for alias in _ALIASES for word in alias.split()} | {
    "free", "inf", "infinity", "nan", "sos", "semi", "semicontinuous", "semiinteger",
}
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*\Z", re.ASCII)
_TOKEN = re.compile(
    r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|"
    r"[A-Za-z_][A-Za-z0-9_.]*|<=|>=|=|:|\+|-", re.ASCII
)
_NUMBER = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z", re.ASCII)


def _name(value):
    if not isinstance(value, str) or not _NAME.fullmatch(value) or value.lower() in _RESERVED:
        raise ValueError(f"Invalid or reserved LP identifier: {value}")
    return value


def _tokens(text):
    result, end = [], 0
    for match in _TOKEN.finditer(text):
        if text[end:match.start()].strip():
            raise ValueError("Unsupported LP syntax")
        if (end == match.start() and result and _NUMBER.fullmatch(result[-1])
                and _NAME.fullmatch(match[0])):
            raise ValueError("Invalid LP number or missing term whitespace")
        result.append(match[0])
        end = match.end()
    if text[end:].strip():
        raise ValueError("Unsupported LP syntax")
    return result


def _signed(tokens, index, *, infinite=False):
    sign = 1
    if index < len(tokens) and tokens[index] in ("+", "-"):
        sign = -1 if tokens[index] == "-" else 1
        index += 1
    if index >= len(tokens):
        raise ValueError("Truncated LP number")
    token = tokens[index]
    if infinite and token.lower() in ("inf", "infinity"):
        return sign * inf, index + 1
    if not _NUMBER.fullmatch(token):
        raise ValueError(f"Invalid LP number: {token}")
    value = sign * text_number(token)
    # Validate individual tokens too: do not hide overflow/underflow by cancellation.
    numeric(value)
    return value, index + 1


def _expression(tokens, index, register, stop=()):
    coefficients, constant, first = {}, Fraction(0), True
    while index < len(tokens) and tokens[index] not in stop:
        sign = 1
        if tokens[index] in ("+", "-"):
            sign = -1 if tokens[index] == "-" else 1
            index += 1
        elif not first:
            raise ValueError("LP terms require a separating sign")
        if index >= len(tokens) or tokens[index] in stop:
            raise ValueError("Truncated LP expression")
        token = tokens[index]
        if _NUMBER.fullmatch(token):
            value, index = _signed(tokens, index)
            value *= sign
            if index < len(tokens) and _NAME.fullmatch(tokens[index]):
                name = _name(tokens[index])
                register(name)
                coefficients[name] = coefficients.get(name, Fraction(0)) + value
                index += 1
            else:
                constant += value
        else:
            name = _name(token)
            register(name)
            coefficients[name] = coefficients.get(name, Fraction(0)) + sign
            index += 1
        first = False
    if first:
        raise ValueError("Empty LP expression")
    return coefficients, constant, index


def parse_lp(text: str) -> Model:
    """Parse the frozen SILO-LP-1 subset, rejecting unsupported constructs."""
    if not isinstance(text, str):
        raise ValueError("LP input must be text")
    sections, section, order = {}, None, -1
    ranks = {"min": 0, "max": 0, "rows": 1, "bounds": 2, "integer": 3, "binary": 4, "end": 5}
    for raw in text.splitlines():
        line = raw.split("\\", 1)[0].strip()
        if not line:
            continue
        if section == "end":
            raise ValueError("LP data after End")
        header = _ALIASES.get(" ".join(line.lower().split()))
        if header is not None:
            if header in sections or ranks[header] <= order:
                raise ValueError("Duplicate or out-of-order LP section")
            sections[header], section, order = [], header, ranks[header]
        elif section is None:
            raise ValueError("LP objective section required first")
        else:
            sections[section].append(line)
    if "end" not in sections or "rows" not in sections or not ({"min", "max"} & sections.keys()):
        raise ValueError("Truncated LP: objective, Subject To and End required")
    columns = {}

    def register(name):
        columns.setdefault(_name(name), {"lower": 0, "upper": inf, "sides": set(),
                                         "type": VariableType.CONTINUOUS})

    sense = "min" if "min" in sections else "max"
    tokens = _tokens(" ".join(sections[sense]))
    if len(tokens) >= 2 and tokens[1] == ":":
        _name(tokens[0])
        tokens = tokens[2:]
    coefficients, constant, end = _expression(tokens, 0, register)
    assert end == len(tokens)
    model = Model(name="lp_model")
    model.set_objective(Objective(
        {k: numeric(v) for k, v in coefficients.items()},
        OptimizationSense.MINIMIZE if sense == "min" else OptimizationSense.MAXIMIZE,
        numeric(constant),
    ))
    tokens = _tokens(" ".join(sections["rows"]))
    explicit = set()
    for i, token in enumerate(tokens[:-1]):
        if tokens[i + 1] == ":":
            name = _name(token)
            if name in explicit:
                raise ValueError(f"Duplicate LP row: {name}")
            explicit.add(name)
    used, index, unnamed = set(explicit), 0, 0
    while index < len(tokens):
        if index + 1 < len(tokens) and tokens[index + 1] == ":":
            name, index = tokens[index], index + 2
        else:
            unnamed += 1
            while f"row_{unnamed}" in used:
                unnamed += 1
            name = f"row_{unnamed}"
            used.add(name)
        coefficients, constant, index = _expression(tokens, index, register, ("<=", ">=", "="))
        if index >= len(tokens):
            raise ValueError("Truncated LP constraint")
        relation, index = tokens[index], index + 1
        rhs, index = _signed(tokens, index)
        model.add_constraint(Constraint(name, {k: numeric(v) for k, v in coefficients.items()},
                                        relation, numeric(rhs - constant)))
    for line in sections.get("bounds", []):
        tokens = _tokens(line)
        if len(tokens) == 2 and tokens[1].lower() == "free":
            name, lower, upper = _name(tokens[0]), -inf, inf
            specified = {"lower", "upper"}
        elif tokens and _NAME.fullmatch(tokens[0]) and tokens[0].lower() not in ("inf", "infinity"):
            name = _name(tokens[0])
            if len(tokens) < 3 or tokens[1] not in ("<=", ">=", "="):
                raise ValueError("Invalid LP bound")
            value, end = _signed(tokens, 2, infinite=True)
            if end != len(tokens):
                raise ValueError("Invalid LP bound suffix")
            specified = ({"lower", "upper"} if tokens[1] == "=" else
                         {"lower"} if tokens[1] == ">=" else {"upper"})
            lower = upper = value
        else:
            value, end = _signed(tokens, 0, infinite=True)
            if end + 1 >= len(tokens) or tokens[end] not in ("<=", ">="):
                raise ValueError("Invalid LP bound")
            relation, name = tokens[end], _name(tokens[end + 1])
            end += 2
            if end == len(tokens):
                specified = {"lower"} if relation == "<=" else {"upper"}
                lower = upper = value
            else:
                if relation != "<=" or tokens[end] != "<=":
                    raise ValueError("Invalid two-sided LP bound")
                lower, (upper, end) = value, _signed(tokens, end + 1, infinite=True)
                if end != len(tokens):
                    raise ValueError("Invalid LP bound suffix")
                specified = {"lower", "upper"}
        register(name)
        column = columns[name]
        if column["sides"] & specified:
            raise ValueError(f"Duplicate LP bound side: {name}")
        column["sides"].update(specified)
        for side, value in (("lower", lower), ("upper", upper)):
            if side in specified:
                column[side] = value if isinstance(value, float) and not isfinite(value) \
                    else numeric(value)
    typed = set()
    for section, typ in (("integer", VariableType.INTEGER), ("binary", VariableType.BINARY)):
        for name in _tokens(" ".join(sections.get(section, []))):
            register(name)
            if name in typed:
                raise ValueError(f"Duplicate or conflicting LP domain: {name}")
            typed.add(name)
            columns[name]["type"] = typ
    if not columns:
        raise ValueError("Unsupported LP zero-variable model")
    for name, column in columns.items():
        lower, upper = column["lower"], column["upper"]
        if lower == inf or upper == -inf:
            raise ValueError("Invalid LP infinite bound direction")
        if column["type"] == VariableType.BINARY:
            lower, upper = max(0, lower), min(1, upper)
        model.add_variable(Variable(name, Bounds(lower, upper), column["type"]))
    model.validate()
    return model


def read_lp_model(path: str | Path) -> Model:
    """Read a UTF-8 SILO-LP-1 model."""
    return parse_lp(Path(path).read_text(encoding="utf-8"))


def _fresh(base, used):
    name, index = base, 1
    while name in used:
        name = f"{base}_{index}"
        index += 1
    used.add(name)
    return name


def _sum(coefficients, constant=0):
    # Include zeros to preserve variable identity, including all-zero columns.
    terms = [f"{'-' if value < 0 else '+'} {spelling(abs(value))} {name}"
             for name, value in coefficients.items()]
    if constant != 0 or not terms:
        terms.append(f"{'-' if constant < 0 else '+'} {spelling(abs(constant))}")
    return " ".join(terms).removeprefix("+ ")


def model_to_lp(model: Model) -> str:
    """Serialize without dropping data; split interval sides deterministically."""
    model.validate()
    if not model.variables:
        raise ValueError("Unsupported LP zero-variable model")
    for name in model.variable_names() + [r.name for r in model.constraints]:
        _name(name)
    used = set(model.variable_names()) | {r.name for r in model.constraints}
    rows = []
    for row in model.constraints:
        lo, hi = row.row_bounds
        if lo == -inf and hi == inf:
            raise ValueError("Unsupported LP completely free row")
        if lo == hi:
            rows.append((row.name, row.coefficients, "=", lo))
        elif isfinite(lo) and isfinite(hi):
            rows.append((_fresh(row.name + "__lower", used), row.coefficients, ">=", lo))
            rows.append((_fresh(row.name + "__upper", used), row.coefficients, "<=", hi))
        elif isfinite(lo):
            rows.append((row.name, row.coefficients, ">=", lo))
        else:
            rows.append((row.name, row.coefficients, "<=", hi))
    objective = {v.name: model.objective.coefficients.get(v.name, 0) for v in model.variables}
    label_names = set(model.variable_names()) | {name for name, _, _, _ in rows}
    lines = ["Minimize" if model.objective.sense == OptimizationSense.MINIMIZE else "Maximize",
             f" {_fresh('obj', label_names)}: {_sum(objective, model.objective.constant)}",
             "Subject To"]
    for name, coefficients, relation, rhs in rows:
        lines.append(f" {name}: {_sum(coefficients)} {relation} {spelling(rhs)}")
    lines.append("Bounds")
    for v in model.variables:
        lo, hi = v.bounds.lower, v.bounds.upper
        if lo == hi:
            lines.append(f" {v.name} = {spelling(lo)}")
        elif lo == -inf and hi == inf:
            lines.append(f" {v.name} free")
        else:
            lower = "-inf" if lo == -inf else spelling(lo)
            upper = "+inf" if hi == inf else spelling(hi)
            lines.append(f" {lower} <= {v.name} <= {upper}")
    for typ, section in ((VariableType.INTEGER, "Generals"), (VariableType.BINARY, "Binaries")):
        names = [v.name for v in model.variables if v.var_type == typ]
        if names:
            lines.extend([section, " " + " ".join(names)])
    lines.append("End")
    return "\n".join(lines) + "\n"


def write_lp_model(model: Model, path: str | Path) -> None:
    """Validate and serialize completely before opening the output file."""
    text = model_to_lp(model)
    Path(path).write_text(text, encoding="utf-8")
