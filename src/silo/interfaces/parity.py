from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite

PrimalValueItems = tuple[tuple[str, float], ...]


class BackendParityMatchStatus(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class BackendParityResult:
    backend_id: str
    status: str
    objective_value: float | None = None
    primal_values: Mapping[str, float] | Sequence[tuple[str, float]] = field(
        default_factory=tuple
    )
    tolerance_label: str = "python_reference_default"
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "backend_id", _normalize_label(self.backend_id, "backend id"))
        object.__setattr__(self, "status", _normalize_label(self.status, "result status"))
        object.__setattr__(
            self,
            "objective_value",
            _normalize_optional_float(self.objective_value, "objective value"),
        )
        object.__setattr__(self, "primal_values", _normalize_primal_values(self.primal_values))
        object.__setattr__(
            self,
            "tolerance_label",
            _normalize_label(self.tolerance_label, "tolerance label"),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


@dataclass(frozen=True)
class BackendParityOutcome:
    fixture_id: str
    reference_backend_id: str
    candidate_backend_id: str
    match_status: BackendParityMatchStatus | str
    tolerance_label: str = "python_reference_default"
    reason: str = "recorded"
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixture_id", _normalize_label(self.fixture_id, "fixture id"))
        object.__setattr__(
            self,
            "reference_backend_id",
            _normalize_label(self.reference_backend_id, "reference backend id"),
        )
        object.__setattr__(
            self,
            "candidate_backend_id",
            _normalize_label(self.candidate_backend_id, "candidate backend id"),
        )
        object.__setattr__(
            self,
            "match_status",
            _normalize_match_status(self.match_status),
        )
        object.__setattr__(
            self,
            "tolerance_label",
            _normalize_label(self.tolerance_label, "tolerance label"),
        )
        object.__setattr__(self, "reason", _normalize_label(self.reason, "parity reason"))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


def _normalize_match_status(
    value: BackendParityMatchStatus | str,
) -> BackendParityMatchStatus:
    if isinstance(value, BackendParityMatchStatus):
        return value
    try:
        return BackendParityMatchStatus(value)
    except ValueError as exc:
        raise ValueError(
            "match status must be a supported BackendParityMatchStatus value."
        ) from exc


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
        raise TypeError("primal values must be a mapping or sequence of pairs.")

    normalized: list[tuple[str, float]] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, Sequence) or isinstance(item, (str, bytes)):
            raise TypeError("primal value entries must be pairs.")
        if len(item) != 2:
            raise ValueError("primal value entries must contain two items.")
        variable_name = _normalize_label(item[0], "primal variable name")
        if variable_name in seen:
            raise ValueError("primal variable names must be unique.")
        value = _normalize_optional_float(item[1], "primal value")
        if value is None:
            raise ValueError("primal values must not be None.")
        normalized.append((variable_name, value))
        seen.add(variable_name)

    return tuple(sorted(normalized))


__all__ = [
    "BackendParityMatchStatus",
    "BackendParityOutcome",
    "BackendParityResult",
    "PrimalValueItems",
]
