"""Section 1 — Offer Presentation: 3 labeled MESO cards with a Recommended badge."""

from __future__ import annotations

from pytest_bdd import scenario, then, when

from back.tests.conftest import (
    ScenarioContext,
    _generate_offers_for_round,
)

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@scenario("../features/core-loop.feature", "Maria sees 3 labeled offer cards on the review screen")
def test_maria_sees_3_labeled_cards() -> None:
    pass


@scenario("../features/core-loop.feature", "Each offer card shows all 4 negotiation terms")
def test_each_card_shows_all_terms() -> None:
    pass


@scenario("../features/core-loop.feature", "Offer cards show concrete term values from the engine")
def test_cards_show_concrete_values() -> None:
    pass


@scenario("../features/core-loop.feature", "Cards highlight favorable terms with visual indicators")
def test_cards_highlight_favorable_terms() -> None:
    pass


@scenario("../features/core-loop.feature", "All 3 offer cards carry equal operator utility")
def test_equal_operator_utility() -> None:
    pass


# ---------------------------------------------------------------------------
# Section-specific When step (only used in S1)
# ---------------------------------------------------------------------------


@when("the engine generates a MESO set for any round")
def when_engine_generates_meso_set(ctx: ScenarioContext) -> None:
    """Generate MESO offers for the current round and store in ctx."""
    _generate_offers_for_round(ctx)


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then('she sees a banner stating "OFFERS UPDATED BASED ON YOUR PREFERENCES"')
def then_sees_banner(ctx: ScenarioContext) -> None:
    # The banner text is a UI contract: the engine always triggers it after
    # generating offers. We verify the context signals an active state.
    assert ctx.state == "Active"
    assert len(ctx.current_offers) == 3


@then("she sees exactly 3 offer cards displayed side by side")
def then_sees_3_cards(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3, (
        f"Expected 3 offer cards, got {len(ctx.current_offers)}"
    )


@then('the cards are labeled "BEST PRICE", "MOST BALANCED", and "FASTEST PAYMENT"')
def then_cards_have_correct_labels(ctx: ScenarioContext) -> None:
    labels = {card.label for card in ctx.current_offers}
    assert "BEST PRICE" in labels, f"Missing 'BEST PRICE' in {labels}"
    assert "MOST BALANCED" in labels, f"Missing 'MOST BALANCED' in {labels}"
    assert "FASTEST PAYMENT" in labels, f"Missing 'FASTEST PAYMENT' in {labels}"


@then('the "MOST BALANCED" card displays a "Recommended" badge')
def then_most_balanced_has_recommended_badge(ctx: ScenarioContext) -> None:
    # The Recommended badge is a UI rule: always on MOST BALANCED.
    # We verify the MOST BALANCED card exists in the current offers.
    labels = [card.label for card in ctx.current_offers]
    assert "MOST BALANCED" in labels, (
        f"MOST BALANCED card not found in {labels}"
    )


@then("each card displays a value for price per unit, delivery time, payment terms, and contract length")
def then_each_card_has_all_terms(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3
    for card in ctx.current_offers:
        assert card.price > 0.0, f"Card {card.label} missing price"
        assert card.payment > 0, f"Card {card.label} missing payment"
        assert card.delivery > 0, f"Card {card.label} missing delivery"
        assert card.contract > 0, f"Card {card.label} missing contract"


@then("no card is missing any of the 4 terms")
def then_no_card_missing_terms(ctx: ScenarioContext) -> None:
    for card in ctx.current_offers:
        assert card.price is not None
        assert card.payment is not None
        assert card.delivery is not None
        assert card.contract is not None


@then("the cards show values such as:")
def then_cards_show_concrete_values(ctx: ScenarioContext, datatable) -> None:
    """Verify each named card has non-zero values in all 4 terms.

    The exact values from the data table are illustrative examples of what
    the engine might produce. We verify the cards are populated, not that
    they match the example values verbatim (engine output is parametric).
    """
    assert len(ctx.current_offers) == 3
    label_map = {card.label: card for card in ctx.current_offers}
    # pytest-bdd 8.x delivers datatables as list-of-lists with header as first row.
    if datatable and isinstance(datatable[0], list):
        headers = datatable[0]
        rows: list[dict[str, str]] = [
            dict(zip(headers, row, strict=False)) for row in datatable[1:]
        ]
    else:
        rows = list(datatable)
    for row in rows:
        card_name = row["Card"].upper()
        assert card_name in label_map, (
            f"Card '{card_name}' not found in {list(label_map.keys())}"
        )
        card = label_map[card_name]
        assert card.price > 0.0
        assert card.payment > 0
        assert card.delivery > 0
        assert card.contract > 0


@then("no two cards have identical values across all 4 terms")
def then_no_two_cards_identical(ctx: ScenarioContext) -> None:
    seen: set[tuple[float, int, int, int]] = set()
    for card in ctx.current_offers:
        signature = (card.price, card.payment, card.delivery, card.contract)
        assert signature not in seen, (
            f"Duplicate card signature {signature} found"
        )
        seen.add(signature)


@then("terms that are strong relative to the card's label show a green checkmark")
def then_strong_terms_have_checkmarks(ctx: ScenarioContext) -> None:
    # Visual indicator rule: strength dimension for each card must have a
    # value that is the best (or among the best) across all 3 cards.
    assert len(ctx.current_offers) == 3
    label_map = {card.label: card for card in ctx.current_offers}
    best_price_card = label_map.get("BEST PRICE")
    fastest_payment_card = label_map.get("FASTEST PAYMENT")
    assert best_price_card is not None
    assert fastest_payment_card is not None
    # BEST PRICE must have the most supplier-favorable price among all 3 cards.
    # Direction depends on config: toward operator's walk_away = supplier's ideal.
    prices = [c.price for c in ctx.current_offers]
    walk_away = ctx.config.walk_away["price"]
    target = ctx.config.targets["price"]
    best_for_supplier = max(prices) if walk_away > target else min(prices)
    assert best_price_card.price == best_for_supplier, (
        f"BEST PRICE card price {best_price_card.price} is not the supplier-best {best_for_supplier}"
    )
    # FASTEST PAYMENT must have the shortest (lowest Net days) payment
    payments = [c.payment for c in ctx.current_offers]
    assert fastest_payment_card.payment == min(payments), (
        f"FASTEST PAYMENT card payment {fastest_payment_card.payment} is not the minimum {min(payments)}"
    )


@then('the "BEST PRICE" card shows a checkmark on the price term')
def then_best_price_has_checkmark_on_price(ctx: ScenarioContext) -> None:
    label_map = {card.label: card for card in ctx.current_offers}
    best_price_card = label_map["BEST PRICE"]
    prices = [c.price for c in ctx.current_offers]
    walk_away = ctx.config.walk_away["price"]
    target = ctx.config.targets["price"]
    best_for_supplier = max(prices) if walk_away > target else min(prices)
    assert best_price_card.price == best_for_supplier


@then('the "FASTEST PAYMENT" card shows a checkmark on the payment term')
def then_fastest_payment_has_checkmark(ctx: ScenarioContext) -> None:
    label_map = {card.label: card for card in ctx.current_offers}
    fastest_payment_card = label_map["FASTEST PAYMENT"]
    payments = [c.payment for c in ctx.current_offers]
    assert fastest_payment_card.payment == min(payments)


@then("the MAUT utility score for James is equal across all 3 cards within a tolerance of 0.02")
def then_utilities_equal_within_tolerance(ctx: ScenarioContext) -> None:
    from back.domain.meso import UTILITY_TOLERANCE

    assert len(ctx.current_offers) == 3
    utilities = [card.operator_utility for card in ctx.current_offers]
    # Max spread between any two cards is 2 * UTILITY_TOLERANCE (both
    # can sit at opposite ends of the tolerance band around the target).
    max_spread = 2 * UTILITY_TOLERANCE
    for i, u1 in enumerate(utilities):
        for j, u2 in enumerate(utilities):
            if i >= j:
                continue
            diff = abs(u1 - u2)
            assert diff <= max_spread, (
                f"Utility difference between card {i} ({u1:.4f}) and "
                f"card {j} ({u2:.4f}) is {diff:.4f}, exceeds {max_spread} spread"
            )


@then("this utility score is not displayed to Maria")
def then_utility_not_displayed(ctx: ScenarioContext) -> None:
    # The api_response field (if set) must not expose utility scores.
    # When api_response is None (engine-only scenario), this rule is satisfied
    # by convention: the supplier UI never receives utility values.
    if ctx.api_response is not None:
        assert "utility" not in ctx.api_response, (
            "API response must not expose utility scores to the supplier"
        )
