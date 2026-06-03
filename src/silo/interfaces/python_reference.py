from silo.interfaces.backend import (
    BackendAvailability,
    BackendAvailabilityStatus,
    BackendCapability,
    BackendKind,
)

PYTHON_REFERENCE_BACKEND_ID = "python-reference"

PYTHON_REFERENCE_CAPABILITY = BackendCapability(
    backend_id=PYTHON_REFERENCE_BACKEND_ID,
    kind=BackendKind.PYTHON_REFERENCE,
    problem_families=("continuous_lp", "mixed_integer_linear"),
    variable_types=("continuous", "binary", "integer"),
    constraint_senses=("<=", ">=", "="),
    diagnostics=(
        "status",
        "objective_value",
        "primal_values",
        "slack_values",
        "reduced_costs",
        "basis_status",
        "node_log",
    ),
    tolerance_label="python_reference_default",
)

PYTHON_REFERENCE_AVAILABILITY = BackendAvailability(
    backend_id=PYTHON_REFERENCE_BACKEND_ID,
    kind=BackendKind.PYTHON_REFERENCE,
    status=BackendAvailabilityStatus.AVAILABLE,
    message="Python reference backend records are available without optional native code.",
)


def python_reference_backend_records() -> tuple[BackendCapability, BackendAvailability]:
    return (PYTHON_REFERENCE_CAPABILITY, PYTHON_REFERENCE_AVAILABILITY)


__all__ = [
    "PYTHON_REFERENCE_AVAILABILITY",
    "PYTHON_REFERENCE_BACKEND_ID",
    "PYTHON_REFERENCE_CAPABILITY",
    "python_reference_backend_records",
]
