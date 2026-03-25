"""MESO offer set generator.

Generates 3 offer cards at approximately equal operator MAUT utility but
with distinct term distributions:
- BEST_PRICE: most supplier-favorable price (toward walk_away)
- FASTEST_PAYMENT: fastest payment terms (shortest days)
- MOST_BALANCED: closest to equal per-term achievement, no single extreme

Specialty cards (BEST_PRICE, FASTEST_PAYMENT) are exempt from the per-term
achievement floor so they can push their key dimension to the extreme.
MOST_BALANCED respects the floor to stay evenly distributed.

Algorithm:
1. Sample a grid of term value combinations within acceptable range.
2. Score each candidate with compute_utility().
3. Keep candidates within target_utility +/- TOLERANCE.
4. Select specialty cards from the full pool (no floor).
5. Among tied specialty candidates (same extremal primary value), rank by
   opponent-cost scoring (logrolling tiebreaker): pick the candidate that
   imposes the highest weighted cost on the supplier's non-specialty
   priorities, creating a genuine tradeoff (Bazerman & Neale logrolling).
6. Select MOST_BALANCED from floor-filtered pool.
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
# Must be tight enough that adjacent rounds don't overlap (smallest drop
# between rounds is ~0.087), but wide enough for visible card differentiation.
UTILITY_TOLERANCE = 0.02

# Number of steps to sample per dimension when generating candidates.
# 16 steps gives 16^4 = 65536 candidates — fine enough to reflect the
# per-round achievement floor as distinct term values after rounding.
_GRID_STEPS = 16

# Scaling factor for the per-term achievement floor.  At a given target
# utility each term must have achievement >= target_utility * _FLOOR_SCALE.
# This prevents any single term from jumping to its walk-away extreme while
# others compensate, ensuring visible improvement across every round.
_FLOOR_SCALE = 0.5


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
    # Generate without floor — per-card filtering happens during selection.
    # Pass opponent_weights to bias the sampling ranges.
    candidates = _generate_candidates(
        config,
        operator_weights,
        target_utility,
        floor_scale=0.0,
        opponent_weights=opponent_weights,
    )

    if len(candidates) < 3:
        for multiplier in [2, 4, 8]:
            candidates = _generate_candidates(
                config,
                operator_weights,
                target_utility,
                UTILITY_TOLERANCE * multiplier,
                floor_scale=0.0,
                opponent_weights=opponent_weights,
            )
            if len(candidates) >= 3:
                break

    if len(candidates) < 3:
        raise ValueError(
            f"Cannot generate MESO set: fewer than 3 candidates at "
            f"target_utility={target_utility:.3f} within tolerance. "
            f"Check term configurations for feasibility."
        )

    floor = target_utility * _FLOOR_SCALE

    # Specialty cards: exempt their key term from floor, keep floor on rest.
    # Per-term floors are scaled by opponent weights so that terms the supplier
    # values (high weight) get a higher floor (must be better for supplier)
    # and terms the supplier traded away (low weight) get a lower floor (can
    # be worse).  This produces the directional trade-off: improve payment +
    # trade delivery → payment gets better, delivery gets worse.
    price_pool = _filter_floor_except(
        candidates,
        config,
        floor,
        exempt="price",
        opponent_weights=opponent_weights,
        term_config=config,
    )
    if not price_pool:
        price_pool = candidates
    best_price = _select_best_price(price_pool, config, opponent_weights)

    payment_pool = _filter_floor_except(
        candidates,
        config,
        floor,
        exempt="payment",
        opponent_weights=opponent_weights,
        term_config=config,
    )
    if not payment_pool:
        payment_pool = candidates
    fastest_payment = _select_fastest_payment(
        payment_pool, config, opponent_weights, exclude=best_price
    )

    # Balanced card: all terms must meet the opponent-weighted floor.
    balanced_pool = [
        c
        for c in candidates
        if _meets_floor(
            c, config, floor, opponent_weights=opponent_weights, term_config=config
        )
    ]
    if not balanced_pool:
        balanced_pool = candidates
    most_balanced = _select_most_balanced(
        balanced_pool, config, opponent_weights, best_price, fastest_payment
    )

    return MesoSet(
        best_price=Offer(label=CardLabel.BEST_PRICE, terms=best_price),
        most_balanced=Offer(label=CardLabel.MOST_BALANCED, terms=most_balanced),
        fastest_payment=Offer(label=CardLabel.FASTEST_PAYMENT, terms=fastest_payment),
    )


def _biased_range(
    cfg: TermConfig,
    opponent_weight: float,
) -> tuple[float, float]:
    """Compute a biased (walk_away, opening) range based on opponent weight.

    The supplier always wants LOWER values for all terms.  For each term the
    "supplier-better" end has lower values and the "supplier-worse" end has
    higher values.

    Improved terms (high weight): shrink from the worse end so the grid only
    produces values that are good for the supplier.

    Traded terms (low weight): shrink from the better end so the grid only
    produces values that are bad for the supplier.

    Neutral (uniform weight 0.25): no change.
    """
    opening = cfg.opening
    walk_away = cfg.walk_away
    ratio = opponent_weight / 0.25  # 1.0 = neutral

    if abs(ratio - 1.0) < 0.01:
        return (walk_away, opening)

    full_range = walk_away - opening  # signed

    # Supplier wants lower values.  Determine which end is "lower".
    if opening < walk_away:
        # opening is the low (supplier-better) end, walk_away is high (worse)
        if ratio > 1.0:
            # Improved: cut from walk_away side (remove high/bad values)
            shrink = min(0.7, (ratio - 1.0) * 2.0)
            new_walk_away = walk_away - shrink * full_range
            return (new_walk_away, opening)
        else:
            # Traded: cut from opening side (remove low/good values)
            shrink = min(0.7, (1.0 - ratio) * 2.0)
            new_opening = opening + shrink * full_range
            return (walk_away, new_opening)
    else:
        # opening is the high end, walk_away is low (supplier-better)
        # e.g. payment: opening=90, walk_away=30 (lower=better for supplier)
        if ratio > 1.0:
            # Improved: cut from opening side (remove high/bad values)
            shrink = min(0.7, (ratio - 1.0) * 2.0)
            new_opening = opening - shrink * (opening - walk_away)
            return (walk_away, new_opening)
        else:
            # Traded: cut from walk_away side (remove low/good values)
            shrink = min(0.7, (1.0 - ratio) * 2.0)
            new_walk_away = walk_away + shrink * (opening - walk_away)
            return (new_walk_away, opening)


def _generate_candidates(
    config: dict[str, TermConfig],
    operator_weights: Weights,
    target_utility: float,
    tolerance: float = UTILITY_TOLERANCE,
    floor_scale: float = _FLOOR_SCALE,
    opponent_weights: Weights | None = None,
) -> list[TermValues]:
    """Sample a grid of term combinations and return those near target utility.

    When opponent_weights are provided, the sampling range for each term is
    biased: improved terms (high weight) sample only values good for the
    supplier, traded terms (low weight) sample only values bad for the
    supplier.  This produces the directional trade-off.
    """
    price_cfg = config["price"]
    payment_cfg = config["payment"]
    delivery_cfg = config["delivery"]
    contract_cfg = config["contract"]

    if opponent_weights is not None:
        pw, po = _biased_range(price_cfg, opponent_weights.price)
        price_range = _sample_range(pw, po, _GRID_STEPS)
        pw, po = _biased_range(payment_cfg, opponent_weights.payment)
        payment_range = _sample_range(pw, po, _GRID_STEPS)
        pw, po = _biased_range(delivery_cfg, opponent_weights.delivery)
        delivery_range = _sample_range(pw, po, _GRID_STEPS)
        pw, po = _biased_range(contract_cfg, opponent_weights.contract)
        contract_range = _sample_range(pw, po, _GRID_STEPS)
    else:
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

    achievement_floor = target_utility * floor_scale

    candidates: list[TermValues] = []
    for price, payment, delivery, contract in itertools.product(
        price_range, payment_range, delivery_range, contract_range
    ):
        terms = TermValues(
            price=price, payment=payment, delivery=delivery, contract=contract
        )
        utility = compute_utility(terms, config, operator_weights)
        if abs(utility - target_utility) > tolerance:
            continue
        # Enforce per-term achievement floor to prevent premature extremes
        if achievement_floor > 0 and (
            _per_term_achievement(price, price_cfg) < achievement_floor
            or _per_term_achievement(payment, payment_cfg) < achievement_floor
            or _per_term_achievement(delivery, delivery_cfg) < achievement_floor
            or _per_term_achievement(contract, contract_cfg) < achievement_floor
        ):
            continue
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
    """Select the candidate with the lowest (cheapest) price.

    Per the feature spec: "the BEST PRICE card has the lowest price among
    the 3 cards."  Best Price = cheapest = most competitive offer.
    """
    best_price_value = min(c.price for c in candidates)
    best_candidates = [c for c in candidates if c.price == best_price_value]

    return _select_by_opponent_secondary(
        best_candidates, opponent_weights, primary_term="price", config=config
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
        best_candidates, opponent_weights, primary_term="payment", config=config
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

        # Bias toward opponent preferences.  The supplier always wants
        # LOWER values.  For aligned terms (lower value = higher achievement),
        # prefer HIGH achievement.  For inverted terms like payment (lower
        # value = lower achievement), prefer LOW achievement.
        opponent_bonus = 0.0
        for t_name in ("price", "payment", "delivery", "contract"):
            w = getattr(opponent_weights, t_name)
            a = _per_term_achievement(getattr(terms, t_name), config[t_name])
            cfg = config[t_name]
            inverted = cfg.target > cfg.walk_away
            if inverted:
                # Prefer LOW achievement (= lower value = better for supplier)
                opponent_bonus += 0.4 * w * a
            else:
                # Prefer HIGH achievement (= lower value = better for supplier)
                opponent_bonus -= 0.4 * w * a
        return variance + opponent_bonus

    return min(available, key=balance_score)


def _opponent_scaled_floor(
    base_floor: float,
    term: str,
    opponent_weights: Weights | None,
    config: dict[str, TermConfig] | None = None,
) -> float:
    """Scale the per-term floor by the opponent's weight for that term.

    The supplier always wants LOWER values (cheaper price, faster payment,
    faster delivery, shorter contract).  For most terms, lower value = higher
    MAUT achievement (aligned).  But when target > walk_away (e.g. payment:
    target=75 > walk_away=30), lower value = LOWER achievement (inverted).

    For aligned terms (price, delivery, contract):
      Higher opponent weight → higher floor → forces higher achievement
      → lower values → better for supplier.

    For inverted terms (payment):
      Higher opponent weight → LOWER floor → allows lower achievement
      → lower values → better for supplier.

    Clamped to [0.2, 1.8] ratio to prevent extreme filtering.
    """
    if opponent_weights is None:
        return base_floor
    weight = getattr(opponent_weights, term)

    # Detect inversion: supplier wants lower values, but for this term
    # lower value means lower achievement (target > walk_away).
    inverted = False
    if config and term in config:
        cfg = config[term]
        inverted = cfg.target > cfg.walk_away

    # Inverted: higher weight → LOWER floor (allows lower achievement = lower value)
    # Aligned: higher weight → HIGHER floor (forces higher achievement = lower value)
    ratio = ((0.25 / weight) if weight > 1e-9 else 5.0) if inverted else weight / 0.25

    ratio = max(0.2, min(1.8, ratio))
    return base_floor * ratio


def _filter_floor_except(
    candidates: list[TermValues],
    config: dict[str, TermConfig],
    floor: float,
    exempt: str,
    opponent_weights: Weights | None = None,
    term_config: dict[str, TermConfig] | None = None,
) -> list[TermValues]:
    """Filter candidates where all terms EXCEPT the exempt one meet the
    opponent-weighted floor (direction-aware)."""
    terms = ["price", "payment", "delivery", "contract"]
    checked = [t for t in terms if t != exempt]
    cfg = term_config or config
    return [
        c
        for c in candidates
        if all(
            _per_term_achievement(getattr(c, t), config[t])
            >= _opponent_scaled_floor(floor, t, opponent_weights, cfg)
            for t in checked
        )
    ]


def _meets_floor(
    terms: TermValues,
    config: dict[str, TermConfig],
    floor: float,
    opponent_weights: Weights | None = None,
    term_config: dict[str, TermConfig] | None = None,
) -> bool:
    """True if all per-term achievements meet the opponent-weighted floor."""
    cfg = term_config or config
    for t in ("price", "payment", "delivery", "contract"):
        scaled = _opponent_scaled_floor(floor, t, opponent_weights, cfg)
        if _per_term_achievement(getattr(terms, t), config[t]) < scaled:
            return False
    return True


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
    config: dict[str, TermConfig],
) -> TermValues:
    """Among tied candidates on the primary dimension, select the one that
    creates the sharpest logrolling tradeoff.

    Logrolling (Bazerman & Neale): "you gain on your top priority, but pay
    for it on your other priorities."  Among candidates with the same extreme
    specialty value, select the one where the supplier's other high-priority
    terms are worst for the supplier (highest operator achievement).

    Args:
        candidates: All candidates with the same extremal primary value.
        opponent_weights: Inferred supplier weights — drives which non-primary
                          terms to push toward the operator's ideal.
        primary_term: Name of the already-extremized dimension (excluded from
                      the cost score).
        config: Term configuration for computing per-term achievement.

    Returns:
        Candidate with highest opponent cost on non-primary terms.
    """
    non_primary = [
        t for t in ("price", "payment", "delivery", "contract") if t != primary_term
    ]

    opponent_w = {
        "price": opponent_weights.price,
        "payment": opponent_weights.payment,
        "delivery": opponent_weights.delivery,
        "contract": opponent_weights.contract,
    }

    def opponent_cost(terms: TermValues) -> float:
        """Higher = worse for supplier on their priorities.

        Weighted sum of operator-side achievement on non-specialty terms,
        weighted by the supplier's own priority weights.
        Achievement 1.0 = at operator's ideal = worst for supplier.
        """
        return sum(
            opponent_w[t] * _per_term_achievement(getattr(terms, t), config[t])
            for t in non_primary
        )

    return max(candidates, key=opponent_cost)
