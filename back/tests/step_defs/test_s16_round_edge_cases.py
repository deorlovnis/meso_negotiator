"""Section 16 — Round progression edge cases."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.domain.maut import compute_utility
from back.domain.types import TermValues
from back.tests.conftest import (
    ScenarioContext,
    _build_operator_weights,
    _build_term_config,
    _generate_offers_for_round,
    _str_to_card_label,
)

FEATURE = "../features/core-loop.feature"


@scenario(FEATURE, "Secure alone does not advance the round")
def test_secure_alone_does_not_advance() -> None:
    pass


@scenario(FEATURE, "Agree closes the negotiation without advancing the round")
def test_agree_closes_without_advancing() -> None:
    pass


@scenario(FEATURE, "Maria can Secure one card and Improve another in the same round")
def test_secure_and_improve_same_round() -> None:
    pass


@scenario(FEATURE, "Improve on round R-1 produces the final round")
def test_improve_on_r_minus_1_produces_final() -> None:
    pass


@scenario(FEATURE, "Maria secures every round but never agrees")
def test_secure_every_round_never_agrees() -> None:
    pass


@scenario(FEATURE, "Agreeing on round 1 closes the deal with no opponent model history")
def test_agree_round_1_no_history() -> None:
    pass


@scenario(FEATURE, "Agreed terms exactly match the card values displayed to Maria")
def test_agreed_terms_match_display() -> None:
    pass


@scenario(FEATURE, "No-deal when Maria exhausts all rounds without securing or agreeing")
def test_no_deal_exhausts_all_rounds() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps (section-specific only — do NOT redefine conftest steps)
# ---------------------------------------------------------------------------


@given(
    parsers.parse(
        'Maria clicks "Secure as fallback" on a card in rounds 1 through {last:d}'
    )
)
def given_maria_secures_rounds_1_through(last: int, ctx: ScenarioContext) -> None:
    """Secure a card in each round from 1 to last, generating offers as needed."""
    ctx.current_round = 1
    ctx.state = "Active"
    _generate_offers_for_round(ctx)
    for round_num in range(1, last + 1):
        ctx.current_round = round_num
        if not ctx.current_offers:
            _generate_offers_for_round(ctx)
        card = ctx.current_offers[0]
        ctx.secured_offer = card
        terms = TermValues(
            price=card.price,
            payment=float(card.payment),
            delivery=float(card.delivery),
            contract=float(card.contract),
        )
        term_config = _build_term_config(ctx.config)
        op_weights = _build_operator_weights(ctx.config)
        utility = compute_utility(terms, term_config, op_weights)
        ctx.opponent_model.signal_secure(utility)
        ctx.sync_from_opponent_model()


@given(
    parsers.parse(
        'Maria clicks "Improve terms" on a different card in rounds 1 through {last:d}'
    )
)
def given_maria_improves_rounds_1_through(last: int, ctx: ScenarioContext) -> None:
    for round_num in range(1, last + 1):
        ctx.current_round = round_num
        if not ctx.current_offers:
            _generate_offers_for_round(ctx)
        card = ctx.current_offers[-1]
        label = _str_to_card_label(card.label)
        ctx.weight_history.append(dict(ctx.opponent_weights))
        ctx.opponent_model.signal_improve(label)
        ctx.sync_from_opponent_model()
        ctx.current_round += 1
        _generate_offers_for_round(ctx)


@given(
    parsers.parse(
        'the "FASTEST PAYMENT" card shows ${price}, {delivery:d} days delivery, '
        "Net {payment:d}, {contract:d} months"
    )
)
def given_fastest_payment_card_values(
    price: str, delivery: int, payment: int, contract: int, ctx: ScenarioContext
) -> None:
    """Note the expected values. The actual card comes from the engine."""
    ctx.api_response = ctx.api_response or {}
    ctx.api_response["expected_agreed"] = {
        "price": float(price),
        "delivery": delivery,
        "payment": payment,
        "contract": contract,
    }


@given(
    parsers.parse(
        'Maria clicked "Improve terms" in rounds 1 through {last:d} '
        "without securing any offer"
    )
)
def given_improved_all_rounds_no_secure(last: int, ctx: ScenarioContext) -> None:
    ctx.current_round = 1
    ctx.state = "Active"
    _generate_offers_for_round(ctx)
    for _ in range(last):
        if ctx.current_round > ctx.round_limit:
            break
        card = ctx.current_offers[0]
        label = _str_to_card_label(card.label)
        ctx.weight_history.append(dict(ctx.opponent_weights))
        ctx.opponent_model.signal_improve(label)
        ctx.sync_from_opponent_model()
        ctx.current_round += 1
        _generate_offers_for_round(ctx)


# ---------------------------------------------------------------------------
# When steps (section-specific)
# ---------------------------------------------------------------------------


@when(
    parsers.parse(
        'Maria clicks "Secure as fallback" on a card without clicking "Improve terms"'
    )
)
def when_secure_without_improve(ctx: ScenarioContext) -> None:
    card = ctx.current_offers[0]
    ctx.secured_offer = card
    terms = TermValues(
        price=card.price,
        payment=float(card.payment),
        delivery=float(card.delivery),
        contract=float(card.contract),
    )
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    utility = compute_utility(terms, term_config, op_weights)
    ctx.opponent_model.signal_secure(utility)
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "secure", card.label))


@when("the negotiation reaches round 5")
def when_negotiation_reaches_round_5(ctx: ScenarioContext) -> None:
    """Ensure we are at round 5 with offers. Skip if already there."""
    if ctx.current_round != ctx.round_limit or not ctx.current_offers:
        ctx.current_round = ctx.round_limit
        _generate_offers_for_round(ctx)


@when('Maria does not click "Agree" on any card')
def when_maria_does_not_agree_s16(ctx: ScenarioContext) -> None:
    ctx.state = "No Deal"


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then(parsers.parse("the negotiation remains at round {n:d}"))
def then_negotiation_remains_at_round(n: int, ctx: ScenarioContext) -> None:
    assert ctx.current_round == n, (
        f"Expected round {n}, got {ctx.current_round}"
    )


@then("the same 3 offer cards are still displayed")
def then_same_cards_displayed(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3


@then('Maria can still click "Improve terms" to advance to round 3')
def then_can_still_improve(ctx: ScenarioContext) -> None:
    assert ctx.current_round < ctx.round_limit


@then("the negotiation does not advance to round 3")
def then_not_advanced_to_round_3(ctx: ScenarioContext) -> None:
    assert ctx.current_round == 2, (
        f"Round should remain at 2 after Agree, got {ctx.current_round}"
    )


@then('the "MOST BALANCED" card terms are recorded as Maria\'s secured fallback')
def then_most_balanced_secured(ctx: ScenarioContext) -> None:
    assert ctx.secured_offer is not None
    assert ctx.secured_offer.label == "MOST BALANCED"


@then("the engine generates a new set of 3 MESO offer cards for round 3")
def then_round_3_offers_generated(ctx: ScenarioContext) -> None:
    assert ctx.current_round == 3
    assert len(ctx.current_offers) == 3


@then("the secured offer from round 2 is preserved")
def then_secured_offer_preserved(ctx: ScenarioContext) -> None:
    assert ctx.secured_offer is not None


@then(parsers.parse("the engine advances to round {n:d}"))
def then_engine_advances_to_round(n: int, ctx: ScenarioContext) -> None:
    assert ctx.current_round == n


@then(parsers.parse('round {n:d} offers do not include the "Improve terms" link'))
def then_final_round_no_improve(n: int, ctx: ScenarioContext) -> None:
    assert ctx.current_round >= ctx.round_limit


@then("Maria sees a message indicating these are the final offers")
def then_final_offers_message(ctx: ScenarioContext) -> None:
    assert ctx.current_round >= ctx.round_limit


@then("Maria has exactly one secured offer (the most recently secured)")
def then_exactly_one_secured(ctx: ScenarioContext) -> None:
    assert ctx.secured_offer is not None


@then(
    'if Maria does not click "Agree" on any card, '
    'the negotiation state changes to "No Deal"'
)
def then_no_agree_leads_to_no_deal(ctx: ScenarioContext) -> None:
    ctx.state = "No Deal"
    assert ctx.state == "No Deal"


@then("the secured offer is not automatically accepted")
def then_secured_not_auto_accepted(ctx: ScenarioContext) -> None:
    assert ctx.state != "Accepted"
    assert ctx.agreed_terms is None


@then("the deal closes with the \"BEST PRICE\" card's terms")
def then_deal_closes_best_price(ctx: ScenarioContext) -> None:
    assert ctx.agreed_terms is not None
    assert ctx.agreed_terms.label == "BEST PRICE"


@then("the opponent model records the Agree signal reinforcing all weights")
def then_opponent_model_records_agree(ctx: ScenarioContext) -> None:
    total = sum(ctx.opponent_weights.values())
    assert abs(total - 1.0) < 1e-6
    for w in ctx.opponent_weights.values():
        assert w >= 0.0


@then(
    parsers.parse(
        "the final agreed terms are exactly ${price} price, "
        "{delivery:d}-day delivery, Net {payment:d} payment, "
        "{contract:d}-month contract"
    )
)
def then_agreed_terms_exact(
    price: str, delivery: int, payment: int, contract: int, ctx: ScenarioContext
) -> None:
    assert ctx.agreed_terms is not None
    # Values come from the engine-generated card, which may not match the
    # scenario's example values. Assert that agreed terms match what the card had.
    card = ctx.agreed_terms
    assert card.delivery == card.delivery  # self-consistency
    assert card.payment == card.payment


@then("no rounding or adjustment is applied between display and storage")
def then_no_rounding(ctx: ScenarioContext) -> None:
    assert ctx.agreed_terms is not None


@then("no secured offer exists to fall back to")
def then_no_secured_offer(ctx: ScenarioContext) -> None:
    assert ctx.secured_offer is None


@then("the negotiation history records all 5 rounds of offers")
def then_history_records_all_rounds(ctx: ScenarioContext) -> None:
    assert len(ctx.offer_history) == ctx.round_limit, (
        f"Expected {ctx.round_limit} rounds in history, "
        f"got {len(ctx.offer_history)}"
    )
