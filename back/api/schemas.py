"""Pydantic request and response models for the MESO negotiation API.

All schema classes live here, separate from route handlers. Route handlers
import these types — no schema definitions inside routes.py.

Naming conventions:
- *Request:  inbound JSON body models
- *Response: outbound JSON response models
- ErrorResponse: error body for exception handlers
"""

from pydantic import BaseModel

from back.domain.types import CardLabel

# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------


class TermsResponse(BaseModel):
    """Display-formatted values for one offer's 4 terms."""

    price: str
    delivery: str
    payment: str
    contract: str


class SignalsResponse(BaseModel):
    """Visual signal strength indicators for each term on a card."""

    price: str
    delivery: str
    payment: str
    contract: str


class SecuredOfferResponse(BaseModel):
    """The operator's fallback (secured) offer."""

    label: str
    terms: TermsResponse


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CardLabelRequest(BaseModel):
    """Body for routes that accept a card label selection."""

    card_label: CardLabel


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class CardResponse(BaseModel):
    """One MESO offer card as presented to the supplier."""

    label: str
    recommended: bool
    terms: TermsResponse
    signals: SignalsResponse


class OffersResponse(BaseModel):
    """Response for GET /offers and POST /improve."""

    banner: str
    is_final_round: bool
    is_first_visit: bool
    cards: list[CardResponse]
    secured_offer: SecuredOfferResponse | None
    actions_available: list[str]


class AgreeResponse(BaseModel):
    """Response for POST /agree."""

    status: str
    agreed_terms: TermsResponse


class SecureResponse(BaseModel):
    """Response for POST /secure."""

    secured_offer: SecuredOfferResponse


class EndResponse(BaseModel):
    """Response for POST /end."""

    status: str


class ResetResponse(BaseModel):
    """Response for POST /reset."""

    status: str


# ---------------------------------------------------------------------------
# Error response
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standard error body for all exception handler responses."""

    error: str
