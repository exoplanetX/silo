from dataclasses import dataclass

from silo.interfaces.backend import BackendAvailabilityStatus

TABLEAU_RATIO_NATIVE_BACKEND_ID = "native-ratio-test"
TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID = "tableau_leaving_row_ratio_test"
TABLEAU_RATIO_NATIVE_TOLERANCE_LABEL = "python_reference_default"


@dataclass(frozen=True)
class TableauRatioNativeDiagnostic:
    diagnostic_id: str
    candidate_id: str
    backend_id: str
    availability_status: BackendAvailabilityStatus | str
    reason: str | None = None
    tolerance_label: str = TABLEAU_RATIO_NATIVE_TOLERANCE_LABEL
    message: str = ""

    def __post_init__(self) -> None:
        status = _normalize_availability_status(self.availability_status)

        object.__setattr__(
            self,
            "diagnostic_id",
            _normalize_label(self.diagnostic_id, "diagnostic id"),
        )
        object.__setattr__(
            self,
            "candidate_id",
            _normalize_label(self.candidate_id, "candidate id"),
        )
        object.__setattr__(
            self,
            "backend_id",
            _normalize_label(self.backend_id, "backend id"),
        )
        object.__setattr__(self, "availability_status", status)
        object.__setattr__(self, "reason", _normalize_reason(self.reason, status))
        object.__setattr__(
            self,
            "tolerance_label",
            _normalize_label(self.tolerance_label, "tolerance label"),
        )
        object.__setattr__(self, "message", _normalize_label(self.message, "message"))


def _normalize_availability_status(
    value: BackendAvailabilityStatus | str,
) -> BackendAvailabilityStatus:
    if isinstance(value, BackendAvailabilityStatus):
        return value
    if isinstance(value, bool):
        raise TypeError("availability status must be a supported value.")
    try:
        return BackendAvailabilityStatus(value)
    except ValueError as exc:
        raise ValueError("availability status must be a supported value.") from exc


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_reason(
    value: str | None,
    status: BackendAvailabilityStatus,
) -> str | None:
    if value is None:
        if status in (
            BackendAvailabilityStatus.UNAVAILABLE,
            BackendAvailabilityStatus.UNSUPPORTED,
        ):
            raise ValueError("unavailable or unsupported diagnostics require a reason.")
        return None

    return _normalize_label(value, "reason")


TABLEAU_RATIO_NATIVE_DIAGNOSTICS = (
    TableauRatioNativeDiagnostic(
        diagnostic_id="ratio-test-native-unavailable",
        candidate_id=TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID,
        backend_id=TABLEAU_RATIO_NATIVE_BACKEND_ID,
        availability_status=BackendAvailabilityStatus.UNAVAILABLE,
        reason="optional_native_runtime_not_installed",
        message=(
            "Optional native runtime for tableau_leaving_row_ratio_test is not installed."
        ),
    ),
    TableauRatioNativeDiagnostic(
        diagnostic_id="ratio-test-native-unsupported",
        candidate_id=TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID,
        backend_id=TABLEAU_RATIO_NATIVE_BACKEND_ID,
        availability_status=BackendAvailabilityStatus.UNSUPPORTED,
        reason="native_ratio_test_implementation_not_approved",
        message=(
            "Native tableau_leaving_row_ratio_test implementation is not approved."
        ),
    ),
)


def tableau_ratio_native_diagnostics() -> tuple[TableauRatioNativeDiagnostic, ...]:
    return TABLEAU_RATIO_NATIVE_DIAGNOSTICS


__all__ = [
    "TABLEAU_RATIO_NATIVE_BACKEND_ID",
    "TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID",
    "TABLEAU_RATIO_NATIVE_DIAGNOSTICS",
    "TABLEAU_RATIO_NATIVE_TOLERANCE_LABEL",
    "TableauRatioNativeDiagnostic",
    "tableau_ratio_native_diagnostics",
]
