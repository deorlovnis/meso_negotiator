"""Negotiation aggregate root — state machine and round progression.

The Negotiation entity is the central domain object. All mutations go through
its methods. External code cannot directly modify state, round counter, or
opponent model — this prevents invariant violations.

State machine:
    PENDING -> ACTIVE (activate)
    ACTIVE -> ACCEPTED (agree)
    ACTIVE -> NO_DEAL (finalize_no_deal)
    ACTIVE stays ACTIVE for: improve, secure

Terminal states: ACCEPTED, NO_DEAL — no further actions are permitted.

Round rules:
- Improve is the only action that advances the round.
- Secure alone does not advance the round.
- Agree closes the negotiation without advancing.
- On the final round (round == max_rounds), Improve is NOT available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from back.domain.exceptions import NegotiationError
from back.domain.types import (
    CardLabel,
    MesoSet,
    NegotiationState,
    TermConfig,
    TermValues,
    Weights,
)

if TYPE_CHECKING:
    from back.domain.opponent_model import OpponentModel

# Re-exported for backward compatibility: existing code that does
# `from back.domain.negotiation import NegotiationError` continues to work.
__all__ = ["Negotiation", "NegotiationError"]


@dataclass
class Negotiation:
    """Aggregate root for a negotiation session.

    Holds all state for one negotiation between an operator configuration
    and a specific supplier. Methods enforce the state machine and invariants.

    Attributes:
        id: Unique identifier for this negotiation.
        state: Current state machine state.
        round: Current round number (1-indexed, starts at 1 after activate).
        max_rounds: Maximum allowed rounds (from operator config).
        config: Term configurations keyed by "price", "payment", "delivery",
                "contract".
        operator_weights: Fixed operator MAUT weights.
        opponent_model: Mutable supplier preference model (owned by this entity).
        current_meso_set: The current 3-card set displayed to the supplier.
                          None until first MESO generation.
        secured_offer: The most recently secured offer terms, or None.
        agreed_terms: Final agreed terms if state is ACCEPTED, else None.
        history: Ordered list of all MESO sets shown, one per round.
    """

    id: str
    state: NegotiationState
    round: int
    max_rounds: int
    config: dict[str, TermConfig]
    operator_weights: Weights
    opponent_model: OpponentModel
    current_meso_set: MesoSet | None = field(default=None)
    secured_offer: TermValues | None = field(default=None)
    agreed_terms: TermValues | None = field(default=None)
    history: list[MesoSet] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        """True if the negotiation has ended (Accepted or No Deal)."""
        return self.state in (NegotiationState.ACCEPTED, NegotiationState.NO_DEAL)

    @property
    def is_final_round(self) -> bool:
        """True if Improve is no longer available (current round is the last)."""
        return self.round >= self.max_rounds

    def activate(self) -> None:
        """Transition from PENDING to ACTIVE.

        Called when the supplier first views the negotiation. Sets round to 1.

        Raises:
            NegotiationError: If state is not PENDING.
        """
        if self.state != NegotiationState.PENDING:
            raise NegotiationError(
                f"Cannot activate negotiation in state {self.state.value}. "
                f"Expected PENDING."
            )
        self.state = NegotiationState.ACTIVE
        self.round = 1

    def agree(self, label: CardLabel) -> TermValues:
        """Accept a card and close the negotiation.

        Transitions to ACCEPTED. Records agreed terms from the current MESO set.

        Args:
            label: Which card the supplier agreed to.

        Returns:
            The agreed TermValues.

        Raises:
            NegotiationError: If state is not ACTIVE or no MESO set exists.
        """
        self._require_active("agree")
        terms = self._get_card_terms(label)
        self.agreed_terms = terms
        self.state = NegotiationState.ACCEPTED
        return terms

    def secure(self, label: CardLabel) -> TermValues:
        """Mark a card as the supplier's fallback position.

        Does NOT advance the round. Replaces any previously secured offer.
        Updates the opponent model utility floor via signal_secure.

        Args:
            label: Which card to secure.

        Returns:
            The secured TermValues.

        Raises:
            NegotiationError: If state is not ACTIVE or no MESO set exists.
        """
        self._require_active("secure")
        terms = self._get_card_terms(label)
        self.secured_offer = terms
        # Opponent model floor is updated by the use case (it needs utility)
        return terms

    def improve(self, label: CardLabel) -> None:
        """Signal preference on a card and advance to the next round.

        Updates opponent model via signal_improve, then advances the round.

        Args:
            label: Which card the supplier clicked Improve on.

        Raises:
            NegotiationError: If state is not ACTIVE, or if it is the final round
                              (Improve unavailable on last round), or no MESO set.
        """
        self._require_active("improve")
        if self.is_final_round:
            raise NegotiationError(
                f"Cannot improve on the final round ({self.round}/{self.max_rounds}). "
                f"Only Agree or Secure are available."
            )
        self.opponent_model.signal_improve(label)
        self.round += 1

    def finalize_no_deal(self) -> None:
        """Transition to NO_DEAL when the supplier takes no action.

        Called when the supplier exhausts the final round without agreeing.

        Raises:
            NegotiationError: If state is not ACTIVE.
        """
        self._require_active("finalize_no_deal")
        self.state = NegotiationState.NO_DEAL

    def set_meso_set(self, meso_set: MesoSet) -> None:
        """Store the current MESO set and append it to history.

        Called by use cases after generating a new MESO set.
        """
        self.current_meso_set = meso_set
        self.history.append(meso_set)

    def _require_active(self, action: str) -> None:
        """Raise NegotiationError if state is not ACTIVE."""
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
        """Retrieve terms for a given card label from the current MESO set.

        Raises:
            NegotiationError: If no MESO set has been generated yet.
        """
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
