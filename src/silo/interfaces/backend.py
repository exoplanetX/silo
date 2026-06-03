from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum


class BackendKind(str, Enum):
    PYTHON_REFERENCE = "python_reference"
    NATIVE_EXPERIMENTAL = "native_experimental"


class BackendAvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class BackendCapability:
    backend_id: str
    kind: BackendKind | str
    problem_families: Sequence[str] = ()
    variable_types: Sequence[str] = ()
    constraint_senses: Sequence[str] = ()
    diagnostics: Sequence[str] = ()
    tolerance_label: str = "default"

    def __post_init__(self) -> None:
        object.__setattr__(self, "backend_id", _normalize_label(self.backend_id, "backend id"))
        object.__setattr__(self, "kind", _normalize_backend_kind(self.kind))
        object.__setattr__(
            self,
            "problem_families",
            _normalize_unique_labels(self.problem_families, "problem families"),
        )
        object.__setattr__(
            self,
            "variable_types",
            _normalize_unique_labels(self.variable_types, "variable types"),
        )
        object.__setattr__(
            self,
            "constraint_senses",
            _normalize_unique_labels(self.constraint_senses, "constraint senses"),
        )
        object.__setattr__(
            self,
            "diagnostics",
            _normalize_unique_labels(self.diagnostics, "diagnostics"),
        )
        object.__setattr__(
            self,
            "tolerance_label",
            _normalize_label(self.tolerance_label, "tolerance label"),
        )


@dataclass(frozen=True)
class BackendAvailability:
    backend_id: str
    kind: BackendKind | str
    status: BackendAvailabilityStatus | str
    reason: str | None = None
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "backend_id", _normalize_label(self.backend_id, "backend id"))
        object.__setattr__(self, "kind", _normalize_backend_kind(self.kind))
        status = _normalize_availability_status(self.status)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "reason", _normalize_optional_reason(self.reason, status))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


def _normalize_backend_kind(value: BackendKind | str) -> BackendKind:
    if isinstance(value, BackendKind):
        return value
    try:
        return BackendKind(value)
    except ValueError as exc:
        raise ValueError("backend kind must be a supported BackendKind value.") from exc


def _normalize_availability_status(
    value: BackendAvailabilityStatus | str,
) -> BackendAvailabilityStatus:
    if isinstance(value, BackendAvailabilityStatus):
        return value
    try:
        return BackendAvailabilityStatus(value)
    except ValueError as exc:
        raise ValueError(
            "availability status must be a supported BackendAvailabilityStatus value."
        ) from exc


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_unique_labels(values: Sequence[str], label: str) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise TypeError(f"{label} must be a sequence of strings.")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _normalize_label(value, f"{label} entry")
        if item in seen:
            raise ValueError(f"{label} must not contain duplicate entries.")
        normalized.append(item)
        seen.add(item)
    return tuple(normalized)


def _normalize_optional_reason(
    value: str | None,
    status: BackendAvailabilityStatus,
) -> str | None:
    if value is None:
        if status in (
            BackendAvailabilityStatus.UNAVAILABLE,
            BackendAvailabilityStatus.UNSUPPORTED,
        ):
            raise ValueError("unavailable or unsupported backends require a reason.")
        return None

    return _normalize_label(value, "availability reason")


__all__ = [
    "BackendAvailability",
    "BackendAvailabilityStatus",
    "BackendCapability",
    "BackendKind",
]
