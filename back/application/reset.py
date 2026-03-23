"""ResetUseCase — reset a negotiation to its initial PENDING state.

Extracted from routes.py:reset_negotiation (the 28-line inline domain
construction). Business logic belongs in use cases, not route handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from back.domain.defaults import DEFAULT_OPERATOR_WEIGHTS, make_default_config
from back.domain.negotiation import Negotiation
from back.domain.opponent_model import OpponentModel
from back.domain.types import NegotiationState

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository


@dataclass(frozen=True)
class ResetDTO:
    """Output of ResetUseCase.execute."""

    status: str
    negotiation_id: str


class ResetUseCase:
    """Reset a negotiation to its initial PENDING state.

    Creates a fresh Negotiation with the canonical default configuration and
    persists it, replacing any existing negotiation with the same ID.
    """

    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(self, negotiation_id: str) -> ResetDTO:
        """Reset the negotiation identified by negotiation_id.

        Creates a new PENDING negotiation with the standard default config,
        overwriting any existing negotiation with that ID.

        Args:
            negotiation_id: The ID of the negotiation to reset.

        Returns:
            ResetDTO with status="reset" and the negotiation ID.
        """
        negotiation = Negotiation(
            id=negotiation_id,
            state=NegotiationState.PENDING,
            round=0,
            max_rounds=5,
            config=make_default_config(),
            operator_weights=DEFAULT_OPERATOR_WEIGHTS,
            opponent_model=OpponentModel.uniform(),
        )
        self._repo.save(negotiation)
        return ResetDTO(status="reset", negotiation_id=negotiation_id)
