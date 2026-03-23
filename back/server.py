"""FastAPI application factory — composition root.

This module is the only place that wires together all layers:
- Imports infrastructure (InMemoryNegotiationRepository)
- Creates the FastAPI app with CORS configured for the React frontend
- Registers the API router
- Seeds a development negotiation on startup

Downstream: routes depend on application use cases via DI.
            dependencies.py holds the singleton repo and use case factories.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from back.dependencies import get_repo
from back.routes import router


def _seed_dev_negotiation() -> None:
    """Create a default negotiation for local development.

    Seeds negotiation ID "demo" so the React frontend can immediately
    hit GET /api/negotiations/demo/offers without manual setup.

    Import is deferred to avoid a hard dependency on domain at import time —
    domain types are populated by the parallel agent and must only be required
    at runtime (startup), not at module load.
    """
    from back.domain.negotiation import Negotiation
    from back.domain.opponent_model import OpponentModel
    from back.domain.types import (
        NegotiationState,
        TermConfig,
        Weights,
    )

    repo = get_repo()

    # Standard 4-term configuration used throughout the feature spec.
    config: dict[str, TermConfig] = {
        "price": TermConfig(opening=11.50, target=12.50, walk_away=14.50, weight=0.40),
        "payment": TermConfig(opening=90, target=75, walk_away=30, weight=0.25),
        "delivery": TermConfig(opening=7, target=10, walk_away=14, weight=0.20),
        "contract": TermConfig(opening=6, target=12, walk_away=24, weight=0.15),
    }
    operator_weights = Weights(price=0.40, payment=0.25, delivery=0.20, contract=0.15)

    negotiation = Negotiation(
        id="demo",
        state=NegotiationState.PENDING,
        round=0,
        max_rounds=5,
        config=config,
        operator_weights=operator_weights,
        opponent_model=OpponentModel.uniform(),
    )
    repo.save(negotiation)


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: seed dev data on startup."""
    _seed_dev_negotiation()
    yield
    # Shutdown: nothing to clean up for in-memory store.


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns a fully wired app ready to be served by uvicorn.
    """
    app = FastAPI(
        title="MESO Negotiation Engine",
        description="Backend for the meso-level negotiation assistant.",
        version="0.1.0",
        lifespan=_lifespan,
    )

    # Allow the React dev server (Vite default port 5173) to call the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    return app


# Module-level app instance for uvicorn: `uvicorn back.server:app`
app = create_app()
