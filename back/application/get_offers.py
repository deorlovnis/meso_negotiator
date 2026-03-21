"""GetOffersUseCase — load negotiation and return current MESO set.

This use case:
1. Loads the negotiation by ID.
2. If PENDING, activates it (first visit) and generates the opening MESO set.
3. Returns the 3 cards stripped of operator utility — the supplier never sees
   internal scoring (ISP: return only what the supplier UI needs).

Output:
- Card labels, term values, signal indicators (which terms are strong)
- Whether Improve is available (false on final round)
- Whether this is the first visit (is_first_visit=True for PENDING->ACTIVE)
- Currently secured offer, if any
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from back.domain import concession as concession_module
from back.domain import meso as meso_module
from back.domain.negotiation import NegotiationError
from back.domain.types import CardLabel, MesoSet, NegotiationState, Offer, TermValues

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository

# Default Boulware beta parameter
_DEFAULT_BETA = 2.0
# Opening utility: offer starts at operator's maximum possible utility
_OPENING_UTILITY = 1.0
# Walkaway utility: minimum acceptable utility (floor prevents card collapse)
_WALKAWAY_UTILITY = 0.15


@dataclass(frozen=True)
class TermSignals:
    """Visual signal indicators for each term on a card.

    'good' = strong relative to the card's label profile.
    'neutral' = average.
    """

    price: str
    payment: str
    delivery: str
    contract: str


@dataclass(frozen=True)
class CardDTO:
    """Supplier-facing representation of one MESO offer card."""

    label: str
    recommended: bool
    terms: TermValues
    signals: TermSignals


@dataclass(frozen=True)
class OffersDTO:
    """Full response for the GET /offers endpoint and POST /improve response."""

    banner: str
    is_final_round: bool
    is_first_visit: bool
    cards: list[CardDTO]
    secured_offer: TermValues | None
    actions_available: list[str]


class GetOffersUseCase:
    """Load negotiation and return current MESO set for the supplier UI."""

    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(self, negotiation_id: str) -> OffersDTO:
        """Load and return the current offers for a negotiation.

        Activates PENDING negotiations on first call.

        Args:
            negotiation_id: ID of the negotiation to load.

        Returns:
            OffersDTO with cards stripped of utility scores.
        """
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
            # Generate opening MESO set
            target = concession_module.target_utility(
                round=negotiation.round,
                max_rounds=negotiation.max_rounds,
                opening_utility=_OPENING_UTILITY,
                walkaway_utility=_WALKAWAY_UTILITY,
                beta=_DEFAULT_BETA,
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
        actions = _build_actions(negotiation.is_final_round)

        return OffersDTO(
            banner="OFFERS UPDATED BASED ON YOUR PREFERENCES",
            is_final_round=negotiation.is_final_round,
            is_first_visit=is_first_visit,
            cards=cards,
            secured_offer=negotiation.secured_offer,
            actions_available=actions,
        )


def _build_cards(meso_set: MesoSet) -> list[CardDTO]:
    """Convert a MesoSet into supplier-facing CardDTOs."""
    return [
        _card_dto(meso_set.best_price, recommended=False),
        _card_dto(meso_set.most_balanced, recommended=True),
        _card_dto(meso_set.fastest_payment, recommended=False),
    ]


def _card_dto(offer: Offer, recommended: bool) -> CardDTO:
    """Build a CardDTO from an Offer, computing signal indicators."""
    label_str = offer.label.value.replace("_", " ")
    signals = _compute_signals(offer.label)
    return CardDTO(
        label=label_str,
        recommended=recommended,
        terms=offer.terms,
        signals=signals,
    )


def _compute_signals(label: CardLabel) -> TermSignals:
    """Compute visual signals for each term based on the card's label profile.

    The 'strength' term for each profile shows 'good'. Others show 'neutral'.
    """
    if label == CardLabel.BEST_PRICE:
        return TermSignals(
            price="good", payment="neutral", delivery="good", contract="neutral"
        )
    elif label == CardLabel.FASTEST_PAYMENT:
        return TermSignals(
            price="neutral", payment="good", delivery="neutral", contract="neutral"
        )
    else:  # MOST_BALANCED
        return TermSignals(
            price="good", payment="good", delivery="good", contract="good"
        )


def _build_actions(is_final_round: bool) -> list[str]:
    """Build the list of available actions for the current round."""
    actions = ["agree", "secure"]
    if not is_final_round:
        actions.append("improve")
    return actions
