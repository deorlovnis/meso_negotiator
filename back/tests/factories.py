"""Shared test factories for the MESO negotiation engine.

Provides deterministic builders for domain objects used across all test layers.
Every factory returns sensible defaults matching the demo seed in server.py,
with **overrides kwargs for per-test customization.

Factories (claims F1-F5 from backend-refactoring-plan.md Phase 1):
- make_config:              F1 — TermConfig dict, defaults = demo seed
- make_negotiation:         F2 — Negotiation in PENDING state
- make_active_negotiation:  F3 — Negotiation in ACTIVE state with stub MESO set
- make_meso_set:            F4 — Deterministic MesoSet for tests needing cards
- make_weights:             F5 — Auto-normalizing Weights (sum forced to 1.0)
"""

from __future__ import annotations

from back.domain.negotiation import Negotiation
from back.domain.opponent_model import OpponentModel
from back.domain.types import (
    CardLabel,
    MesoSet,
    NegotiationState,
    Offer,
    TermConfig,
    TermValues,
    Weights,
)

# ---------------------------------------------------------------------------
# Default values — these MUST match the demo seed in server.py exactly.
# If server.py changes, update these. F11 safety-net test will catch drift.
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, TermConfig] = {
    "price": TermConfig(opening=11.50, target=12.50, walk_away=14.50, weight=0.40),
    "payment": TermConfig(opening=90, target=75, walk_away=30, weight=0.25),
    "delivery": TermConfig(opening=7, target=10, walk_away=14, weight=0.20),
    "contract": TermConfig(opening=6, target=12, walk_away=24, weight=0.15),
}

DEFAULT_WEIGHTS = Weights(price=0.40, payment=0.25, delivery=0.20, contract=0.15)

DEFAULT_MESO_SET = MesoSet(
    best_price=Offer(
        label=CardLabel.BEST_PRICE,
        terms=TermValues(price=12.00, payment=45, delivery=12, contract=18),
    ),
    most_balanced=Offer(
        label=CardLabel.MOST_BALANCED,
        terms=TermValues(price=13.00, payment=60, delivery=11, contract=15),
    ),
    fastest_payment=Offer(
        label=CardLabel.FASTEST_PAYMENT,
        terms=TermValues(price=13.50, payment=75, delivery=13, contract=20),
    ),
)


# ---------------------------------------------------------------------------
# F1: make_config
# ---------------------------------------------------------------------------


def make_config(**overrides: TermConfig) -> dict[str, TermConfig]:
    """Build a TermConfig dict with defaults matching the demo seed.

    Override individual terms by name:
        make_config(price=TermConfig(opening=10, target=11, walk_away=13, weight=0.5))

    Returns a new dict each time — no shared mutable state between tests.
    """
    config = dict(DEFAULT_CONFIG)
    config.update(overrides)
    return config


# ---------------------------------------------------------------------------
# F5: make_weights
# ---------------------------------------------------------------------------


def make_weights(
    *,
    price: float = 0.40,
    payment: float = 0.25,
    delivery: float = 0.20,
    contract: float = 0.15,
    auto_normalize: bool = True,
) -> Weights:
    """Build a Weights value object, auto-normalizing to sum=1.0 by default.

    When auto_normalize=True (default), the raw values are scaled so their
    sum is exactly 1.0. This prevents ValueError from Weights.__post_init__
    when callers provide approximate values.

    Set auto_normalize=False to test Weights validation directly.
    """
    if auto_normalize:
        total = price + payment + delivery + contract
        if total > 0.0:
            price /= total
            payment /= total
            delivery /= total
            contract /= total
    return Weights(
        price=price,
        payment=payment,
        delivery=delivery,
        contract=contract,
    )


# ---------------------------------------------------------------------------
# F4: make_meso_set
# ---------------------------------------------------------------------------


def make_meso_set(
    *,
    best_price_terms: TermValues | None = None,
    most_balanced_terms: TermValues | None = None,
    fastest_payment_terms: TermValues | None = None,
) -> MesoSet:
    """Build a deterministic MesoSet for tests that need cards to reference.

    Override individual card terms:
        make_meso_set(best_price_terms=TermValues(price=11, payment=50, delivery=10, contract=12))
    """
    return MesoSet(
        best_price=Offer(
            label=CardLabel.BEST_PRICE,
            terms=best_price_terms or DEFAULT_MESO_SET.best_price.terms,
        ),
        most_balanced=Offer(
            label=CardLabel.MOST_BALANCED,
            terms=most_balanced_terms or DEFAULT_MESO_SET.most_balanced.terms,
        ),
        fastest_payment=Offer(
            label=CardLabel.FASTEST_PAYMENT,
            terms=fastest_payment_terms
            or DEFAULT_MESO_SET.fastest_payment.terms,
        ),
    )


# ---------------------------------------------------------------------------
# F2: make_negotiation
# ---------------------------------------------------------------------------


def make_negotiation(
    *,
    neg_id: str = "test-neg-001",
    state: NegotiationState = NegotiationState.PENDING,
    current_round: int = 0,
    max_rounds: int = 5,
    config: dict[str, TermConfig] | None = None,
    operator_weights: Weights | None = None,
    opponent_model: OpponentModel | None = None,
) -> Negotiation:
    """Build a Negotiation in PENDING state with demo-seed defaults.

    Override any field:
        make_negotiation(max_rounds=3, neg_id="custom")
    """
    return Negotiation(
        id=neg_id,
        state=state,
        round=current_round,
        max_rounds=max_rounds,
        config=config or make_config(),
        operator_weights=operator_weights or DEFAULT_WEIGHTS,
        opponent_model=opponent_model or OpponentModel.uniform(),
    )


# ---------------------------------------------------------------------------
# F3: make_active_negotiation
# ---------------------------------------------------------------------------


def make_active_negotiation(
    *,
    neg_id: str = "test-neg-001",
    max_rounds: int = 5,
    config: dict[str, TermConfig] | None = None,
    operator_weights: Weights | None = None,
    opponent_model: OpponentModel | None = None,
    meso_set: MesoSet | None = None,
) -> Negotiation:
    """Build an ACTIVE negotiation with a MESO set already loaded.

    Activates a PENDING negotiation and assigns the given (or default) MESO set.
    """
    neg = make_negotiation(
        neg_id=neg_id,
        max_rounds=max_rounds,
        config=config,
        operator_weights=operator_weights,
        opponent_model=opponent_model,
    )
    neg.activate()
    neg.set_meso_set(meso_set or make_meso_set())
    return neg
