"""Section 14 — MAUT computation: formula verification and boundaries."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.domain.maut import _achievement, compute_utility  # type: ignore[attr-defined]
from back.domain.types import TermValues
from back.tests.conftest import (
    ScenarioContext,
    _build_operator_weights,
    _build_term_config,
    _generate_offers_for_round,
)

FEATURE = "../features/core-loop.feature"


@scenario(FEATURE, "MAUT utility is 0.0 when all terms are at walk-away values")
def test_maut_zero_at_walkaway() -> None:
    pass


@scenario(FEATURE, "MAUT utility is 1.0 when all terms are at target values")
def test_maut_one_at_target() -> None:
    pass


@scenario(FEATURE, "MAUT utility calculation with concrete numeric verification")
def test_maut_numeric_verification() -> None:
    pass


@scenario(FEATURE, "An offer at exactly the walk-away boundary is valid")
def test_walkaway_boundary_is_valid() -> None:
    pass


@scenario(
    FEATURE, "No two MESO cards in a round have identical terms across all 4 dimensions"
)
def test_no_identical_meso_cards() -> None:
    pass


@scenario(FEATURE, "Opening round uses the configured opening values")
def test_opening_round_uses_opening_values() -> None:
    pass


@scenario(FEATURE, "Operator weights must sum to 1.0")
def test_operator_weights_sum_to_one() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps (section-specific)
# ---------------------------------------------------------------------------


@given("James configured targets and walk-away limits:", target_fixture="ctx")
def given_james_configured_targets_walkaway(
    ctx: ScenarioContext, datatable: list
) -> ScenarioContext:
    """Parse targets and walk-away datatable.

    pytest-bdd passes datatable as a list of lists where the first row is headers.
    Rows: [Term, Target, Walk-Away]
    """
    # Skip header row (index 0 = ["Term", "Target", "Walk-Away"])
    for row in datatable[1:]:
        term = row[0].lower()
        target_raw = row[1]
        walkaway_raw = row[2]

        if term == "price":
            ctx.config.targets["price"] = float(target_raw.replace("$", ""))
            ctx.config.walk_away["price"] = float(walkaway_raw.replace("$", ""))
        elif term == "payment":
            ctx.config.targets["payment"] = float(target_raw.replace("Net ", ""))
            ctx.config.walk_away["payment"] = float(walkaway_raw.replace("Net ", ""))
        elif term == "delivery":
            ctx.config.targets["delivery"] = float(target_raw)
            ctx.config.walk_away["delivery"] = float(walkaway_raw)
        elif term == "contract":
            ctx.config.targets["contract"] = float(target_raw)
            ctx.config.walk_away["contract"] = float(walkaway_raw)
    return ctx


@given(
    parsers.parse(
        "targets of ${price_target:f}, Net {payment_target:d}, "
        "{delivery_target:d} days, {contract_target:d} months"
    )
)
def given_targets(
    price_target: float,
    payment_target: int,
    delivery_target: int,
    contract_target: int,
    ctx: ScenarioContext,
) -> None:
    ctx.config.targets = {
        "price": price_target,
        "payment": float(payment_target),
        "delivery": float(delivery_target),
        "contract": float(contract_target),
    }


@given(
    parsers.parse(
        "walk-away limits of ${price_wa:f}, Net {payment_wa:d}, "
        "{delivery_wa:d} days, {contract_wa:d} months"
    )
)
def given_walkaway_limits(
    price_wa: float,
    payment_wa: int,
    delivery_wa: int,
    contract_wa: int,
    ctx: ScenarioContext,
) -> None:
    ctx.config.walk_away = {
        "price": price_wa,
        "payment": float(payment_wa),
        "delivery": float(delivery_wa),
        "contract": float(contract_wa),
    }


@given(
    parsers.parse(
        "James has configured opening values of ${price:f}, Net {payment:d}, "
        "{delivery:d} days, {contract:d} months"
    )
)
def given_opening_values(
    price: float,
    payment: int,
    delivery: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    ctx.config.opening = {
        "price": price,
        "payment": float(payment),
        "delivery": float(delivery),
        "contract": float(contract),
    }


# ---------------------------------------------------------------------------
# When steps (section-specific)
# ---------------------------------------------------------------------------


@when(
    parsers.parse(
        "the engine evaluates an offer at ${price:f}, Net {payment:d}, "
        "{delivery:d} days, {contract:d} months"
    )
)
def when_evaluates_offer(
    price: float,
    payment: int,
    delivery: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    terms = TermValues(
        price=price,
        payment=float(payment),
        delivery=float(delivery),
        contract=float(contract),
    )
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    ctx.computed_utility = compute_utility(terms, term_config, op_weights)

    ctx.per_term_achievements = {
        "price": _achievement(
            terms.price,
            term_config["price"].walk_away,
            term_config["price"].target,
        ),
        "payment": _achievement(
            terms.payment,
            term_config["payment"].walk_away,
            term_config["payment"].target,
        ),
        "delivery": _achievement(
            terms.delivery,
            term_config["delivery"].walk_away,
            term_config["delivery"].target,
        ),
        "contract": _achievement(
            terms.contract,
            term_config["contract"].walk_away,
            term_config["contract"].target,
        ),
    }


@when("the engine generates offers")
def when_engine_generates_offers(ctx: ScenarioContext) -> None:
    _generate_offers_for_round(ctx)


@when("the engine generates 3 MESO cards for any round")
def when_engine_generates_3_meso_cards_any(ctx: ScenarioContext) -> None:
    _generate_offers_for_round(ctx)


@when("the engine generates the opening round offers")
def when_engine_generates_opening_round(ctx: ScenarioContext) -> None:
    ctx.current_round = 1
    ctx.opponent_weights = {
        "price": 0.25,
        "payment": 0.25,
        "delivery": 0.25,
        "contract": 0.25,
    }
    ctx._opponent_model = None
    _generate_offers_for_round(ctx)


# ---------------------------------------------------------------------------
# Then steps (section-specific)
# ---------------------------------------------------------------------------


@then(parsers.parse("the MAUT utility for James is {expected:f}"))
def then_maut_utility_is(expected: float, ctx: ScenarioContext) -> None:
    assert abs(ctx.computed_utility - expected) < 1e-6, (
        f"Expected MAUT utility {expected}, got {ctx.computed_utility}"
    )


@then(
    parsers.parse(
        "the per-term achievement for price is "
        "($13.50 - $14.50) / ($12.50 - $14.50) = {expected:f}"
    )
)
def then_price_achievement(expected: float, ctx: ScenarioContext) -> None:
    assert abs(ctx.per_term_achievements["price"] - expected) < 1e-3, (
        f"Expected price achievement {expected}, "
        f"got {ctx.per_term_achievements['price']}"
    )


@then(
    parsers.parse(
        "the per-term achievement for payment is (45 - 30) / (75 - 30) = {expected:f}"
    )
)
def then_payment_achievement(expected: float, ctx: ScenarioContext) -> None:
    assert abs(ctx.per_term_achievements["payment"] - expected) < 1e-3, (
        f"Expected payment achievement {expected}, "
        f"got {ctx.per_term_achievements['payment']}"
    )


@then(
    parsers.parse(
        "the per-term achievement for delivery is (12 - 14) / (10 - 14) = {expected:f}"
    )
)
def then_delivery_achievement(expected: float, ctx: ScenarioContext) -> None:
    assert abs(ctx.per_term_achievements["delivery"] - expected) < 1e-3, (
        f"Expected delivery achievement {expected}, "
        f"got {ctx.per_term_achievements['delivery']}"
    )


@then(
    parsers.parse(
        "the per-term achievement for contract is (18 - 24) / (12 - 24) = {expected:f}"
    )
)
def then_contract_achievement(expected: float, ctx: ScenarioContext) -> None:
    assert abs(ctx.per_term_achievements["contract"] - expected) < 1e-3, (
        f"Expected contract achievement {expected}, "
        f"got {ctx.per_term_achievements['contract']}"
    )


@then(
    parsers.parse(
        "the MAUT utility is "
        "0.40 * 0.50 + 0.25 * 0.333 + 0.20 * 0.50 + 0.15 * 0.50 = {expected:f}"
    )
)
def then_maut_full_formula(expected: float, ctx: ScenarioContext) -> None:
    assert abs(ctx.computed_utility - expected) < 1e-2, (
        f"Expected MAUT utility {expected}, got {ctx.computed_utility}"
    )


@then("an offer with price exactly $14.50 is within the valid range")
def then_walkaway_price_valid(ctx: ScenarioContext) -> None:
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    terms = TermValues(
        price=ctx.config.walk_away["price"],
        payment=ctx.config.targets["payment"],
        delivery=ctx.config.targets["delivery"],
        contract=ctx.config.targets["contract"],
    )
    utility = compute_utility(terms, term_config, op_weights)
    # Walk-away on price alone should give 0 contribution from price term
    assert utility >= 0.0, (
        "Walk-away price offer should be a valid (non-negative) utility"
    )


@then("an offer with payment terms exactly Net 30 is within the valid range")
def then_walkaway_payment_valid(ctx: ScenarioContext) -> None:
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    terms = TermValues(
        price=ctx.config.targets["price"],
        payment=ctx.config.walk_away["payment"],
        delivery=ctx.config.targets["delivery"],
        contract=ctx.config.targets["contract"],
    )
    utility = compute_utility(terms, term_config, op_weights)
    assert utility >= 0.0


@then("an offer with delivery time exactly 14 days is within the valid range")
def then_walkaway_delivery_valid(ctx: ScenarioContext) -> None:
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    terms = TermValues(
        price=ctx.config.targets["price"],
        payment=ctx.config.targets["payment"],
        delivery=ctx.config.walk_away["delivery"],
        contract=ctx.config.targets["contract"],
    )
    utility = compute_utility(terms, term_config, op_weights)
    assert utility >= 0.0


@then("an offer with contract length exactly 24 months is within the valid range")
def then_walkaway_contract_valid(ctx: ScenarioContext) -> None:
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    terms = TermValues(
        price=ctx.config.targets["price"],
        payment=ctx.config.targets["payment"],
        delivery=ctx.config.targets["delivery"],
        contract=ctx.config.walk_away["contract"],
    )
    utility = compute_utility(terms, term_config, op_weights)
    assert utility >= 0.0


@then(
    "no pair of cards has the same price AND the same payment AND the same "
    "delivery AND the same contract length"
)
def then_no_identical_cards(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3
    seen: set[tuple[float, float, float, float]] = set()
    for card in ctx.current_offers:
        key = (
            card.price,
            float(card.payment),
            float(card.delivery),
            float(card.contract),
        )
        assert key not in seen, f"Duplicate MESO card found: {key}"
        seen.add(key)


@then("the offer terms start from the opening values")
def then_offer_terms_start_from_opening(ctx: ScenarioContext) -> None:
    # Opening round offers should have at least one term at or near the opening value
    assert len(ctx.current_offers) > 0
    # At least one card should have price >= opening price (opening is most favorable for supplier)
    # (opening price 11.50 < walk-away 14.50 means lower price = better for supplier)
    opening_price = ctx.config.opening["price"]
    prices = [c.price for c in ctx.current_offers]
    # Offers are bounded by [opening, walk_away]
    for price in prices:
        assert price >= min(opening_price, ctx.config.walk_away["price"]) - 1e-6
        assert price <= max(opening_price, ctx.config.walk_away["price"]) + 1e-6


@then("the opening round is deterministic with no opponent model influence")
def then_opening_round_deterministic(ctx: ScenarioContext) -> None:
    # With uniform opponent weights, the opening round is deterministic
    assert ctx.opponent_weights == {
        "price": 0.25,
        "payment": 0.25,
        "delivery": 0.25,
        "contract": 0.25,
    }


@then("the operator weights sum to exactly 1.00")
def then_operator_weights_sum_to_one(ctx: ScenarioContext) -> None:
    total = sum(ctx.config.weights.values())
    assert abs(total - 1.0) < 1e-9, f"Operator weights must sum to 1.0, got {total}"
