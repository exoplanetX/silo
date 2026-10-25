"""Mathematical selector invariants, independent of any capacity oracle."""

from fractions import Fraction

import numpy as np
import pytest

from silo.lp.sparse_ratio import leaving_order


def safe(direction, position, tolerance):
    return abs(direction[position]) > tolerance * (1 + np.max(abs(direction), initial=0))


def order(x, d, keys=None, primal=1e-7, pivot=1e-10):
    x, d = np.asarray(x, dtype=float), np.asarray(d, dtype=float)
    return leaving_order(x, d, keys or tuple((str(i),) for i in range(len(x))), primal, pivot, safe)


def test_stable_nonminimum_row_closes_exact_tie_gap():
    result = order([0, 1e-8], [1e-12, 1])
    assert result.positive == (0, 1) and result.rows == (1,)
    rho = Fraction.from_float(1e-8)
    y = (-rho * Fraction.from_float(1e-12), rho)
    assert float(min(y)) >= -1e-7 * (1 + max(map(abs, map(float, y))))
    assert result.strict_minimum == 0 < float(rho) < result.window


def test_tiny_positive_blocker_limits_window_even_when_new_norm_would_hide_violation():
    # The stable row would amplify the negative-direction coordinate and make
    # a new-norm-only tolerance enormous. The old-scale window must forbid it.
    result = order([0, 1, 1], [1e-6, 2e-5, -1e5])
    assert result.positive == (0, 1) and result.rows == ()
    assert result.window == pytest.approx(64 * np.finfo(np.float64).eps / 1e-6)
    rho = 1 / 2e-5
    y = np.array([0, 1, 1]) - rho * np.array([1e-6, 2e-5, -1e5])
    y[1] = rho
    assert min(y) < -result.allowance
    assert min(y) >= -1e-7 * (1 + max(abs(y)))


def test_different_actual_ratios_use_stable_pivot_then_semantic_tie():
    result = order([1, 1 + 1e-15], [1, 1], keys=(("z",), ("a",)))
    assert result.rows == (1, 0)  # The ratios are deliberately not equal.


@pytest.mark.parametrize("d", [[0, 0], [-1, -2], [-1e-300, 0]])
def test_only_empty_positive_set_has_no_blocker(d):
    result = order([0, 1], d)
    assert result.positive == result.rows == ()


def test_positive_overflow_ratio_still_has_a_blocker():
    tiny = np.nextafter(0.0, 1.0)
    result = order([1], [tiny])
    assert result.positive == (0,) and result.rows == () and result.window == float("inf")


def test_positive_headroom_sum_does_not_spuriously_overflow_before_division():
    maximum = np.finfo(np.float64).max
    result = order([maximum], [maximum])
    assert result.positive == result.rows == (0,)
    assert np.isfinite(result.window) and 1 <= result.window < 1 + 1e-12


@pytest.mark.parametrize("negative", [-2e-7, -1e-7, -1e-15])
def test_existing_tolerated_deficit_has_nonnegative_row_headroom(negative):
    result = order([negative, 1], [1, 0])
    assert result.rows == (0,) and result.window >= 0
    if negative == -2e-7:
        assert result.window == 0


def test_unrelated_large_basic_coordinate_cannot_erase_tiny_real_blocker():
    result = order([0, 1e4], [1e-8, 1e4])
    assert result.positive == (0, 1) and result.rows == ()
    assert result.window == pytest.approx(64 * np.finfo(np.float64).eps / 1e-8)
    assert result.window < 1  # Independent exact LP optimum remains0.


@pytest.mark.parametrize(
    "x,d", [([np.nan], [1]), ([0], [np.nan]), ([0], [np.inf]), ([np.inf], [1])]
)
def test_nonfinite_state_or_direction_cannot_be_an_empty_blocker_ray(x, d):
    with pytest.raises(np.linalg.LinAlgError, match="Nonfinite"):
        order(x, d)


def test_nonfinite_allowance_is_failure():
    with pytest.raises(np.linalg.LinAlgError, match="allowance"):
        order([2], [1], primal=1e308)


def test_negative_actual_rho_is_not_clamped_by_candidate_ordering():
    result = order([-1e-15, 0], [1, -2e8], pivot=1e-12)
    assert result.rows == (0,)
    actual_rho = -1e-15
    y = np.array([-1e-15, 0]) - actual_rho * np.array([1, -2e8])
    y[0] = actual_rho
    assert min(y) < -1e-7 * (1 + max(abs(y)))
    # Membership is a proposal; the unchanged raw-coordinate gate rejects it.


@pytest.mark.parametrize("x,d", [([1, 2, 3], [1, -2, 0.25]), ([0, 1, 2], [1e-12, 1, -1])])
def test_nonnegative_actual_step_window_bounds_all_nonleaving_coordinates(x, d):
    result = order(x, d)
    for row in result.rows:
        xf, df = list(map(Fraction, x)), list(map(Fraction, d))
        rho = xf[row] / df[row]
        assert rho >= 0
        for i in range(len(x)):
            if i != row:
                assert float(xf[i] - rho * df[i]) >= -result.allowance - 1e-15


def test_current_infeasibility_requires_recovery_before_ratio():
    with pytest.raises(np.linalg.LinAlgError, match="current feasible"):
        order([-1], [1])


def test_shape_error_remains_a_programming_error():
    with pytest.raises(ValueError, match="dimensions"):
        order([1], [1, 2])
