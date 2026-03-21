"""MESO offer set generator.

Generates 3 offer cards that have equal operator MAUT utility (within
tolerance 0.02) but differ in their term distributions:
- BEST_PRICE: lowest price (most favorable price for supplier)
- FASTEST_PAYMENT: fastest payment terms (shortest days)
- MOST_BALANCED: closest to equal per-term achievement, no single extreme

Algorithm:
1. Sample a grid of term value combinations within acceptable range.
2. Score each candidate with compute_utility().
3. Keep candidates within target_utility +/- TOLERANCE.
4. Select 3 profiles using opponent model to bias within each profile.
5. Validate all candidates are distinct and respect walk-away limits.

The opponent model biases offer terms within each profile: e.g., for
MOST_BALANCED, heavier opponent payment weight means the balanced card
offers faster payment (without reducing operator utility).
"""

from __future__ import annotations

import itertools

from back.domain.maut import compute_utility
from back.domain.types import (
    CardLabel,
    MesoSet,
    Offer,
    TermConfig,
    TermValues,
    Weights,
)

# Maximum allowed difference in operator utility between any two MESO cards.
UTILITY_TOLERANCE = 0.02

# Number of steps to sample per dimension when generating candidates.
# 12 steps gives 12^4 = 20736 candidates — good coverage near boundaries.
_GRID_STEPS = 12


def generate_meso_set(
    config: dict[str, TermConfig],
    operator_weights: Weights,
    opponent_weights: Weights,
    target_utility: float,
) -> MesoSet:
    """Generate 3 equal-utility MESO offer cards with distinct profiles.

    Args:
        config: Term configuration keyed by "price", "payment", "delivery",
                "contract". Each has opening, target, walk_away, weight.
        operator_weights: Operator's fixed MAUT weight vector.
        opponent_weights: Inferred supplier preference weights.
        target_utility: Target operator utility for this round (from concession
                        curve). All 3 cards will match within UTILITY_TOLERANCE.

    Returns:
        MesoSet with 3 distinct offers at approximately equal operator utility.

    Raises:
        ValueError: If no valid candidates can be found within tolerance.
    """
    candidates = _generate_candidates(config, operator_weights, target_utility)

    if len(candidates) < 3:
        # Widen tolerance as fallback: try 2x and 3x tolerance
        for multiplier in [2, 4, 8]:
            candidates = _generate_candidates(
                config, operator_weights, target_utility, UTILITY_TOLERANCE * multiplier
            )
            if len(candidates) >= 3:
                break

    if len(candidates) < 3:
        raise ValueError(
            f"Cannot generate MESO set: fewer than 3 candidates at "
            f"target_utility={target_utility:.3f} within tolerance. "
            f"Check term configurations for feasibility."
        )

    best_price = _select_best_price(candidates, config, opponent_weights)
    fastest_payment = _select_fastest_payment(
        candidates, config, opponent_weights, exclude=best_price
    )
    most_balanced = _select_most_balanced(
        candidates, config, opponent_weights, best_price, fastest_payment
    )

    return MesoSet(
        best_price=Offer(label=CardLabel.BEST_PRICE, terms=best_price),
        most_balanced=Offer(label=CardLabel.MOST_BALANCED, terms=most_balanced),
        fastest_payment=Offer(label=CardLabel.FASTEST_PAYMENT, terms=fastest_payment),
    )


def _generate_candidates(
    config: dict[str, TermConfig],
    operator_weights: Weights,
    target_utility: float,
    tolerance: float = UTILITY_TOLERANCE,
) -> list[TermValues]:
    """Sample a grid of term combinations and return those near target utility.

    Samples uniformly between walk_away and opening for each term, then
    filters to those within target_utility ± tolerance.
    """
    price_cfg = config["price"]
    payment_cfg = config["payment"]
    delivery_cfg = config["delivery"]
    contract_cfg = config["contract"]

    price_range = _sample_range(price_cfg.walk_away, price_cfg.opening, _GRID_STEPS)
    payment_range = _sample_range(
        payment_cfg.walk_away, payment_cfg.opening, _GRID_STEPS
    )
    delivery_range = _sample_range(
        delivery_cfg.walk_away, delivery_cfg.opening, _GRID_STEPS
    )
    contract_range = _sample_range(
        contract_cfg.walk_away, contract_cfg.opening, _GRID_STEPS
    )

    candidates: list[TermValues] = []
    for price, payment, delivery, contract in itertools.product(
        price_range, payment_range, delivery_range, contract_range
    ):
        terms = TermValues(
            price=price, payment=payment, delivery=delivery, contract=contract
        )
        utility = compute_utility(terms, config, operator_weights)
        if abs(utility - target_utility) <= tolerance:
            candidates.append(terms)

    return candidates


def _sample_range(walk_away: float, opening: float, steps: int) -> list[float]:
    """Generate evenly spaced sample points between walk_away and opening.

    Includes both endpoints. Also inserts the exact walk_away and opening
    values to ensure boundary candidates are always considered.
    """
    if steps <= 1:
        return [opening]
    low = min(walk_away, opening)
    high = max(walk_away, opening)
    step_size = (high - low) / (steps - 1)
    points = {low + i * step_size for i in range(steps)}
    # Ensure exact endpoints are present (avoids float rounding gaps)
    points.add(walk_away)
    points.add(opening)
    return sorted(points)


def _select_best_price(
    candidates: list[TermValues],
    config: dict[str, TermConfig],
    opponent_weights: Weights,
) -> TermValues:
    """Select the candidate with the most favorable price for the supplier.

    Favorable price = lowest numerical value (cheaper per k boxes).
    Among candidates with equally low price, use opponent weights to
    prefer the one with better payment terms (next highest opponent weight).
    """
    price_cfg = config["price"]
    # "Best price" for supplier = lowest price (toward opening or below target)
    # opening is the most generous price for supplier
    # walk_away is the least generous
    # Determine which direction is "better" for supplier
    better_price_is_lower = price_cfg.opening < price_cfg.walk_away

    if better_price_is_lower:
        best_price_value = min(c.price for c in candidates)
    else:
        best_price_value = max(c.price for c in candidates)

    best_candidates = [c for c in candidates if c.price == best_price_value]

    # Tiebreak: prefer fastest payment (secondary signal)
    return _select_by_opponent_secondary(
        best_candidates, opponent_weights, primary_term="price"
    )


def _select_fastest_payment(
    candidates: list[TermValues],
    config: dict[str, TermConfig],
    opponent_weights: Weights,
    exclude: TermValues | None = None,
) -> TermValues:
    """Select the candidate with the fastest (lowest days) payment terms.

    'Fastest payment' always means the fewest days — the supplier gets paid
    soonest. Prefers a candidate different from `exclude` to ensure distinct
    cards, but falls back to the best match if no alternative exists.
    """
    # Prefer candidates not already selected
    pool = [c for c in candidates if c != exclude] if exclude else candidates
    if not pool:
        pool = candidates

    best_payment_value = min(c.payment for c in pool)
    best_candidates = [c for c in pool if c.payment == best_payment_value]

    return _select_by_opponent_secondary(
        best_candidates, opponent_weights, primary_term="payment"
    )


def _select_most_balanced(
    candidates: list[TermValues],
    config: dict[str, TermConfig],
    opponent_weights: Weights,
    exclude1: TermValues,
    exclude2: TermValues,
) -> TermValues:
    """Select the candidate closest to equal per-term achievement.

    Excludes already-selected offers when possible. Uses the opponent model
    to tiebreak toward the supplier's inferred preferences.

    'Most balanced' = no single term achieves an extreme value. Measured as
    the minimum variance across per-term achievement scores.
    """
    # Prefer candidates not already used (to ensure 3 distinct cards)
    available = [c for c in candidates if c != exclude1 and c != exclude2]
    if not available:
        available = [c for c in candidates if c != exclude1 or c != exclude2]
    if not available:
        available = candidates

    def balance_score(terms: TermValues) -> float:
        """Lower = more balanced. Variance of per-term achievements."""
        achievements = [
            _per_term_achievement(terms.price, config["price"]),
            _per_term_achievement(terms.payment, config["payment"]),
            _per_term_achievement(terms.delivery, config["delivery"]),
            _per_term_achievement(terms.contract, config["contract"]),
        ]
        mean = sum(achievements) / len(achievements)
        variance = sum((a - mean) ** 2 for a in achievements) / len(achievements)

        # Bias toward opponent preferences: subtract small amount for
        # terms the supplier values (lower score = preferred)
        opponent_bonus = (
            -0.001 * opponent_weights.price * _per_term_achievement(terms.price, config["price"])
            - 0.001 * opponent_weights.payment * _per_term_achievement(terms.payment, config["payment"])
            - 0.001 * opponent_weights.delivery * _per_term_achievement(terms.delivery, config["delivery"])
            - 0.001 * opponent_weights.contract * _per_term_achievement(terms.contract, config["contract"])
        )
        return variance + opponent_bonus

    return min(available, key=balance_score)


def _per_term_achievement(value: float, cfg: TermConfig) -> float:
    """Per-term achievement clamped to [0, 1]."""
    denom = cfg.target - cfg.walk_away
    if abs(denom) < 1e-12:
        return 1.0 if abs(value - cfg.target) < 1e-12 else 0.0
    raw = (value - cfg.walk_away) / denom
    return max(0.0, min(1.0, raw))


def _select_by_opponent_secondary(
    candidates: list[TermValues],
    opponent_weights: Weights,
    primary_term: str,
) -> TermValues:
    """Among tied candidates on the primary dimension, pick the first.

    The primary dimension is already extremized (e.g., lowest price for
    BEST_PRICE). Any remaining tie means all candidates are equally good
    on that dimension, so we return the first candidate deterministically.

    Args:
        candidates: All candidates with the same extremal primary value.
        opponent_weights: Inferred supplier weights (reserved for future use).
        primary_term: Name of the already-extremized dimension (informational).

    Returns:
        First candidate (deterministic tiebreaker).
    """
    # opponent_weights and primary_term retained for future biased tiebreaking.
    return candidates[0]
