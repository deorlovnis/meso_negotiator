"""Negotiation aggregate root — state machine and round progression.

V2 changes:
- Both Improve and Secure advance the round.
- Secure accumulates up to 3 offers (was: single offer, replaced on each secure).
- Improve takes explicit improve_term + trade_term (was: card label).
- agree_secured() allows agreeing to a previously secured offer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from back.domain.exceptions import NegotiationError
from back.domain.types import (
    CardLabel,
    MesoSet,
    NegotiationState,
    SecuredOffer,
    TermConfig,
    TermValues,
    Weights,
)

if TYPE_CHECKING:
    from back.domain.opponent_model import OpponentModel

__all__ = ["Negotiation", "NegotiationError"]

MAX_SECURED_OFFERS = 3


@dataclass
class Negotiation:
    """Aggregate root for a negotiation session."""

    id: str
    state: NegotiationState
    round: int
    max_rounds: int
    config: dict[str, TermConfig]
    operator_weights: Weights
    opponent_model: OpponentModel
    current_meso_set: MesoSet | None = field(default=None)
    secured_offers: list[SecuredOffer] = field(default_factory=list)
    agreed_terms: TermValues | None = field(default=None)
    history: list[MesoSet] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        return self.state in (NegotiationState.ACCEPTED, NegotiationState.NO_DEAL)

    @property
    def is_final_round(self) -> bool:
        return self.round >= self.max_rounds

    @property
    def can_secure(self) -> bool:
        return (
            not self.is_final_round
            and not self.is_terminal
            and len(self.secured_offers) < MAX_SECURED_OFFERS
        )

    def activate(self) -> None:
        if self.state != NegotiationState.PENDING:
            raise NegotiationError(
                f"Cannot activate negotiation in state {self.state.value}. "
                f"Expected PENDING."
            )
        self.state = NegotiationState.ACTIVE
        self.round = 1

    def agree(self, label: CardLabel) -> TermValues:
        self._require_active("agree")
        terms = self._get_card_terms(label)
        self.agreed_terms = terms
        self.state = NegotiationState.ACCEPTED
        return terms

    def agree_secured(self, index: int) -> TermValues:
        """Agree to a previously secured offer by index."""
        self._require_active("agree_secured")
        if index < 0 or index >= len(self.secured_offers):
            raise NegotiationError(
                f"Invalid secured offer index {index}. "
                f"Have {len(self.secured_offers)} secured offers."
            )
        terms = self.secured_offers[index].offer.terms
        self.agreed_terms = terms
        self.state = NegotiationState.ACCEPTED
        return terms

    def secure(self, label: CardLabel, operator_utility: float) -> SecuredOffer:
        """Secure a card as fallback. Advances the round. Max 3."""
        self._require_active("secure")
        if len(self.secured_offers) >= MAX_SECURED_OFFERS:
            raise NegotiationError(
                f"Cannot secure: already have {MAX_SECURED_OFFERS} secured offers."
            )
        if self.is_final_round:
            raise NegotiationError(
                f"Cannot secure on the final round ({self.round}/{self.max_rounds})."
            )
        terms = self._get_card_terms(label)
        from back.domain.types import Offer

        secured = SecuredOffer(
            offer=Offer(label=label, terms=terms),
            round_secured=self.round,
            operator_utility=operator_utility,
        )
        self.secured_offers.append(secured)
        self.round += 1
        return secured

    def improve(self, improve_term: str, trade_term: str | None) -> None:
        """Signal preference and advance to the next round."""
        self._require_active("improve")
        if self.is_final_round:
            raise NegotiationError(
                f"Cannot improve on the final round ({self.round}/{self.max_rounds})."
            )
        self.opponent_model.signal_improve(improve_term, trade_term)
        self.round += 1

    def finalize_no_deal(self) -> None:
        self._require_active("finalize_no_deal")
        self.state = NegotiationState.NO_DEAL

    def set_meso_set(self, meso_set: MesoSet) -> None:
        self.current_meso_set = meso_set
        self.history.append(meso_set)

    def _require_active(self, action: str) -> None:
        if self.is_terminal:
            raise NegotiationError(
                f"Cannot {action}: negotiation is already in terminal state "
                f"{self.state.value}."
            )
        if self.state != NegotiationState.ACTIVE:
            raise NegotiationError(
                f"Cannot {action}: negotiation is not active "
                f"(current state: {self.state.value})."
            )

    def _get_card_terms(self, label: CardLabel) -> TermValues:
        if self.current_meso_set is None:
            raise NegotiationError(
                "No MESO set has been generated yet. "
                "Call GetOffersUseCase first."
            )
        meso = self.current_meso_set
        if label == CardLabel.BEST_PRICE:
            return meso.best_price.terms
        elif label == CardLabel.MOST_BALANCED:
            return meso.most_balanced.terms
        else:
            return meso.fastest_payment.terms
