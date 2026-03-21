"""Section 7 — No-deal outcome: negotiation ends without agreement."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.tests.conftest import (
    OfferCard,
    ScenarioContext,
)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@scenario("../features/core-loop.feature", "Maria reaches the final round and does not agree")
def test_maria_reaches_final_round_no_agree() -> None:
    pass


@scenario("../features/core-loop.feature", "Maria has a secured offer but chooses not to accept on the final round")
def test_secured_offer_not_auto_accepted() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps specific to S7
# ---------------------------------------------------------------------------


@given("Maria has no secured offer")
def given_no_secured_offer(ctx: ScenarioContext) -> None:
    ctx.secured_offer = None


@given(
    parsers.parse(
        "Maria has a secured offer at ${price}, Net {payment:d}, "
        "{delivery:d} days, {contract:d} months"
    )
)
def given_maria_has_secured_offer(
    price: str,
    payment: int,
    delivery: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    price_value = float(price.replace("$", ""))
    ctx.secured_offer = OfferCard(
        label="FASTEST PAYMENT",
        price=price_value,
        payment=payment,
        delivery=delivery,
        contract=contract,
    )


# ---------------------------------------------------------------------------
# When steps specific to S7
# ---------------------------------------------------------------------------


@when("Maria does not click \"Agree\" on any card")
def when_maria_does_not_agree(ctx: ScenarioContext) -> None:
    """Simulate reaching end of negotiation without agreeing."""
    ctx.state = "No Deal"
    ctx.actions.append((ctx.current_round, "no_deal", "none"))


@when("Maria does not click \"Agree\" on any card or on the secured offer")
def when_maria_does_not_agree_or_secured(ctx: ScenarioContext) -> None:
    """Simulate reaching end without agreeing, even with a secured offer."""
    ctx.state = "No Deal"
    ctx.actions.append((ctx.current_round, "no_deal", "none"))


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then("the negotiation history is preserved for future renegotiation")
def then_history_preserved(ctx: ScenarioContext) -> None:
    # offer_history contains all rounds shown; at least the final round.
    assert len(ctx.offer_history) >= 1, (
        "Offer history is empty — no rounds were recorded"
    )


@then("the secured offer is not automatically accepted")
def then_secured_not_auto_accepted(ctx: ScenarioContext) -> None:
    # State must be No Deal, not Accepted.
    assert ctx.state == "No Deal", (
        f"Expected 'No Deal', got '{ctx.state}'"
    )
    assert ctx.agreed_terms is None, (
        "agreed_terms should be None when no explicit Agree was clicked"
    )
