"""Pydantic request and response models — v2 API contract."""

from typing import Self

from pydantic import BaseModel, model_validator

from back.domain.types import CardLabel


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


class SecuredOfferResponse(BaseModel):
    rank: int
    label: str
    terms: TermsResponse
    round_secured: int


class CardLabelRequest(BaseModel):
    card_label: CardLabel


class ImproveRequest(BaseModel):
    improve_term: str
    trade_term: str | None = None


class AgreeRequest(BaseModel):
    card_label: CardLabel | None = None
    secured_index: int | None = None

    @model_validator(mode="after")
    def exactly_one(self) -> Self:
        if (self.card_label is None) == (self.secured_index is None):
            raise ValueError("Provide exactly one of card_label or secured_index")
        return self


class CardResponse(BaseModel):
    label: str
    recommended: bool
    terms: TermsResponse
    signals: SignalsResponse


class OffersResponse(BaseModel):
    banner: str
    is_final_round: bool
    is_first_visit: bool
    cards: list[CardResponse]
    secured_offers: list[SecuredOfferResponse]
    can_secure: bool
    actions_available: list[str]


class AgreeResponse(BaseModel):
    status: str
    agreed_terms: TermsResponse


class EndResponse(BaseModel):
    status: str


class ResetResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    error: str
