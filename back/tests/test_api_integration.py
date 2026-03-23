"""HTTP-level integration tests for the MESO negotiation API.

These tests exercise the full FastAPI stack via TestClient: route parsing,
dependency injection, use case orchestration, domain logic, and JSON
serialization.  Every test gets its own fresh in-memory repository so there
is zero state leakage between tests.

Error categories covered (STS Ch 1):
- Integration errors: HTTP contract (status codes, response shapes)
- Interface errors: correct routing, parameter passing, card_label validation
- Logic errors: state machine transitions, terminal-state enforcement
- Data errors: is_first_visit flag, secured_offer persistence, actions_available

Factory migration (F6): local _make_config/_seed_negotiation replaced with
shared factories from back.tests.factories. Fixtures client and
final_round_client now use conftest's _make_test_client pattern.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from back.api.dependencies import get_repo
from back.infrastructure.memory_repo import InMemoryNegotiationRepository
from back.server import create_app
from back.tests.factories import make_negotiation

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

NEG_ID = "test-neg"
CARD_LABELS = ["BEST_PRICE", "MOST_BALANCED", "FASTEST_PAYMENT"]


# ---------------------------------------------------------------------------
# Fixtures (F6: migrated to shared factories)
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    """TestClient with a fresh, isolated in-memory repo per test.

    Uses make_negotiation from shared factories (F6 migration).
    Overrides the get_repo dependency so the module-level singleton is never
    touched.
    """
    fresh_repo = InMemoryNegotiationRepository()
    fresh_repo.save(make_negotiation(neg_id=NEG_ID))

    app = create_app()
    app.dependency_overrides[get_repo] = lambda: fresh_repo
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def final_round_client() -> TestClient:
    """TestClient with a negotiation that has max_rounds=1 (already final)."""
    fresh_repo = InMemoryNegotiationRepository()
    fresh_repo.save(make_negotiation(neg_id=NEG_ID, max_rounds=1))

    app = create_app()
    app.dependency_overrides[get_repo] = lambda: fresh_repo
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _offers_url(neg_id: str = NEG_ID) -> str:
    return f"/api/negotiations/{neg_id}/offers"


def _agree_url(neg_id: str = NEG_ID) -> str:
    return f"/api/negotiations/{neg_id}/agree"


def _secure_url(neg_id: str = NEG_ID) -> str:
    return f"/api/negotiations/{neg_id}/secure"


def _improve_url(neg_id: str = NEG_ID) -> str:
    return f"/api/negotiations/{neg_id}/improve"


def _end_url(neg_id: str = NEG_ID) -> str:
    return f"/api/negotiations/{neg_id}/end"


# ===========================================================================
# 1. GET /offers — Response structure
#    Error category: Integration errors (API contract)
# ===========================================================================


class TestGetOffersStructure:
    """Falsifiable claim: GET /offers returns 3 cards with the correct schema."""

    def test_get_offers_returns_200_with_three_cards(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation
        WHEN the supplier GETs offers for the first time
        THEN the response is 200 with exactly 3 cards."""
        resp = client.get(_offers_url())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cards"]) == 3

    def test_each_card_has_required_fields(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation
        WHEN the supplier GETs offers
        THEN each card has label, recommended, terms (4 fields), signals (4 fields)."""
        resp = client.get(_offers_url())
        for card in resp.json()["cards"]:
            assert "label" in card
            assert "recommended" in card
            assert isinstance(card["recommended"], bool)
            for field in ("price", "delivery", "payment", "contract"):
                assert field in card["terms"], f"Missing terms.{field}"
                assert field in card["signals"], f"Missing signals.{field}"

    def test_card_labels_are_the_three_expected_profiles(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation
        WHEN the supplier GETs offers
        THEN the card labels are BEST PRICE, MOST BALANCED, FASTEST PAYMENT."""
        resp = client.get(_offers_url())
        labels = {card["label"] for card in resp.json()["cards"]}
        assert labels == {"BEST PRICE", "MOST BALANCED", "FASTEST PAYMENT"}

    def test_exactly_one_card_is_recommended(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation
        WHEN the supplier GETs offers
        THEN exactly one card has recommended=true (MOST BALANCED)."""
        resp = client.get(_offers_url())
        recommended = [c for c in resp.json()["cards"] if c["recommended"]]
        assert len(recommended) == 1
        assert recommended[0]["label"] == "MOST BALANCED"

    def test_terms_are_formatted_strings_not_raw_numbers(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation
        WHEN the supplier GETs offers
        THEN terms are display-formatted: price as $X.XX, payment as Net N,
        delivery as N days, contract as N months."""
        resp = client.get(_offers_url())
        terms = resp.json()["cards"][0]["terms"]
        assert terms["price"].startswith("$")
        assert terms["payment"].startswith("Net ")
        assert terms["delivery"].endswith(" days")
        assert terms["contract"].endswith(" months")

    def test_response_includes_banner_and_actions(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation
        WHEN the supplier GETs offers
        THEN the response includes a banner string and actions_available list."""
        data = client.get(_offers_url()).json()
        assert isinstance(data["banner"], str)
        assert len(data["banner"]) > 0
        assert isinstance(data["actions_available"], list)
        assert len(data["actions_available"]) > 0

    def test_initial_offers_have_no_secured_offer(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation with no prior secure action
        WHEN the supplier GETs offers
        THEN secured_offer is null."""
        data = client.get(_offers_url()).json()
        assert data["secured_offer"] is None


# ===========================================================================
# 2. is_first_visit flag
#    Error category: Data errors (stale state)
# ===========================================================================


class TestIsFirstVisit:
    """Falsifiable claim: is_first_visit is true on first GET, false after."""

    def test_first_get_sets_is_first_visit_true(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation
        WHEN the supplier GETs offers for the first time
        THEN is_first_visit is true."""
        data = client.get(_offers_url()).json()
        assert data["is_first_visit"] is True

    def test_second_get_sets_is_first_visit_false(self, client: TestClient) -> None:
        """GIVEN an already-activated negotiation
        WHEN the supplier GETs offers again
        THEN is_first_visit is false."""
        client.get(_offers_url())  # activate
        data = client.get(_offers_url()).json()
        assert data["is_first_visit"] is False


# ===========================================================================
# 3. Action response shapes
#    Error category: Integration errors (serialization contract)
# ===========================================================================


class TestActionResponseShapes:
    """Falsifiable claims about each action endpoint's response structure."""

    def test_agree_returns_status_and_agreed_terms(self, client: TestClient) -> None:
        """GIVEN an active negotiation
        WHEN the supplier agrees on MOST_BALANCED
        THEN the response has status='accepted' and agreed_terms with 4 term fields."""
        client.get(_offers_url())  # activate
        resp = client.post(_agree_url(), json={"card_label": "MOST_BALANCED"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        for field in ("price", "delivery", "payment", "contract"):
            assert field in data["agreed_terms"]

    def test_secure_returns_secured_offer_with_label_and_terms(
        self, client: TestClient
    ) -> None:
        """GIVEN an active negotiation
        WHEN the supplier secures BEST_PRICE
        THEN the response has secured_offer with label and terms."""
        client.get(_offers_url())  # activate
        resp = client.post(_secure_url(), json={"card_label": "BEST_PRICE"})
        assert resp.status_code == 200
        data = resp.json()
        assert "secured_offer" in data
        assert "label" in data["secured_offer"]
        assert "terms" in data["secured_offer"]
        for field in ("price", "delivery", "payment", "contract"):
            assert field in data["secured_offer"]["terms"]

    def test_improve_returns_offers_response_shape(self, client: TestClient) -> None:
        """GIVEN an active negotiation (not final round)
        WHEN the supplier improves on FASTEST_PAYMENT
        THEN the response has the same shape as GET /offers."""
        client.get(_offers_url())  # activate
        resp = client.post(_improve_url(), json={"card_label": "FASTEST_PAYMENT"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["cards"]) == 3
        assert "banner" in data
        assert "is_final_round" in data
        assert "actions_available" in data

    def test_end_returns_no_deal_status(self, client: TestClient) -> None:
        """GIVEN an active negotiation
        WHEN the supplier ends the negotiation
        THEN the response has status='no_deal'."""
        client.get(_offers_url())  # activate
        resp = client.post(_end_url())
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_deal"


# ===========================================================================
# 4. Terminal state enforcement (409 Conflict)
#    Error category: Logic errors (state machine)
# ===========================================================================


class TestTerminalStateAfterAgree:
    """Falsifiable claim: After agree, ALL actions return 409."""

    def _activate_and_agree(self, client: TestClient) -> None:
        client.get(_offers_url())
        resp = client.post(_agree_url(), json={"card_label": "MOST_BALANCED"})
        assert resp.status_code == 200

    def test_get_offers_after_agree_returns_409(self, client: TestClient) -> None:
        self._activate_and_agree(client)
        resp = client.get(_offers_url())
        assert resp.status_code == 409

    def test_improve_after_agree_returns_409(self, client: TestClient) -> None:
        self._activate_and_agree(client)
        resp = client.post(_improve_url(), json={"card_label": "BEST_PRICE"})
        assert resp.status_code == 409

    def test_secure_after_agree_returns_409(self, client: TestClient) -> None:
        self._activate_and_agree(client)
        resp = client.post(_secure_url(), json={"card_label": "BEST_PRICE"})
        assert resp.status_code == 409

    def test_agree_after_agree_returns_409(self, client: TestClient) -> None:
        self._activate_and_agree(client)
        resp = client.post(_agree_url(), json={"card_label": "BEST_PRICE"})
        assert resp.status_code == 409

    def test_end_after_agree_returns_409(self, client: TestClient) -> None:
        self._activate_and_agree(client)
        resp = client.post(_end_url())
        assert resp.status_code == 409


class TestTerminalStateAfterEnd:
    """Falsifiable claim: After end (no_deal), ALL actions return 409."""

    def _activate_and_end(self, client: TestClient) -> None:
        client.get(_offers_url())
        resp = client.post(_end_url())
        assert resp.status_code == 200

    def test_get_offers_after_end_returns_409(self, client: TestClient) -> None:
        self._activate_and_end(client)
        resp = client.get(_offers_url())
        assert resp.status_code == 409

    def test_improve_after_end_returns_409(self, client: TestClient) -> None:
        self._activate_and_end(client)
        resp = client.post(_improve_url(), json={"card_label": "BEST_PRICE"})
        assert resp.status_code == 409

    def test_secure_after_end_returns_409(self, client: TestClient) -> None:
        self._activate_and_end(client)
        resp = client.post(_secure_url(), json={"card_label": "BEST_PRICE"})
        assert resp.status_code == 409

    def test_agree_after_end_returns_409(self, client: TestClient) -> None:
        self._activate_and_end(client)
        resp = client.post(_agree_url(), json={"card_label": "BEST_PRICE"})
        assert resp.status_code == 409

    def test_end_after_end_returns_409(self, client: TestClient) -> None:
        self._activate_and_end(client)
        resp = client.post(_end_url())
        assert resp.status_code == 409


# ===========================================================================
# 5. Full negotiation flow (happy path through multiple rounds)
#    Error category: Integration errors (end-to-end flow)
# ===========================================================================


class TestFullNegotiationFlow:
    """Falsifiable claim: A full flow of GET -> improve -> improve -> secure ->
    agree works end-to-end and each step returns valid data."""

    def test_multi_round_flow_to_agreement(self, client: TestClient) -> None:
        """GIVEN a PENDING negotiation with max_rounds=5
        WHEN the supplier: GETs offers, improves twice, secures, then agrees
        THEN each step succeeds with the correct status code and response shape,
        and the final agree returns status='accepted'."""
        # Round 1: GET offers (activates)
        r1 = client.get(_offers_url())
        assert r1.status_code == 200
        data1 = r1.json()
        assert data1["is_first_visit"] is True
        assert data1["is_final_round"] is False
        assert "improve" in data1["actions_available"]

        # Round 1 -> 2: Improve on BEST_PRICE
        r2 = client.post(_improve_url(), json={"card_label": "BEST_PRICE"})
        assert r2.status_code == 200
        data2 = r2.json()
        assert data2["is_first_visit"] is False
        assert len(data2["cards"]) == 3

        # Round 2 -> 3: Improve on MOST_BALANCED
        r3 = client.post(_improve_url(), json={"card_label": "MOST_BALANCED"})
        assert r3.status_code == 200

        # Secure FASTEST_PAYMENT as fallback (does not advance round)
        r4 = client.post(_secure_url(), json={"card_label": "FASTEST_PAYMENT"})
        assert r4.status_code == 200
        assert "secured_offer" in r4.json()

        # Verify secured offer is now visible in GET offers
        r5 = client.get(_offers_url())
        assert r5.status_code == 200
        assert r5.json()["secured_offer"] is not None

        # Agree on MOST_BALANCED
        r6 = client.post(_agree_url(), json={"card_label": "MOST_BALANCED"})
        assert r6.status_code == 200
        assert r6.json()["status"] == "accepted"

        # Confirm terminal: mutation actions return 409
        r7 = client.post(_improve_url(), json={"card_label": "BEST_PRICE"})
        assert r7.status_code == 409


# ===========================================================================
# 6. Final round behavior
#    Error category: Logic errors (boundary condition on round counter)
# ===========================================================================


class TestFinalRoundBehavior:
    """Falsifiable claim: On the final round, 'improve' is NOT in
    actions_available, and POST /improve returns an error."""

    def test_final_round_excludes_improve_from_actions(
        self, final_round_client: TestClient
    ) -> None:
        """GIVEN a negotiation with max_rounds=1
        WHEN the supplier GETs offers (activating at round 1 = final round)
        THEN actions_available does NOT include 'improve'."""
        data = final_round_client.get(_offers_url()).json()
        assert data["is_final_round"] is True
        assert "improve" not in data["actions_available"]
        assert "agree" in data["actions_available"]
        assert "secure" in data["actions_available"]

    def test_improve_on_final_round_is_rejected(
        self, final_round_client: TestClient
    ) -> None:
        """GIVEN a negotiation on its final round
        WHEN the supplier attempts to improve
        THEN the API returns an error (not 200).

        NOTE: Currently returns 500 because _raise_terminal in routes.py only
        checks for 'terminal'/'accepted'/'no_deal' in the error message, but
        the NegotiationError for final-round improve says 'Cannot improve on
        the final round' which matches none of those keywords.
        """
        final_round_client.get(_offers_url())  # activate
        resp = final_round_client.post(
            _improve_url(), json={"card_label": "BEST_PRICE"}
        )
        assert resp.status_code != 200

    def test_improve_on_final_round_returns_409_not_500(
        self, final_round_client: TestClient
    ) -> None:
        """GIVEN a negotiation on its final round
        WHEN the supplier attempts to improve
        THEN the API should return 409 (not 500)."""
        final_round_client.get(_offers_url())  # activate
        resp = final_round_client.post(
            _improve_url(), json={"card_label": "BEST_PRICE"}
        )
        assert resp.status_code == 409

    def test_reaching_final_round_via_improves(self, client: TestClient) -> None:
        """GIVEN a negotiation with max_rounds=5
        WHEN the supplier improves 4 times (rounds 1->2->3->4->5)
        THEN the 5th round response has is_final_round=true and no 'improve'."""
        client.get(_offers_url())  # activate, round 1
        for _ in range(4):
            resp = client.post(
                _improve_url(), json={"card_label": "MOST_BALANCED"}
            )
            assert resp.status_code == 200
        # After 4 improves we are at round 5 (the final round)
        data = resp.json()  # type: ignore[possibly-undefined]
        assert data["is_final_round"] is True
        assert "improve" not in data["actions_available"]


# ===========================================================================
# 7. Secured offer persistence
#    Error category: Data errors (state not persisted across requests)
# ===========================================================================


class TestSecuredOfferPersistence:
    """Falsifiable claim: After POST /secure, subsequent GET /offers shows
    the secured_offer."""

    def test_secured_offer_appears_in_subsequent_get(self, client: TestClient) -> None:
        """GIVEN an active negotiation
        WHEN the supplier secures BEST_PRICE, then GETs offers
        THEN the response includes secured_offer with formatted terms."""
        client.get(_offers_url())  # activate
        client.post(_secure_url(), json={"card_label": "BEST_PRICE"})
        data = client.get(_offers_url()).json()
        secured = data["secured_offer"]
        assert secured is not None
        assert "label" in secured
        assert "terms" in secured
        assert secured["terms"]["price"].startswith("$")

    def test_secure_can_be_overwritten(self, client: TestClient) -> None:
        """GIVEN an active negotiation with BEST_PRICE secured
        WHEN the supplier secures FASTEST_PAYMENT instead
        THEN GET /offers shows the new secured offer (terms may differ)."""
        client.get(_offers_url())  # activate
        client.post(_secure_url(), json={"card_label": "BEST_PRICE"})

        client.post(_secure_url(), json={"card_label": "FASTEST_PAYMENT"})
        data = client.get(_offers_url()).json()
        # Terms may coincidentally match across profiles; the important assertion
        # is that the secured offer is still set after overwriting.
        assert data["secured_offer"] is not None


# ===========================================================================
# 8. Invalid card_label (input validation)
#    Error category: Input/output errors (boundary: invalid enum value)
# ===========================================================================


class TestInvalidCardLabel:
    """Falsifiable claim: Invalid card_label values return 422."""

    def test_agree_with_invalid_label_returns_422(self, client: TestClient) -> None:
        client.get(_offers_url())
        resp = client.post(_agree_url(), json={"card_label": "NONEXISTENT"})
        assert resp.status_code == 422

    def test_improve_with_empty_label_returns_422(self, client: TestClient) -> None:
        client.get(_offers_url())
        resp = client.post(_improve_url(), json={"card_label": ""})
        assert resp.status_code == 422

    def test_secure_with_lowercase_label_returns_422(self, client: TestClient) -> None:
        """card_label must match the enum exactly (uppercase with underscores)."""
        client.get(_offers_url())
        resp = client.post(_secure_url(), json={"card_label": "best_price"})
        assert resp.status_code == 422


# ===========================================================================
# 9. Nonexistent negotiation
#    Error category: Input/output errors (missing resource)
# ===========================================================================


class TestNonexistentNegotiation:
    """Falsifiable claim: Requesting a non-existent negotiation returns an error."""

    def test_get_offers_for_missing_negotiation(self, client: TestClient) -> None:
        resp = client.get(_offers_url("does-not-exist"))
        # InMemoryRepo raises KeyError; FastAPI will return 500 unless caught.
        assert resp.status_code >= 400

    def test_agree_for_missing_negotiation(self, client: TestClient) -> None:
        resp = client.post(
            _agree_url("does-not-exist"),
            json={"card_label": "BEST_PRICE"},
        )
        assert resp.status_code >= 400


# ===========================================================================
# 10. Improve advances round; secure does not
#     Error category: Logic errors (state mutation side-effects)
# ===========================================================================


class TestRoundAdvancement:
    """Falsifiable claim: Improve advances the round; Secure does not."""

    def test_improve_changes_the_offers(self, client: TestClient) -> None:
        """GIVEN an active negotiation at round 1
        WHEN the supplier improves
        THEN the returned cards may differ from the original round 1 cards
        AND is_first_visit is false on the improve response."""
        client.get(_offers_url()).json()
        improved = client.post(
            _improve_url(), json={"card_label": "BEST_PRICE"}
        ).json()
        assert improved["is_first_visit"] is False
        # Cards should generally change (concession curve moves target utility)
        # but we only verify the structural contract holds.
        assert len(improved["cards"]) == 3

    def test_secure_does_not_change_cards(self, client: TestClient) -> None:
        """GIVEN an active negotiation
        WHEN the supplier secures a card, then GETs offers
        THEN the cards remain the same (round did not advance)."""
        first = client.get(_offers_url()).json()
        client.post(_secure_url(), json={"card_label": "BEST_PRICE"})
        second = client.get(_offers_url()).json()
        # Same cards (round unchanged)
        first_terms = [c["terms"] for c in first["cards"]]
        second_terms = [c["terms"] for c in second["cards"]]
        assert first_terms == second_terms


# ===========================================================================
# 11. 409 error response body
#     Error category: Integration errors (error serialization)
# ===========================================================================


class TestErrorResponseBody:
    """Falsifiable claim: 409 responses contain a JSON body with 'detail.error'."""

    def test_409_has_error_detail(self, client: TestClient) -> None:
        """GIVEN a terminal negotiation (agreed)
        WHEN any action is attempted
        THEN the 409 body has detail.error as a descriptive string."""
        client.get(_offers_url())
        client.post(_agree_url(), json={"card_label": "MOST_BALANCED"})
        resp = client.post(_improve_url(), json={"card_label": "BEST_PRICE"})
        assert resp.status_code == 409
        detail = resp.json()["detail"]
        assert "error" in detail
        assert isinstance(detail["error"], str)
        assert len(detail["error"]) > 0
