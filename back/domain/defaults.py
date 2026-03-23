"""Shared default domain configuration for the MESO negotiation engine.

Single source of truth for:
- The standard 4-term negotiation configuration (price, payment, delivery, contract)
- Default operator weights

Both server.py (seed) and application/reset.py (reset use case) must produce
identical configurations. All duplication is eliminated here.
"""

from __future__ import annotations

from back.domain.types import TermConfig, Weights

# ---------------------------------------------------------------------------
# Default operator weights — must sum to 1.0
# ---------------------------------------------------------------------------

DEFAULT_OPERATOR_WEIGHTS = Weights(
    price=0.40,
    payment=0.25,
    delivery=0.20,
    contract=0.15,
)


# ---------------------------------------------------------------------------
# Default 4-term TermConfig factory
# ---------------------------------------------------------------------------


def make_default_config() -> dict[str, TermConfig]:
    """Return the standard 4-term negotiation configuration.

    This is the canonical "packaging, mid-spend, commodity" cohort config.
    Used by the dev seed in server.py and the reset use case.

    Returns a new dict each call — no shared mutable state between callers.
    """
    return {
        "price": TermConfig(opening=11.50, target=12.50, walk_away=14.50, weight=0.40),
        "payment": TermConfig(opening=90, target=75, walk_away=30, weight=0.25),
        "delivery": TermConfig(opening=7, target=10, walk_away=14, weight=0.20),
        "contract": TermConfig(opening=6, target=12, walk_away=24, weight=0.15),
    }
