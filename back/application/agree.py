"""AgreeUseCase — accept a card and close the negotiation.

This use case:
1. Validates the negotiation is ACTIVE.
2. Calls negotiation.agree(label) which transitions to ACCEPTED and records
   the agreed terms.
3. Calls opponent_model.signal_agree() to reinforce current weights.
4. Saves the updated negotiation.
5. Returns agreed terms DTO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from back.domain.negotiation import NegotiationError

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository
    from back.domain.types import CardLabel, TermValues


@dataclass(frozen=True)
class AgreeDTO:
    """Response for the POST /agree endpoint."""

    status: str
    agreed_terms: TermValues


class AgreeUseCase:
    """Accept a card and finalize the negotiation as Accepted."""

    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(self, negotiation_id: str, label: CardLabel) -> AgreeDTO:
        """Process an Agree action.

        Args:
            negotiation_id: ID of the negotiation to close.
            label: Card label the supplier agreed to.

        Returns:
            AgreeDTO with final agreed terms.

        Raises:
            NegotiationError: If negotiation is already in a terminal state.
        """
        negotiation = self._repo.get(negotiation_id)

        if negotiation.is_terminal:
            raise NegotiationError(
                f"Cannot agree: negotiation {negotiation_id} is in "
                f"terminal state {negotiation.state.value}."
            )

        agreed_terms = negotiation.agree(label)
        negotiation.opponent_model.signal_agree()
        self._repo.save(negotiation)

        return AgreeDTO(status="accepted", agreed_terms=agreed_terms)
