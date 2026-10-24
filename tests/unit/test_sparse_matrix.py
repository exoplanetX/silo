"""Sparse affine maps and activity provenance, without an optimizer reference."""

import subprocess
import sys
from math import inf
from pathlib import Path

import numpy as np
import pytest

from silo.io import model_from_dict
from silo.modeling import matrix_ops
from silo.modeling.general import IndexedAffine, linear_data, normalize
from silo.presolve.activity import propagate

pytest.importorskip("scipy")


def mixed():
    return model_from_dict(
        {
            "name": "mixed-affine",
            "sense": "maximize",
            "variables": [
                {"name": "f", "lower": 2, "upper": 2},
                {"name": "x", "lower": -2, "upper": 5},
                {"name": "r", "lower": None, "upper": 3},
                {"name": "w", "lower": None, "upper": None},
            ],
            "objective": {"constant": 7, "coefficients": {"f": 2, "x": 3, "r": -4, "w": 5}},
            "constraints": [
                {
                    "name": "interval",
                    "coefficients": {"f": 2, "x": 3, "r": -4, "w": 5},
                    "lower": -7,
                    "upper": 11,
                },
                {"name": "eq", "coefficients": {"x": 1, "w": 1}, "sense": "=", "rhs": 1},
                {"name": "free", "coefficients": {"r": 1}, "lower": None, "upper": None},
                {"name": "zero", "coefficients": {}, "sense": "=", "rhs": 0},
            ],
        }
    )


@pytest.mark.parametrize("scaling", [False, True])
def test_sparse_affine_map_matches_dense_and_never_densifies(monkeypatch, scaling):
    from scipy.sparse import csc_matrix, csr_matrix

    model = mixed()
    dense = linear_data(model)
    expected = normalize(dense, dense.lower, dense.upper, scaling)

    def forbidden(*args, **kwargs):
        raise AssertionError("Global sparse-to-dense conversion")

    monkeypatch.setattr(csr_matrix, "toarray", forbidden)
    monkeypatch.setattr(csc_matrix, "toarray", forbidden)
    data = linear_data(model, 0, engine="sparse")
    result = normalize(data, data.lower, data.upper, scaling)
    assert isinstance(result.transform, IndexedAffine)
    assert result.row_keys == expected.row_keys
    assert result.column_origins == expected.column_origins
    assert result.matrix.shape == expected.matrix.shape
    for i in range(expected.matrix.shape[0]):
        indices, values = matrix_ops.row_support(result.matrix, i)
        reconstructed = np.zeros(expected.matrix.shape[1])
        reconstructed[indices] = values
        np.testing.assert_array_equal(reconstructed, expected.matrix[i])
    for field in ("offset", "rhs", "costs", "row_scale", "col_scale"):
        np.testing.assert_array_equal(getattr(result, field), getattr(expected, field))
    z = np.arange(len(result.costs), dtype=float) + 0.25
    np.testing.assert_array_equal(result.point(z), expected.point(z))
    np.testing.assert_array_equal(result.ray(z), expected.ray(z))
    np.testing.assert_array_equal(result.transform.T @ dense.c, expected.transform.T @ dense.c)
    lam, rc = np.arange(len(result.rhs), dtype=float), np.arange(len(result.costs), dtype=float)
    for got, want in zip(result.multipliers(lam, rc), expected.multipliers(lam, rc), strict=True):
        np.testing.assert_array_equal(got, want)


def test_sparse_input_gate_precedes_matrix_allocation(monkeypatch):
    def forbidden():
        raise AssertionError("Library loaded before sparse input gate")

    monkeypatch.setattr("silo.modeling.general.sparse_module", forbidden)
    with pytest.raises(MemoryError, match="max_sparse_nnz"):
        linear_data(mixed(), engine="sparse", max_sparse_nnz=1)


@pytest.mark.parametrize("bound", [False, True])
def test_affine_expansion_and_upper_row_gates(bound):
    payload = {
        "variables": [{"name": "x", "lower": 0 if bound else None, "upper": 1 if bound else None}],
        "constraints": [{"name": "r", "coefficients": {"x": 1}, "lower": -1, "upper": 1}],
        "objective": {"coefficients": {}},
    }
    data = linear_data(model_from_dict(payload), engine="sparse", max_sparse_nnz=2)
    with pytest.raises(MemoryError, match="max_sparse_nnz"):
        normalize(data, data.lower, data.upper)


def test_sparse_activity_matches_dense_and_recovers_original_sources():
    model = model_from_dict(
        {
            "variables": [{"name": "x"}, {"name": "y"}],
            "constraints": [{"name": "sum", "coefficients": {"x": 1, "y": 1}, "rhs": 4}],
            "objective": {"coefficients": {}},
        }
    )
    data = linear_data(model, engine="sparse")
    result = propagate(data)
    reference = propagate(linear_data(model))
    np.testing.assert_array_equal(result.lower, [0, 0])
    np.testing.assert_array_equal(result.upper, [4, 4])
    assert result.history == reference.history
    recovered = result.recover_multipliers(
        (np.zeros(1), np.zeros(1), np.zeros(2), np.array([1.0, 0]))
    )
    for got, want in zip(recovered, ([0], [1], [0, 1], [0, 0]), strict=True):
        np.testing.assert_array_equal(got, want)


def test_sparse_activity_unbounded_contribution_can_exclude_its_own_variable():
    model = model_from_dict(
        {
            "variables": [{"name": "x", "lower": None}, {"name": "y", "lower": 1, "upper": 2}],
            "constraints": [{"name": "r", "coefficients": {"x": 1, "y": 1}, "rhs": 4}],
            "objective": {"coefficients": {}},
        }
    )
    data = linear_data(model, engine="sparse")
    result = propagate(data)
    assert result.lower[0] == -inf and result.upper[0] == 3
    assert result.upper[1] == 2


def test_matrix_append_identity_and_nonzero_views():
    from scipy.sparse import csr_matrix

    matrix = csr_matrix([[1, 0], [0, 2]], dtype=float)
    extended = matrix_ops.append_rows(matrix, [(3.0, 0.0)])
    assert extended.format == "csr" and extended.shape == (3, 2)
    assert matrix_ops.nnz(extended) == 3
    indices, values = matrix_ops.column_support(extended, 0)
    np.testing.assert_array_equal(indices, [0, 2])
    np.testing.assert_array_equal(values, [1, 3])
    identity = matrix_ops.coefficient_identity(extended)
    matrix.data[0] = 99
    assert matrix_ops.coefficient_identity(extended) == identity
    assert isinstance(matrix_ops.append_rows(np.eye(2), [(3.0, 0.0)]), np.ndarray)


def test_default_modeling_import_does_not_load_scipy():
    root = Path(__file__).resolve().parents[2]
    code = (
        f"import sys;sys.path.insert(0,{str(root / 'src')!r});"
        "import silo.modeling.general;assert 'scipy' not in sys.modules"
    )
    subprocess.run([sys.executable, "-I", "-c", code], check=True, timeout=10)


@pytest.mark.parametrize("kind", ["dense", "csr", "csc"])
def test_complete_matrix_boundary_preserves_format_order_and_vectors(monkeypatch, kind):
    from scipy.sparse import csc_matrix, csr_matrix

    original = np.array([[2.0, 0, -1], [0, 3, 4]])
    matrix = (
        original.copy()
        if kind == "dense"
        else {"csr": csr_matrix, "csc": csc_matrix}[kind](original)
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("Structural operation densified a sparse model")

    monkeypatch.setattr(csr_matrix, "toarray", forbidden)
    monkeypatch.setattr(csc_matrix, "toarray", forbidden)

    def same(result, expected):
        expected = np.asarray(expected, dtype=float)
        assert result.shape == expected.shape
        if kind == "dense":
            assert isinstance(result, np.ndarray)
            np.testing.assert_array_equal(result, expected)
        else:
            assert result.format == kind
            for row in range(expected.shape[0]):
                indices, values = matrix_ops.row_support(result, row)
                reconstructed = np.zeros(expected.shape[1])
                reconstructed[indices] = values
                np.testing.assert_array_equal(reconstructed, expected[row])

    assert matrix_ops.shape(matrix) == (2, 3) and matrix_ops.all_finite(matrix)
    for result, expected in (
        (matrix_ops.matvec(matrix, [1, 2, 3]), [-1, 18]),
        (matrix_ops.transposed_matvec(matrix, [5, -1]), [10, -3, -9]),
        (matrix_ops.abs_matvec(matrix, [-1, 2, -3]), [5, 18]),
        (matrix_ops.abs_transposed_matvec(matrix, [-5, 1]), [10, 3, 9]),
    ):
        assert isinstance(result, np.ndarray) and result.ndim == 1
        np.testing.assert_array_equal(result, expected)
    same(matrix_ops.extract_basis(matrix, [2, 0]), [[-1, 2], [4, 0]])
    same(matrix_ops.select_rows(matrix, [1, 0]), original[[1, 0]])
    same(matrix_ops.select_columns(matrix, [2, 0]), original[:, [2, 0]])
    same(matrix_ops.delete_rows(matrix, [0]), original[[1]])
    same(matrix_ops.delete_columns(matrix, [1]), original[:, [0, 2]])
    same(matrix_ops.delete_rows(matrix, [0, 1]), np.empty((0, 3)))
    same(matrix_ops.delete_columns(matrix, [0, 1, 2]), np.empty((2, 0)))
    same(matrix_ops.append_rows(matrix, [(1, 2, 3)]), [[2, 0, -1], [0, 3, 4], [1, 2, 3]])
    same(matrix_ops.append_columns(matrix, [(1, 2), (3, 4)]), [[2, 0, -1, 1, 3], [0, 3, 4, 2, 4]])
    same(matrix_ops.unit_columns(matrix, [1, 0], [-1, 1]), [[0, 1], [-1, 0]])
    same(
        matrix_ops.append_unit_columns(matrix, [1, 0], [-1, 1]),
        [[2, 0, -1, 0, 1], [0, 3, 4, -1, 0]],
    )
    same(matrix_ops.scale_rows(matrix, [2, 0.5]), [[4, 0, -2], [0, 1.5, 2]])
    same(matrix_ops.scale_columns(matrix, [0.5, 2, 4]), [[1, 0, -4], [0, 6, 16]])
    same(matrix_ops.append_columns(matrix, []), original)
    same(matrix, original)


@pytest.mark.parametrize("kind", ["dense", "csr", "csc"])
def test_matrix_boundary_rejects_wrong_vectors_indices_and_scales(kind):
    from scipy.sparse import csc_matrix, csr_matrix

    matrix = (
        np.eye(2) if kind == "dense" else {"csr": csr_matrix, "csc": csc_matrix}[kind](np.eye(2))
    )
    with pytest.raises(ValueError, match="vector"):
        matrix_ops.matvec(matrix, [[1], [2]])
    with pytest.raises(ValueError, match="distinct"):
        matrix_ops.extract_basis(matrix, [0, 0])
    with pytest.raises(IndexError):
        matrix_ops.select_rows(matrix, [-1])
    with pytest.raises(ValueError, match="integers"):
        matrix_ops.select_columns(matrix, [0.5])
    for scale in ([1, 0], [1, -1], [1, np.nan]):
        with pytest.raises(ValueError, match="positive"):
            matrix_ops.scale_rows(matrix, scale)
    changed = matrix.copy()
    if kind == "dense":
        changed[0, 0] = np.nan
    else:
        changed.data[0] = np.nan
    assert not matrix_ops.all_finite(changed)
