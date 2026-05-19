import pytest

from silo.lp.simplex.basis import BASIC, NONBASIC_LOWER, Basis


def test_basis_validate_accepts_valid_basis() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 1))

    basis.validate(column_count=3, row_count=1)


def test_basis_validate_rejects_duplicate_basic_columns() -> None:
    basis = Basis(basic_columns=(2, 2), nonbasic_columns=(0, 1))

    with pytest.raises(ValueError, match="duplicate basic"):
        basis.validate(column_count=3, row_count=2)


def test_basis_validate_rejects_duplicate_nonbasic_columns() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 0))

    with pytest.raises(ValueError, match="duplicate nonbasic"):
        basis.validate(column_count=3, row_count=1)


def test_basis_validate_rejects_overlapping_columns() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 2))

    with pytest.raises(ValueError, match="overlap"):
        basis.validate(column_count=3, row_count=1)


def test_basis_validate_rejects_missing_columns() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0,))

    with pytest.raises(ValueError, match="missing columns"):
        basis.validate(column_count=3, row_count=1)


def test_basis_validate_rejects_out_of_range_columns() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 1, 3))

    with pytest.raises(ValueError, match="out-of-range"):
        basis.validate(column_count=3, row_count=1)


def test_basis_validate_rejects_wrong_basic_count() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 1, 3))

    with pytest.raises(ValueError, match="one basic column per row"):
        basis.validate(column_count=4, row_count=2)


def test_basis_reports_basic_membership_and_status() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 1))

    assert basis.is_basic(2)
    assert not basis.is_basic(1)
    assert basis.status_for_column(2) == BASIC
    assert basis.status_for_column(1) == NONBASIC_LOWER


def test_basis_status_rejects_unknown_column() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 1))

    with pytest.raises(ValueError, match="not present"):
        basis.status_for_column(3)


def test_basis_pivot_replaces_leaving_basic_column() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 1))

    new_basis = basis.pivot(leaving_row=0, entering_column=0)

    assert new_basis.basic_columns == (0,)
    assert new_basis.nonbasic_columns == (1, 2)
    assert basis.basic_columns == (2,)
    assert basis.nonbasic_columns == (0, 1)


def test_basis_pivot_preserves_deterministic_nonbasic_ordering() -> None:
    basis = Basis(basic_columns=(3, 4), nonbasic_columns=(0, 1, 2))

    new_basis = basis.pivot(leaving_row=1, entering_column=1)

    assert new_basis.basic_columns == (3, 1)
    assert new_basis.nonbasic_columns == (0, 2, 4)


def test_basis_pivot_rejects_invalid_leaving_row() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 1))

    with pytest.raises(ValueError, match="Invalid leaving row"):
        basis.pivot(leaving_row=1, entering_column=0)


def test_basis_pivot_rejects_basic_entering_column() -> None:
    basis = Basis(basic_columns=(2,), nonbasic_columns=(0, 1))

    with pytest.raises(ValueError, match="not nonbasic"):
        basis.pivot(leaving_row=0, entering_column=2)
