"""HTTP route handlers — thin adapters between HTTP and application use cases.

Responsibilities (only):
- Parse incoming JSON into use case inputs.
- Call the appropriate use case.
- Serialize the use case output into the JSON response.

Routes MUST NOT contain domain logic, try/except for domain errors, or
repository instantiation. Domain exceptions are handled centrally by
exception_handlers.py (registered in server.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter

from back.api.dependencies import (  # noqa: TC001
    AgreeDep,
    EndNegotiationDep,
    GetOffersDep,
    ImproveDep,
    ResetDep,
    SecureDep,
)
from back.api.schemas import (
    AgreeResponse,
    CardLabelRequest,
    EndResponse,
    OffersResponse,
    ResetResponse,
    SecuredOfferResponse,
    SecureResponse,
    SignalsResponse,
    TermsResponse,
)
from back.application.get_offers import OffersDTO  # noqa: TC001

if TYPE_CHECKING:
    from back.domain.types import TermValues

router = APIRouter(prefix="/api")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def _format_terms(terms: TermValues) -> TermsResponse:
    """Format raw numeric TermValues into display strings.

    Conventions (from feature spec):
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


def _build_offers_response(dto: OffersDTO) -> OffersResponse:
    """Convert an OffersDTO to an OffersResponse."""
    from back.api.schemas import CardResponse

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

    secured: SecuredOfferResponse | None = None
    if dto.secured_offer is not None:
        secured = SecuredOfferResponse(
            label="SECURED",
            terms=_format_terms(dto.secured_offer),
        )

    return OffersResponse(
        banner=dto.banner,
        is_final_round=dto.is_final_round,
        is_first_visit=dto.is_first_visit,
        cards=cards,
        secured_offer=secured,
        actions_available=dto.actions_available,
    )


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
    dto = use_case.execute(negotiation_id)
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
    dto = use_case.execute(negotiation_id, body.card_label)
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
    dto = use_case.execute(negotiation_id, body.card_label)
    return SecureResponse(
        secured_offer=SecuredOfferResponse(
            label="SECURED",
            terms=_format_terms(dto.secured_offer),
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
    dto = use_case.execute(negotiation_id, body.card_label)
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
    use_case.execute(negotiation_id)
    return EndResponse(status="no_deal")


@router.post(
    "/negotiations/{negotiation_id}/reset",
    response_model=ResetResponse,
)
async def reset_negotiation(
    negotiation_id: str,
    use_case: ResetDep,
) -> ResetResponse:
    """Reset a negotiation to its initial state (demo convenience endpoint)."""
    use_case.execute(negotiation_id)
    return ResetResponse(status="reset")
