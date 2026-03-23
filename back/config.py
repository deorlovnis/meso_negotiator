"""Application configuration via pydantic-settings.

Single source of truth for all configurable values. Environment variables
(or a .env file) override defaults. No magic strings or hardcoded constants
anywhere else.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configurable values for the MESO negotiation backend.

    Attributes:
        cors_origins:      Allowed origins for CORS (pipe-separated in env).
        debug:             Enable debug mode / verbose error responses.
        app_title:         FastAPI application title shown in /docs.
        seed_demo:         Whether to seed a demo negotiation on startup.
        default_beta:      Boulware concession curve shape parameter.
        opening_utility:   Starting utility on the concession curve (round 1).
        walkaway_utility:  Minimum acceptable utility (floor for offer generation).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    cors_origins: list[str] = ["http://localhost:5173"]
    debug: bool = False
    app_title: str = "MESO Negotiation Engine"
    seed_demo: bool = True

    # Concession curve parameters (duplicated in get_offers.py, improve.py,
    # and conftest.py — those will be updated in Step 3)
    default_beta: float = 2.0
    opening_utility: float = 1.0
    walkaway_utility: float = 0.35


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Reads from environment variables / .env file on first call.
    Use dependency injection in tests: override with a Settings() instance.
    """
    return Settings()
