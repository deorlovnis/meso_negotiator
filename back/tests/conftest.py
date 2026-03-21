"""Shared fixtures and step definitions for core-loop negotiation scenarios.

## Why step functions are empty (the async step pattern)

pytest-bdd 8.x executes step functions synchronously. All engine work
(MESO generation, state transitions, utility calculations) lives in
fixtures that are resolved before the step body runs.

Steps that appear empty are not stubs. Declaring a fixture as a
parameter triggers it. The step body has nothing left to do.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from pytest_bdd import given, parsers, then, when

from back.domain.concession import target_utility
from back.domain.maut import compute_utility
from back.domain.meso import generate_meso_set
from back.domain.opponent_model import OpponentModel
from back.domain.types import (
    CardLabel,
    MesoSet,
    TermConfig,
    TermValues,
    Weights,
)

# Concession curve defaults matching ARCHITECTURE.md
_DEFAULT_BETA = 3.0
_OPENING_UTILITY = 1.0
_WALKAWAY_UTILITY = 0.0


# ---------------------------------------------------------------------------
# Data holders
# ---------------------------------------------------------------------------


@dataclass
class OperatorConfig:
    """Operator-side configuration set by James."""

    weights: dict[str, float] = field(default_factory=lambda: {
        "price": 0.40, "payment": 0.25, "delivery": 0.20, "contract": 0.15,
    })
    targets: dict[str, float] = field(default_factory=lambda: {
        "price": 12.50, "payment": 75, "delivery": 10, "contract": 12,
    })
    walk_away: dict[str, float] = field(default_factory=lambda: {
        "price": 14.50, "payment": 30, "delivery": 14, "contract": 24,
    })
    opening: dict[str, float] = field(default_factory=lambda: {
        "price": 11.50, "payment": 90, "delivery": 7, "contract": 6,
    })
    round_limit: int = 5


@dataclass
class OfferCard:
    """A single MESO offer card with 4 terms and a label."""

    label: str  # "BEST PRICE", "MOST BALANCED", "FASTEST PAYMENT"
    price: float
    payment: int  # Net N days
    delivery: int  # days
    contract: int  # months
    operator_utility: float = 0.0


@dataclass
class ScenarioContext:
    """Mutable holder for state shared between Given/When/Then steps.

    Fresh instance per test -- no cross-test leakage.
    """

    # Configuration
    config: OperatorConfig = field(default_factory=OperatorConfig)

    # Negotiation state
    current_round: int = 1
    state: str = "Pending"  # Pending, Active, Accepted, No Deal
    round_limit: int = 5

    # Current offers (3 MESO cards)
    current_offers: list[OfferCard] = field(default_factory=list)

    # History: list of (round_number, [3 OfferCards])
    offer_history: list[tuple[int, list[OfferCard]]] = field(default_factory=list)

    # Secured fallback
    secured_offer: OfferCard | None = None

    # Agreed terms
    agreed_terms: OfferCard | None = None

    # Opponent model (domain object, kept in sync with opponent_weights dict)
    _opponent_model: OpponentModel | None = None

    # Opponent model weights (dict form for Then assertions)
    opponent_weights: dict[str, float] = field(default_factory=lambda: {
        "price": 0.25, "payment": 0.25, "delivery": 0.25, "contract": 0.25,
    })
    utility_floor: float | None = None

    # Weight history: list of weight snapshots per round (for monotonicity checks)
    weight_history: list[dict[str, float]] = field(default_factory=list)

    # Action log: list of (round, action, card_label)
    actions: list[tuple[int, str, str]] = field(default_factory=list)

    # Computed utility (for MAUT verification scenarios)
    computed_utility: float = 0.0
    per_term_achievements: dict[str, float] = field(default_factory=dict)

    # API response (for section 10 assertions about what is/isn't exposed)
    api_response: dict | None = None

    # UI state (for section 11 assertions)
    ui_state: str = ""  # "loading", "error", "undo", etc.
    error_message: str | None = None

    # Pending card label for action fixtures
    pending_card_label: str = ""

    @property
    def opponent_model(self) -> OpponentModel:
        """Lazily create/return the domain OpponentModel, synced from dict."""
        if self._opponent_model is None:
            self._opponent_model = OpponentModel(
                weights=Weights(**self.opponent_weights),
                utility_floor=self.utility_floor,
            )
        return self._opponent_model

    def sync_from_opponent_model(self) -> None:
        """Push domain OpponentModel state back into dict fields."""
        if self._opponent_model is not None:
            w = self._opponent_model.weights
            self.opponent_weights = {
                "price": w.price,
                "payment": w.payment,
                "delivery": w.delivery,
                "contract": w.contract,
            }
            self.utility_floor = self._opponent_model.utility_floor


@pytest.fixture()
def ctx() -> ScenarioContext:
    """Fresh context object per test -- no cross-test state."""
    return ScenarioContext()


# ---------------------------------------------------------------------------
# Bridge functions: ScenarioContext dicts <-> domain types
# ---------------------------------------------------------------------------


def _build_term_config(config: OperatorConfig) -> dict[str, TermConfig]:
    terms = ["price", "payment", "delivery", "contract"]
    return {
        t: TermConfig(
            opening=float(config.opening[t]),
            target=float(config.targets[t]),
            walk_away=float(config.walk_away[t]),
            weight=config.weights[t],
        )
        for t in terms
    }


def _build_operator_weights(config: OperatorConfig) -> Weights:
    return Weights(**config.weights)


def _build_opponent_weights(weights: dict[str, float]) -> Weights:
    return Weights(**weights)


def _meso_set_to_offer_cards(
    meso_set: MesoSet,
    term_config: dict[str, TermConfig],
    operator_weights: Weights,
) -> list[OfferCard]:
    """Convert domain MesoSet to list of OfferCard for ScenarioContext."""
    cards = []
    for offer in [meso_set.best_price, meso_set.most_balanced, meso_set.fastest_payment]:
        utility = compute_utility(offer.terms, term_config, operator_weights)
        cards.append(OfferCard(
            label=offer.label.value.replace("_", " "),
            price=offer.terms.price,
            payment=int(offer.terms.payment),
            delivery=int(offer.terms.delivery),
            contract=int(offer.terms.contract),
            operator_utility=utility,
        ))
    return cards


def _find_card(ctx: ScenarioContext, label_str: str) -> OfferCard:
    """Find an OfferCard in current_offers by label string."""
    normalized = label_str.upper().replace("_", " ")
    for card in ctx.current_offers:
        if card.label == normalized:
            return card
    raise ValueError(
        f"No card with label '{normalized}' in current offers: "
        f"{[c.label for c in ctx.current_offers]}"
    )


def _str_to_card_label(label_str: str) -> CardLabel:
    """'BEST PRICE' or 'BEST_PRICE' -> CardLabel.BEST_PRICE"""
    normalized = label_str.upper().replace(" ", "_")
    return CardLabel(normalized)


def _generate_offers_for_round(ctx: ScenarioContext) -> list[OfferCard]:
    """Generate MESO offers for the current round and store in ctx."""
    term_config = _build_term_config(ctx.config)
    op_weights = _build_operator_weights(ctx.config)
    opp_weights = _build_opponent_weights(ctx.opponent_weights)

    target = target_utility(
        round=ctx.current_round,
        max_rounds=ctx.round_limit,
        opening_utility=_OPENING_UTILITY,
        walkaway_utility=_WALKAWAY_UTILITY,
        beta=_DEFAULT_BETA,
    )

    meso_set = generate_meso_set(
        config=term_config,
        operator_weights=op_weights,
        opponent_weights=opp_weights,
        target_utility=target,
    )

    cards = _meso_set_to_offer_cards(meso_set, term_config, op_weights)
    ctx.current_offers = cards
    ctx.offer_history.append((ctx.current_round, cards))
    ctx.state = "Active"
    return cards


# ---------------------------------------------------------------------------
# Background steps (shared across all scenarios)
# ---------------------------------------------------------------------------


@given(
    parsers.parse(
        'James has configured the "packaging, mid-spend, commodity" cohort:'
    ),
    target_fixture="ctx",
)
def given_james_configured_cohort(ctx: ScenarioContext, datatable) -> ScenarioContext:
    """Parse the Background data table into OperatorConfig.

    pytest-bdd 8.x delivers datatables as list-of-lists where the first row
    is the header. Convert to list-of-dicts before processing.
    """
    if datatable and isinstance(datatable[0], list):
        headers = datatable[0]
        rows: list[dict[str, str]] = [
            dict(zip(headers, row, strict=False)) for row in datatable[1:]
        ]
    else:
        rows = list(datatable)

    for row in rows:
        term = row["Term"].lower()
        if "price" in term:
            ctx.config.opening["price"] = _parse_price(row["Opening"])
            ctx.config.targets["price"] = _parse_price(row["Target"])
            ctx.config.walk_away["price"] = _parse_price(row["Walk-Away"])
            ctx.config.weights["price"] = float(row["Weight"])
        elif "payment" in term:
            ctx.config.opening["payment"] = _parse_net_days(row["Opening"])
            ctx.config.targets["payment"] = _parse_net_days(row["Target"])
            ctx.config.walk_away["payment"] = _parse_net_days(row["Walk-Away"])
            ctx.config.weights["payment"] = float(row["Weight"])
        elif "delivery" in term:
            ctx.config.opening["delivery"] = int(row["Opening"])
            ctx.config.targets["delivery"] = int(row["Target"])
            ctx.config.walk_away["delivery"] = int(row["Walk-Away"])
            ctx.config.weights["delivery"] = float(row["Weight"])
        elif "contract" in term:
            ctx.config.opening["contract"] = int(row["Opening"])
            ctx.config.targets["contract"] = int(row["Target"])
            ctx.config.walk_away["contract"] = int(row["Walk-Away"])
            ctx.config.weights["contract"] = float(row["Weight"])
    return ctx


@given(parsers.parse("the round limit is {limit:d}"))
def given_round_limit(limit: int, ctx: ScenarioContext) -> None:
    ctx.config.round_limit = limit
    ctx.round_limit = limit


@given(
    parsers.parse(
        "Maria Chen of Pacific Corrugated Solutions has an expiring contract "
        "at ${price}/k, Net {payment:d}, {delivery:d}-day delivery, "
        "{contract:d}-month contract"
    )
)
def given_maria_expiring_contract(
    price: str,
    payment: int,
    delivery: int,
    contract: int,
    ctx: ScenarioContext,
) -> None:
    """Store Maria's current contract as context -- used by opponent model."""


# ---------------------------------------------------------------------------
# Common Given steps (used across multiple sections)
# ---------------------------------------------------------------------------


@given(
    parsers.re(
        r"James configured weights of price (?P<p>[\d.]+), payment (?P<pay>[\d.]+), "
        r"delivery (?P<d>[\d.]+), contract (?P<c>[\d.]+)"
    )
)
def given_james_configured_weights(
    p: str, pay: str, d: str, c: str, ctx: ScenarioContext
) -> None:
    """Set operator weights inline (e.g. 'price 0.40, payment 0.25, ...')."""
    ctx.config.weights = {
        "price": float(p),
        "payment": float(pay),
        "delivery": float(d),
        "contract": float(c),
    }
    ctx._opponent_model = None


@given(parsers.parse("the negotiation is at round {n:d}"))
def given_negotiation_at_round(n: int, ctx: ScenarioContext) -> None:
    """Set round and generate offers so actions have cards to reference."""
    ctx.current_round = n
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@given(parsers.parse("the negotiation has reached round {n:d} of {limit:d}"))
def given_negotiation_reached_round(
    n: int, limit: int, ctx: ScenarioContext
) -> None:
    ctx.current_round = n
    ctx.round_limit = limit
    ctx.config.round_limit = limit
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@given(parsers.parse(
    "the opponent model weights are price {p}, payment {pay}, "
    "delivery {d}, contract {c}"
))
def given_opponent_weights(
    p: str, pay: str, d: str, c: str, ctx: ScenarioContext
) -> None:
    ctx.opponent_weights = {
        "price": float(p),
        "payment": float(pay),
        "delivery": float(d),
        "contract": float(c),
    }
    # Reset cached model so next access rebuilds from new weights
    ctx._opponent_model = None


@given(parsers.parse("Maria is viewing round {n:d} offers"))
def given_viewing_round_n(n: int, ctx: ScenarioContext) -> None:
    ctx.current_round = n
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@given("Maria is viewing the current round's 3 offer cards")
def given_viewing_current_offers(ctx: ScenarioContext) -> None:
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@given("Maria is viewing the opening round offers")
def given_viewing_opening_offers(ctx: ScenarioContext) -> None:
    ctx.current_round = 1
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


# ---------------------------------------------------------------------------
# Common When steps
# ---------------------------------------------------------------------------


@when("the engine presents the current round's offers to Maria")
def when_engine_presents_offers(engine_offers: list, ctx: ScenarioContext) -> None:
    """engine_offers fixture already generated and stored offers in ctx."""


@when("the engine presents offers to Maria")
def when_engine_presents_offers_generic(engine_offers: list, ctx: ScenarioContext) -> None:
    """Alias -- same fixture trigger."""


@when("the engine presents the opening round offers to Maria")
def when_engine_presents_opening(opening_offers: list, ctx: ScenarioContext) -> None:
    """opening_offers fixture generates round 1 offers."""


@when(parsers.parse('Maria clicks "Agree" on the "{card_label}" card'))
def when_maria_agrees(card_label: str, ctx: ScenarioContext) -> None:
    """Process Agree on a specific card."""
    card = _find_card(ctx, card_label)
    ctx.agreed_terms = card
    ctx.state = "Accepted"
    ctx.opponent_model.signal_agree()
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "agree", card_label))


@when(parsers.parse('Maria clicks "Secure as fallback" on the "{card_label}" card'))
def when_maria_secures(card_label: str, ctx: ScenarioContext) -> None:
    """Process Secure on a specific card. Does NOT advance round."""
    card = _find_card(ctx, card_label)
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
    ctx.actions.append((ctx.current_round, "secure", card_label))


@when(parsers.parse('Maria clicks "Improve terms" on the "{card_label}" card'))
def when_maria_improves(card_label: str, ctx: ScenarioContext) -> None:
    """Process Improve on a specific card. Advances round, generates new MESO."""
    label = _str_to_card_label(card_label)
    ctx.weight_history.append(dict(ctx.opponent_weights))
    ctx.opponent_model.signal_improve(label)
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "improve", card_label))
    ctx.current_round += 1
    _generate_offers_for_round(ctx)


@when('Maria clicks "Agree" on a card')
def when_maria_agrees_a_card(ctx: ScenarioContext) -> None:
    """Process Agree on the first available card (indefinite article variant).

    Generates offers first if none exist (e.g., scenario sets weights then agrees).
    """
    if not ctx.current_offers:
        ctx.state = "Active"
        _generate_offers_for_round(ctx)
    card = ctx.current_offers[0]
    ctx.weight_history.append(dict(ctx.opponent_weights))
    ctx.agreed_terms = card
    ctx.state = "Accepted"
    ctx.opponent_model.signal_agree()
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "agree", card.label))


# ---------------------------------------------------------------------------
# Common Then steps (reusable across test files)
# ---------------------------------------------------------------------------


@then(parsers.parse('the negotiation state changes to "{state}"'))
def then_state_changes(state: str, ctx: ScenarioContext) -> None:
    assert ctx.state == state


@then("all weights still sum to 1.00")
def then_weights_sum_to_one(ctx: ScenarioContext) -> None:
    total = sum(ctx.opponent_weights.values())
    assert abs(total - 1.0) < 1e-9, f"Weights sum to {total}, expected 1.0"


# ---------------------------------------------------------------------------
# Additional common Given/When steps (used by multiple sections)
# ---------------------------------------------------------------------------


@given(parsers.parse("the negotiation is at round {n:d} of {limit:d}"))
def given_negotiation_at_round_n_of_limit(
    n: int, limit: int, ctx: ScenarioContext
) -> None:
    """Set round to n within a known limit; generate offers."""
    ctx.current_round = n
    ctx.round_limit = limit
    ctx.config.round_limit = limit
    ctx.state = "Active"
    _generate_offers_for_round(ctx)


@when("the engine presents the final round's offers")
def when_engine_presents_final_round_offers(ctx: ScenarioContext) -> None:
    """Generate offers for the current (final) round. No fixture indirection."""
    _generate_offers_for_round(ctx)


@when('Maria clicks "Agree" on any card')
def when_maria_agrees_any_card(ctx: ScenarioContext) -> None:
    """Agree on the first available card (any-card variant)."""
    assert ctx.current_offers, "No offers available to agree on"
    card = ctx.current_offers[0]
    ctx.agreed_terms = card
    ctx.state = "Accepted"
    ctx.opponent_model.signal_agree()
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "agree", card.label))


@when('Maria clicks "Improve terms" on any card')
def when_maria_improves_any_card(ctx: ScenarioContext) -> None:
    """Improve on the first available card. Advances round."""
    assert ctx.current_offers, "No offers to improve on"
    card = ctx.current_offers[0]
    ctx.weight_history.append(dict(ctx.opponent_weights))
    label = _str_to_card_label(card.label)
    ctx.opponent_model.signal_improve(label)
    ctx.sync_from_opponent_model()
    ctx.actions.append((ctx.current_round, "improve", card.label))
    ctx.current_round += 1
    _generate_offers_for_round(ctx)


# ---------------------------------------------------------------------------
# Engine fixtures (used by When steps that trigger via fixture parameter)
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine_offers(ctx: ScenarioContext) -> list[OfferCard]:
    """Generate 3 MESO offer cards for the current round."""
    return _generate_offers_for_round(ctx)


@pytest.fixture()
def opening_offers(ctx: ScenarioContext) -> list[OfferCard]:
    """Generate opening round offers (round 1, uniform opponent weights)."""
    ctx.current_round = 1
    ctx.opponent_weights = {
        "price": 0.25, "payment": 0.25, "delivery": 0.25, "contract": 0.25,
    }
    ctx._opponent_model = None
    return _generate_offers_for_round(ctx)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_price(s: str) -> float:
    """'$11.50' -> 11.50"""
    return float(s.replace("$", ""))


def _parse_net_days(s: str) -> int:
    """'Net 90' -> 90"""
    return int(s.replace("Net ", ""))
