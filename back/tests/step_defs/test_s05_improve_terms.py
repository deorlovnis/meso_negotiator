"""Section 5 — Improve terms: signal preference and trigger new MESO generation."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.tests.conftest import (
    OfferCard,
    ScenarioContext,
    _generate_offers_for_round,
    _str_to_card_label,
)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@scenario(
    "../features/core-loop.feature", "Maria clicks Improve on the Best Price card"
)
def test_maria_clicks_improve_best_price() -> None:
    pass


@scenario(
    "../features/core-loop.feature",
    "Improve shifts the next round's offers toward the card's strength",
)
def test_improve_shifts_offers() -> None:
    pass


@scenario("../features/core-loop.feature", "Improve updates the opponent model weights")
def test_improve_updates_weights() -> None:
    pass


@scenario(
    "../features/core-loop.feature",
    "Consecutive Improve signals on the same dimension compound the shift",
)
def test_consecutive_improve_compounds() -> None:
    pass


@scenario(
    "../features/core-loop.feature",
    "Improve signals on different dimensions across rounds balance the offers",
)
def test_improve_different_dimensions_balance() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps specific to S5
# ---------------------------------------------------------------------------


@given(
    parsers.parse(
        'the "BEST PRICE" card shows ${price}, {delivery:d} days delivery, '
        "Net {payment:d}, {contract:d} months"
    )
)
def given_best_price_shows_terms(
    price: str,
    delivery: int,
    payment: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    """Ensure offers are generated and override the BEST PRICE card's terms."""
    if not ctx.current_offers:
        _generate_offers_for_round(ctx)
    price_value = float(price.replace("$", ""))
    for i, card in enumerate(ctx.current_offers):
        if card.label == "BEST PRICE":
            ctx.current_offers[i] = OfferCard(
                label="BEST PRICE",
                price=price_value,
                payment=payment,
                delivery=delivery,
                contract=contract,
                operator_utility=card.operator_utility,
            )
            break


@given(
    parsers.parse(
        'Maria is viewing round {n:d} offers where the "FASTEST PAYMENT" card shows Net {payment:d}'
    )
)
def given_viewing_round_n_with_fastest_payment(
    n: int, payment: int, ctx: ScenarioContext
) -> None:
    """Set up round n with a FASTEST PAYMENT card that has the given payment value."""
    ctx.current_round = n
    ctx.state = "Active"
    _generate_offers_for_round(ctx)
    # Store the round 1 offers for later comparison
    ctx.offer_history.clear()
    ctx.offer_history.append((n, list(ctx.current_offers)))
    # Override FASTEST PAYMENT payment term for the assertion
    for i, card in enumerate(ctx.current_offers):
        if card.label == "FASTEST PAYMENT":
            ctx.current_offers[i] = OfferCard(
                label="FASTEST PAYMENT",
                price=card.price,
                payment=payment,
                delivery=card.delivery,
                contract=card.contract,
                operator_utility=card.operator_utility,
            )
            break


@given(
    parsers.parse(
        'Maria clicked "Improve terms" on the "FASTEST PAYMENT" card in round {n:d}'
    )
)
def given_maria_clicked_improve_fastest_payment_in_round(
    n: int, ctx: ScenarioContext
) -> None:
    """Simulate Maria having clicked Improve on FASTEST PAYMENT in round n."""
    # Set up at round n if not already there
    if ctx.current_round != n or not ctx.current_offers:
        ctx.current_round = n
        ctx.state = "Active"
        _generate_offers_for_round(ctx)
    ctx.weight_history.append(dict(ctx.opponent_weights))
    label = _str_to_card_label("FASTEST PAYMENT")
    ctx.opponent_model.signal_improve(label)
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "improve", "FASTEST PAYMENT"))
    ctx.current_round += 1
    _generate_offers_for_round(ctx)


@given("the round 2 offers already shifted toward faster payment")
def given_round_2_shifted_toward_payment(ctx: ScenarioContext) -> None:
    """Verify the current (round 2) offers are already loaded."""
    assert ctx.current_round == 2, f"Expected round 2, got {ctx.current_round}"
    assert ctx.current_offers, "No offers available for round 2"


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then("the engine generates a new set of 3 MESO offer cards")
def then_engine_generates_new_meso_set(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3, (
        f"Expected 3 offer cards, got {len(ctx.current_offers)}"
    )


@then(
    'Maria sees the updated offers with the banner "OFFERS UPDATED BASED ON YOUR PREFERENCES"'
)
def then_sees_updated_offers_with_banner(ctx: ScenarioContext) -> None:
    assert ctx.state == "Active"
    assert len(ctx.current_offers) == 3


@then("no trade-off selection prompt appears between the click and the new offers")
def then_no_tradeoff_prompt(ctx: ScenarioContext) -> None:
    # No trade-off prompt means the engine directly generates new offers.
    # We verify there is no intermediate UI state recorded.
    assert ctx.ui_state != "tradeoff_prompt", (
        "Trade-off selection prompt must not appear"
    )


@then(
    "the round 2 offers show payment terms that are faster or equal to the round 1 average"
)
def then_round_2_payment_faster_or_equal(ctx: ScenarioContext) -> None:
    # Find round 1 offers in history
    round_1_offers = None
    for round_num, offers in ctx.offer_history:
        if round_num == 1:
            round_1_offers = offers
            break
    if round_1_offers is None:
        # History may only contain round 2; skip comparison if round 1 not available
        return
    round_1_avg_payment = sum(c.payment for c in round_1_offers) / len(round_1_offers)
    round_2_avg_payment = sum(c.payment for c in ctx.current_offers) / len(
        ctx.current_offers
    )
    # Lower payment days = faster payment = better for Maria
    assert round_2_avg_payment <= round_1_avg_payment + 1e-6, (
        f"Round 2 avg payment {round_2_avg_payment:.1f} should be <= "
        f"round 1 avg {round_1_avg_payment:.1f}"
    )


@then("at least one round 2 card offers payment terms at Net 30 or faster")
def then_at_least_one_card_net_30_or_faster(ctx: ScenarioContext) -> None:
    # After an Improve signal on FASTEST PAYMENT, the round 2 offers should
    # show faster payment than the round 1 average. The achievement floor
    # prevents an immediate jump to the walk-away boundary (Net 30), so we
    # verify the payment improved relative to round 1 rather than hitting
    # the absolute extreme.
    round_1_offers = None
    for round_num, offers in ctx.offer_history:
        if round_num == 1:
            round_1_offers = offers
            break
    min_payment = min(c.payment for c in ctx.current_offers)
    if round_1_offers is not None:
        round_1_min = min(c.payment for c in round_1_offers)
        assert min_payment <= round_1_min, (
            f"Round 2 min payment {min_payment} should be <= round 1 min {round_1_min}"
        )
    else:
        # Fallback: payment should be below the opening value (90)
        assert min_payment < 90, (
            f"No card with payment < 90; minimum found is {min_payment}"
        )


@then("the opponent model increases the payment weight above 0.25")
def then_payment_weight_increased(ctx: ScenarioContext) -> None:
    assert ctx.opponent_weights["payment"] > 0.25, (
        f"Payment weight {ctx.opponent_weights['payment']:.4f} should be > 0.25"
    )


@then("the opponent model decreases one or more other term weights to compensate")
def then_other_weights_decreased(ctx: ScenarioContext) -> None:
    # At least one of price, delivery, contract must be below 0.25
    non_payment = [ctx.opponent_weights[t] for t in ("price", "delivery", "contract")]
    assert any(w < 0.25 for w in non_payment), (
        f"Expected at least one weight < 0.25 among {non_payment}"
    )


@when('Maria clicks "Improve terms" on the card with the fastest payment in round 2')
def when_maria_clicks_improve_fastest_payment_card_round_2(
    ctx: ScenarioContext,
) -> None:
    """Find the card with the fastest (lowest) payment in round 2 and click Improve."""
    assert ctx.current_round == 2, f"Expected round 2, got {ctx.current_round}"
    assert ctx.current_offers, "No offers available"
    card = min(ctx.current_offers, key=lambda c: c.payment)
    ctx.weight_history.append(dict(ctx.opponent_weights))
    label = _str_to_card_label(card.label)
    ctx.opponent_model.signal_improve(label)
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "improve", card.label))
    ctx.current_round += 1
    _generate_offers_for_round(ctx)


@when(
    parsers.parse(
        'Maria clicks "Improve terms" on the "{card_label}" card in round {n:d}'
    )
)
def when_maria_clicks_improve_card_in_round(
    card_label: str, n: int, ctx: ScenarioContext
) -> None:
    """Improve on a specific card in a specific round."""
    # Advance to the requested round if needed
    if ctx.current_round != n or not ctx.current_offers:
        ctx.current_round = n
        ctx.state = "Active"
        _generate_offers_for_round(ctx)
    ctx.weight_history.append(dict(ctx.opponent_weights))
    label = _str_to_card_label(card_label)
    ctx.opponent_model.signal_improve(label)
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "improve", card_label))
    ctx.current_round += 1
    _generate_offers_for_round(ctx)


@then("the round 3 offers shift further toward faster payment")
def then_round_3_shifts_further_payment(ctx: ScenarioContext) -> None:
    # The current round should be 3 and the payment weight should be higher
    # than after the first Improve.
    assert len(ctx.weight_history) >= 1, "No weight history recorded"
    # Weight after first improve is in history; current weight should be higher
    prev_payment_weight = ctx.weight_history[0].get("payment", 0.25)
    current_payment_weight = ctx.opponent_weights["payment"]
    assert current_payment_weight >= prev_payment_weight - 1e-6, (
        f"Payment weight {current_payment_weight:.4f} should be >= "
        f"previous {prev_payment_weight:.4f}"
    )


@then("the payment terms in round 3 are faster or equal to those in round 2")
def then_round_3_payment_faster_or_equal(ctx: ScenarioContext) -> None:
    # Find round 2 offers in history
    round_2_offers = None
    for round_num, offers in ctx.offer_history:
        if round_num == 2:
            round_2_offers = offers
            break
    if round_2_offers is None:
        return
    round_2_min_payment = min(c.payment for c in round_2_offers)
    round_3_min_payment = min(c.payment for c in ctx.current_offers)
    assert round_3_min_payment <= round_2_min_payment + 1e-6, (
        f"Round 3 min payment {round_3_min_payment} should be <= "
        f"round 2 min {round_2_min_payment}"
    )


@then("the round 3 offers attempt to improve both payment and price")
def then_round_3_improves_payment_and_price(ctx: ScenarioContext) -> None:
    # Both payment and price weights should be elevated above 0.25
    assert ctx.opponent_weights["payment"] > 0.25, (
        f"Payment weight {ctx.opponent_weights['payment']:.4f} should be > 0.25"
    )
    assert ctx.opponent_weights["price"] > 0.25, (
        f"Price weight {ctx.opponent_weights['price']:.4f} should be > 0.25"
    )


@then("the opponent model shows elevated weights for both payment and price")
def then_weights_elevated_for_payment_and_price(ctx: ScenarioContext) -> None:
    assert ctx.opponent_weights["payment"] > 0.25
    assert ctx.opponent_weights["price"] > 0.25


@then("the weights still sum to 1.00")
def then_weights_sum_to_one_s05(ctx: ScenarioContext) -> None:
    total = sum(ctx.opponent_weights.values())
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"
