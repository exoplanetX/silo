"""Large objective translations and opt-in preservation of numerical gates."""

from fractions import Fraction as F
from itertools import product
from math import fsum, inf, nextafter, ulp

import pytest

from silo.core.enums import ConstraintSense as S
from silo.decomposition import dag_column_generation as cg
from silo.decomposition.dag_pricing import DagArc, DagPricingProblem, DagPricingResult

from .test_dag_cg_reoptimization_oracles import (
    MODES,
    Trace,
    audit_result,
    full_cold_references,
    original_paths,
    run_mode,
    square_problem,
    vertex_value,
)

CONSTANTS = (0, 2**40, -2**40, 2**60, -2**60)
CASES = list(product(range(6), (False, True), CONSTANTS))


@pytest.mark.parametrize('k,reverse,constant', CASES)
def test_translated_objectives_keep_low_order_evidence(k, reverse, constant, monkeypatch):
    p, optimum = square_problem(k, F(1, 2), F(1, 2), 0, reverse, constant)
    data = original_paths(p.graph)
    assert vertex_value(p, data) == optimum
    full_cold_references(p, data, optimum)
    for mode in MODES:
        with monkeypatch.context() as patch:
            trace = Trace(patch)
            result = run_mode(p, mode)
            audit_result(p, result, data, optimum, mode == 'warm-revised')
            trace.audit(result, mode == 'warm-revised')


def one_path(cost=0, other=None, constant=0):
    arcs = [DagArc('seed', 's', 't', cost)]
    if other is not None:
        arcs.append(DagArc('other', 's', 't', other))
    graph = DagPricingProblem(('s', 't'), arcs, 's', 't', ('conv',),
                              base_coefficients={'conv': 1})
    return cg.DagColumnGenerationProblem(graph, [cg.DagMasterRow('conv', S.EQ, 1)],
                                         'conv', [('seed',)], constant)


@pytest.mark.parametrize('cost,expected', ((-1e-9, 'TOLERANCE_REACHED'),
    (-.9e-9, 'TOLERANCE_REACHED'), (-1.1e-9, 'ITERATION_LIMIT')))
def test_opt_in_keeps_strict_rho_threshold_on_real_data(cost, expected):
    result = cg.solve_dag_column_generation(one_path(other=cost), reoptimize_rmp=True,
                                            iteration_limit=1)
    record = result.iterations[0]
    assert result.status == getattr(cg.DagColumnGenerationStatus, expected)
    assert record.rho == cost and record.objective_gap == -cost
    assert record.rmp_reoptimization is not None and record.accepted_path is None


def test_large_c0_can_hide_a_real_gap_without_changing_the_signed_gap():
    result = cg.solve_dag_column_generation(one_path(other=-1, constant=2**60),
                                            reoptimize_rmp=True, iteration_limit=1)
    record = result.iterations[0]
    assert record.numerical_gap == 0 and record.objective_gap == 1
    assert result.status == cg.DagColumnGenerationStatus.ITERATION_LIMIT


@pytest.mark.parametrize('gap,scale,accepted', ((-ulp(2.), 1., True),
    (-32*ulp(2.), 1., True), (-33*ulp(2.), 1., False),
    (-1e-10, 2**40, False), (1e-9, 1., True),
    (nextafter(1e-9, inf), 1., False)))
def test_injected_signed_gap_boundary_uses_original_rule(monkeypatch, gap, scale, accepted):
    def objective(*args):
        # Two cancelling terms set the local scale independently of the gap.
        return 0., 0., (scale, -scale, gap), ()

    monkeypatch.setattr(cg, '_master_objectives', objective)
    result = cg.solve_dag_column_generation(one_path(), reoptimize_rmp=True)
    record = result.iterations[0]
    assert result.status == (cg.DagColumnGenerationStatus.TOLERANCE_REACHED if accepted else
                             cg.DagColumnGenerationStatus.NUMERICAL_ISSUE)
    assert record.rmp_reoptimization is not None
    if accepted:
        assert record.objective_gap == gap
        assert record.roundoff_allowance == 32*ulp(fsum((scale, scale, abs(gap))))
    else:
        assert record.objective_gap is record.roundoff_allowance is None


@pytest.mark.parametrize('where', ('product', 'sum'))
def test_nonfinite_reconstruction_keeps_diagnostics_and_valid_history(monkeypatch, where):
    if where == 'product':
        def overflow(*args):
            # Synthetic source terms exercise the unchanged finite-product gate.
            return cg._product(1e308, 2)
        monkeypatch.setattr(cg, '_master_objectives', overflow)
    else:
        monkeypatch.setattr(cg, '_master_objectives', lambda *a: (0, 0, (1e308, 1e308), ()))
    result = cg.solve_dag_column_generation(one_path(), reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert result.iterations[0].rmp_reoptimization is not None
    assert result.last_valid_master_iteration == (None if where == 'product' else 1)


def test_existing_significantly_negative_path_remains_a_failure(monkeypatch):
    monkeypatch.setattr(cg, '_master_objectives', lambda *a: (0, 0, (0,), ()))
    monkeypatch.setattr(cg, '_check_candidate', lambda *a: (('seed',), 0, {'conv': 1}, -1))
    result = cg.solve_dag_column_generation(one_path(), reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert 'already existing' in result.message
    assert result.iterations[0].objective_gap is None


def test_pricing_numerical_status_fails_after_valid_rmp(monkeypatch):
    from silo.decomposition.dag_pricing import DagPricingStatus

    monkeypatch.setattr(cg, 'price_dag', lambda *a, **kw:
                        DagPricingResult(DagPricingStatus.NUMERICAL_ISSUE))
    result = cg.solve_dag_column_generation(one_path(), reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.PRICING_FAILURE
    assert result.last_valid_master_iteration == 1
