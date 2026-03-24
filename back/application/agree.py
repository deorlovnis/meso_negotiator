"""AgreeUseCase — v2: supports agreeing to current card or secured offer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from back.domain.negotiation import NegotiationError

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository
    from back.domain.types import CardLabel, TermValues


@dataclass(frozen=True)
class AgreeDTO:
    status: str
    agreed_terms: TermValues


class AgreeUseCase:
    def __init__(self, repo: NegotiationRepository) -> None:
        self._repo = repo

    def execute(
        self,
        negotiation_id: str,
        label: CardLabel | None = None,
        secured_index: int | None = None,
    ) -> AgreeDTO:
        negotiation = self._repo.get(negotiation_id)

        if negotiation.is_terminal:
            raise NegotiationError(
                f"Cannot agree: negotiation {negotiation_id} is in "
                f"terminal state {negotiation.state.value}."
            )

        if secured_index is not None:
            agreed_terms = negotiation.agree_secured(secured_index)
        elif label is not None:
            agreed_terms = negotiation.agree(label)
        else:
            raise NegotiationError("Must provide either card_label or secured_index.")

        negotiation.opponent_model.signal_agree()
        self._repo.save(negotiation)

        return AgreeDTO(status="accepted", agreed_terms=agreed_terms)
