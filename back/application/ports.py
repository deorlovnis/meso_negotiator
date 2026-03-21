"""Abstract interfaces (ports) for the application layer.

These Protocol classes define the contracts that infrastructure must implement.
They live in the application layer, not infrastructure — this is the Dependency
Inversion Principle: high-level policy (use cases) defines the interfaces,
low-level detail (repositories) implements them.

No framework imports. No implementation details.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime

    from back.domain.negotiation import Negotiation


class NegotiationRepository(Protocol):
    """Port for loading and persisting Negotiation aggregates."""

    def get(self, negotiation_id: str) -> Negotiation:
        """Load a negotiation by ID.

        Raises:
            KeyError: If no negotiation with the given ID exists.
        """
        ...

    def save(self, negotiation: Negotiation) -> None:
        """Persist the current state of a negotiation."""
        ...


class Clock(Protocol):
    """Port for time access, enabling deterministic testing."""

    def now(self) -> datetime:
        """Return the current UTC datetime."""
        ...
