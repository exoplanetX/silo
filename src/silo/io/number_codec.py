"""Exact text accumulation followed by the declared LP numeric conversion gate."""

from decimal import Decimal, InvalidOperation
from fractions import Fraction
from math import isfinite


def text_number(token: str) -> Fraction:
    """Check the finite/underflow boundary before allocating a rational power."""
    try:
        decimal = Decimal(token)
        value = float(decimal)
    except (InvalidOperation, OverflowError, ValueError) as exc:
        raise ValueError("Invalid LP number") from exc
    if not isfinite(value) or (decimal and value == 0):
        raise ValueError("Invalid LP number: nonfinite or nonzero underflow")
    result = Fraction(decimal)
    numeric(result)
    return result


def numeric(value: Fraction) -> int | float:
    """Reject nonfinite, lost integers and nonzero underflow before model creation."""
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError("Invalid LP number: expected finite binary64 value") from exc
    if not isfinite(result) or (value and result == 0):
        raise ValueError("Invalid LP number: nonfinite or nonzero underflow")
    if value.denominator == 1:
        if Fraction(result) != value:
            raise ValueError("Invalid LP number: integer not exactly representable")
        return value.numerator
    return result


def spelling(value) -> str:
    """Print actual integer-valued floats, avoiding a different decimal integer."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("Invalid LP number")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("Invalid LP number: expected finite value")
    numeric(Fraction(value))
    return str(int(value)) if isinstance(value, int) or value.is_integer() else repr(value)
