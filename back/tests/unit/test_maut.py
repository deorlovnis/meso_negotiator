"""Unit tests for MAUT utility computation.

Error categories targeted:
- Computation errors: off-by-one, floating-point precision, operator precedence
- Boundary errors: walk-away = 0.0, target = 1.0, clamping at [0, 1]
- Interface errors: wrong argument order, missing terms, weight validation

Source spec: core-loop.feature section 14.
Architecture ref: ARCHITECTURE.md domain/maut.py contract.

Formula under test:
    U(offer) = sum_i( w_i * clamp( (value_i - walkaway_i) / (target_i - walkaway_i), 0, 1 ) )
"""

from __future__ import annotations

import pytest

from back.domain.maut import compute_utility
from back.domain.types import TermConfig, TermValues, Weights

# ---------------------------------------------------------------------------
# Test data: the Background configuration from core-loop.feature
# ---------------------------------------------------------------------------

BACKGROUND_CONFIG = {
    "price": TermConfig(opening=11.50, target=12.50, walk_away=14.50, weight=0.40),
    "payment": TermConfig(opening=90, target=75, walk_away=30, weight=0.25),
    "delivery": TermConfig(opening=7, target=10, walk_away=14, weight=0.20),
    "contract": TermConfig(opening=6, target=12, walk_away=24, weight=0.15),
}

OPERATOR_WEIGHTS = Weights(price=0.40, payment=0.25, delivery=0.20, contract=0.15)


class TestMautBoundaryValues:
    """Falsifiable claim: utility is exactly 0.0 at walk-away, exactly 1.0 at target.

    These are the highest-risk boundary tests. If clamping is off by one
    direction or the formula denominator is inverted, these fail.
    """

    def test_all_terms_at_walk_away_gives_zero(self):
        """section 14: 'MAUT utility is 0.0 when all terms are at walk-away values'

        Walk-away values: $14.50, Net 30, 14 days, 24 months.
        Every per-term achievement should be 0.0, so weighted sum is 0.0.
        """
        terms = TermValues(price=14.50, payment=30, delivery=14, contract=24)
        result = compute_utility(terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
        assert result == 0.0, f"Expected 0.0 at walk-away, got {result}"

    def test_all_terms_at_target_gives_one(self):
        """section 14: 'MAUT utility is 1.0 when all terms are at target values'

        Target values: $12.50, Net 75, 10 days, 12 months.
        Every per-term achievement should be 1.0, so weighted sum is 1.0.
        """
        terms = TermValues(price=12.50, payment=75, delivery=10, contract=12)
        result = compute_utility(terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
        assert result == 1.0, f"Expected 1.0 at target, got {result}"

    def test_values_beyond_target_are_clamped_to_one(self):
        """Adversarial: values better than target should clamp achievement to 1.0.

        If clamping is missing, achievement > 1.0 inflates utility.
        Price $10.00 is better-than-target for operator (lower is better for them
        to offer to supplier? No -- lower price is worse for operator revenue).

        Correction: per the spec, target is the ideal for the operator.
        Price target = $12.50 (operator wants lower price offered to supplier).
        Walk-away = $14.50 (worst the operator would accept).
        A value of $11.00 is better-than-target, achievement should clamp to 1.0.
        """
        terms = TermValues(price=11.00, payment=90, delivery=7, contract=6)
        result = compute_utility(terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
        assert result == 1.0, (
            f"Values beyond target should clamp to 1.0 achievement, got {result}"
        )

    def test_values_beyond_walk_away_are_clamped_to_zero(self):
        """Adversarial: values worse than walk-away should clamp achievement to 0.0.

        If clamping is missing, achievement < 0.0 drags utility negative.
        Price $16.00 is worse than walk-away $14.50.
        """
        terms = TermValues(price=16.00, payment=20, delivery=18, contract=30)
        result = compute_utility(terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
        assert result == 0.0, (
            f"Values beyond walk-away should clamp to 0.0, got {result}"
        )


class TestMautConcreteFormula:
    """Falsifiable claim: MAUT = sum(weight_i * achievement_i).

    Concrete numeric verification from section 14 scenario.
    """

    def test_section14_concrete_verification(self):
        """section 14: offer at $13.50, Net 45, 12 days, 18 months.

        Per-term achievement:
            price:    (13.50 - 14.50) / (12.50 - 14.50) = -1.00 / -2.00 = 0.50
            payment:  (45 - 30) / (75 - 30) = 15 / 45 = 0.3333...
            delivery: (12 - 14) / (10 - 14) = -2 / -4 = 0.50
            contract: (18 - 24) / (12 - 24) = -6 / -12 = 0.50

        MAUT = 0.40*0.50 + 0.25*0.3333 + 0.20*0.50 + 0.15*0.50
             = 0.200 + 0.08333 + 0.100 + 0.075
             = 0.45833...
        """
        terms = TermValues(price=13.50, payment=45, delivery=12, contract=18)
        result = compute_utility(terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
        expected = 0.40 * 0.50 + 0.25 * (1 / 3) + 0.20 * 0.50 + 0.15 * 0.50
        assert abs(result - expected) < 1e-6, (
            f"Expected {expected:.6f}, got {result:.6f}"
        )

    def test_single_term_at_midpoint_others_at_walk_away(self):
        """Only price at midpoint, rest at walk-away. Verifies per-term isolation.

        price achievement = 0.50, others = 0.0
        MAUT = 0.40 * 0.50 = 0.20
        """
        terms = TermValues(price=13.50, payment=30, delivery=14, contract=24)
        result = compute_utility(terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
        assert abs(result - 0.20) < 1e-6, (
            f"Expected 0.20 (only price contributing), got {result}"
        )

    def test_uniform_weights_equal_contribution(self):
        """With uniform weights, each term contributes equally.

        All terms at midpoint (achievement 0.5 each), uniform weights (0.25 each).
        MAUT = 4 * 0.25 * 0.50 = 0.50
        """
        uniform_weights = Weights(price=0.25, payment=0.25, delivery=0.25, contract=0.25)
        # Midpoints: price=(12.50+14.50)/2=13.50, payment=(75+30)/2=52.5,
        #            delivery=(10+14)/2=12, contract=(12+24)/2=18
        terms = TermValues(price=13.50, payment=52.5, delivery=12, contract=18)
        result = compute_utility(terms, BACKGROUND_CONFIG, uniform_weights)
        assert abs(result - 0.50) < 1e-6, (
            f"Expected 0.50 with uniform weights at midpoint, got {result}"
        )


class TestMautWeightValidation:
    """Falsifiable claim: weights must sum to 1.0 and be non-negative.

    Error category: Interface errors (invalid arguments).
    """

    def test_weights_not_summing_to_one_raises_error(self):
        """Weights summing to 0.95 should be rejected."""
        with pytest.raises(ValueError, match=r"sum to 1\.0"):
            Weights(price=0.40, payment=0.25, delivery=0.20, contract=0.10)

    def test_negative_weight_raises_error(self):
        """A negative weight should be rejected."""
        with pytest.raises(ValueError):
            Weights(price=-0.10, payment=0.40, delivery=0.40, contract=0.30)

    def test_zero_weight_is_valid(self):
        """A zero weight is valid -- the term simply doesn't contribute."""
        w = Weights(price=0.0, payment=0.50, delivery=0.25, contract=0.25)
        terms = TermValues(price=12.50, payment=75, delivery=10, contract=12)
        result = compute_utility(terms, BACKGROUND_CONFIG, w)
        # Price at target contributes 0.0 * 1.0 = 0. Others at target = 1.0 each.
        expected = 0.0 * 1.0 + 0.50 * 1.0 + 0.25 * 1.0 + 0.25 * 1.0
        assert abs(result - expected) < 1e-6

    def test_all_weight_on_single_term(self):
        """Extreme skew: all weight on price. Only price achievement matters."""
        w = Weights(price=1.0, payment=0.0, delivery=0.0, contract=0.0)
        terms = TermValues(price=13.50, payment=30, delivery=14, contract=24)
        result = compute_utility(terms, BACKGROUND_CONFIG, w)
        # price achievement = 0.50, MAUT = 1.0 * 0.50 = 0.50
        assert abs(result - 0.50) < 1e-6


class TestMautEdgeCases:
    """Adversarial edge cases designed to falsify robustness claims.

    Error category: Computation errors (division, precision).
    """

    def test_target_equals_walk_away_single_term(self):
        """When target == walk-away for a term, denominator is zero.

        The function must handle this without division-by-zero.
        Expected: achievement is 1.0 if value == target, else 0.0.
        """
        degenerate_config = {
            "price": TermConfig(opening=12.50, target=12.50, walk_away=12.50, weight=0.40),
            "payment": TermConfig(opening=75, target=75, walk_away=30, weight=0.25),
            "delivery": TermConfig(opening=10, target=10, walk_away=14, weight=0.20),
            "contract": TermConfig(opening=12, target=12, walk_away=24, weight=0.15),
        }
        terms = TermValues(price=12.50, payment=75, delivery=10, contract=12)
        # Should not raise ZeroDivisionError
        result = compute_utility(terms, degenerate_config, OPERATOR_WEIGHTS)
        # price achievement: target==walk_away==value, should be treated as 1.0
        # others: normal calculation
        assert result >= 0.0
        assert result <= 1.0

    def test_floating_point_precision_near_boundary(self):
        """Values extremely close to walk-away should produce near-zero utility.

        This tests that floating-point arithmetic does not produce negative
        utility from rounding errors.
        """
        # Price just barely above walk-away: 14.4999999999
        terms = TermValues(price=14.4999999999, payment=30.0001, delivery=13.9999, contract=23.9999)
        result = compute_utility(terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
        assert result >= 0.0, f"Near-boundary value produced negative utility: {result}"
        assert result < 0.01, f"Near-walk-away value should be near zero, got {result}"
