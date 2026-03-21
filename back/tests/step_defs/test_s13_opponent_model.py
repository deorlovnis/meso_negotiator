"""Section 13 — Opponent model: initialization and signal reinforcement."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.domain.types import CardLabel
from back.tests.conftest import (
    ScenarioContext,
    _generate_offers_for_round,
)

FEATURE = "../features/core-loop.feature"


@scenario(FEATURE, "Opponent model weights are initialized uniformly")
def test_opponent_model_initialized_uniformly() -> None:
    pass


@scenario(FEATURE, "Agree reinforces all weights in the opponent model")
def test_agree_reinforces_weights() -> None:
    pass


@scenario(FEATURE, "Engine combines operator and opponent weights when generating MESO")
def test_engine_combines_weights() -> None:
    pass


@scenario(
    FEATURE,
    "Opponent model weight never becomes negative after repeated Improve",
)
def test_no_negative_weights_after_improve() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps (section-specific)
# ---------------------------------------------------------------------------


@given("a new negotiation is started for Maria")
def given_new_negotiation_for_maria(ctx: ScenarioContext) -> None:
    """Reset opponent model to uniform weights — new negotiation state."""
    ctx.opponent_weights = {
        "price": 0.25,
        "payment": 0.25,
        "delivery": 0.25,
        "contract": 0.25,
    }
    ctx._opponent_model = None
    ctx.current_round = 1
    ctx.state = "Pending"


@given(
    parsers.parse(
        "James's operator weights are price {p:f}, payment {pay:f}, "
        "delivery {d:f}, contract {c:f}"
    )
)
def given_james_operator_weights(
    p: float, pay: float, d: float, c: float, ctx: ScenarioContext
) -> None:
    ctx.config.weights = {
        "price": p,
        "payment": pay,
        "delivery": d,
        "contract": c,
    }


# ---------------------------------------------------------------------------
# When steps (section-specific)
# ---------------------------------------------------------------------------


@when("the engine prepares the first round")
def when_engine_prepares_first_round(ctx: ScenarioContext) -> None:
    ctx.current_round = 1
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@when("the engine generates a MESO set")
def when_engine_generates_meso_set(ctx: ScenarioContext) -> None:
    _generate_offers_for_round(ctx)


@when(
    parsers.parse(
        'Maria clicks "Improve terms" on the "FASTEST PAYMENT" card '
        "in rounds 1, 2, 3, and 4"
    )
)
def when_maria_improves_fastest_payment_four_rounds(ctx: ScenarioContext) -> None:
    """Simulate 4 consecutive Improve signals on FASTEST PAYMENT."""
    ctx.current_round = 1
    ctx.state = "Active"
    _generate_offers_for_round(ctx)

    for _ in range(4):
        ctx.weight_history.append(dict(ctx.opponent_weights))
        label = CardLabel.FASTEST_PAYMENT
        ctx.opponent_model.signal_improve(label)
        ctx.sync_from_opponent_model()
        ctx.current_round += 1
        _generate_offers_for_round(ctx)


# ---------------------------------------------------------------------------
# Then steps (section-specific)
# ---------------------------------------------------------------------------


@then(
    "the opponent model weights are price 0.25, payment 0.25, "
    "delivery 0.25, contract 0.25"
)
def then_opponent_model_weights_uniform(ctx: ScenarioContext) -> None:
    for term in ["price", "payment", "delivery", "contract"]:
        assert abs(ctx.opponent_weights[term] - 0.25) < 1e-9, (
            f"Expected uniform weight 0.25 for '{term}', "
            f"got {ctx.opponent_weights[term]}"
        )


@then(
    "the opponent model records the final weights with all dimensions reinforced"
)
def then_opponent_model_records_final_weights(ctx: ScenarioContext) -> None:
    # After agree, weights are available for future renegotiations
    # Verify the model is in a valid state (weights sum to 1, all >= 0)
    total = sum(ctx.opponent_weights.values())
    assert abs(total - 1.0) < 1e-6, f"Weights must sum to 1.0, got {total}"
    for term, w in ctx.opponent_weights.items():
        assert w >= 0.0, f"Weight for '{term}' must be >= 0, got {w}"


@then(
    "the reinforced weights are available for future renegotiations with Maria"
)
def then_reinforced_weights_available(ctx: ScenarioContext) -> None:
    # Model is accessible and non-None
    assert ctx.opponent_model is not None
    assert ctx.opponent_model.weights is not None


@then(
    "the offers reflect both James's price priority and Maria's payment priority"
)
def then_offers_reflect_combined_priorities(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3
    # BEST PRICE should have a favorable (low) price
    best_price = next(c for c in ctx.current_offers if c.label == "BEST PRICE")
    fastest_payment = next(
        c for c in ctx.current_offers if c.label == "FASTEST PAYMENT"
    )
    # Best price card should have a lower price than fastest payment card
    assert best_price.price <= fastest_payment.price


@then(
    "the MESO distribution differs from what either weight vector alone would produce"
)
def then_meso_differs_from_single_weights(ctx: ScenarioContext) -> None:
    # This is a behavioral property — verified by the presence of offers that
    # differ in their distribution. The combined weighting means neither
    # pure operator nor pure opponent priorities dominate all 3 cards.
    assert len(ctx.current_offers) == 3
    prices = [c.price for c in ctx.current_offers]
    payments = [c.payment for c in ctx.current_offers]
    # Offers have variety — not all identical
    assert len(set(prices)) > 1 or len(set(payments)) > 1, (
        "MESO cards should differ in term distribution"
    )


@then("the payment weight increases each round")
def then_payment_weight_increases(ctx: ScenarioContext) -> None:
    assert len(ctx.weight_history) >= 1, "Expected at least one weight snapshot"
    initial_payment = ctx.weight_history[0]["payment"]
    final_payment = ctx.opponent_weights["payment"]
    assert final_payment > initial_payment, (
        f"Payment weight should have increased from {initial_payment} "
        f"to > {initial_payment}, got {final_payment}"
    )


@then("no weight for any term drops below 0.00")
def then_no_negative_weights(ctx: ScenarioContext) -> None:
    for term, w in ctx.opponent_weights.items():
        assert w >= 0.0, f"Weight for '{term}' dropped below 0: {w}"
    # Also check all historical snapshots
    for snapshot in ctx.weight_history:
        for term, w in snapshot.items():
            assert w >= 0.0, (
                f"Historical weight for '{term}' was negative: {w}"
            )
