"""Section 4 — Secure as fallback: mark a card as reservation value."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.domain.maut import compute_utility
from back.domain.types import TermValues
from back.tests.conftest import (
    OfferCard,
    ScenarioContext,
    _build_operator_weights,
    _build_term_config,
    _find_card,
    _generate_offers_for_round,
)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@scenario("../features/core-loop.feature", "Maria secures an offer and the negotiation continues")
def test_maria_secures_offer() -> None:
    pass


@scenario("../features/core-loop.feature", "Only one offer can be secured at a time")
def test_only_one_offer_secured() -> None:
    pass


@scenario("../features/core-loop.feature", "Secured offer is preserved across rounds")
def test_secured_offer_preserved() -> None:
    pass


@scenario("../features/core-loop.feature", "Securing updates the opponent model utility floor")
def test_securing_updates_utility_floor() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps specific to S4
# ---------------------------------------------------------------------------


@given(
    parsers.parse(
        'the "FASTEST PAYMENT" card shows ${price}, {delivery:d} days delivery, '
        "Net {payment:d}, {contract:d} months"
    )
)
def given_fastest_payment_shows_terms(
    price: str,
    delivery: int,
    payment: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    """Ensure offers are generated and override the FASTEST PAYMENT card's terms."""
    if not ctx.current_offers:
        _generate_offers_for_round(ctx)
    price_value = float(price.replace("$", ""))
    for i, card in enumerate(ctx.current_offers):
        if card.label == "FASTEST PAYMENT":
            ctx.current_offers[i] = OfferCard(
                label="FASTEST PAYMENT",
                price=price_value,
                payment=payment,
                delivery=delivery,
                contract=contract,
                operator_utility=card.operator_utility,
            )
            break


@given(
    parsers.parse(
        'Maria previously secured the "FASTEST PAYMENT" card in round {n:d}'
    )
)
def given_maria_previously_secured_fastest_payment(
    n: int, ctx: ScenarioContext
) -> None:
    """Set up a previously secured FASTEST PAYMENT card from round n."""
    # Generate offers for round n and secure the FASTEST PAYMENT card
    prev_round = ctx.current_round
    ctx.current_round = n
    _generate_offers_for_round(ctx)
    card = _find_card(ctx, "FASTEST PAYMENT")
    ctx.secured_offer = card
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    terms = TermValues(
        price=card.price,
        payment=float(card.payment),
        delivery=float(card.delivery),
        contract=float(card.contract),
    )
    utility = compute_utility(terms, term_config, op_weights)
    ctx.opponent_model.signal_secure(utility)
    ctx.sync_from_opponent_model()
    # Restore round and regenerate for the current round
    ctx.current_round = prev_round


@given(parsers.parse("she is now viewing round {n:d} offers"))
def given_she_is_now_viewing_round_n(n: int, ctx: ScenarioContext) -> None:
    ctx.current_round = n
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@given(
    parsers.parse(
        "Maria secured an offer showing ${price}, Net {payment:d}, "
        "{delivery:d} days, {contract:d} months in round {n:d}"
    )
)
def given_maria_secured_offer_in_round(
    price: str,
    payment: int,
    delivery: int,
    contract: int,
    n: int,
    ctx: ScenarioContext,
) -> None:
    """Record a secured offer with specific terms from a past round."""
    price_value = float(price.replace("$", ""))
    secured = OfferCard(
        label="FASTEST PAYMENT",
        price=price_value,
        payment=payment,
        delivery=delivery,
        contract=contract,
    )
    ctx.secured_offer = secured
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    terms = TermValues(
        price=price_value,
        payment=float(payment),
        delivery=float(delivery),
        contract=float(contract),
    )
    utility = compute_utility(terms, term_config, op_weights)
    ctx.opponent_model.signal_secure(utility)
    ctx.sync_from_opponent_model()


@given(parsers.parse("the negotiation is now in round {n:d}"))
def given_negotiation_is_now_in_round(n: int, ctx: ScenarioContext) -> None:
    ctx.current_round = n
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@given("the opponent model has no utility floor set")
def given_no_utility_floor(ctx: ScenarioContext) -> None:
    ctx.utility_floor = None
    ctx.opponent_model._utility_floor = None


# ---------------------------------------------------------------------------
# When steps specific to S4
# ---------------------------------------------------------------------------


@when(
    parsers.parse(
        'Maria clicks "Secure as fallback" on a card with operator utility {utility:f}'
    )
)
def when_maria_secures_card_with_utility(
    utility: float, ctx: ScenarioContext
) -> None:
    """Secure the card whose operator utility is closest to the given value."""
    if not ctx.current_offers:
        _generate_offers_for_round(ctx)
    # Find the card closest to the stated utility
    card = min(
        ctx.current_offers,
        key=lambda c: abs(c.operator_utility - utility),
    )
    ctx.secured_offer = card
    ctx.opponent_model.signal_secure(utility)
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "secure", card.label))


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then("the card is visually marked as her secured fallback")
def then_card_marked_as_secured(ctx: ScenarioContext) -> None:
    assert ctx.secured_offer is not None, "No secured offer recorded"


@then("the negotiation does not end")
def then_negotiation_does_not_end(ctx: ScenarioContext) -> None:
    assert ctx.state == "Active", (
        f"Expected state 'Active', got '{ctx.state}'"
    )


@then('Maria can still click "Improve terms" on any card to continue negotiating')
def then_improve_still_available(ctx: ScenarioContext) -> None:
    assert ctx.state == "Active"
    assert ctx.current_round < ctx.round_limit, (
        f"Cannot improve: at final round {ctx.current_round}/{ctx.round_limit}"
    )
    assert len(ctx.current_offers) == 3


@then('the "MOST BALANCED" card is marked as her new secured fallback')
def then_most_balanced_is_new_secured(ctx: ScenarioContext) -> None:
    assert ctx.secured_offer is not None
    assert ctx.secured_offer.label == "MOST BALANCED", (
        f"Expected MOST BALANCED as secured, got {ctx.secured_offer.label}"
    )


@then("the previously secured offer is no longer marked")
def then_previously_secured_no_longer_marked(ctx: ScenarioContext) -> None:
    # Only one secured offer at a time; the new one replaced the old one.
    assert ctx.secured_offer is not None
    assert ctx.secured_offer.label != "FASTEST PAYMENT", (
        "FASTEST PAYMENT should no longer be the secured offer"
    )


@then(
    parsers.parse(
        "the secured offer terms remain recorded at "
        "${price}, Net {payment:d}, {delivery:d} days, {contract:d} months"
    )
)
def then_secured_terms_remain(
    price: str,
    payment: int,
    delivery: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    price_value = float(price.replace("$", ""))
    assert ctx.secured_offer is not None, "No secured offer recorded"
    assert ctx.secured_offer.price == price_value
    assert ctx.secured_offer.payment == payment
    assert ctx.secured_offer.delivery == delivery
    assert ctx.secured_offer.contract == contract


@then("the secured offer is available as an option on the final round")
def then_secured_available_on_final_round(ctx: ScenarioContext) -> None:
    assert ctx.secured_offer is not None, "No secured offer to offer on the final round"


@then("the engine records a supplier utility floor based on the secured offer")
def then_utility_floor_recorded(ctx: ScenarioContext) -> None:
    assert ctx.utility_floor is not None, "Utility floor was not recorded"
    assert ctx.utility_floor > 0.0, (
        f"Utility floor {ctx.utility_floor} should be positive"
    )


@then("subsequent MESO offers account for the secured terms as an acceptable threshold")
def then_meso_accounts_for_floor(ctx: ScenarioContext) -> None:
    # The opponent model stores the utility floor; future MESO generation
    # will not produce offers below this threshold.
    assert ctx.opponent_model.utility_floor is not None
    assert ctx.opponent_model.utility_floor > 0.0
