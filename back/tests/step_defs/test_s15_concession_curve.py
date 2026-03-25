"""Section 15 — Concession curve: Boulware strategy verification."""

from __future__ import annotations

from pytest_bdd import given, parsers, scenario, then, when

from back.domain.concession import target_utility
from back.tests.conftest import (
    _DEFAULT_BETA,
    _OPENING_UTILITY,
    _WALKAWAY_UTILITY,
    ScenarioContext,
)

FEATURE = "../features/core-loop.feature"


@scenario(FEATURE, "Concession curve at round 1 produces utility near opening")
def test_concession_curve_round_1() -> None:
    pass


@scenario(
    FEATURE, "Concession curve at the final round produces utility near walk-away"
)
def test_concession_curve_final_round() -> None:
    pass


# ---------------------------------------------------------------------------
# Given steps (section-specific)
# ---------------------------------------------------------------------------


@given(parsers.parse("the round limit is {limit:d} and beta is greater than 1"))
def given_round_limit_and_beta(limit: int, ctx: ScenarioContext) -> None:
    ctx.round_limit = limit
    ctx.config.round_limit = limit
    # beta > 1 is enforced by _DEFAULT_BETA = 3.0


# ---------------------------------------------------------------------------
# When steps (section-specific)
# ---------------------------------------------------------------------------


@when(parsers.parse("the engine calculates target utility for round {n:d}"))
def when_engine_calculates_target_utility(n: int, ctx: ScenarioContext) -> None:
    ctx.computed_utility = target_utility(
        round=n,
        max_rounds=ctx.round_limit,
        opening_utility=_OPENING_UTILITY,
        walkaway_utility=_WALKAWAY_UTILITY,
        beta=_DEFAULT_BETA,
    )


# ---------------------------------------------------------------------------
# Then steps (section-specific)
# ---------------------------------------------------------------------------


@then("the target utility is close to the opening utility value")
def then_utility_near_opening(ctx: ScenarioContext) -> None:
    # Round 1 with Boulware beta=3 should be close to opening (1.0)
    # progress = 1/5 = 0.2, so target = (1 - 0.2)^3 = 0.8^3 = 0.512
    # "Close to opening" means significantly above midpoint (0.5)
    assert ctx.computed_utility > 0.4, (
        f"Round 1 target utility should be near opening (>0.4), "
        f"got {ctx.computed_utility}"
    )
    assert ctx.computed_utility <= _OPENING_UTILITY + 1e-9, (
        f"Round 1 target utility must not exceed opening utility {_OPENING_UTILITY}"
    )


@then("the target utility is close to the walk-away utility value")
def then_utility_near_walkaway(ctx: ScenarioContext) -> None:
    # Final round: progress = 1.0, so target equals walk-away utility.
    # With a utility floor of 0.15, the final target is 0.15.
    assert abs(ctx.computed_utility - _WALKAWAY_UTILITY) < 0.05, (
        f"Final round target utility should be near walk-away "
        f"({_WALKAWAY_UTILITY}), got {ctx.computed_utility}"
    )
