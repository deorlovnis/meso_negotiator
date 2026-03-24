"""Opponent model: inferred supplier preferences, updated from click signals.

V2: signal_improve takes explicit improve_term and trade_term instead of
inferring from card label.
"""

from __future__ import annotations

from back.domain.types import Weights

_LEARNING_RATE = 0.15


class OpponentModel:
    """Tracks inferred supplier preferences as a normalized weight vector."""

    def __init__(
        self,
        weights: Weights,
        utility_floor: float | None = None,
    ) -> None:
        self._weights = weights
        self._utility_floor = utility_floor

    @classmethod
    def uniform(cls) -> OpponentModel:
        return cls(Weights(price=0.25, payment=0.25, delivery=0.25, contract=0.25))

    @property
    def weights(self) -> Weights:
        return self._weights

    @property
    def utility_floor(self) -> float | None:
        return self._utility_floor

    def signal_improve(self, improve_term: str, trade_term: str | None) -> None:
        """Update weights based on explicit term selection.

        Args:
            improve_term: The term the supplier wants to improve.
            trade_term: The term to trade off, or None for "Balance other terms".
        """
        w = {
            "price": self._weights.price,
            "payment": self._weights.payment,
            "delivery": self._weights.delivery,
            "contract": self._weights.contract,
        }

        delta = _LEARNING_RATE * (1.0 - w[improve_term])
        w[improve_term] += delta

        if trade_term is not None:
            # Decrease only the specific trade term
            w[trade_term] = max(0.0, w[trade_term] - delta)
        else:
            # Distribute decrease across all other terms proportionally
            other_terms = [t for t in w if t != improve_term]
            other_total = sum(w[t] for t in other_terms)
            if other_total > 0.0:
                for term in other_terms:
                    w[term] -= delta * (w[term] / other_total)

        self._weights = _normalize(w)

    def signal_secure(self, utility: float) -> None:
        self._utility_floor = utility

    def signal_agree(self) -> None:
        pass


def _normalize(w: dict[str, float]) -> Weights:
    w = {k: max(0.0, v) for k, v in w.items()}
    total = sum(w.values())
    if total <= 0.0:
        return Weights(price=0.25, payment=0.25, delivery=0.25, contract=0.25)
    return Weights(
        price=w["price"] / total,
        payment=w["payment"] / total,
        delivery=w["delivery"] / total,
        contract=w["contract"] / total,
    )
