"""SecureUseCase — mark a card as the supplier's fallback.

This use case:
1. Validates the negotiation is ACTIVE.
2. Calls negotiation.secure(label) to record the secured offer.
3. Computes the operator utility of the secured offer.
4. Updates opponent model utility floor via signal_secure.
5. Saves the updated negotiation.
6. Returns the secured offer DTO.

Does NOT advance the round — securing is a passive action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from back.domain.maut import compute_utility
from back.domain.negotiation import NegotiationError

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository
    from back.domain.types import CardLabel, TermValues


@dataclass(frozen=True)
class SecureDTO:
    """Response for the POST /secure endpoint."""

    secured_offer: TermValues


class SecureUseCase:
    """Mark a card as the supplier's fallback reservation value."""

    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(self, negotiation_id: str, label: CardLabel) -> SecureDTO:
        """Process a Secure action.

        Args:
            negotiation_id: ID of the negotiation to update.
            label: Card label the supplier secured as fallback.

        Returns:
            SecureDTO confirming the secured offer terms.

        Raises:
            NegotiationError: If negotiation is in a terminal state.
        """
        negotiation = self._repo.get(negotiation_id)

        if negotiation.is_terminal:
            raise NegotiationError(
                f"Cannot secure: negotiation {negotiation_id} is in "
                f"terminal state {negotiation.state.value}."
            )

        secured_terms = negotiation.secure(label)

        # Compute operator utility for the secured offer to set the floor
        utility = compute_utility(
            terms=secured_terms,
            config=negotiation.config,
            weights=negotiation.operator_weights,
        )
        negotiation.opponent_model.signal_secure(utility)
        self._repo.save(negotiation)

        return SecureDTO(secured_offer=secured_terms)
