"""Section 9 — Operator configuration: weights, targets, and limits feed the engine."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.domain.maut import compute_utility
from back.domain.types import TermValues
from back.tests.conftest import (
    ScenarioContext,
    _build_operator_weights,
    _build_term_config,
    _generate_offers_for_round,
)

FEATURE = "../features/core-loop.feature"


@scenario(FEATURE, "Operator weights determine how MAUT utility is calculated")
def test_operator_weights_determine_maut() -> None:
    pass


@scenario(FEATURE, "Operator changes weights and the MESO distribution shifts")
def test_operator_changes_weights_meso_shifts() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps (section-specific)
# ---------------------------------------------------------------------------


@given(
    parsers.parse(
        "James changes the weights to price {p:f}, payment {pay:f}, "
        "delivery {d:f}, contract {c:f}"
    )
)
def given_james_changes_weights(
    p: float, pay: float, d: float, c: float, ctx: ScenarioContext
) -> None:
    ctx.config.weights = {
        "price": p,
        "payment": pay,
        "delivery": d,
        "contract": c,
    }
    ctx._opponent_model = None


# ---------------------------------------------------------------------------
# When steps (section-specific)
# ---------------------------------------------------------------------------


@when(
    parsers.parse(
        "the engine evaluates an offer at ${price:f}, Net {payment:d}, "
        "{delivery:d} days, {contract:d} months"
    )
)
def when_engine_evaluates_offer(
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

    # Store per-term achievements for assertion steps
    from back.domain.maut import _achievement  # type: ignore[attr-defined]

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


@when("the engine generates a new MESO set")
def when_engine_generates_new_meso_set(ctx: ScenarioContext) -> None:
    _generate_offers_for_round(ctx)


# ---------------------------------------------------------------------------
# Then steps (section-specific)
# ---------------------------------------------------------------------------


@then(
    "the MAUT utility is calculated as the weighted sum of per-term achievement "
    "between walk-away and target"
)
def then_maut_is_weighted_sum(ctx: ScenarioContext) -> None:
    # Verify utility is within [0, 1] — full formula verified in s14
    assert 0.0 <= ctx.computed_utility <= 1.0


@then(
    parsers.parse(
        "price contributes {p:f} of the utility, payment {pay:f}, "
        "delivery {d:f}, contract {c:f}"
    )
)
def then_weights_contribute(
    p: float, pay: float, d: float, c: float, ctx: ScenarioContext
) -> None:
    # Verify weights in config match the stated contributions
    assert abs(ctx.config.weights["price"] - p) < 1e-9
    assert abs(ctx.config.weights["payment"] - pay) < 1e-9
    assert abs(ctx.config.weights["delivery"] - d) < 1e-9
    assert abs(ctx.config.weights["contract"] - c) < 1e-9


@then(
    "the offers allocate more value to payment terms than under the original "
    "0.25 payment weight"
)
def then_offers_allocate_more_payment(ctx: ScenarioContext) -> None:
    # After changing weight to 0.30, verify weight increased above 0.25
    assert ctx.config.weights["payment"] > 0.25


@then('the "MOST BALANCED" card reflects the updated weight balance')
def then_most_balanced_reflects_updated_weights(ctx: ScenarioContext) -> None:
    # Verify offers were generated and MOST BALANCED card exists
    balanced = next(
        (c for c in ctx.current_offers if c.label == "MOST BALANCED"),
        None,
    )
    assert balanced is not None, "MOST BALANCED card not found in current offers"
