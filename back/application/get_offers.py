"""GetOffersUseCase — load negotiation and return current MESO set.

V2: secured_offers is a list, signals use 'better'/'neutral'/'worse',
actions depend on can_secure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from back.config import get_settings
from back.domain import concession as concession_module
from back.domain import meso as meso_module
from back.domain.negotiation import NegotiationError
from back.domain.types import (
    CardLabel,
    MesoSet,
    NegotiationState,
    Offer,
    SecuredOffer,
    TermValues,
)

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository


@dataclass(frozen=True)
class TermSignals:
    price: str
    payment: str
    delivery: str
    contract: str


@dataclass(frozen=True)
class CardDTO:
    label: str
    recommended: bool
    terms: TermValues
    signals: TermSignals


@dataclass(frozen=True)
class OffersDTO:
    banner: str
    is_final_round: bool
    is_first_visit: bool
    cards: list[CardDTO]
    secured_offers: list[SecuredOffer]
    can_secure: bool
    actions_available: list[str]


class GetOffersUseCase:
    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(self, negotiation_id: str) -> OffersDTO:
        negotiation = self._repo.get(negotiation_id)
        is_first_visit = False

        if negotiation.state in (NegotiationState.ACCEPTED, NegotiationState.NO_DEAL):
            raise NegotiationError(
                f"Negotiation {negotiation_id} is already terminal "
                f"(state={negotiation.state.value})."
            )

        if negotiation.state == NegotiationState.PENDING:
            negotiation.activate()
            is_first_visit = True
            settings = get_settings()
            target = concession_module.target_utility(
                round=negotiation.round,
                max_rounds=negotiation.max_rounds,
                opening_utility=settings.opening_utility,
                walkaway_utility=settings.walkaway_utility,
                beta=settings.default_beta,
            )
            meso_set = meso_module.generate_meso_set(
                config=negotiation.config,
                operator_weights=negotiation.operator_weights,
                opponent_weights=negotiation.opponent_model.weights,
                target_utility=target,
            )
            negotiation.set_meso_set(meso_set)
            self._repo.save(negotiation)

        meso_set = negotiation.current_meso_set
        if meso_set is None:
            raise RuntimeError(
                f"Negotiation {negotiation_id} is ACTIVE but has no MESO set."
            )

        cards = _build_cards(meso_set)
        actions = _build_actions(negotiation.is_final_round, negotiation.can_secure)

        return OffersDTO(
            banner="OFFERS UPDATED BASED ON YOUR PREFERENCES",
            is_final_round=negotiation.is_final_round,
            is_first_visit=is_first_visit,
            cards=cards,
            secured_offers=negotiation.secured_offers,
            can_secure=negotiation.can_secure,
            actions_available=actions,
        )


def _build_cards(meso_set: MesoSet) -> list[CardDTO]:
    return [
        _card_dto(meso_set.best_price, recommended=False),
        _card_dto(meso_set.most_balanced, recommended=True),
        _card_dto(meso_set.fastest_payment, recommended=False),
    ]


def _card_dto(offer: Offer, recommended: bool) -> CardDTO:
    label_str = offer.label.value.replace("_", " ")
    signals = _compute_signals(offer.label)
    return CardDTO(
        label=label_str,
        recommended=recommended,
        terms=offer.terms,
        signals=signals,
    )


def _compute_signals(label: CardLabel) -> TermSignals:
    """Compute visual signals: 'better' for strength dimension, 'neutral' for others."""
    if label == CardLabel.BEST_PRICE:
        return TermSignals(price="better", payment="neutral", delivery="better", contract="neutral")
    elif label == CardLabel.FASTEST_PAYMENT:
        return TermSignals(price="neutral", payment="better", delivery="neutral", contract="neutral")
    else:  # MOST_BALANCED
        return TermSignals(price="neutral", payment="neutral", delivery="neutral", contract="neutral")


def _build_actions(is_final_round: bool, can_secure: bool = True) -> list[str]:
    if is_final_round:
        return ["agree"]
    actions = ["agree"]
    if can_secure:
        actions.append("secure")
    actions.append("improve")
    return actions
