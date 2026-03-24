"""ImproveUseCase — v2: explicit term selection, advance round, new MESO set."""

from __future__ import annotations

from typing import TYPE_CHECKING

from back.application.get_offers import OffersDTO, _build_actions, _build_cards
from back.config import get_settings
from back.domain import concession as concession_module
from back.domain import meso as meso_module
from back.domain.negotiation import NegotiationError

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository


class ImproveUseCase:
    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(
        self,
        negotiation_id: str,
        improve_term: str,
        trade_term: str | None,
    ) -> OffersDTO:
        negotiation = self._repo.get(negotiation_id)

        if negotiation.is_terminal:
            raise NegotiationError(
                f"Cannot improve: negotiation {negotiation_id} is in "
                f"terminal state {negotiation.state.value}."
            )

        negotiation.improve(improve_term, trade_term)

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

        cards = _build_cards(meso_set)
        actions = _build_actions(negotiation.is_final_round, negotiation.can_secure)

        return OffersDTO(
            banner="OFFERS UPDATED BASED ON YOUR PREFERENCES",
            is_final_round=negotiation.is_final_round,
            is_first_visit=False,
            cards=cards,
            secured_offers=negotiation.secured_offers,
            can_secure=negotiation.can_secure,
            actions_available=actions,
        )
