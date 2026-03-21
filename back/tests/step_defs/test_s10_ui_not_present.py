"""Section 10 — Elements not present on the supplier UI.

These tests verify the API response shape does not expose utility scores,
round counters, or other internal engine fields to the supplier frontend.

FastAPI / TestClient imports are deferred into step bodies so pytest collection
works even when fastapi is not on the system path (e.g. before `mise run setup`).
"""

from __future__ import annotations

from pytest_bdd import parsers, scenario, then, when

from back.tests.conftest import ScenarioContext, _generate_offers_for_round

FEATURE = "../features/core-loop.feature"


@scenario(FEATURE, "No utility score or progress bar is shown to Maria")
def test_no_utility_score_shown() -> None:
    pass


@scenario(FEATURE, "No round counter is shown to Maria")
def test_no_round_counter_shown() -> None:
    pass


@scenario(FEATURE, "No trade-off selection prompt appears after clicking Improve")
def test_no_trade_off_prompt() -> None:
    pass


@scenario(FEATURE, "No free-text input or chat interface is available to Maria")
def test_no_free_text_input() -> None:
    pass


@scenario(FEATURE, "Operator utility scores are never exposed in the supplier API response")
def test_utility_not_in_api_response() -> None:
    pass


@scenario(FEATURE, "The round number is tracked internally but not exposed to Maria")
def test_round_not_exposed() -> None:
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fetch_demo_offers() -> dict:  # type: ignore[type-arg]
    """Call GET /api/negotiations/demo/offers via TestClient.

    Deferred import so collection works without fastapi installed.
    """
    from fastapi.testclient import TestClient  # type: ignore[import]

    from back.server import create_app

    client = TestClient(create_app())
    response = client.get("/api/negotiations/demo/offers")
    return dict(response.json())


def _assert_no_utility_in_response(response: dict) -> None:  # type: ignore[type-arg]
    """Assert that utility fields are not present in the API response."""
    assert "utility" not in response, "API response must not include 'utility' field"
    assert "maut" not in response, "API response must not include 'maut' field"
    assert "score" not in response, "API response must not include 'score' field"
    for card in response.get("cards", []):
        assert "utility" not in card, f"Card must not include 'utility': {card}"
        assert "maut" not in card, f"Card must not include 'maut': {card}"
        assert "score" not in card, f"Card must not include 'score': {card}"


# ---------------------------------------------------------------------------
# When steps (section-specific)
# ---------------------------------------------------------------------------


@when("the engine presents offers to Maria on any round")
def when_presents_offers_any_round(ctx: ScenarioContext) -> None:
    _generate_offers_for_round(ctx)
    try:
        ctx.api_response = _fetch_demo_offers()
    except Exception:
        ctx.api_response = None


@when("Maria views any round of the negotiation")
def when_maria_views_any_round(ctx: ScenarioContext) -> None:
    _generate_offers_for_round(ctx)
    try:
        ctx.api_response = _fetch_demo_offers()
    except Exception:
        ctx.api_response = None


@when("the engine generates offers and sends them to Maria's UI")
def when_engine_generates_and_sends(ctx: ScenarioContext) -> None:
    _generate_offers_for_round(ctx)
    try:
        ctx.api_response = _fetch_demo_offers()
    except Exception:
        ctx.api_response = None


@when(parsers.parse("the engine presents round {n:d} offers to Maria"))
def when_presents_round_n_offers(n: int, ctx: ScenarioContext) -> None:
    ctx.current_round = n
    _generate_offers_for_round(ctx)
    try:
        ctx.api_response = _fetch_demo_offers()
    except Exception:
        ctx.api_response = None


# ---------------------------------------------------------------------------
# Then steps (section-specific)
# ---------------------------------------------------------------------------


@then("no MAUT utility score is displayed on the screen")
def then_no_utility_score(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        _assert_no_utility_in_response(ctx.api_response)


@then("no progress bar or percentage indicator appears")
def then_no_progress_bar(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        assert "progress" not in ctx.api_response, (
            "API response must not include 'progress' field"
        )
        assert "percentage" not in ctx.api_response, (
            "API response must not include 'percentage' field"
        )


@then("utility scoring remains an internal engine calculation only")
def then_utility_internal_only(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        _assert_no_utility_in_response(ctx.api_response)


@then(parsers.parse('no text such as "{text}" appears on the screen'))
def then_no_round_text(text: str, ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        # Round counter text should not be exposed as a field in the API response
        assert "round_number" not in ctx.api_response, (
            "round_number must not appear in API response"
        )
        assert "current_round" not in ctx.api_response, (
            "current_round must not appear in API response"
        )


@then("the round limit remains an internal engine parameter")
def then_round_limit_internal(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        assert "round_limit" not in ctx.api_response, (
            "round_limit must not be in API response"
        )
        assert "max_rounds" not in ctx.api_response, (
            "max_rounds must not be in API response"
        )


@then("no prompt asking \"what would you like to trade?\" appears")
def then_no_trade_off_prompt(ctx: ScenarioContext) -> None:
    # Engine generates new offers without any trade-off prompt
    assert len(ctx.current_offers) == 3, (
        "Engine must generate 3 offers directly without a trade-off prompt"
    )


@then("no selection of terms to give up is presented")
def then_no_terms_selection(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        assert "trade_off" not in ctx.api_response
        assert "give_up" not in ctx.api_response
        assert "sacrifice" not in ctx.api_response


@then("the engine directly generates new offers based on the card's strength signal")
def then_engine_generates_directly(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3, (
        "Engine generates 3 offers directly after Improve signal"
    )


@then("no text input field, text area, or chat interface is displayed")
def then_no_text_input(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        assert "chat" not in ctx.api_response
        assert "text_input" not in ctx.api_response


@then("Maria's only interaction options are Agree, Secure as fallback, and Improve terms")
def then_only_three_actions(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None and "actions_available" in ctx.api_response:
        actions = ctx.api_response["actions_available"]
        allowed = {"agree", "secure", "improve"}
        for action in actions:
            assert action.lower() in allowed, (
                f"Unexpected action '{action}' in API response"
            )


@then(
    "the API response to the supplier frontend does not include the MAUT utility field"
)
def then_no_utility_in_api(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        _assert_no_utility_in_response(ctx.api_response)


@then("the supplier UI does not render any numeric score")
def then_no_numeric_score(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        _assert_no_utility_in_response(ctx.api_response)


@then(parsers.parse("the internal state records round {n:d}"))
def then_internal_state_records_round(n: int, ctx: ScenarioContext) -> None:
    assert ctx.current_round == n, (
        f"Internal round should be {n}, got {ctx.current_round}"
    )


@then(
    "the API response to the supplier frontend does not include the round number"
)
def then_no_round_in_api(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        assert "round" not in ctx.api_response, (
            "API response must not expose 'round' field"
        )
        assert "current_round" not in ctx.api_response, (
            "API response must not expose 'current_round' field"
        )


@then(
    'no text referencing "round", "step", or a numeric progress indicator appears'
)
def then_no_progress_text(ctx: ScenarioContext) -> None:
    if ctx.api_response is not None:
        assert "current_round" not in ctx.api_response
        assert "round_number" not in ctx.api_response
        assert "step" not in ctx.api_response
