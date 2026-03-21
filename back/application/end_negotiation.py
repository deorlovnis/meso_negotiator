"""EndNegotiationUseCase — finalize a negotiation as No Deal.

This use case:
1. Validates the negotiation is ACTIVE.
2. Calls negotiation.finalize_no_deal() to transition to NO_DEAL.
3. Saves the updated negotiation.
4. Returns a No Deal confirmation DTO.

Called when the supplier takes no action on the final round, or explicitly
ends the negotiation without agreeing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from back.domain.negotiation import NegotiationError

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository


@dataclass(frozen=True)
class EndNegotiationDTO:
    """Response for the POST /end endpoint."""

    status: str


class EndNegotiationUseCase:
    """Transition negotiation to No Deal state."""

    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(self, negotiation_id: str) -> EndNegotiationDTO:
        """Process a no-deal finalization.

        Args:
            negotiation_id: ID of the negotiation to close as No Deal.

        Returns:
            EndNegotiationDTO with status "no_deal".

        Raises:
            NegotiationError: If negotiation is already in a terminal state.
        """
        negotiation = self._repo.get(negotiation_id)

        if negotiation.is_terminal:
            raise NegotiationError(
                f"Cannot end negotiation: {negotiation_id} is already in "
                f"terminal state {negotiation.state.value}."
            )

        negotiation.finalize_no_deal()
        self._repo.save(negotiation)

        return EndNegotiationDTO(status="no_deal")
