from dataclasses import dataclass

from silo.interfaces.backend import (
    BackendAvailability,
    BackendAvailabilityStatus,
    BackendCapability,
    BackendKind,
)
from silo.interfaces.python_reference import (
    PYTHON_REFERENCE_AVAILABILITY,
    PYTHON_REFERENCE_BACKEND_ID,
    PYTHON_REFERENCE_CAPABILITY,
)

NO_FALLBACK_POLICY = "no_fallback"
DEFAULT_PYTHON_REFERENCE_REASON = "default_python_reference"
REQUESTED_PYTHON_REFERENCE_REASON = "requested_python_reference"
UNSUPPORTED_BACKEND_REASON = "unsupported_backend_id"

BackendSelectionPayload = tuple[
    BackendCapability | None,
    BackendAvailability,
    "BackendSelectionDecision",
]


@dataclass(frozen=True)
class BackendSelectionRequest:
    requested_backend_id: str | None = None
    fallback_policy: str = NO_FALLBACK_POLICY

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requested_backend_id",
            _normalize_optional_label(self.requested_backend_id, "requested backend id"),
        )
        object.__setattr__(
            self,
            "fallback_policy",
            _normalize_label(self.fallback_policy, "fallback policy"),
        )


@dataclass(frozen=True)
class BackendSelectionDecision:
    selected_backend_id: str
    selected_kind: BackendKind | str
    availability_status: BackendAvailabilityStatus | str
    fallback_policy: str = NO_FALLBACK_POLICY
    reason: str = DEFAULT_PYTHON_REFERENCE_REASON
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "selected_backend_id",
            _normalize_label(self.selected_backend_id, "selected backend id"),
        )
        object.__setattr__(self, "selected_kind", _normalize_backend_kind(self.selected_kind))
        object.__setattr__(
            self,
            "availability_status",
            _normalize_availability_status(self.availability_status),
        )
        object.__setattr__(
            self,
            "fallback_policy",
            _normalize_label(self.fallback_policy, "fallback policy"),
        )
        object.__setattr__(self, "reason", _normalize_label(self.reason, "selection reason"))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


def select_backend(
    request: BackendSelectionRequest | None = None,
) -> BackendSelectionPayload:
    normalized_request = _normalize_request(request)
    if normalized_request.requested_backend_id is None:
        return _python_reference_payload(
            fallback_policy=normalized_request.fallback_policy,
            reason=DEFAULT_PYTHON_REFERENCE_REASON,
        )
    if normalized_request.requested_backend_id == PYTHON_REFERENCE_BACKEND_ID:
        return _python_reference_payload(
            fallback_policy=normalized_request.fallback_policy,
            reason=REQUESTED_PYTHON_REFERENCE_REASON,
        )

    availability = BackendAvailability(
        backend_id=normalized_request.requested_backend_id,
        kind=BackendKind.NATIVE_EXPERIMENTAL,
        status=BackendAvailabilityStatus.UNSUPPORTED,
        reason=UNSUPPORTED_BACKEND_REASON,
        message=(
            "No-op backend selector does not dispatch to non-Python-reference "
            "backends."
        ),
    )
    decision = BackendSelectionDecision(
        selected_backend_id=availability.backend_id,
        selected_kind=availability.kind,
        availability_status=availability.status,
        fallback_policy=normalized_request.fallback_policy,
        reason=UNSUPPORTED_BACKEND_REASON,
        message=availability.message,
    )
    return (None, availability, decision)


def _python_reference_payload(
    *,
    fallback_policy: str,
    reason: str,
) -> BackendSelectionPayload:
    decision = BackendSelectionDecision(
        selected_backend_id=PYTHON_REFERENCE_AVAILABILITY.backend_id,
        selected_kind=PYTHON_REFERENCE_AVAILABILITY.kind,
        availability_status=PYTHON_REFERENCE_AVAILABILITY.status,
        fallback_policy=fallback_policy,
        reason=reason,
        message=PYTHON_REFERENCE_AVAILABILITY.message,
    )
    return (PYTHON_REFERENCE_CAPABILITY, PYTHON_REFERENCE_AVAILABILITY, decision)


def _normalize_request(request: BackendSelectionRequest | None) -> BackendSelectionRequest:
    if request is None:
        return BackendSelectionRequest()
    if not isinstance(request, BackendSelectionRequest):
        raise TypeError("backend selection request must be a BackendSelectionRequest.")
    return request


def _normalize_backend_kind(value: BackendKind | str) -> BackendKind:
    if isinstance(value, BackendKind):
        return value
    try:
        return BackendKind(value)
    except ValueError as exc:
        raise ValueError("selected kind must be a supported BackendKind value.") from exc


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


def _normalize_optional_label(value: str | None, label: str) -> str | None:
    if value is None:
        return None
    return _normalize_label(value, label)


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


__all__ = [
    "DEFAULT_PYTHON_REFERENCE_REASON",
    "NO_FALLBACK_POLICY",
    "REQUESTED_PYTHON_REFERENCE_REASON",
    "UNSUPPORTED_BACKEND_REASON",
    "BackendSelectionDecision",
    "BackendSelectionPayload",
    "BackendSelectionRequest",
    "select_backend",
]
