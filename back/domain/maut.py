"""MAUT (Multi-Attribute Utility Theory) utility computation.

Pure function with no side effects. Computes operator utility for a given
offer, configuration, and weights.

U(offer) = sum over terms:
    w_i * clamp( (value_i - walkaway_i) / (target_i - walkaway_i), 0.0, 1.0 )

Interpretation:
- 0.0 = all terms at walk-away (worst acceptable for operator)
- 1.0 = all terms at target (best achievable for operator)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from back.domain.types import TermConfig, TermValues, Weights


def _achievement(value: float, walk_away: float, target: float) -> float:
    """Compute per-term achievement, clamped to [0, 1].

    achievement = (value - walk_away) / (target - walk_away)

    When target == walk_away the term is degenerate (no range). Return 1.0 if
    the value equals the target, else 0.0.
    """
    denom = target - walk_away
    if abs(denom) < 1e-12:
        return 1.0 if abs(value - target) < 1e-12 else 0.0
    raw = (value - walk_away) / denom
    return max(0.0, min(1.0, raw))


def compute_utility(
    terms: TermValues,
    config: dict[str, TermConfig],
    weights: Weights,
) -> float:
    """Compute operator MAUT utility for a given offer.

    Args:
        terms: The concrete term values of the offer to evaluate.
        config: Term configuration keyed by term name:
                "price", "payment", "delivery", "contract".
        weights: Operator weight vector (must sum to 1.0).

    Returns:
        Float in [0.0, 1.0] representing operator utility.
    """
    price_a = _achievement(
        terms.price, config["price"].walk_away, config["price"].target
    )
    payment_a = _achievement(
        terms.payment, config["payment"].walk_away, config["payment"].target
    )
    delivery_a = _achievement(
        terms.delivery, config["delivery"].walk_away, config["delivery"].target
    )
    contract_a = _achievement(
        terms.contract, config["contract"].walk_away, config["contract"].target
    )

    return (
        weights.price * price_a
        + weights.payment * payment_a
        + weights.delivery * delivery_a
        + weights.contract * contract_a
    )
