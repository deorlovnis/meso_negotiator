"""HTTP route handlers — v2 API contract."""

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
    AgreeRequest,
    AgreeResponse,
    CardLabelRequest,
    EndResponse,
    ImproveRequest,
    OffersResponse,
    ResetResponse,
    SecuredOfferResponse,
    SignalsResponse,
    TermsResponse,
)
from back.application.get_offers import OffersDTO  # noqa: TC001

if TYPE_CHECKING:
    from back.domain.types import TermValues

router = APIRouter(prefix="/api")


def _format_terms(terms: TermValues) -> TermsResponse:
    return TermsResponse(
        price=f"${terms.price:.2f}",
        payment=f"Net {int(terms.payment)}",
        delivery=f"{int(terms.delivery)} days",
        contract=f"{int(terms.contract)} months",
    )


def _build_offers_response(dto: OffersDTO) -> OffersResponse:
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

    # Build secured offers list sorted by operator utility (Bot Rank)
    sorted_secured = sorted(
        dto.secured_offers,
        key=lambda s: s.operator_utility,
        reverse=True,
    )
    secured_responses = [
        SecuredOfferResponse(
            rank=i + 1,
            label=s.offer.label.value.replace("_", " "),
            terms=_format_terms(s.offer.terms),
            round_secured=s.round_secured,
        )
        for i, s in enumerate(sorted_secured)
    ]

    return OffersResponse(
        banner=dto.banner,
        is_final_round=dto.is_final_round,
        is_first_visit=dto.is_first_visit,
        cards=cards,
        secured_offers=secured_responses,
        can_secure=dto.can_secure,
        actions_available=dto.actions_available,
    )


@router.get(
    "/negotiations/{negotiation_id}/offers",
    response_model=OffersResponse,
)
async def get_offers(
    negotiation_id: str,
    use_case: GetOffersDep,
) -> OffersResponse:
    dto = use_case.execute(negotiation_id)
    return _build_offers_response(dto)


@router.post(
    "/negotiations/{negotiation_id}/agree",
    response_model=AgreeResponse,
)
async def agree(
    negotiation_id: str,
    body: AgreeRequest,
    use_case: AgreeDep,
) -> AgreeResponse:
    dto = use_case.execute(
        negotiation_id,
        label=body.card_label,
        secured_index=body.secured_index,
    )
    return AgreeResponse(
        status="accepted",
        agreed_terms=_format_terms(dto.agreed_terms),
    )


@router.post(
    "/negotiations/{negotiation_id}/secure",
    response_model=OffersResponse,
)
async def secure(
    negotiation_id: str,
    body: CardLabelRequest,
    use_case: SecureDep,
) -> OffersResponse:
    dto = use_case.execute(negotiation_id, body.card_label)
    return _build_offers_response(dto)


@router.post(
    "/negotiations/{negotiation_id}/improve",
    response_model=OffersResponse,
)
async def improve(
    negotiation_id: str,
    body: ImproveRequest,
    use_case: ImproveDep,
) -> OffersResponse:
    dto = use_case.execute(negotiation_id, body.improve_term, body.trade_term)
    return _build_offers_response(dto)


@router.post(
    "/negotiations/{negotiation_id}/end",
    response_model=EndResponse,
)
async def end_negotiation(
    negotiation_id: str,
    use_case: EndNegotiationDep,
) -> EndResponse:
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
    use_case.execute(negotiation_id)
    return ResetResponse(status="reset")
