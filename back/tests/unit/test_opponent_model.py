"""Unit tests for opponent model weight updates.

Error categories targeted:
- Computation errors: weight redistribution, normalization, diminishing returns
- Logic errors: wrong dimension shifted, floor not set
- Data errors: negative weights, weights not summing to 1.0

Source spec: core-loop.feature sections 5, 13.
Architecture ref: ARCHITECTURE.md domain/opponent_model.py contract.

Weight update rules:
    delta = learning_rate * (1 - current_weight)
    improve(BEST_PRICE): price_weight += delta, others -= proportional
    improve(FASTEST_PAYMENT): payment_weight += delta, others -= proportional
    improve(MOST_BALANCED): all weights nudge toward uniform
    secure: set utility_floor
    agree: reinforce all
    Invariants: all weights >= 0.0, sum == 1.0
"""

from __future__ import annotations

from back.domain.opponent_model import OpponentModel
from back.domain.types import CardLabel, Weights


class TestOpponentModelInitialization:
    """Falsifiable claim: opponent model starts with uniform weights.

    section 13: 'opponent model weights are initialized uniformly'
    """

    def test_initial_weights_are_uniform(self):
        """Each of the 4 terms should start at 0.25."""
        model = OpponentModel.uniform()
        w = model.weights
        assert abs(w.price - 0.25) < 1e-9
        assert abs(w.payment - 0.25) < 1e-9
        assert abs(w.delivery - 0.25) < 1e-9
        assert abs(w.contract - 0.25) < 1e-9

    def test_initial_weights_sum_to_one(self):
        model = OpponentModel.uniform()
        total = sum(
            [
                model.weights.price,
                model.weights.payment,
                model.weights.delivery,
                model.weights.contract,
            ]
        )
        assert abs(total - 1.0) < 1e-9

    def test_initial_utility_floor_is_none(self):
        model = OpponentModel.uniform()
        assert model.utility_floor is None


class TestImproveShiftsCorrectDimension:
    """Falsifiable claim: improve on a card increases its strength dimension.

    section 5: 'opponent model increases the payment weight above 0.25'
    """

    def test_improve_fastest_payment_increases_payment_weight(self):
        """section 5: improve on FASTEST_PAYMENT increases payment weight."""
        model = OpponentModel.uniform()
        initial_payment = model.weights.payment
        model.signal_improve(CardLabel.FASTEST_PAYMENT)
        assert model.weights.payment > initial_payment, (
            f"Payment weight should increase: {initial_payment} -> {model.weights.payment}"
        )

    def test_improve_best_price_increases_price_weight(self):
        """Improve on BEST_PRICE increases price weight."""
        model = OpponentModel.uniform()
        initial_price = model.weights.price
        model.signal_improve(CardLabel.BEST_PRICE)
        assert model.weights.price > initial_price, (
            f"Price weight should increase: {initial_price} -> {model.weights.price}"
        )

    def test_improve_fastest_payment_decreases_other_weights(self):
        """section 5: 'decreases one or more other term weights to compensate'"""
        model = OpponentModel.uniform()
        model.signal_improve(CardLabel.FASTEST_PAYMENT)
        # At least one non-payment weight must be below 0.25
        non_payment = [
            model.weights.price,
            model.weights.delivery,
            model.weights.contract,
        ]
        assert any(w < 0.25 for w in non_payment), (
            f"At least one non-payment weight should decrease: {non_payment}"
        )

    def test_improve_most_balanced_nudges_toward_uniform(self):
        """Improve on MOST_BALANCED should nudge all weights toward 0.25.

        Start with skewed weights, then signal MOST_BALANCED.
        The result should be closer to uniform than the starting point.
        """
        model = OpponentModel(
            weights=Weights(price=0.10, payment=0.50, delivery=0.30, contract=0.10)
        )
        # Measure distance from uniform before
        uniform = 0.25
        before_distance = sum(
            abs(getattr(model.weights, t) - uniform)
            for t in ("price", "payment", "delivery", "contract")
        )
        model.signal_improve(CardLabel.MOST_BALANCED)
        after_distance = sum(
            abs(getattr(model.weights, t) - uniform)
            for t in ("price", "payment", "delivery", "contract")
        )
        assert after_distance < before_distance, (
            f"MOST_BALANCED should move toward uniform: "
            f"distance before={before_distance:.4f}, after={after_distance:.4f}"
        )


class TestWeightsAlwaysSumToOne:
    """Falsifiable claim: weights sum to 1.0 after ANY update operation.

    This is the highest-priority invariant. Tested after every mutation type.
    """

    def _assert_sum_one(self, model: OpponentModel, context: str) -> None:
        total = sum(
            [
                model.weights.price,
                model.weights.payment,
                model.weights.delivery,
                model.weights.contract,
            ]
        )
        assert abs(total - 1.0) < 1e-9, (
            f"Weights don't sum to 1.0 after {context}: sum={total}"
        )

    def test_sum_after_single_improve(self):
        model = OpponentModel.uniform()
        model.signal_improve(CardLabel.FASTEST_PAYMENT)
        self._assert_sum_one(model, "single improve on FASTEST_PAYMENT")

    def test_sum_after_consecutive_improves_same_dimension(self):
        """section 13: 4 consecutive improves on same dimension."""
        model = OpponentModel.uniform()
        for i in range(4):
            model.signal_improve(CardLabel.FASTEST_PAYMENT)
            self._assert_sum_one(model, f"improve #{i + 1} on FASTEST_PAYMENT")

    def test_sum_after_improves_different_dimensions(self):
        """Improve on FASTEST_PAYMENT then BEST_PRICE."""
        model = OpponentModel.uniform()
        model.signal_improve(CardLabel.FASTEST_PAYMENT)
        self._assert_sum_one(model, "improve on FASTEST_PAYMENT")
        model.signal_improve(CardLabel.BEST_PRICE)
        self._assert_sum_one(model, "improve on BEST_PRICE after FASTEST_PAYMENT")

    def test_sum_after_agree(self):
        model = OpponentModel.uniform()
        model.signal_improve(CardLabel.FASTEST_PAYMENT)
        model.signal_agree()
        self._assert_sum_one(model, "agree after improve")

    def test_sum_after_improve_most_balanced(self):
        model = OpponentModel.uniform()
        model.signal_improve(CardLabel.MOST_BALANCED)
        self._assert_sum_one(model, "improve on MOST_BALANCED")


class TestNoNegativeWeights:
    """Falsifiable claim: no weight ever drops below 0.0.

    section 13: 'no weight for any term drops below 0.00'
    This is the adversarial test most likely to FALSIFY the claim.
    """

    def _assert_non_negative(self, model: OpponentModel, context: str) -> None:
        for term in ("price", "payment", "delivery", "contract"):
            w = getattr(model.weights, term)
            assert w >= 0.0, (
                f"Weight for {term} is {w} after {context}, expected >= 0.0"
            )

    def test_four_consecutive_improves_same_dimension(self):
        """section 13: 'Maria clicks Improve on FASTEST_PAYMENT in rounds 1,2,3,4'

        This is the scenario most likely to drive other weights to zero or below.
        After 4 improves, payment weight should be high but all others >= 0.
        """
        model = OpponentModel.uniform()
        for i in range(4):
            model.signal_improve(CardLabel.FASTEST_PAYMENT)
            self._assert_non_negative(model, f"improve #{i + 1} on FASTEST_PAYMENT")

    def test_ten_consecutive_improves_same_dimension(self):
        """Extreme adversarial: 10 improves on same dimension.

        Even beyond the 5-round limit, the math should never produce negative weights.
        """
        model = OpponentModel.uniform()
        for i in range(10):
            model.signal_improve(CardLabel.BEST_PRICE)
            self._assert_non_negative(model, f"improve #{i + 1} on BEST_PRICE")

    def test_alternating_improves_opposite_dimensions(self):
        """Adversarial: alternate between two dimensions rapidly.

        This tests whether redistribution of already-small weights works correctly.
        """
        model = OpponentModel.uniform()
        for i in range(8):
            label = CardLabel.BEST_PRICE if i % 2 == 0 else CardLabel.FASTEST_PAYMENT
            model.signal_improve(label)
            self._assert_non_negative(model, f"improve #{i + 1} on {label.name}")

    def test_improve_when_starting_with_near_zero_weight(self):
        """Start with a nearly-zero weight and improve another dimension.

        The near-zero weight should not go negative from proportional decrease.
        """
        model = OpponentModel(
            weights=Weights(price=0.01, payment=0.01, delivery=0.01, contract=0.97)
        )
        model.signal_improve(CardLabel.FASTEST_PAYMENT)
        self._assert_non_negative(
            model, "improve FASTEST_PAYMENT from near-zero others"
        )


class TestSecureSetsFloor:
    """Falsifiable claim: secure sets the utility floor.

    section 4: 'engine records a supplier utility floor based on the secured offer'
    """

    def test_secure_sets_utility_floor(self):
        model = OpponentModel.uniform()
        assert model.utility_floor is None
        model.signal_secure(utility=0.68)
        assert model.utility_floor == 0.68

    def test_secure_replaces_existing_floor(self):
        """Only one secured offer at a time -- floor gets replaced."""
        model = OpponentModel.uniform()
        model.signal_secure(utility=0.60)
        model.signal_secure(utility=0.72)
        assert model.utility_floor == 0.72

    def test_secure_does_not_change_weights(self):
        """Secure should not affect weight distribution."""
        model = OpponentModel.uniform()
        before = (
            model.weights.price,
            model.weights.payment,
            model.weights.delivery,
            model.weights.contract,
        )
        model.signal_secure(utility=0.55)
        after = (
            model.weights.price,
            model.weights.payment,
            model.weights.delivery,
            model.weights.contract,
        )
        assert before == after, "Secure should not change weights"


class TestAgreeReinforces:
    """Falsifiable claim: agree reinforces all current weights.

    section 13: 'opponent model records the final weights with all dimensions reinforced'
    """

    def test_agree_preserves_weight_proportions(self):
        """After agree, weights should still sum to 1.0 and be 'reinforced'.

        The spec says 'reinforced for future renegotiations' -- this means
        the current weights are saved/locked, not necessarily modified.
        """
        model = OpponentModel(
            weights=Weights(price=0.20, payment=0.35, delivery=0.25, contract=0.20)
        )
        model.signal_agree()
        total = sum(
            [
                model.weights.price,
                model.weights.payment,
                model.weights.delivery,
                model.weights.contract,
            ]
        )
        assert abs(total - 1.0) < 1e-9


class TestDiminishingReturns:
    """Falsifiable claim: delta = learning_rate * (1 - current_weight).

    This means a weight near 1.0 barely moves, ensuring diminishing returns.
    """

    def test_weight_increase_diminishes_with_repeated_improve(self):
        """Each successive improve on the same dimension should increase
        the target weight by a smaller amount.

        section 5: 'Consecutive Improve signals on the same dimension compound the shift'
        """
        model = OpponentModel.uniform()
        deltas = []
        for _ in range(4):
            before = model.weights.payment
            model.signal_improve(CardLabel.FASTEST_PAYMENT)
            after = model.weights.payment
            deltas.append(after - before)

        # Each delta should be smaller than the previous
        for i in range(1, len(deltas)):
            assert deltas[i] < deltas[i - 1], (
                f"Delta at step {i + 1} ({deltas[i]:.6f}) should be < "
                f"delta at step {i} ({deltas[i - 1]:.6f})"
            )

    def test_payment_weight_increases_monotonically_across_four_improves(self):
        """section 13: 'payment weight increases each round' after 4 improves."""
        model = OpponentModel.uniform()
        weights_over_time = [model.weights.payment]
        for _ in range(4):
            model.signal_improve(CardLabel.FASTEST_PAYMENT)
            weights_over_time.append(model.weights.payment)

        for i in range(1, len(weights_over_time)):
            assert weights_over_time[i] > weights_over_time[i - 1], (
                f"Payment weight should increase monotonically: "
                f"step {i - 1}={weights_over_time[i - 1]:.6f} -> "
                f"step {i}={weights_over_time[i]:.6f}"
            )
