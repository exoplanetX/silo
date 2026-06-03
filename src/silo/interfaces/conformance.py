from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

from silo.interfaces.python_reference import PYTHON_REFERENCE_BACKEND_ID

PrimalValueItems = tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class BackendConformanceFixture:
    fixture_id: str
    model_path: str
    expected_status: str
    expected_backend_id: str = PYTHON_REFERENCE_BACKEND_ID
    expected_objective_value: float | None = None
    expected_primal_values: Mapping[str, float] | Sequence[tuple[str, float]] = field(
        default_factory=tuple
    )
    tolerance_label: str = "python_reference_default"
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixture_id", _normalize_label(self.fixture_id, "fixture id"))
        object.__setattr__(self, "model_path", _normalize_label(self.model_path, "model path"))
        object.__setattr__(
            self,
            "expected_status",
            _normalize_label(self.expected_status, "expected status"),
        )
        object.__setattr__(
            self,
            "expected_backend_id",
            _normalize_label(self.expected_backend_id, "expected backend id"),
        )
        object.__setattr__(
            self,
            "expected_objective_value",
            _normalize_optional_float(
                self.expected_objective_value,
                "expected objective value",
            ),
        )
        object.__setattr__(
            self,
            "expected_primal_values",
            _normalize_primal_values(self.expected_primal_values),
        )
        object.__setattr__(
            self,
            "tolerance_label",
            _normalize_label(self.tolerance_label, "tolerance label"),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_optional_float(value: float | None, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric.")
    normalized = float(value)
    if not isfinite(normalized):
        raise ValueError(f"{label} must be finite.")
    return normalized


def _normalize_primal_values(
    values: Mapping[str, float] | Sequence[tuple[str, float]],
) -> PrimalValueItems:
    if isinstance(values, Mapping):
        items = tuple(values.items())
    elif isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        items = tuple(values)
    else:
        raise TypeError("expected primal values must be a mapping or sequence of pairs.")

    normalized: list[tuple[str, float]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes)):
            raise TypeError("expected primal value entries must be pairs.")
        if len(item) != 2:
            raise ValueError("expected primal value entries must contain two items.")
        variable_name = _normalize_label(item[0], "expected primal variable name")
        if variable_name in seen:
            raise ValueError("expected primal variable names must be unique.")
        value = _normalize_optional_float(item[1], "expected primal value")
        if value is None:
            raise ValueError("expected primal values must not be None.")
        normalized.append((variable_name, value))
        seen.add(variable_name)

    return tuple(sorted(normalized))


PYTHON_REFERENCE_LP_CONFORMANCE_FIXTURES: tuple[BackendConformanceFixture, ...] = (
    BackendConformanceFixture(
        fixture_id="lp-production-optimal",
        model_path="tests/fixtures/lp_small/production.json",
        expected_status="optimal",
        expected_objective_value=21.0,
        expected_primal_values={"x1": 2.0, "x2": 3.0},
    ),
    BackendConformanceFixture(
        fixture_id="lp-diet-minimize-unsupported",
        model_path="tests/fixtures/lp_small/diet.json",
        expected_status="error",
        message="Current Python reference LP solvers support maximization fixtures only.",
    ),
)


def python_reference_lp_conformance_fixtures() -> tuple[BackendConformanceFixture, ...]:
    return PYTHON_REFERENCE_LP_CONFORMANCE_FIXTURES


__all__ = [
    "BackendConformanceFixture",
    "PYTHON_REFERENCE_LP_CONFORMANCE_FIXTURES",
    "python_reference_lp_conformance_fixtures",
]
