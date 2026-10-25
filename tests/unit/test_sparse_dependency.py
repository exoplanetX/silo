"""A floating proposal can delete a row only after a bounded exact sparse proof."""

from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy.sparse import csc_matrix, csr_matrix  # noqa: E402

from silo import SolveOptions  # noqa: E402
from silo.lp import sparse_dependency as sd  # noqa: E402
from silo.lp import sparse_kernel as sk
from silo.utils.rational import ProofBudget, ProofLimitError  # noqa: E402


def problem(raw, rhs, scales=None, origins=None, offset=None):
    raw = csr_matrix(raw, dtype=float)
    q, n = raw.shape
    origins = tuple(origins or [(i, 1) for i in range(n)])
    scales = np.ones(q) if scales is None else np.array(scales, dtype=float)
    offset = np.zeros(n) if offset is None else np.array(offset, dtype=float)
    rows = tuple(("row", f"r{i}", "equal") for i in range(q))
    data = SimpleNamespace(
        names=tuple(f"x{i}" for i in range(n)), row_names=tuple(f"r{i}" for i in range(q)),
        a=raw, row_lower=np.array(rhs, dtype=float), row_upper=np.array(rhs, dtype=float),
    )
    normalized = raw[:, [i for i, _ in origins]].multiply([d for _, d in origins])
    model = SimpleNamespace(
        data=data, matrix=normalized.multiply(scales[:, None]).tocsr(),
        rhs=scales * (np.array(rhs, dtype=float) - raw @ offset), costs=np.zeros(len(origins)),
        senses=("=",) * q, column_origins=origins, row_keys=rows,
        row_scale=scales, col_scale=np.ones(len(origins)), offset=offset, upper=np.full(n, np.inf),
    )
    matrix, _, _, basis, _, keys, _ = sk._standard(model, SolveOptions())
    basis[0] = 0
    return model, matrix, basis, rows, keys


@pytest.mark.parametrize(
    "raw,rhs,scales,origins,offset",
    [
        ([[1], [2]], [1, 2], [0.5, 0.25], None, None),
        ([[1], [-2]], [1, -2], [0.5, 0.25], None, None),
        ([[1, 3], [4, 6]], [7, 16], [0.5, 0.25], [(1, -1)], [1, 2]),
        ([[1], [2]], [1, 2], [1, 1], [(0, 1), (0, -1)], None),
    ],
)
def test_exact_relation_handles_flips_scale_offset_fixed_and_split(
    raw, rhs, scales, origins, offset
):
    model, matrix, basis, rows, keys = problem(raw, rhs, scales, origins, offset)
    witness = np.linalg.solve(matrix[:, basis].toarray().T, [0, 1])
    budget = ProofBudget()
    assert sd.prove_dependency(model, matrix, basis, rows, keys, 1, witness, budget)
    assert 0 < budget.peak_cells <= 2 * len(rows) + 2 * len(model.data.names) + 32
    assert budget.live_cells == 0


def test_small_nonzero_binary_coefficient_is_not_an_exact_dependency():
    model, matrix, basis, rows, keys = problem([[1, 1], [2, 2 + 2.0**-39]], [1, 2])
    witness = np.linalg.solve(matrix[:, basis].toarray().T, [0, 1])
    assert not sd.prove_dependency(model, matrix, basis, rows, keys, 1, witness, ProofBudget())


def test_slack_column_prevents_a_false_structural_only_proof():
    model, _, _, rows, _ = problem([[1], [1]], [2, 2])
    model.senses = ("<=", "=")
    model.row_keys = (("bound", "x0", "upper"), rows[1])
    model.upper[0] = 2
    matrix, _, _, basis, _, keys, _ = sk._standard(model, SolveOptions())
    basis[0] = 0
    witness = np.array([-1.0, 1.0])
    assert not sd.prove_dependency(
        model, matrix, basis, model.row_keys, keys, 1, witness, ProofBudget()
    )


def test_other_basic_artificial_support_must_have_zero_weight():
    model, matrix, _, rows, keys = problem([[1], [1]], [1, 1])
    assert not sd.prove_dependency(model, matrix, [1, 2], rows, keys, 1, [-1, 1], ProofBudget())


@pytest.mark.parametrize("witness", [[-0.9, 1], [float("nan"), 1], [-1, 0]])
def test_bad_or_unrecoverable_proposal_is_never_accepted(witness):
    model, matrix, basis, rows, keys = problem([[1], [1]], [1, 1])
    assert not sd.prove_dependency(model, matrix, basis, rows, keys, 1, witness, ProofBudget())


def test_large_relation_keeps_linear_workspace_and_never_densifies(monkeypatch):
    model, matrix, basis, rows, keys = problem(np.ones((976, 1)), np.ones(976))

    def forbidden(*args, **kwargs):
        raise AssertionError("Dense proof matrix requested")

    monkeypatch.setattr(csc_matrix, "toarray", forbidden)
    witness = np.zeros(976)
    witness[0], witness[1] = -1, 1
    budget = ProofBudget()
    assert sd.prove_dependency(model, matrix, basis, rows, keys, 1, witness, budget)
    assert budget.peak_cells == 1986 and budget.live_cells == 0


def test_operation_limit_is_checked_before_fraction_containers(monkeypatch):
    model, matrix, basis, rows, keys = problem([[1], [1]], [1, 1])

    def forbidden(*args, **kwargs):
        raise AssertionError("Fraction allocated before budget preflight")

    monkeypatch.setattr(sd, "Fraction", forbidden)
    with pytest.raises(ProofLimitError):
        sd.prove_dependency(model, matrix, basis, rows, keys, 1, [-1, 1], ProofBudget(operations=0))


def test_exact_workspace_ceiling_can_be_used_without_a_dense_basis():
    model, matrix, basis, rows, keys = problem(np.ones((32751, 1)), np.ones(32751))
    witness = np.zeros(32751)
    witness[0], witness[1] = -1, 1
    budget = ProofBudget()
    assert sd.prove_dependency(model, matrix, basis, rows, keys, 1, witness, budget)
    assert budget.peak_cells == 65536 and budget.live_cells == 0


def test_excess_workspace_is_rejected_before_any_fraction(monkeypatch):
    model, matrix, basis, rows, keys = problem(np.ones((32752, 1)), np.ones(32752))
    witness = np.zeros(32752)
    witness[0], witness[1] = -1, 1

    def forbidden(*args, **kwargs):
        raise AssertionError("Rational allocation above the unchanged65536-cell ceiling")

    monkeypatch.setattr(sd, "Fraction", forbidden)
    budget = ProofBudget()
    with pytest.raises(ProofLimitError, match="65536"):
        sd.prove_dependency(model, matrix, basis, rows, keys, 1, witness, budget)
    assert budget.peak_cells == budget.live_cells == 0
