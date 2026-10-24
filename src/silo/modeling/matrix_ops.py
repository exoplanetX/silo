"""Small matrix boundary over NumPy and explicitly selected SciPy sparse data.

Importing this module does not import SciPy. Dense callers keep their original
arrays; sparse callers receive canonical CSR/CSC and one-dimensional vectors.
"""

import numpy as np


def is_sparse(matrix):
    return hasattr(matrix, "tocsr") and hasattr(matrix, "indptr")


def sparse_module():
    """Load the optional matrix library only after sparse engine selection."""
    from scipy import sparse

    return sparse


def nnz(matrix):
    return int(matrix.nnz if is_sparse(matrix) else np.count_nonzero(matrix))


def vector(value):
    return np.asarray(value, dtype=float).reshape(-1)


def shape(matrix):
    return tuple(matrix.shape)


def all_finite(matrix):
    return bool(np.isfinite(matrix.data if is_sparse(matrix) else matrix).all())


def _operand(values, size):
    values = np.asarray(values, dtype=float)
    if values.shape != (size,):
        raise ValueError("Matrix operand must be a vector of the matching dimension.")
    return values


def matvec(matrix, values):
    return vector(matrix @ _operand(values, matrix.shape[1]))


def transposed_matvec(matrix, values):
    return vector(matrix.T @ _operand(values, matrix.shape[0]))


def abs_matvec(matrix, values):
    """Contribution scale abs(A) @ abs(x), retaining a one-dimensional result."""
    return vector(abs(matrix) @ np.abs(_operand(values, matrix.shape[1])))


def abs_transposed_matvec(matrix, values):
    return vector(abs(matrix).T @ np.abs(_operand(values, matrix.shape[0])))


def _positions(indices, size):
    positions = list(indices)
    if any(isinstance(i, bool) or not isinstance(i, int | np.integer) for i in positions):
        raise ValueError("Matrix positions must be integers.")
    if any(i < 0 or i >= size for i in positions):
        raise IndexError("Matrix position outside its dimension.")
    return positions


def select_rows(matrix, indices):
    return matrix[_positions(indices, matrix.shape[0]), :].copy()


def select_columns(matrix, indices):
    return matrix[:, _positions(indices, matrix.shape[1])].copy()


def delete_rows(matrix, indices):
    keep = np.ones(matrix.shape[0], dtype=bool)
    keep[_positions(indices, matrix.shape[0])] = False
    return select_rows(matrix, np.flatnonzero(keep))


def delete_columns(matrix, indices):
    keep = np.ones(matrix.shape[1], dtype=bool)
    keep[_positions(indices, matrix.shape[1])] = False
    return select_columns(matrix, np.flatnonzero(keep))


def extract_basis(matrix, columns):
    """Extract a square basis in the supplied semantic column order."""
    columns = _positions(columns, matrix.shape[1])
    if len(columns) != matrix.shape[0] or len(set(columns)) != len(columns):
        raise ValueError("Basis needs one distinct column per row.")
    return select_columns(matrix, columns)


def row_support(matrix, row):
    if is_sparse(matrix):
        csr = matrix if matrix.format == "csr" else matrix.tocsr()
        start, stop = csr.indptr[row : row + 2]
        return csr.indices[start:stop], csr.data[start:stop]
    values = matrix[row]
    indices = np.flatnonzero(values)
    return indices, values[indices]


def column_support(matrix, column):
    if is_sparse(matrix):
        csc = matrix if matrix.format == "csc" else matrix.tocsc()
        start, stop = csc.indptr[column : column + 2]
        return csc.indices[start:stop], csc.data[start:stop]
    values = matrix[:, column]
    indices = np.flatnonzero(values)
    return indices, values[indices]


def append_rows(matrix, rows):
    """Append existing numeric rows, preserving matrix representation/order."""
    if is_sparse(matrix):
        sparse = sparse_module()
        additions = [
            r if is_sparse(r) else sparse.csr_matrix(np.asarray(r).reshape(1, -1)) for r in rows
        ]
        return sparse.vstack([matrix, *additions], format=matrix.format)
    return np.vstack([matrix, *rows])


def append_columns(matrix, columns):
    """Append column vectors in order, retaining ndarray, CSR or CSC format."""
    if is_sparse(matrix):
        sparse = sparse_module()
        additions = [
            c if is_sparse(c) else sparse.csc_matrix(_operand(c, matrix.shape[0])[:, None])
            for c in columns
        ]
        return sparse.hstack([matrix, *additions], format=matrix.format)
    additions = [_operand(column, matrix.shape[0]) for column in columns]
    return np.column_stack([matrix, *additions])


def unit_columns(matrix, rows, values=None):
    """Create signed unit columns with the same row count and representation."""
    rows = _positions(rows, matrix.shape[0])
    values = np.ones(len(rows)) if values is None else _operand(values, len(rows))
    if not np.isfinite(values).all():
        raise ValueError("Unit column coefficients must be finite.")
    if is_sparse(matrix):
        sparse = sparse_module()
        return sparse.coo_matrix(
            (values, (rows, np.arange(len(rows)))), shape=(matrix.shape[0], len(rows))
        ).asformat(matrix.format)
    result = np.zeros((matrix.shape[0], len(rows)))
    result[rows, np.arange(len(rows))] = values
    return result


def append_unit_columns(matrix, rows, values=None):
    units = unit_columns(matrix, rows, values)
    if is_sparse(matrix):
        return sparse_module().hstack([matrix, units], format=matrix.format)
    return np.hstack([matrix, units])


def _scales(values, size):
    values = _operand(values, size)
    if not np.isfinite(values).all() or np.any(values <= 0):
        raise ValueError("Matrix scaling must be positive and finite.")
    return values


def scale_rows(matrix, scales):
    scales = _scales(scales, matrix.shape[0])
    if is_sparse(matrix):
        return matrix.multiply(scales[:, None]).asformat(matrix.format)
    return scales[:, None] * matrix


def scale_columns(matrix, scales):
    scales = _scales(scales, matrix.shape[1])
    if is_sparse(matrix):
        return matrix.multiply(scales).asformat(matrix.format)
    return matrix * scales


def coefficient_identity(matrix):
    """Immutable actual coefficients, with zero removal and canonical indices."""
    if is_sparse(matrix):
        csr = matrix.tocsr(copy=True)
        csr.sum_duplicates()
        csr.eliminate_zeros()
        csr.sort_indices()
        return (
            csr.shape,
            csr.dtype.str,
            tuple(map(int, csr.indptr)),
            tuple(map(int, csr.indices)),
            tuple(map(float, csr.data)),
        )
    return matrix.shape, matrix.dtype.str, tuple(map(tuple, matrix))


def row_max_abs(matrix):
    if not is_sparse(matrix):
        return np.max(np.abs(matrix), axis=1, initial=0)
    csr = matrix.tocsr(copy=False)
    result = np.zeros(csr.shape[0])
    np.maximum.at(result, np.repeat(np.arange(csr.shape[0]), np.diff(csr.indptr)), np.abs(csr.data))
    return result


def column_max_abs(matrix):
    if not is_sparse(matrix):
        return np.max(np.abs(matrix), axis=0, initial=0)
    csr = matrix.tocsr(copy=False)
    result = np.zeros(csr.shape[1])
    np.maximum.at(result, csr.indices, np.abs(csr.data))
    return result
