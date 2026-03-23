"""FastAPI application factory — composition root.

This module is the only place that wires together all layers:
- Reads configuration from Settings (back.config)
- Creates the FastAPI app with CORS configured from Settings
- Registers the API router (back.api.routes)
- Registers centralized exception handlers (back.api.exception_handlers)
- Seeds a development negotiation on startup (if settings.seed_demo is True)

Downstream: routes depend on application use cases via DI.
            back.api.dependencies holds the singleton repo and use case factories.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from back.api.dependencies import get_repo
from back.api.exception_handlers import register_exception_handlers
from back.api.routes import router
from back.config import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)


def _seed_dev_negotiation() -> None:
    """Create a default negotiation for local development.

    Seeds negotiation ID "demo" so the React frontend can immediately
    hit GET /api/negotiations/demo/offers without manual setup.

    Import is deferred to avoid a hard dependency on domain at import time.
    """
    from back.domain.defaults import DEFAULT_OPERATOR_WEIGHTS, make_default_config
    from back.domain.negotiation import Negotiation
    from back.domain.opponent_model import OpponentModel
    from back.domain.types import NegotiationState

    logger.info("Seeding development negotiation: demo")
    repo = get_repo()
    negotiation = Negotiation(
        id="demo",
        state=NegotiationState.PENDING,
        round=0,
        max_rounds=5,
        config=make_default_config(),
        operator_weights=DEFAULT_OPERATOR_WEIGHTS,
        opponent_model=OpponentModel.uniform(),
    )
    repo.save(negotiation)
    logger.info("Successfully seeded negotiation: demo")


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: seed dev data on startup."""
    settings = get_settings()
    if settings.seed_demo:
        _seed_dev_negotiation()
    yield
    # Shutdown: nothing to clean up for in-memory store.


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application.

    Returns a fully wired app ready to be served by uvicorn.
    """
    settings = get_settings()
    logger.info(
        "Creating FastAPI app: %s (debug=%s)",
        settings.app_title,
        settings.debug,
    )

    app = FastAPI(
        title=settings.app_title,
        description="Backend for the meso-level negotiation assistant.",
        version="0.1.0",
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.debug("CORS configured for origins: %s", settings.cors_origins)

    register_exception_handlers(app)
    app.include_router(router)
    logger.info("FastAPI app fully configured and ready")

    return app


# Module-level app instance for uvicorn: `uvicorn back.server:app`
app = create_app()
