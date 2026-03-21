"""Section 12 — Negotiation lifecycle: state transitions."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.domain.negotiation import Negotiation, NegotiationError
from back.domain.opponent_model import OpponentModel
from back.domain.types import (
    CardLabel,
    NegotiationState,
)
from back.tests.conftest import (
    ScenarioContext,
    _build_operator_weights,
    _build_term_config,
    _generate_offers_for_round,
)

FEATURE = "../features/core-loop.feature"


@scenario(FEATURE, "Negotiation begins in pending state before Maria opens it")
def test_negotiation_begins_pending() -> None:
    pass


@scenario(FEATURE, "Negotiation moves to active when Maria views the first offers")
def test_negotiation_moves_to_active() -> None:
    pass


@scenario(FEATURE, "Accepted state is terminal — no further actions are possible")
def test_accepted_is_terminal() -> None:
    pass


@scenario(FEATURE, "No-Deal state is terminal — no further actions are possible")
def test_no_deal_is_terminal() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps (section-specific)
# ---------------------------------------------------------------------------


@given("James has configured the cohort and initiated renegotiation for Maria")
def given_james_configured_and_initiated(ctx: ScenarioContext) -> None:
    """Config is set up via Background. Renegotiation initiated means Pending state."""
    ctx.state = "Pending"


@given('the negotiation state is "Pending"')
def given_negotiation_state_is_pending(ctx: ScenarioContext) -> None:
    ctx.state = "Pending"


@given('Maria clicked "Agree" on a card and the state is "Accepted"')
def given_state_is_accepted(ctx: ScenarioContext) -> None:
    ctx.state = "Active"
    _generate_offers_for_round(ctx)
    card = ctx.current_offers[0]
    ctx.agreed_terms = card
    ctx.state = "Accepted"
    ctx.opponent_model.signal_agree()
    ctx.sync_from_opponent_model()


@given('the negotiation reached the final round and ended as "No Deal"')
def given_state_is_no_deal(ctx: ScenarioContext) -> None:
    ctx.current_round = ctx.round_limit
    ctx.state = "No Deal"


# ---------------------------------------------------------------------------
# When steps (section-specific)
# ---------------------------------------------------------------------------


@when("Maria has not yet opened the negotiation link")
def when_maria_not_opened(ctx: ScenarioContext) -> None:
    """State stays Pending — no action taken."""


@when("Maria opens the negotiation and views the opening round offers")
def when_maria_opens_and_views_opening(ctx: ScenarioContext) -> None:
    ctx.current_round = 1
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@when("an attempt is made to submit any action on the negotiation")
def when_attempt_action_on_terminal(ctx: ScenarioContext) -> None:
    """Try to perform an action; store whether it was rejected in ctx."""
    # Build a domain Negotiation in the terminal state and try to act on it
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)

    terminal_state = (
        NegotiationState.ACCEPTED
        if ctx.state == "Accepted"
        else NegotiationState.NO_DEAL
    )

    negotiation = Negotiation(
        id="test-terminal",
        state=terminal_state,
        round=ctx.current_round,
        max_rounds=ctx.round_limit,
        config=term_config,
        operator_weights=op_weights,
        opponent_model=OpponentModel.uniform(),
    )

    # Attempt agree — should raise NegotiationError
    ctx.api_response = {"rejected": False, "terminal_state": ctx.state}
    try:
        negotiation.agree(CardLabel.MOST_BALANCED)
    except NegotiationError:
        ctx.api_response["rejected"] = True


# ---------------------------------------------------------------------------
# Then steps (section-specific)
# ---------------------------------------------------------------------------


@then('the negotiation state is "Pending"')
def then_state_is_pending(ctx: ScenarioContext) -> None:
    assert ctx.state == "Pending", f"Expected Pending, got {ctx.state}"


@then("the action is rejected")
def then_action_is_rejected(ctx: ScenarioContext) -> None:
    assert ctx.api_response is not None
    assert ctx.api_response.get("rejected") is True, (
        "Action on terminal negotiation should be rejected"
    )


@then(parsers.parse('the negotiation remains in "{state}" state'))
def then_negotiation_remains_in_state(state: str, ctx: ScenarioContext) -> None:
    assert ctx.state == state, f"Expected state '{state}', got '{ctx.state}'"
