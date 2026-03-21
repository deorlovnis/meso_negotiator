"""ImproveUseCase — signal preference and generate new MESO set.

This use case:
1. Validates the negotiation is ACTIVE and not on the final round.
2. Calls negotiation.improve(label) which updates the opponent model and
   advances the round.
3. Computes the new target utility from the Boulware concession curve.
4. Generates a new MESO set biased toward the supplier's inferred preferences.
5. Saves the updated negotiation.
6. Returns new offers DTO (same shape as GetOffersUseCase output).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from back.application.get_offers import OffersDTO, _build_actions, _build_cards
from back.domain import concession as concession_module
from back.domain import meso as meso_module
from back.domain.negotiation import NegotiationError

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository
    from back.domain.types import CardLabel

_DEFAULT_BETA = 2.0
_OPENING_UTILITY = 1.0
_WALKAWAY_UTILITY = 0.35


class ImproveUseCase:
    """Signal supplier preference and advance to the next round."""

    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(self, negotiation_id: str, label: CardLabel) -> OffersDTO:
        """Process an Improve action and return new offers.

        Args:
            negotiation_id: ID of the negotiation to update.
            label: Card label the supplier clicked Improve on.

        Returns:
            OffersDTO with new 3-card MESO set.

        Raises:
            NegotiationError: If negotiation is terminal or on final round.
        """
        negotiation = self._repo.get(negotiation_id)

        if negotiation.is_terminal:
            raise NegotiationError(
                f"Cannot improve: negotiation {negotiation_id} is in "
                f"terminal state {negotiation.state.value}."
            )

        # negotiation.improve updates opponent model and advances round
        negotiation.improve(label)

        # Generate new MESO set with updated opponent weights + concession curve
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

        cards = _build_cards(meso_set)
        actions = _build_actions(negotiation.is_final_round)

        return OffersDTO(
            banner="OFFERS UPDATED BASED ON YOUR PREFERENCES",
            is_final_round=negotiation.is_final_round,
            is_first_visit=False,
            cards=cards,
            secured_offer=negotiation.secured_offer,
            actions_available=actions,
        )
