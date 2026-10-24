"""Dependency evidence only: no SILO solve and no external optimizer calls."""

import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from .ledger import CONTRACT, ROOT, environment, identity


def inspect():
    import numpy as np
    import scipy
    from scipy.sparse import csc_matrix
    from scipy.sparse.linalg import splu

    assert scipy.__version__ == "1.16.3"
    assert sys.version_info >= (3, 11)
    assert (1, 25, 2) <= tuple(map(int, np.__version__.split(".")[:3])) < (2, 6, 0)
    matrix = csc_matrix([[2.0, 1.0], [0.0, 3.0]])
    lu = splu(matrix)
    for transpose in (False, True):
        rhs = (matrix.T if transpose else matrix) @ np.array([1.0, 2.0])
        result = lu.solve(rhs, trans="T" if transpose else "N")
        assert np.max(np.abs(result - [1, 2])) < 1e-14
    uv = shutil.which("uv")
    python311 = None
    if uv is not None:
        found = subprocess.run(
            [uv, "python", "find", "3.11"], capture_output=True, text=True, timeout=30, check=False
        )
        if found.returncode == 0:
            python311 = found.stdout.strip()
    return {
        "contract": CONTRACT,
        "environment": environment(),
        "identity": identity(),
        "sparse_dependency": {
            "scipy": scipy.__version__,
            "requires": importlib.metadata.requires("scipy"),
            "lu_forward_transpose": "passed",
        },
        "uv": uv,
        "python311": python311,
        "python313": sys.executable,
        "windows": platform.system() == "Windows",
        "native_solver_calls": 0,
        "external_optimizer_calls": 0,
        "threads_are_one": all(
            os.environ.get(n) == "1"
            for n in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        ),
    }


def main(output):
    result = inspect()
    Path(output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "preflight": "passed",
                "python311": result["python311"],
                "native_solver_calls": 0,
                "repository": str(ROOT),
            }
        )
    )
