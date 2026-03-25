"""Section 3 — Agree: accept deal and close negotiation."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then

from back.tests.conftest import (
    OfferCard,
    ScenarioContext,
    _generate_offers_for_round,
)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@scenario("../features/core-loop.feature", "Maria agrees to the Most Balanced offer")
def test_maria_agrees_to_most_balanced() -> None:
    pass


@scenario(
    "../features/core-loop.feature",
    "Maria agrees on the first round without further negotiation",
)
def test_maria_agrees_first_round() -> None:
    pass


@scenario(
    "../features/core-loop.feature",
    "Agree is available on every round including the final round",
)
def test_agree_available_on_final_round() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps specific to S3
# ---------------------------------------------------------------------------


@given(
    parsers.parse(
        'the "MOST BALANCED" card shows ${price}, {delivery:d} days delivery, '
        "Net {payment:d}, {contract:d} months"
    )
)
def given_most_balanced_shows_terms(
    price: str,
    delivery: int,
    payment: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    """Ensure offers are generated and override the MOST BALANCED card's terms
    with the values specified in the scenario so downstream Then steps can
    check the exact agreed terms."""
    if not ctx.current_offers:
        _generate_offers_for_round(ctx)
    price_value = float(price.replace("$", ""))
    for i, card in enumerate(ctx.current_offers):
        if card.label == "MOST BALANCED":
            ctx.current_offers[i] = OfferCard(
                label="MOST BALANCED",
                price=price_value,
                payment=payment,
                delivery=delivery,
                contract=contract,
                operator_utility=card.operator_utility,
            )
            break


# (When steps for "Agree on any card" and "presents the final round's offers"
#  are defined in conftest.py to be available across all section files.)


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then(
    parsers.parse(
        "the final agreed terms are ${price} price, {delivery:d}-day delivery, "
        "Net {payment:d} payment, {contract:d}-month contract"
    )
)
def then_final_agreed_terms(
    price: str,
    delivery: int,
    payment: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    price_value = float(price.replace("$", ""))
    assert ctx.agreed_terms is not None, "No agreed terms recorded"
    assert ctx.agreed_terms.price == price_value, (
        f"Agreed price {ctx.agreed_terms.price} != {price_value}"
    )
    assert ctx.agreed_terms.delivery == delivery, (
        f"Agreed delivery {ctx.agreed_terms.delivery} != {delivery}"
    )
    assert ctx.agreed_terms.payment == payment, (
        f"Agreed payment {ctx.agreed_terms.payment} != {payment}"
    )
    assert ctx.agreed_terms.contract == contract, (
        f"Agreed contract {ctx.agreed_terms.contract} != {contract}"
    )


@then("Maria sees a deal summary confirming the accepted terms")
def then_sees_deal_summary(ctx: ScenarioContext) -> None:
    assert ctx.state == "Accepted"
    assert ctx.agreed_terms is not None


@then("the deal closes with that card's terms")
def then_deal_closes_with_card_terms(ctx: ScenarioContext) -> None:
    assert ctx.state == "Accepted"
    assert ctx.agreed_terms is not None


@then("the negotiation ends after a single round")
def then_negotiation_ends_after_single_round(ctx: ScenarioContext) -> None:
    assert ctx.current_round == 1, f"Expected round 1, got {ctx.current_round}"
    assert ctx.state == "Accepted"


@then('each card still shows the "Agree" button')
def then_each_card_still_shows_agree(ctx: ScenarioContext) -> None:
    # On the final round, Agree is available on all 3 cards.
    assert len(ctx.current_offers) == 3


@then('Maria can close the deal by clicking "Agree" on any card')
def then_maria_can_close_deal(ctx: ScenarioContext) -> None:
    # Verify the negotiation is still Active (Agree not yet clicked).
    assert ctx.state == "Active"
    assert len(ctx.current_offers) == 3
