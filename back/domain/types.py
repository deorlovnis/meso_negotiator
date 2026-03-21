"""Core value objects for the MESO negotiation engine.

All types are immutable frozen dataclasses or enums. These are the vocabulary
of the system — they have no dependencies on any other layer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


class CardLabel(Enum):
    """Labels identifying the profile of a MESO offer card."""

    BEST_PRICE = "BEST_PRICE"
    MOST_BALANCED = "MOST_BALANCED"
    FASTEST_PAYMENT = "FASTEST_PAYMENT"


class NegotiationState(Enum):
    """State machine states for a Negotiation."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    ACCEPTED = "ACCEPTED"
    NO_DEAL = "NO_DEAL"


@dataclass(frozen=True)
class TermConfig:
    """Configuration for a single negotiation term.

    All values are in raw numeric form:
    - price: dollars per thousand boxes (higher = worse for operator)
    - payment: days (lower = better/faster for supplier, worse for operator)
    - delivery: days (lower = faster = better for supplier)
    - contract: months (higher = longer commitment, better for operator)

    opening: the starting position for this term
    target: the operator's ideal value (best achievable)
    walk_away: the operator's limit — any offer beyond this is unacceptable
    weight: this term's contribution to MAUT utility (across all terms, sum=1.0)
    """

    opening: float
    target: float
    walk_away: float
    weight: float


@dataclass(frozen=True)
class TermValues:
    """Concrete term values in a single offer.

    price: dollars per thousand boxes
    payment: days (e.g., Net 30 -> 30, Net 60 -> 60)
    delivery: days
    contract: months
    """

    price: float
    payment: float
    delivery: float
    contract: float


@dataclass(frozen=True)
class Offer:
    """A single MESO offer card."""

    label: CardLabel
    terms: TermValues


@dataclass(frozen=True)
class MesoSet:
    """The 3-card output of the MESO generator for one round."""

    best_price: Offer
    most_balanced: Offer
    fastest_payment: Offer


@dataclass(frozen=True)
class Weights:
    """Normalized 4-dimensional weight vector for MAUT.

    All weights must be >= 0.0 and sum to 1.0 within floating-point tolerance.
    Validation is enforced in __post_init__.
    """

    price: float
    payment: float
    delivery: float
    contract: float

    def __post_init__(self) -> None:
        for name, value in [
            ("price", self.price),
            ("payment", self.payment),
            ("delivery", self.delivery),
            ("contract", self.contract),
        ]:
            if value < 0.0:
                raise ValueError(
                    f"Weight '{name}' must be >= 0.0, got {value}"
                )
        total = self.price + self.payment + self.delivery + self.contract
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(
                f"Weights must sum to 1.0, got {total}"
            )
