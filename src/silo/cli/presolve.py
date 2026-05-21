import json
from pathlib import Path
from typing import Any

from silo.presolve import PresolveResult, PresolveWarning, ReductionRecord


def presolve_to_dict(model_path: str | Path, result: PresolveResult) -> dict[str, Any]:
    diagnostics = result.diagnostics
    return {
        "model_path": Path(model_path).as_posix(),
        "presolve": {
            "status": diagnostics.status.value,
            "changed": result.changed,
            "message": result.message,
            "removed_rows": list(diagnostics.removed_rows),
            "removed_variables": list(diagnostics.removed_variables),
            "fixed_variables": list(diagnostics.fixed_variables),
            "warnings": [_warning_to_dict(warning) for warning in diagnostics.warnings],
            "notes": list(diagnostics.notes),
        },
        "reductions": [
            _reduction_to_dict(reduction) for reduction in result.reductions
        ],
        "scaling": {
            "max_abs_coefficient": result.scaling.max_abs_coefficient,
            "min_abs_nonzero_coefficient": result.scaling.min_abs_nonzero_coefficient,
            "coefficient_ratio": result.scaling.coefficient_ratio,
            "max_abs_rhs": result.scaling.max_abs_rhs,
            "max_abs_objective": result.scaling.max_abs_objective,
            "warnings": [
                _warning_to_dict(warning) for warning in result.scaling.warnings
            ],
        },
    }


def presolve_to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_presolve_json(payload: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(presolve_to_json(payload), encoding="utf-8")


def _warning_to_dict(warning: PresolveWarning) -> dict[str, str | None]:
    return {
        "code": warning.code,
        "message": warning.message,
        "source": warning.source,
    }


def _reduction_to_dict(reduction: ReductionRecord) -> dict[str, Any]:
    return {
        "type": reduction.reduction_type.value,
        "target": reduction.target,
        "description": reduction.description,
        "data": {key: value for key, value in reduction.data},
    }
