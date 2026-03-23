"""FastAPI dependency providers.

Wires InMemoryNegotiationRepository as a process-level singleton and
provides factory functions for each use case. Route handlers depend only
on application interfaces, never on infrastructure directly.

RepoDep is typed as NegotiationRepository (the protocol), not the concrete
InMemoryNegotiationRepository. This satisfies the DIP: high-level routes
depend on the abstract interface, not the low-level implementation.
"""

from typing import Annotated

from fastapi import Depends

from back.application.agree import AgreeUseCase
from back.application.end_negotiation import EndNegotiationUseCase
from back.application.get_offers import GetOffersUseCase
from back.application.improve import ImproveUseCase
from back.application.ports import NegotiationRepository
from back.application.reset import ResetUseCase
from back.application.secure import SecureUseCase
from back.infrastructure.memory_repo import InMemoryNegotiationRepository

# Process-level singleton — one shared in-memory store for dev.
_repo = InMemoryNegotiationRepository()


def get_repo() -> NegotiationRepository:
    """Return the singleton NegotiationRepository."""
    return _repo


RepoDep = Annotated[NegotiationRepository, Depends(get_repo)]


def get_offers_use_case(repo: RepoDep) -> GetOffersUseCase:
    """Construct GetOffersUseCase with injected repository."""
    return GetOffersUseCase(repo)


def get_agree_use_case(repo: RepoDep) -> AgreeUseCase:
    """Construct AgreeUseCase with injected repository."""
    return AgreeUseCase(repo)


def get_secure_use_case(repo: RepoDep) -> SecureUseCase:
    """Construct SecureUseCase with injected repository."""
    return SecureUseCase(repo)


def get_improve_use_case(repo: RepoDep) -> ImproveUseCase:
    """Construct ImproveUseCase with injected repository."""
    return ImproveUseCase(repo)


def get_end_negotiation_use_case(repo: RepoDep) -> EndNegotiationUseCase:
    """Construct EndNegotiationUseCase with injected repository."""
    return EndNegotiationUseCase(repo)


def get_reset_use_case(repo: RepoDep) -> ResetUseCase:
    """Construct ResetUseCase with injected repository."""
    return ResetUseCase(repo)


GetOffersDep = Annotated[GetOffersUseCase, Depends(get_offers_use_case)]
AgreeDep = Annotated[AgreeUseCase, Depends(get_agree_use_case)]
SecureDep = Annotated[SecureUseCase, Depends(get_secure_use_case)]
ImproveDep = Annotated[ImproveUseCase, Depends(get_improve_use_case)]
EndNegotiationDep = Annotated[
    EndNegotiationUseCase, Depends(get_end_negotiation_use_case)
]
ResetDep = Annotated[ResetUseCase, Depends(get_reset_use_case)]
