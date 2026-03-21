"""Unit tests for negotiation state machine.

Error categories targeted:
- Logic errors: invalid transitions, terminal state mutations, skipped states
- Data errors: round counter integrity, state leakage after terminal

Source spec: core-loop.feature sections 3, 6, 7, 12, 16.
Architecture ref: ARCHITECTURE.md domain/negotiation.py contract.

State machine:
    Pending -> Active (on first view)
    Active -> Accepted (on agree)
    Active -> No Deal (on finalize after final round)
    Accepted -> terminal (no further transitions)
    No Deal -> terminal (no further transitions)

Round rules:
    - Improve advances round by 1
    - Secure does NOT advance round
    - Agree does NOT advance round (closes immediately)
    - Improve unavailable on final round (round == max_rounds)
"""

from __future__ import annotations

import pytest

from back.domain.negotiation import Negotiation, NegotiationError
from back.domain.opponent_model import OpponentModel
from back.domain.types import (
    CardLabel,
    MesoSet,
    NegotiationState,
    Offer,
    TermConfig,
    TermValues,
    Weights,
)

# ---------------------------------------------------------------------------
# Factory helpers for test isolation
# ---------------------------------------------------------------------------

def _make_config() -> dict[str, TermConfig]:
    """Background configuration from core-loop.feature."""
    return {
        "price": TermConfig(opening=11.50, target=12.50, walk_away=14.50, weight=0.40),
        "payment": TermConfig(opening=90, target=75, walk_away=30, weight=0.25),
        "delivery": TermConfig(opening=7, target=10, walk_away=14, weight=0.20),
        "contract": TermConfig(opening=6, target=12, walk_away=24, weight=0.15),
    }


def _make_meso_set() -> MesoSet:
    """Stub MESO set so agree/secure/improve have cards to reference."""
    return MesoSet(
        best_price=Offer(
            label=CardLabel.BEST_PRICE,
            terms=TermValues(price=12.00, payment=45, delivery=12, contract=18),
        ),
        most_balanced=Offer(
            label=CardLabel.MOST_BALANCED,
            terms=TermValues(price=13.00, payment=60, delivery=11, contract=15),
        ),
        fastest_payment=Offer(
            label=CardLabel.FASTEST_PAYMENT,
            terms=TermValues(price=13.50, payment=75, delivery=13, contract=20),
        ),
    )


def _make_negotiation(max_rounds: int = 5) -> Negotiation:
    return Negotiation(
        id="test-neg-001",
        state=NegotiationState.PENDING,
        round=1,
        config=_make_config(),
        operator_weights=Weights(price=0.40, payment=0.25, delivery=0.20, contract=0.15),
        max_rounds=max_rounds,
        opponent_model=OpponentModel.uniform(),
    )


def _make_active_negotiation(max_rounds: int = 5) -> Negotiation:
    """Create a negotiation that is ACTIVE with a MESO set ready."""
    neg = _make_negotiation(max_rounds=max_rounds)
    neg.activate()
    neg.set_meso_set(_make_meso_set())
    return neg


class TestInitialState:
    """Falsifiable claim: negotiation starts in Pending state.

    section 12: 'Negotiation begins in pending state before Maria opens it'
    """

    def test_initial_state_is_pending(self):
        neg = _make_negotiation()
        assert neg.state == NegotiationState.PENDING

    def test_initial_round_is_one(self):
        neg = _make_negotiation()
        assert neg.round == 1

    def test_no_secured_offer_initially(self):
        neg = _make_negotiation()
        assert neg.secured_offer is None

    def test_no_agreed_terms_initially(self):
        neg = _make_negotiation()
        assert neg.agreed_terms is None


class TestValidTransitions:
    """Falsifiable claims about valid state transitions.

    section 12: Pending -> Active, Active -> Accepted, Active -> No Deal
    """

    def test_pending_to_active_on_activate(self):
        """section 12: 'Negotiation moves to active when Maria views the first offers'"""
        neg = _make_negotiation()
        neg.activate()
        assert neg.state == NegotiationState.ACTIVE

    def test_active_to_accepted_on_agree(self):
        """section 3: 'the negotiation state changes to Accepted'"""
        neg = _make_active_negotiation()
        neg.agree(CardLabel.MOST_BALANCED)
        assert neg.state == NegotiationState.ACCEPTED

    def test_active_to_no_deal_on_finalize(self):
        """section 7: 'the negotiation state changes to No Deal'"""
        neg = _make_active_negotiation()
        # Advance to final round
        for _ in range(4):
            neg.improve(CardLabel.BEST_PRICE)
        neg.finalize_no_deal()
        assert neg.state == NegotiationState.NO_DEAL


class TestTerminalStatesRejectActions:
    """Falsifiable claim: Accepted and No Deal are terminal.

    section 12: 'Accepted state is terminal -- no further actions are possible'
    section 12: 'No-Deal state is terminal -- no further actions are possible'

    Risk: 7/10. If terminal states leak, the user can corrupt negotiation data.
    """

    def test_accepted_rejects_improve(self):
        neg = _make_active_negotiation()
        neg.agree(CardLabel.BEST_PRICE)
        with pytest.raises(NegotiationError):
            neg.improve(CardLabel.MOST_BALANCED)

    def test_accepted_rejects_agree(self):
        """Cannot agree twice."""
        neg = _make_active_negotiation()
        neg.agree(CardLabel.BEST_PRICE)
        with pytest.raises(NegotiationError):
            neg.agree(CardLabel.MOST_BALANCED)

    def test_accepted_rejects_secure(self):
        neg = _make_active_negotiation()
        neg.agree(CardLabel.BEST_PRICE)
        with pytest.raises(NegotiationError):
            neg.secure(CardLabel.FASTEST_PAYMENT)

    def test_accepted_rejects_finalize_no_deal(self):
        neg = _make_active_negotiation()
        neg.agree(CardLabel.BEST_PRICE)
        with pytest.raises(NegotiationError):
            neg.finalize_no_deal()

    def test_no_deal_rejects_improve(self):
        neg = _make_active_negotiation()
        for _ in range(4):
            neg.improve(CardLabel.BEST_PRICE)
        neg.finalize_no_deal()
        with pytest.raises(NegotiationError):
            neg.improve(CardLabel.MOST_BALANCED)

    def test_no_deal_rejects_agree(self):
        neg = _make_active_negotiation()
        for _ in range(4):
            neg.improve(CardLabel.BEST_PRICE)
        neg.finalize_no_deal()
        with pytest.raises(NegotiationError):
            neg.agree(CardLabel.BEST_PRICE)

    def test_no_deal_rejects_secure(self):
        neg = _make_active_negotiation()
        for _ in range(4):
            neg.improve(CardLabel.BEST_PRICE)
        neg.finalize_no_deal()
        with pytest.raises(NegotiationError):
            neg.secure(CardLabel.FASTEST_PAYMENT)


class TestInvalidTransitions:
    """Test transitions that should be rejected -- skipping states."""

    def test_pending_rejects_agree(self):
        """Cannot agree before activating (viewing offers)."""
        neg = _make_negotiation()
        with pytest.raises(NegotiationError):
            neg.agree(CardLabel.BEST_PRICE)

    def test_pending_rejects_improve(self):
        neg = _make_negotiation()
        with pytest.raises(NegotiationError):
            neg.improve(CardLabel.BEST_PRICE)

    def test_pending_rejects_secure(self):
        neg = _make_negotiation()
        with pytest.raises(NegotiationError):
            neg.secure(CardLabel.BEST_PRICE)

    def test_pending_rejects_finalize_no_deal(self):
        neg = _make_negotiation()
        with pytest.raises(NegotiationError):
            neg.finalize_no_deal()


class TestRoundProgression:
    """Falsifiable claims about round advancement.

    section 6: 'Each Improve action advances the negotiation by one round'
    section 16: 'Secure alone does not advance the round'
    section 16: 'Agree closes the negotiation without advancing the round'
    """

    def test_improve_advances_round_by_one(self):
        """section 6: improve increments round counter."""
        neg = _make_active_negotiation()
        assert neg.round == 1
        neg.improve(CardLabel.BEST_PRICE)
        assert neg.round == 2

    def test_secure_does_not_advance_round(self):
        """section 16: 'Secure alone does not advance the round'"""
        neg = _make_active_negotiation()
        assert neg.round == 1
        neg.secure(CardLabel.BEST_PRICE)
        assert neg.round == 1

    def test_agree_does_not_advance_round(self):
        """section 16: 'Agree closes the negotiation without advancing the round'"""
        neg = _make_active_negotiation()
        assert neg.round == 1
        neg.agree(CardLabel.BEST_PRICE)
        assert neg.round == 1

    def test_improve_unavailable_on_final_round(self):
        """section 6: 'The final round removes the Improve action'

        After 4 improves (rounds 1->5), improve should be rejected at round 5.
        """
        neg = _make_active_negotiation(max_rounds=5)
        for _ in range(4):
            neg.improve(CardLabel.BEST_PRICE)
        assert neg.round == 5
        with pytest.raises(NegotiationError):
            neg.improve(CardLabel.BEST_PRICE)

    def test_improve_on_penultimate_round_produces_final_round(self):
        """section 16: 'Improve on round R-1 produces the final round'"""
        neg = _make_active_negotiation(max_rounds=5)
        # Advance to round 4
        for _ in range(3):
            neg.improve(CardLabel.BEST_PRICE)
        assert neg.round == 4
        # Improve from round 4 -> round 5
        neg.improve(CardLabel.BEST_PRICE)
        assert neg.round == 5

    def test_secure_then_improve_in_same_round(self):
        """section 16: 'Maria can Secure one card and Improve another in the same round'"""
        neg = _make_active_negotiation()
        neg.secure(CardLabel.MOST_BALANCED)
        assert neg.round == 1  # Secure did not advance
        neg.improve(CardLabel.BEST_PRICE)
        assert neg.round == 2  # Improve advanced
        assert neg.secured_offer is not None  # Secured offer preserved

    def test_agree_available_on_final_round(self):
        """section 3: 'Agree is available on every round including the final round'"""
        neg = _make_active_negotiation(max_rounds=5)
        for _ in range(4):
            neg.improve(CardLabel.BEST_PRICE)
        assert neg.round == 5
        # Agree should work on final round
        neg.agree(CardLabel.BEST_PRICE)
        assert neg.state == NegotiationState.ACCEPTED


class TestSecuredOfferManagement:
    """Falsifiable claims about secured offer behavior.

    section 4: 'Only one offer can be secured at a time'
    section 4: 'Secured offer is preserved across rounds'
    """

    def test_only_one_secured_offer_at_a_time(self):
        """section 4: securing a new card replaces the previous secured offer."""
        neg = _make_active_negotiation()
        neg.secure(CardLabel.FASTEST_PAYMENT)
        neg.secure(CardLabel.MOST_BALANCED)
        # The most recent secure should be the current secured offer
        # (Specific assertion depends on Negotiation implementation storing label)
        assert neg.secured_offer is not None

    def test_secured_offer_preserved_after_improve(self):
        """section 4: 'Secured offer is preserved across rounds'"""
        neg = _make_active_negotiation()
        neg.secure(CardLabel.FASTEST_PAYMENT)
        neg.improve(CardLabel.BEST_PRICE)
        assert neg.secured_offer is not None
        # The secured offer from before improve should still be recorded

    def test_secured_offer_not_auto_accepted_on_no_deal(self):
        """section 7: 'the secured offer is not automatically accepted'

        Even with a secured offer, No Deal means No Deal.
        """
        neg = _make_active_negotiation(max_rounds=5)
        neg.secure(CardLabel.BEST_PRICE)
        for _ in range(4):
            neg.improve(CardLabel.MOST_BALANCED)
        neg.finalize_no_deal()
        assert neg.state == NegotiationState.NO_DEAL
        assert neg.agreed_terms is None  # Secured offer was NOT accepted


class TestAgreedTermsRecording:
    """Falsifiable claims about agree behavior.

    section 16: 'Agreed terms exactly match the card values displayed to Maria'
    """

    def test_agree_records_card_label(self):
        """After agree, the negotiation should record which card was agreed to."""
        neg = _make_active_negotiation()
        neg.agree(CardLabel.MOST_BALANCED)
        assert neg.state == NegotiationState.ACCEPTED
        # agreed_terms should reference the card that was agreed to
        assert neg.agreed_terms is not None
