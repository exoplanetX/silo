"""Static dependency checks distinguish sparse linear algebra from optimizers."""

import importlib.util
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "module,source,allowed",
    [
        ("lp/sample", "from scipy.sparse import csc_matrix,hstack", True),
        ("lp/sample", "from scipy.sparse.linalg import splu", True),
        ("modeling/matrix_ops", "from scipy import sparse", True),
        ("lp/sample", "import scipy", False),
        ("lp/sample", "from scipy import sparse", False),
        ("lp/sample", "from scipy.optimize import linprog", False),
        ("lp/sample", "from scipy import optimize", False),
        ("lp/sample", "from scipy.sparse.csgraph import maximum_flow", False),
        ("core/sample", "from scipy.sparse import csc_matrix", False),
    ],
)
def test_numeric_import_exception_stays_narrow(tmp_path, module, source, allowed):
    path = Path(__file__).resolve().parents[2] / "scripts/check_project_structure.py"
    spec = importlib.util.spec_from_file_location("sparse_structure_policy", path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    sample = tmp_path / "src/silo" / (module + ".py")
    sample.parent.mkdir(parents=True)
    sample.write_text(source, encoding="utf-8")
    errors = []
    checker.check_imports(tmp_path, errors)
    assert bool(errors) != allowed
