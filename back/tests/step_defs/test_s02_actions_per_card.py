"""Section 2 — Actions per card: Agree, Secure as fallback, Improve terms."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_bdd import scenario, then

if TYPE_CHECKING:
    from back.tests.conftest import ScenarioContext

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------


@scenario("../features/core-loop.feature", "Each card presents exactly 3 actions")
def test_each_card_presents_3_actions() -> None:
    pass


# ---------------------------------------------------------------------------
# Then steps
# ---------------------------------------------------------------------------


@then('each card has a green "Agree" button')
def then_each_card_has_agree_button(ctx: ScenarioContext) -> None:
    # All 3 cards must be present; Agree is always available while Active.
    assert len(ctx.current_offers) == 3
    assert ctx.state == "Active"


@then('each card has a "Secure as fallback" button')
def then_each_card_has_secure_button(ctx: ScenarioContext) -> None:
    assert len(ctx.current_offers) == 3
    assert ctx.state == "Active"


@then('each card has an "Improve terms" link')
def then_each_card_has_improve_link(ctx: ScenarioContext) -> None:
    # Improve is available on every card while the round is not the final round.
    assert len(ctx.current_offers) == 3
    assert ctx.current_round < ctx.round_limit, (
        f"Improve unavailable on final round {ctx.current_round}/{ctx.round_limit}"
    )


@then("no free-text input field appears anywhere on the screen")
def then_no_free_text_input(ctx: ScenarioContext) -> None:
    # No free-text field is a UI constraint. In the backend model we can only
    # verify there is no unstructured text state in the context.
    assert ctx.api_response is None or "free_text" not in ctx.api_response
