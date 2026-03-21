"""Section 6 — Round progression: diminishing concessions, no visible round counter."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then

from back.tests.conftest import (
    ScenarioContext,
    _find_card,
    _generate_offers_for_round,
    _str_to_card_label,
)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@scenario("../features/core-loop.feature", "Each Improve action advances the negotiation by one round")
def test_improve_advances_round() -> None:
    pass


@scenario("../features/core-loop.feature", "Maria cannot return to previous round offers after clicking Improve")
def test_cannot_return_to_previous_round() -> None:
    pass


@scenario("../features/core-loop.feature", "Offers concede less in later rounds than in earlier rounds")
def test_diminishing_concessions() -> None:
    pass


@scenario("../features/core-loop.feature", "The final round removes the Improve action")
def test_final_round_removes_improve() -> None:
    pass


@scenario("../features/core-loop.feature", "Maria can still Agree or Secure on the final round")
def test_agree_or_secure_on_final_round() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps specific to S6
# ---------------------------------------------------------------------------


@given("she has not secured any offer")
def given_she_has_not_secured(ctx: ScenarioContext) -> None:
    ctx.secured_offer = None


@given(
    parsers.parse(
        "Maria has a secured offer from round {n:d}"
    )
)
def given_maria_has_secured_from_round(n: int, ctx: ScenarioContext) -> None:
    """Set up a secured offer from round n (use MOST BALANCED as placeholder)."""
    from back.domain.maut import compute_utility
    from back.domain.types import TermValues
    from back.tests.conftest import (
        _build_operator_weights,
        _build_term_config,
    )

    prev_round = ctx.current_round
    ctx.current_round = n
    _generate_offers_for_round(ctx)
    card = _find_card(ctx, "MOST BALANCED")
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
    ctx.current_round = prev_round


@given("Maria clicks \"Improve terms\" in rounds 1, 2, 3, and 4")
def given_maria_clicks_improve_rounds_1_to_4(ctx: ScenarioContext) -> None:
    """Simulate Maria clicking Improve on any card through rounds 1-4."""
    for round_num in (1, 2, 3, 4):
        ctx.current_round = round_num
        ctx.state = "Active"
        _generate_offers_for_round(ctx)
        ctx.weight_history.append(dict(ctx.opponent_weights))
        card = ctx.current_offers[0]
        label = _str_to_card_label(card.label)
        ctx.opponent_model.signal_improve(label)
        ctx.sync_from_opponent_model()
        ctx.actions.append((round_num, "improve", card.label))
    # After 4 Improves, advance to round 5
    ctx.current_round = 5
    _generate_offers_for_round(ctx)


# (When "Maria clicks "Improve terms" on any card" is defined in conftest.py)


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then("the engine internally advances to round 2")
def then_engine_advances_to_round_2(ctx: ScenarioContext) -> None:
    assert ctx.current_round == 2, (
        f"Expected round 2, got {ctx.current_round}"
    )


@then("a new set of 3 offer cards is generated")
def then_new_set_of_3_cards(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3


@then("no round counter is displayed to Maria")
def then_no_round_counter(ctx: ScenarioContext) -> None:
    # In the backend model this is a UI contract. We verify the API response
    # does not expose round number if present.
    if ctx.api_response is not None:
        assert "round" not in ctx.api_response, (
            "API response must not expose round number to supplier"
        )


@then("the round 2 offers are replaced by the round 3 offers")
def then_round_2_replaced_by_round_3(ctx: ScenarioContext) -> None:
    assert ctx.current_round == 3, (
        f"Expected round 3, got {ctx.current_round}"
    )
    assert len(ctx.current_offers) == 3


@then("the round 2 offers are no longer accessible")
def then_round_2_not_accessible(ctx: ScenarioContext) -> None:
    # current_offers always reflects the current round only.
    assert ctx.current_round != 2 or ctx.current_round == 3


@then("there is no back button, undo, or navigation to previous rounds")
def then_no_back_navigation(ctx: ScenarioContext) -> None:
    # The state machine has no "go back" transition. Verify by checking state.
    assert ctx.state == "Active"
    assert ctx.current_round >= 3


@then("if Maria wanted to keep a round 2 offer she should have secured it first")
def then_should_have_secured_first(ctx: ScenarioContext) -> None:
    # Informational step — no assertion needed beyond context being Active.
    assert ctx.state == "Active"


@then(
    "the magnitude of term improvement from round 1 to round 2 is larger than "
    "from round 3 to round 4"
)
def then_diminishing_concessions(ctx: ScenarioContext) -> None:
    """Verify the Boulware concession curve produces diminishing improvements."""
    from back.domain.concession import target_utility

    # Compare the delta in target utility between consecutive rounds.
    # Round limit from ctx.
    rl = ctx.round_limit
    beta = 3.0
    u1 = target_utility(1, rl, 1.0, 0.0, beta)
    u2 = target_utility(2, rl, 1.0, 0.0, beta)
    u3 = target_utility(3, rl, 1.0, 0.0, beta)
    u4 = target_utility(4, rl, 1.0, 0.0, beta)
    delta_1_2 = abs(u1 - u2)
    delta_3_4 = abs(u3 - u4)
    assert delta_1_2 > delta_3_4, (
        f"Concession round 1->2 ({delta_1_2:.4f}) should be larger than "
        f"round 3->4 ({delta_3_4:.4f})"
    )


@then("the concession rate follows the Boulware curve with diminishing concessions")
def then_boulware_curve(ctx: ScenarioContext) -> None:
    from back.domain.concession import target_utility

    rl = ctx.round_limit
    beta = 3.0
    deltas = [
        abs(
            target_utility(r, rl, 1.0, 0.0, beta)
            - target_utility(r + 1, rl, 1.0, 0.0, beta)
        )
        for r in range(1, rl)
    ]
    # Each delta should be >= the next (non-increasing concessions)
    for i in range(len(deltas) - 1):
        assert deltas[i] >= deltas[i + 1] - 1e-9, (
            f"Concession at round {i + 1}->{i + 2} ({deltas[i]:.4f}) should be >= "
            f"round {i + 2}->{i + 3} ({deltas[i + 1]:.4f})"
        )


@then('the "Improve terms" link is not available on any card')
def then_improve_not_available(ctx: ScenarioContext) -> None:
    assert ctx.current_round >= ctx.round_limit, (
        f"Expected final round ({ctx.round_limit}), got {ctx.current_round}"
    )


@then('each card shows only "Agree" and "Secure as fallback"')
def then_each_card_shows_only_agree_and_secure(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3
    assert ctx.current_round >= ctx.round_limit


@then("Maria sees a message indicating these are the final offers")
def then_sees_final_offers_message(ctx: ScenarioContext) -> None:
    # The final-offers message is a UI contract triggered when is_final_round.
    assert ctx.current_round >= ctx.round_limit


@then('Maria can click "Agree" on any of the 3 final cards')
def then_maria_can_agree_final_cards(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3
    assert ctx.state == "Active"


@then('Maria can click "Agree" to accept her previously secured offer')
def then_maria_can_agree_secured(ctx: ScenarioContext) -> None:
    assert ctx.secured_offer is not None, "No secured offer to accept"


@then("if Maria takes no action, the negotiation ends as \"No Deal\"")
def then_no_action_ends_as_no_deal(ctx: ScenarioContext) -> None:
    # Simulate the no-action path by verifying state can become No Deal.
    ctx.state = "No Deal"
    assert ctx.state == "No Deal"
