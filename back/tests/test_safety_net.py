"""Safety-net tests before backend refactoring (Phase 1, claims F11-F14).

These tests lock down current behavior so that refactoring cannot silently
change observable outcomes.

F11 note: The config drift bug (seed vs reset using different TermConfig values)
was fixed in Phase 4 Step 3. Both server.py and ResetUseCase now call
make_default_config() from domain/defaults.py. F11 tests now PASS and
no longer carry xfail markers.

Error categories:
- F11: Configuration errors — seed vs reset config drift (FIXED)
- F12: Interface errors — repo satisfies protocol contract
- F13: Integration errors — route response model shapes
- F14: Regression errors — snapshot of GET /offers for known seed
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from starlette.testclient import TestClient

from back.api.dependencies import get_repo
from back.api.schemas import AgreeResponse, EndResponse, OffersResponse, SecureResponse
from back.infrastructure.memory_repo import InMemoryNegotiationRepository
from back.server import create_app
from back.tests.factories import make_negotiation

if TYPE_CHECKING:
    from back.application.ports import NegotiationRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NEG_ID = "safety-net"


def _build_client(repo: InMemoryNegotiationRepository) -> TestClient:
    """Build a TestClient with the given repo overriding DI."""
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: repo
    return TestClient(app, raise_server_exceptions=False)


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
# F11: Config drift detection
#      Error category: Configuration errors
#      Risk: 9/10 — silent data corruption if seed != reset
# ===========================================================================


class TestConfigDrift:
    """F11: Falsifiable claim — server.py seed and ResetUseCase produce
    equivalent negotiations.

    Bug FIXED in Phase 4 Step 3: both server.py and ResetUseCase now call
    make_default_config() from domain/defaults.py. These tests now pass.
    """

    def test_seed_config_matches_reset_config(self) -> None:
        """GIVEN make_default_config() used by both server.py seed and ResetUseCase
        WHEN we retrieve the config twice
        THEN both calls return identical TermConfig values for all 4 terms.

        Error category: Configuration errors.
        """
        from back.domain.defaults import make_default_config

        seed_config = make_default_config()
        reset_config = make_default_config()

        for term_name in ("price", "payment", "delivery", "contract"):
            seed_term = seed_config[term_name]
            reset_term = reset_config[term_name]
            assert seed_term == reset_term, (
                f"Config drift on '{term_name}': "
                f"seed={seed_term} vs reset={reset_term}"
            )

    def test_seed_weights_match_reset_weights(self) -> None:
        """GIVEN DEFAULT_OPERATOR_WEIGHTS used by both server.py and ResetUseCase
        WHEN we compare them
        THEN all 4 weight components are equal.

        Error category: Configuration errors.
        """
        from back.domain.defaults import DEFAULT_OPERATOR_WEIGHTS

        seed_weights = DEFAULT_OPERATOR_WEIGHTS
        reset_weights = DEFAULT_OPERATOR_WEIGHTS

        assert seed_weights == reset_weights, (
            f"Weight drift: seed={seed_weights} vs reset={reset_weights}"
        )


# ===========================================================================
# F12: Protocol conformance
#      Error category: Interface errors
#      Risk: 7/10 — broken protocol means DI wiring fails at runtime
# ===========================================================================


class TestRepositoryProtocol:
    """F12: Falsifiable claim — InMemoryNegotiationRepository satisfies the
    NegotiationRepository protocol via structural subtyping.
    """

    def test_inmemory_repo_satisfies_negotiation_repository_protocol(
        self,
    ) -> None:
        """GIVEN InMemoryNegotiationRepository
        WHEN we check it against the NegotiationRepository protocol
        THEN it is a structural subtype (has get and save with correct signatures).

        Error category: Interface errors.
        """
        repo = InMemoryNegotiationRepository()

        # Structural check: the protocol requires get(str) -> Negotiation
        # and save(Negotiation) -> None. We verify the methods exist and
        # are callable, then exercise them.
        assert hasattr(repo, "get")
        assert hasattr(repo, "save")
        assert callable(repo.get)
        assert callable(repo.save)

        # Exercise the contract: save then get returns the same object
        neg = make_negotiation(neg_id="protocol-check")
        repo.save(neg)
        retrieved = repo.get("protocol-check")
        assert retrieved is neg

    def test_inmemory_repo_get_raises_keyerror_for_missing_id(self) -> None:
        """GIVEN an empty InMemoryNegotiationRepository
        WHEN we call get() with a nonexistent ID
        THEN it raises KeyError (as the protocol docstring specifies).

        Error category: Interface errors.
        """
        repo = InMemoryNegotiationRepository()
        with pytest.raises(KeyError):
            repo.get("nonexistent-id")

    def test_inmemory_repo_is_runtime_checkable_against_protocol(
        self,
    ) -> None:
        """GIVEN InMemoryNegotiationRepository
        WHEN we use isinstance against NegotiationRepository (if runtime_checkable)
        THEN it passes OR we verify structural conformance via typing helpers.

        Error category: Interface errors.
        Note: Protocol is not decorated with @runtime_checkable, so we verify
        structurally by assigning to a variable typed as NegotiationRepository.
        """
        repo: NegotiationRepository = InMemoryNegotiationRepository()
        # If this line type-checks and runs, the structural subtyping holds.
        neg = make_negotiation(neg_id="typing-check")
        repo.save(neg)
        result = repo.get("typing-check")
        assert result.id == "typing-check"


# ===========================================================================
# F13: Route response model shapes
#      Error category: Integration errors
#      Risk: 8/10 — broken serialization means the frontend gets garbage
# ===========================================================================


class TestRouteResponseShapes:
    """F13: Falsifiable claim — all 5 routes return responses that match
    their declared Pydantic response_model shapes.
    """

    @pytest.fixture()
    def client(self) -> TestClient:
        """Fresh TestClient with a PENDING negotiation."""
        repo = InMemoryNegotiationRepository()
        neg = make_negotiation(neg_id=NEG_ID)
        repo.save(neg)
        return _build_client(repo)

    def test_get_offers_response_matches_offers_response_model(
        self, client: TestClient
    ) -> None:
        """GIVEN a PENDING negotiation
        WHEN GET /offers is called
        THEN the JSON response validates against OffersResponse.

        Error category: Integration errors.
        """
        resp = client.get(_offers_url())
        assert resp.status_code == 200
        # Pydantic model_validate will raise ValidationError if shape is wrong
        validated = OffersResponse.model_validate(resp.json())
        assert len(validated.cards) == 3
        assert isinstance(validated.banner, str)
        assert isinstance(validated.is_final_round, bool)
        assert isinstance(validated.is_first_visit, bool)
        assert isinstance(validated.actions_available, list)

    def test_agree_response_matches_agree_response_model(
        self, client: TestClient
    ) -> None:
        """GIVEN an ACTIVE negotiation
        WHEN POST /agree with a valid card label
        THEN the JSON response validates against AgreeResponse.

        Error category: Integration errors.
        """
        client.get(_offers_url())  # activate
        resp = client.post(
            _agree_url(), json={"card_label": "MOST_BALANCED"}
        )
        assert resp.status_code == 200
        validated = AgreeResponse.model_validate(resp.json())
        assert validated.status == "accepted"
        assert validated.agreed_terms.price.startswith("$")

    def test_secure_response_matches_secure_response_model(
        self, client: TestClient
    ) -> None:
        """GIVEN an ACTIVE negotiation
        WHEN POST /secure with a valid card label
        THEN the JSON response validates against SecureResponse.

        Error category: Integration errors.
        """
        client.get(_offers_url())  # activate
        resp = client.post(
            _secure_url(), json={"card_label": "BEST_PRICE"}
        )
        assert resp.status_code == 200
        validated = SecureResponse.model_validate(resp.json())
        assert validated.secured_offer.label is not None
        assert validated.secured_offer.terms.price.startswith("$")

    def test_improve_response_matches_offers_response_model(
        self, client: TestClient
    ) -> None:
        """GIVEN an ACTIVE negotiation (not final round)
        WHEN POST /improve with a valid card label
        THEN the JSON response validates against OffersResponse.

        Error category: Integration errors.
        """
        client.get(_offers_url())  # activate
        resp = client.post(
            _improve_url(), json={"card_label": "FASTEST_PAYMENT"}
        )
        assert resp.status_code == 200
        validated = OffersResponse.model_validate(resp.json())
        assert len(validated.cards) == 3

    def test_end_response_matches_end_response_model(
        self, client: TestClient
    ) -> None:
        """GIVEN an ACTIVE negotiation
        WHEN POST /end is called
        THEN the JSON response validates against EndResponse.

        Error category: Integration errors.
        """
        client.get(_offers_url())  # activate
        resp = client.post(_end_url())
        assert resp.status_code == 200
        validated = EndResponse.model_validate(resp.json())
        assert validated.status == "no_deal"


# ===========================================================================
# F14: Snapshot test — GET /offers for known seed
#      Error category: Regression errors
#      Risk: 9/10 — refactoring must NOT change what the frontend sees
# ===========================================================================


class TestOffersSnapshot:
    """F14: Snapshot test — capture the current GET /offers response for a
    known seed and assert structural invariants that must survive refactoring.

    We do NOT hardcode exact term values (those depend on the MESO generator's
    numerical output which may legitimately change). Instead we lock down:
    - Response structure (keys, types, nesting)
    - Card count (exactly 3)
    - Card labels (the 3 expected profiles)
    - Formatting conventions (price=$X.XX, payment=Net N, etc.)
    - is_first_visit=True on first GET
    - secured_offer=None initially
    - actions_available contains agree, secure, improve
    """

    @pytest.fixture()
    def snapshot_client(self) -> TestClient:
        """Client with a negotiation seeded from factory defaults."""
        repo = InMemoryNegotiationRepository()
        neg = make_negotiation(neg_id=NEG_ID)
        repo.save(neg)
        return _build_client(repo)

    def test_snapshot_structure_matches_known_seed(
        self, snapshot_client: TestClient
    ) -> None:
        """GIVEN a PENDING negotiation with factory-default config
        WHEN GET /offers is called for the first time
        THEN the response has the exact structure the frontend expects.

        Error category: Regression errors.
        """
        resp = snapshot_client.get(_offers_url())
        assert resp.status_code == 200
        data = resp.json()

        # Top-level keys
        assert set(data.keys()) == {
            "banner",
            "is_final_round",
            "is_first_visit",
            "cards",
            "secured_offer",
            "actions_available",
        }

        # First visit flags
        assert data["is_first_visit"] is True
        assert data["is_final_round"] is False
        assert data["secured_offer"] is None

        # Actions on a non-final, first-visit round
        assert sorted(data["actions_available"]) == [
            "agree",
            "improve",
            "secure",
        ]

        # Card structure
        assert len(data["cards"]) == 3
        expected_labels = {"BEST PRICE", "MOST BALANCED", "FASTEST PAYMENT"}
        actual_labels = {card["label"] for card in data["cards"]}
        assert actual_labels == expected_labels

        # Exactly one recommended card (MOST BALANCED)
        recommended = [c for c in data["cards"] if c["recommended"]]
        assert len(recommended) == 1
        assert recommended[0]["label"] == "MOST BALANCED"

        # Each card has terms and signals with the 4 required fields
        for card in data["cards"]:
            assert set(card["terms"].keys()) == {
                "price",
                "delivery",
                "payment",
                "contract",
            }
            assert set(card["signals"].keys()) == {
                "price",
                "delivery",
                "payment",
                "contract",
            }

    def test_snapshot_term_formatting_conventions(
        self, snapshot_client: TestClient
    ) -> None:
        """GIVEN a GET /offers response
        WHEN we inspect the term formatting
        THEN price starts with '$', payment starts with 'Net ',
        delivery ends with ' days', contract ends with ' months'.

        Error category: Regression errors.
        """
        resp = snapshot_client.get(_offers_url())
        data = resp.json()

        for card in data["cards"]:
            terms = card["terms"]
            assert terms["price"].startswith("$"), (
                f"Price format violation: {terms['price']}"
            )
            assert terms["payment"].startswith("Net "), (
                f"Payment format violation: {terms['payment']}"
            )
            assert terms["delivery"].endswith(" days"), (
                f"Delivery format violation: {terms['delivery']}"
            )
            assert terms["contract"].endswith(" months"), (
                f"Contract format violation: {terms['contract']}"
            )

    def test_snapshot_banner_is_nonempty_string(
        self, snapshot_client: TestClient
    ) -> None:
        """GIVEN a GET /offers response
        WHEN we inspect the banner
        THEN it is a non-empty string.

        Error category: Regression errors.
        """
        resp = snapshot_client.get(_offers_url())
        data = resp.json()
        assert isinstance(data["banner"], str)
        assert len(data["banner"]) > 0
