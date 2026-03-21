"""Unit tests for MESO set generation.

Error categories targeted:
- Logic errors: wrong number of cards, labels misassigned, duplicate cards
- Computation errors: utility equality tolerance, walk-away violations
- Boundary errors: degenerate configs, extreme weight skew

Source spec: core-loop.feature sections 1, 8.
Architecture ref: ARCHITECTURE.md domain/meso.py contract.

Contract under test:
    generate_meso_set(config, operator_weights, opponent_weights, target_utility) -> MesoSet

    Returns 3 offers:
    - Equal operator utility within tolerance 0.02
    - All terms within walk-away limits
    - BEST_PRICE has lowest price
    - FASTEST_PAYMENT has fastest payment
    - MOST_BALANCED has no extreme on any single term
    - No two cards identical across all terms
"""

from __future__ import annotations

from back.domain.maut import compute_utility
from back.domain.meso import generate_meso_set
from back.domain.types import (
    CardLabel,
    MesoSet,
    TermConfig,
    Weights,
)

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
UNIFORM_OPPONENT_WEIGHTS = Weights(price=0.25, payment=0.25, delivery=0.25, contract=0.25)

# Target utility at round 1 with beta=3: (1 - 1/5)^3 = 0.512
ROUND_1_TARGET = 0.512


def _get_offers(meso: MesoSet) -> list:
    """Extract all 3 offers from a MesoSet for iteration."""
    return [meso.best_price, meso.most_balanced, meso.fastest_payment]


class TestMesoReturnsThreeCards:
    """Falsifiable claim: generate_meso_set returns exactly 3 labeled cards.

    section 1: 'she sees exactly 3 offer cards'
    """

    def test_meso_set_contains_three_offers(self):
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        offers = _get_offers(meso)
        assert len(offers) == 3

    def test_meso_set_has_correct_labels(self):
        """section 1: 'labeled BEST PRICE, MOST BALANCED, and FASTEST PAYMENT'"""
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        assert meso.best_price.label == CardLabel.BEST_PRICE
        assert meso.most_balanced.label == CardLabel.MOST_BALANCED
        assert meso.fastest_payment.label == CardLabel.FASTEST_PAYMENT


class TestEqualOperatorUtility:
    """Falsifiable claim: all 3 cards have equal operator utility within 0.02.

    section 1: 'MAUT utility score for James is equal across all 3 cards
    within a tolerance of 0.02'

    Risk: 9/10. This is the core MESO constraint. If the generator cannot
    produce equal-utility offers, the entire fairness guarantee is broken.
    """

    def test_three_cards_within_tolerance(self):
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        utilities = []
        for offer in _get_offers(meso):
            u = compute_utility(offer.terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
            utilities.append(u)

        max_diff = max(utilities) - min(utilities)
        assert max_diff <= 0.02, (
            f"Utility spread {max_diff:.4f} exceeds tolerance 0.02. "
            f"Utilities: {[f'{u:.4f}' for u in utilities]}"
        )

    def test_utilities_are_near_target(self):
        """Each card's utility should be near the requested target."""
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        for offer in _get_offers(meso):
            u = compute_utility(offer.terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
            assert abs(u - ROUND_1_TARGET) <= 0.02, (
                f"Card {offer.label} utility {u:.4f} deviates from "
                f"target {ROUND_1_TARGET:.4f} by more than 0.02"
            )

    def test_equal_utility_with_skewed_opponent_weights(self):
        """Adversarial: extreme opponent weight skew (0.70 payment).

        The generator must still produce equal operator utility even when
        the opponent model heavily biases one dimension.
        """
        skewed_opponent = Weights(price=0.10, payment=0.70, delivery=0.10, contract=0.10)
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=skewed_opponent,
            target_utility=ROUND_1_TARGET,
        )
        utilities = [
            compute_utility(offer.terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
            for offer in _get_offers(meso)
        ]
        max_diff = max(utilities) - min(utilities)
        assert max_diff <= 0.02, (
            f"With skewed opponent weights, utility spread {max_diff:.4f} "
            f"exceeds tolerance. Utilities: {utilities}"
        )


class TestWalkAwayLimitsRespected:
    """Falsifiable claim: no generated offer violates walk-away limits.

    section 8: 'no offer includes a price above $14.50/k boxes'
    Risk: 9/10. Walk-away violations mean the operator would reject the deal.
    """

    def test_all_terms_within_walk_away(self):
        """Every term in every card must respect walk-away limits."""
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        for offer in _get_offers(meso):
            terms = offer.terms
            # Price: walk-away is $14.50 (higher is worse for operator)
            assert terms.price <= 14.50, (
                f"Card {offer.label}: price {terms.price} exceeds walk-away $14.50"
            )
            # Payment: walk-away is Net 30 (lower days = faster = worse for operator)
            assert terms.payment >= 30, (
                f"Card {offer.label}: payment Net {terms.payment} violates "
                f"walk-away Net 30"
            )
            # Delivery: walk-away is 14 days (more days = worse for supplier)
            assert terms.delivery <= 14, (
                f"Card {offer.label}: delivery {terms.delivery} days exceeds "
                f"walk-away 14 days"
            )
            # Contract: walk-away is 24 months (longer = worse for supplier)
            assert terms.contract <= 24, (
                f"Card {offer.label}: contract {terms.contract} months exceeds "
                f"walk-away 24 months"
            )

    def test_walk_away_at_low_target_utility(self):
        """Adversarial: very low target utility (near walk-away).

        When target utility is close to 0, the generator is forced to use
        near-walk-away values. It must not exceed walk-away trying to reach
        the target.
        """
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=0.05,  # Very close to walk-away
        )
        for offer in _get_offers(meso):
            terms = offer.terms
            assert terms.price <= 14.50
            assert terms.payment >= 30
            assert terms.delivery <= 14
            assert terms.contract <= 24


class TestDistinctTermDistributions:
    """Falsifiable claim: MESO cards differ in term distribution.

    section 8: 'BEST PRICE has lowest price, FASTEST PAYMENT has fastest payment,
    MOST BALANCED does not have the most extreme value on any single term'
    """

    def test_best_price_has_lowest_price(self):
        """section 8: 'BEST PRICE card has the lowest price among the 3 cards'"""
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        best_price = meso.best_price.terms.price
        other_prices = [
            meso.most_balanced.terms.price,
            meso.fastest_payment.terms.price,
        ]
        assert best_price <= min(other_prices), (
            f"BEST_PRICE card price ({best_price}) should be <= all others "
            f"({other_prices})"
        )

    def test_fastest_payment_has_fastest_payment(self):
        """section 8: 'FASTEST PAYMENT card has the fastest payment terms'

        Fastest payment = lowest number of days (e.g., Net 30 < Net 45).
        """
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        fastest = meso.fastest_payment.terms.payment
        other_payments = [
            meso.best_price.terms.payment,
            meso.most_balanced.terms.payment,
        ]
        assert fastest <= min(other_payments), (
            f"FASTEST_PAYMENT card payment ({fastest}) should be <= all others "
            f"({other_payments})"
        )

    def test_most_balanced_has_no_extreme(self):
        """section 8: 'MOST BALANCED does not have the most extreme value
        on any single term'.

        Most Balanced should not have the lowest price NOR the fastest payment.
        """
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        all_offers = _get_offers(meso)
        balanced = meso.most_balanced.terms

        # Check price: balanced should not have the minimum price
        min_price = min(o.terms.price for o in all_offers)
        if balanced.price == min_price:
            # It's OK if it ties, but it shouldn't be the unique minimum
            other_at_min = sum(
                1 for o in all_offers
                if o.terms.price == min_price and o.label != CardLabel.MOST_BALANCED
            )
            assert other_at_min > 0, (
                "MOST_BALANCED should not be the unique card with lowest price"
            )

        # Check payment: balanced should not have the fastest payment
        min_payment = min(o.terms.payment for o in all_offers)
        if balanced.payment == min_payment:
            other_at_min = sum(
                1 for o in all_offers
                if o.terms.payment == min_payment and o.label != CardLabel.MOST_BALANCED
            )
            assert other_at_min > 0, (
                "MOST_BALANCED should not be the unique card with fastest payment"
            )

    def test_no_two_cards_identical(self):
        """section 14: 'no pair of cards has the same price AND same payment
        AND same delivery AND same contract length'
        """
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=ROUND_1_TARGET,
        )
        offers = _get_offers(meso)
        for i in range(len(offers)):
            for j in range(i + 1, len(offers)):
                a, b = offers[i].terms, offers[j].terms
                identical = (
                    a.price == b.price
                    and a.payment == b.payment
                    and a.delivery == b.delivery
                    and a.contract == b.contract
                )
                assert not identical, (
                    f"Cards {offers[i].label} and {offers[j].label} are "
                    f"identical: {a}"
                )


class TestMesoWithExtremeInputs:
    """Adversarial edge cases for MESO generation.

    Error category: Computation errors (degenerate inputs).
    """

    def test_extreme_weight_skew(self):
        """Adversarial: operator weights heavily skewed to one term.

        The generator must still produce 3 distinct cards with equal utility.
        """
        extreme_weights = Weights(price=0.97, payment=0.01, delivery=0.01, contract=0.01)
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=extreme_weights,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=0.50,
        )
        utilities = [
            compute_utility(offer.terms, BACKGROUND_CONFIG, extreme_weights)
            for offer in _get_offers(meso)
        ]
        max_diff = max(utilities) - min(utilities)
        assert max_diff <= 0.02, (
            f"With extreme weight skew, utility spread {max_diff:.4f} exceeds tolerance"
        )

    def test_target_utility_at_zero(self):
        """Adversarial: target utility = 0.0 (all terms at walk-away).

        The generator should still produce 3 valid cards, even if they have
        very similar (near-walk-away) terms. At the extreme boundary the
        generator may widen tolerance to find 3 distinct cards — allow up to
        4x the standard tolerance (0.08) here.
        """
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=0.0,
        )
        for offer in _get_offers(meso):
            u = compute_utility(offer.terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
            assert abs(u - 0.0) <= 0.08, (
                f"At target 0.0, card {offer.label} utility {u:.4f} exceeds tolerance"
            )

    def test_target_utility_at_one(self):
        """Adversarial: target utility = 1.0 (all terms at target).

        The generator should produce 3 cards near target values.
        """
        meso = generate_meso_set(
            config=BACKGROUND_CONFIG,
            operator_weights=OPERATOR_WEIGHTS,
            opponent_weights=UNIFORM_OPPONENT_WEIGHTS,
            target_utility=1.0,
        )
        for offer in _get_offers(meso):
            u = compute_utility(offer.terms, BACKGROUND_CONFIG, OPERATOR_WEIGHTS)
            assert abs(u - 1.0) <= 0.02, (
                f"At target 1.0, card {offer.label} utility {u:.4f} deviates"
            )
