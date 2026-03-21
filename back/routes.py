"""HTTP route handlers — thin adapter between HTTP and application use cases.

Responsibilities:
- Parse incoming JSON into use case inputs.
- Call the appropriate use case.
- Serialize the use case output into the JSON contract from ARCHITECTURE.md.
- Map terminal-state errors to 409 Conflict.

Routes MUST NOT import from infrastructure or instantiate repositories.
All use cases arrive via FastAPI dependency injection.
"""

from typing import Any, NoReturn

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from back.dependencies import (
    AgreeDep,
    EndNegotiationDep,
    GetOffersDep,
    ImproveDep,
    SecureDep,
)
from back.domain.negotiation import NegotiationError
from back.domain.types import CardLabel, TermValues

router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class CardLabelRequest(BaseModel):
    card_label: str


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class TermsResponse(BaseModel):
    price: str
    delivery: str
    payment: str
    contract: str


class SignalsResponse(BaseModel):
    price: str
    delivery: str
    payment: str
    contract: str


class CardResponse(BaseModel):
    label: str
    recommended: bool
    terms: TermsResponse
    signals: SignalsResponse


class SecuredOfferResponse(BaseModel):
    label: str
    terms: TermsResponse


class OffersResponse(BaseModel):
    banner: str
    is_final_round: bool
    is_first_visit: bool
    cards: list[CardResponse]
    secured_offer: SecuredOfferResponse | None
    actions_available: list[str]


class AgreeResponse(BaseModel):
    status: str
    agreed_terms: TermsResponse


class SecureResponse(BaseModel):
    secured_offer: SecuredOfferResponse


class EndResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_card_label(raw: str) -> CardLabel:
    """Parse a string card label from the request body into a CardLabel enum.

    Raises:
        HTTPException: 422 Unprocessable Entity if the label is invalid.
    """
    try:
        return CardLabel(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": f"Invalid card_label '{raw}'. "
                f"Must be one of: {[e.value for e in CardLabel]}"
            },
        ) from exc


def _format_terms(terms: TermValues) -> TermsResponse:
    """Format raw numeric TermValues into display strings for the API response.

    Conventions (from feature spec examples):
    - price: dollars per thousand boxes -> "$120.00"
    - payment: days -> "Net 60"
    - delivery: days -> "10 days"
    - contract: months -> "12 months"
    """
    return TermsResponse(
        price=f"${terms.price:.2f}",
        payment=f"Net {int(terms.payment)}",
        delivery=f"{int(terms.delivery)} days",
        contract=f"{int(terms.contract)} months",
    )


def _build_offers_response(dto: Any) -> OffersResponse:
    """Convert GetOffersUseCase / ImproveUseCase output DTO to response model."""
    cards = [
        CardResponse(
            label=card.label,
            recommended=card.recommended,
            terms=_format_terms(card.terms),
            signals=SignalsResponse(
                price=card.signals.price,
                delivery=card.signals.delivery,
                payment=card.signals.payment,
                contract=card.signals.contract,
            ),
        )
        for card in dto.cards
    ]

    # dto.secured_offer is TermValues | None (no label available in DTO)
    secured: SecuredOfferResponse | None = None
    if dto.secured_offer is not None:
        secured = SecuredOfferResponse(
            label="SECURED",
            terms=_format_terms(dto.secured_offer),
        )

    return OffersResponse(
        banner=dto.banner,
        is_final_round=dto.is_final_round,
        is_first_visit=getattr(dto, "is_first_visit", False),
        cards=cards,
        secured_offer=secured,
        actions_available=dto.actions_available,
    )


def _raise_terminal(exc: NegotiationError | ValueError) -> NoReturn:
    """Re-raise exc as 409 Conflict when it signals a terminal negotiation state.

    Always raises — either HTTPException (409) or the original exc.
    Typed -> NoReturn so mypy treats the except branch as unreachable.
    """
    msg = str(exc).lower()
    if "terminal" in msg or "accepted" in msg or "no_deal" in msg or "no deal" in msg:
        raise HTTPException(status_code=409, detail={"error": str(exc)})
    raise exc


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/negotiations/{negotiation_id}/offers",
    response_model=OffersResponse,
)
async def get_offers(
    negotiation_id: str,
    use_case: GetOffersDep,
) -> OffersResponse:
    """Return current MESO offer set for the supplier UI."""
    try:
        dto = use_case.execute(negotiation_id)
    except (NegotiationError, ValueError) as exc:
        _raise_terminal(exc)  # _raise_terminal always raises
    return _build_offers_response(dto)


@router.post(
    "/negotiations/{negotiation_id}/agree",
    response_model=AgreeResponse,
)
async def agree(
    negotiation_id: str,
    body: CardLabelRequest,
    use_case: AgreeDep,
) -> AgreeResponse:
    """Accept a card and close the deal."""
    label = _parse_card_label(body.card_label)
    try:
        dto = use_case.execute(negotiation_id, label)
    except (NegotiationError, ValueError) as exc:
        _raise_terminal(exc)
    return AgreeResponse(
        status="accepted",
        agreed_terms=_format_terms(dto.agreed_terms),
    )


@router.post(
    "/negotiations/{negotiation_id}/secure",
    response_model=SecureResponse,
)
async def secure(
    negotiation_id: str,
    body: CardLabelRequest,
    use_case: SecureDep,
) -> SecureResponse:
    """Mark a card as the fallback secured offer."""
    label = _parse_card_label(body.card_label)
    try:
        dto = use_case.execute(negotiation_id, label)
    except (NegotiationError, ValueError) as exc:
        _raise_terminal(exc)
    # dto.secured_offer is expected to be the TermValues of the secured offer.
    # The label is carried by dto.label if the use case provides it,
    # or derived from dto directly. Fall back gracefully.
    secured_label: str = getattr(dto, "label", "SECURED")
    secured_terms: TermValues = getattr(dto, "secured_offer", dto)
    return SecureResponse(
        secured_offer=SecuredOfferResponse(
            label=secured_label,
            terms=_format_terms(secured_terms),
        )
    )


@router.post(
    "/negotiations/{negotiation_id}/improve",
    response_model=OffersResponse,
)
async def improve(
    negotiation_id: str,
    body: CardLabelRequest,
    use_case: ImproveDep,
) -> OffersResponse:
    """Signal preference, advance round, return updated MESO set."""
    label = _parse_card_label(body.card_label)
    try:
        dto = use_case.execute(negotiation_id, label)
    except (NegotiationError, ValueError) as exc:
        _raise_terminal(exc)
    return _build_offers_response(dto)


@router.post(
    "/negotiations/{negotiation_id}/end",
    response_model=EndResponse,
)
async def end_negotiation(
    negotiation_id: str,
    use_case: EndNegotiationDep,
) -> EndResponse:
    """Handle supplier taking no action on final round — transition to No Deal."""
    try:
        use_case.execute(negotiation_id)
    except (NegotiationError, ValueError) as exc:
        _raise_terminal(exc)
    return EndResponse(status="no_deal")
