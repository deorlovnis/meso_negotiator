"""Centralized exception handlers for the MESO negotiation API.

Replaces 5 copies of identical try/except in routes.py with a single
registration point. Routes are now free of error-mapping boilerplate.

Handlers:
- negotiation_error_handler: NegotiationError -> 409 Conflict
- not_found_handler:         KeyError -> 404 Not Found

No global ValueError handler — Pydantic already handles validation errors
with 422 Unprocessable Entity before they reach route handlers.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request  # noqa: TC002
from fastapi.responses import JSONResponse

from back.api.schemas import ErrorResponse
from back.domain.exceptions import NegotiationError

logger = logging.getLogger(__name__)


async def negotiation_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Map NegotiationError to 409 Conflict.

    NegotiationError means the requested action is not valid for the current
    negotiation state (e.g., agreeing on a terminal negotiation).

    Response body mirrors FastAPI's HTTPException format:
        {"detail": {"error": "..."}}
    """
    assert isinstance(exc, NegotiationError)
    logger.warning("NegotiationError: %s", str(exc))
    body = ErrorResponse(error=str(exc))
    return JSONResponse(
        status_code=409,
        content={"detail": body.model_dump()},
    )


async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Map KeyError to 404 Not Found.

    Repository.get() raises KeyError when no negotiation exists for the
    given ID. We surface this as a 404.

    Response body mirrors FastAPI's HTTPException format:
        {"detail": {"error": "..."}}
    """
    assert isinstance(exc, KeyError)
    neg_id = exc.args[0] if exc.args else "unknown"
    logger.warning("Negotiation not found: %s", neg_id)
    body = ErrorResponse(error=f"Negotiation '{neg_id}' not found.")
    return JSONResponse(
        status_code=404,
        content={"detail": body.model_dump()},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers on the FastAPI app."""
    app.add_exception_handler(NegotiationError, negotiation_error_handler)
    app.add_exception_handler(KeyError, not_found_handler)
