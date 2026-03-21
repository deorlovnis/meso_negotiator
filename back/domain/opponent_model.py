"""Opponent model: inferred supplier preferences, updated from click signals.

The OpponentModel tracks a weight vector representing the supplier's inferred
term priorities. It is updated by three signals:
- signal_improve(label): Supplier clicked Improve on a card profile.
  Increases the profile's strength dimension, decreases others proportionally.
- signal_secure(utility): Supplier secured a card. Records utility floor.
- signal_agree(): Supplier agreed. Reinforces all current weights (no-op on
  the vector since weights already reflect observed preferences).

Invariants enforced after every update:
- All weights >= 0.0
- Weights sum to 1.0 (within float tolerance)

Delta calculation: delta = learning_rate * (1 - current_weight)
This gives diminishing returns (weight near 1.0 barely moves) and prevents
any weight from going negative (decrease is proportional to each weight).
"""

from __future__ import annotations

from back.domain.types import CardLabel, Weights

# How strongly each Improve signal shifts the weight vector.
# Tuned to give meaningful but not extreme updates.
_LEARNING_RATE = 0.15


def _card_label_to_term(label: CardLabel) -> str | None:
    """Map a card label to its strength dimension term name, or None for balanced."""
    mapping: dict[CardLabel, str | None] = {
        CardLabel.BEST_PRICE: "price",
        CardLabel.FASTEST_PAYMENT: "payment",
        CardLabel.MOST_BALANCED: None,
    }
    return mapping[label]


class OpponentModel:
    """Tracks inferred supplier preferences as a normalized weight vector.

    Instantiate with uniform weights for a new negotiation. Mutated in place
    by signal methods. The Negotiation entity owns this object.
    """

    def __init__(
        self,
        weights: Weights,
        utility_floor: float | None = None,
    ) -> None:
        self._weights = weights
        self._utility_floor = utility_floor

    @classmethod
    def uniform(cls) -> OpponentModel:
        """Create an opponent model with equal weights across all 4 terms."""
        return cls(Weights(price=0.25, payment=0.25, delivery=0.25, contract=0.25))

    @property
    def weights(self) -> Weights:
        """Current normalized weight vector."""
        return self._weights

    @property
    def utility_floor(self) -> float | None:
        """Utility floor set by the most recent Secure signal, or None."""
        return self._utility_floor

    def signal_improve(self, label: CardLabel) -> None:
        """Update weights based on supplier clicking Improve on a card.

        For BEST_PRICE or FASTEST_PAYMENT: increase that dimension's weight,
        decrease others proportionally, then renormalize.

        For MOST_BALANCED: nudge all weights toward uniform (0.25 each).
        """
        w = {
            "price": self._weights.price,
            "payment": self._weights.payment,
            "delivery": self._weights.delivery,
            "contract": self._weights.contract,
        }

        if label == CardLabel.MOST_BALANCED:
            # Nudge all weights toward uniform
            uniform = 1.0 / 4.0
            for term in w:
                w[term] += _LEARNING_RATE * (uniform - w[term])
        else:
            target_term = _card_label_to_term(label)
            assert target_term is not None, (
                f"Expected a non-None term for label {label}"
            )
            # Increase target term using diminishing-returns delta
            delta = _LEARNING_RATE * (1.0 - w[target_term])
            w[target_term] += delta
            # Decrease others proportionally so they absorb the delta
            other_terms = [t for t in w if t != target_term]
            other_total = sum(w[t] for t in other_terms)
            if other_total > 0.0:
                for term in other_terms:
                    w[term] -= delta * (w[term] / other_total)

        self._weights = _normalize(w)

    def signal_secure(self, utility: float) -> None:
        """Record the utility floor from a Secure action.

        Args:
            utility: Operator utility of the secured offer, used as the
                     minimum acceptable threshold for future MESO generation.
        """
        self._utility_floor = utility

    def signal_agree(self) -> None:
        """Reinforce all current weights (record for future negotiations).

        This is a no-op on the weight vector itself — it signals that the
        current weights accurately reflect the supplier's preferences and
        should be retained for future renegotiations.
        """
        # Weights are already up-to-date; agreement confirms them.
        # In a persistent system, the caller should save this model.


def _normalize(w: dict[str, float]) -> Weights:
    """Renormalize a weight dict to sum to 1.0, clamp negatives to 0."""
    # Clamp any tiny negatives from floating-point arithmetic
    w = {k: max(0.0, v) for k, v in w.items()}
    total = sum(w.values())
    if total <= 0.0:
        # Fallback: uniform (should never happen in practice)
        return Weights(price=0.25, payment=0.25, delivery=0.25, contract=0.25)
    return Weights(
        price=w["price"] / total,
        payment=w["payment"] / total,
        delivery=w["delivery"] / total,
        contract=w["contract"] / total,
    )
