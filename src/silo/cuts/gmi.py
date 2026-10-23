"""Exact GMI derivation from an explicitly integer basic variable's tableau row.

No MIP/LP solver is imported. A row is xB=bbar-sum(a_j*z_j), z>=0. All tags
and affine coordinate maps are explicit. Returned cuts are NODE_LOCAL.
"""

from dataclasses import dataclass
from fractions import Fraction as F
from functools import wraps
from math import floor, isfinite

import numpy as np

from silo.core.enums import ConstraintSense
from silo.cuts.candidate import CutCandidate, CutMetadata, CutValidityScope
from silo.lp.tableau_view import GmiTableauRow
from silo.utils.rational import ProofBudget


def bounded_proof(function):
    @wraps(function)
    def checked(*args, budget=None, **kwargs):
        budget = ProofBudget() if budget is None else budget
        try:
            budget.charge()
            return function(*args, budget=budget, **kwargs)
        except (ValueError, OverflowError, ZeroDivisionError):
            return None

    return checked


def strings(values, budget):
    return [str(budget.guard(value)) for value in values]


def box_error(coefficients, exacts, lower, upper, budget):
    deltas, correction = [], F(0)
    for value, exact, lo, hi in zip(coefficients, exacts, lower, upper, strict=True):
        delta = budget.guard(F(value) - budget.guard(exact))
        deltas.append(delta)
        if delta:
            bound = lo if delta > 0 else hi
            if not isfinite(bound):
                raise ValueError("Outward conversion needs a finite error bound.")
            correction = budget.guard(correction + budget.guard(delta * F(float(bound))))
    return deltas, correction


@dataclass(frozen=True)
class ExactGmi:
    coefficients: tuple[F, ...]
    lower: F
    extended_coefficients: tuple[F, ...]
    fraction: F
    source: GmiTableauRow

    @bounded_proof
    def to_candidate(self, names, lower, upper, node_id, cut_number, *, budget):
        """Outward float relaxation over the node box; reject unbounded errors."""
        values = [float(budget.guard(v)) for v in self.coefficients]
        if not all(isfinite(v) and abs(v) <= 1e8 for v in values):
            return None
        _, correction = box_error(values, self.coefficients, lower, upper, budget)
        rhs_exact = budget.guard(self.lower + correction)
        rhs = float(rhs_exact)
        if not isfinite(rhs):
            return None
        if F(rhs) > rhs_exact:
            rhs = float(np.nextafter(rhs, -np.inf))
        if not any(values):
            return None
        return CutCandidate(
            dict(zip(names, values, strict=True)),
            ConstraintSense.GE,
            rhs,
            CutMetadata(
                "gmi",
                scope=CutValidityScope.NODE_LOCAL,
                cut_id=f"gmi_{node_id}_{cut_number}",
                node_id=node_id,
                message="Exact split/modular derivation; outward float box bound.",
            ),
        )

    @bounded_proof
    def proof(self, *, budget):
        coordinates = []
        for value in self.source.coordinates:
            budget.charge()
            coordinates.append(
                None
                if value is None
                else {
                    "key": value.key,
                    "constant": str(budget.guard(value.constant)),
                    "coefficients": strings(value.coefficients, budget),
                    "integer": value.integer,
                }
            )
        budget.charge(
            len(self.source.provenance)
            + len(self.source.basis_keys)
            + len(self.source.effective_box)
        )
        return {
            "kind": "gmi",
            "basic": self.source.basic_key,
            "bbar": str(budget.guard(self.source.rhs)),
            "fraction": str(budget.guard(self.fraction)),
            "a": strings(self.source.coefficients, budget),
            "integer_tags": [None if v is None else v.integer for v in self.source.coordinates],
            "alpha": strings(self.extended_coefficients, budget),
            "original_coefficients": strings(self.coefficients, budget),
            "original_lower": str(budget.guard(self.lower)),
            "scope": "node_local",
            "provenance": self.source.provenance,
            "basic_integer": self.source.basic_integer,
            "basis_keys": self.source.basis_keys,
            "effective_box": self.source.effective_box,
            "nonbasic_coordinates": coordinates,
        }

    @bounded_proof
    def float_proof(self, candidate, names, lower, upper, *, budget):
        coefficients = dict(candidate.coefficients)
        deltas, correction = box_error(
            [coefficients[name] for name in names], self.coefficients, lower, upper, budget
        )
        limit = budget.guard(self.lower + correction)
        if F(candidate.rhs) > limit:
            return None
        budget.charge(len(names))
        return {
            "coefficient_deltas": strings(deltas, budget),
            "minimum_box_error": str(correction),
            "box": [
                (name, str(lo), str(hi)) for name, lo, hi in zip(names, lower, upper, strict=True)
            ],
            "rhs_limit": str(limit),
            "float_rhs_exact": str(F(candidate.rhs)),
            "float_coefficients_exact": [str(F(coefficients[name])) for name in names],
        }


@bounded_proof
def derive_gmi(row: GmiTableauRow, variable_count: int, *, budget):
    if not row.basic_integer or len(row.coefficients) != len(row.coordinates):
        return None
    f0 = budget.guard(row.rhs - floor(budget.guard(row.rhs)))
    if f0 <= F(1, 10000000) or f0 >= 1 - F(1, 10000000):
        return None
    alphas, projected, constant = [], [F(0)] * variable_count, F(0)
    for a, coordinate in zip(row.coefficients, row.coordinates, strict=True):
        budget.guard(a)
        if coordinate is not None and coordinate.integer:
            fraction = budget.guard(a - floor(a))
            alpha = fraction if fraction <= f0 else f0 * (1 - fraction) / (1 - f0)
        else:
            alpha = a if a >= 0 else -f0 * a / (1 - f0)
        budget.guard(alpha)
        if alpha and coordinate is None:
            return None  # a free split cannot be uniquely projected
        if alpha < 0 or alpha > 100000000:
            return None
        alphas.append(alpha)
        if coordinate is not None:
            constant = budget.guard(constant + budget.guard(alpha * coordinate.constant))
            for j, value in enumerate(coordinate.coefficients):
                projected[j] = budget.guard(projected[j] + budget.guard(alpha * value))
    return ExactGmi(tuple(projected), budget.guard(f0 - constant), tuple(alphas), f0, row)
