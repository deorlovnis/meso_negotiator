"""In-memory implementation of NegotiationRepository."""

from back.domain.negotiation import Negotiation


class InMemoryNegotiationRepository:
    """Dict-backed repository for development and testing.

    Implements the NegotiationRepository protocol defined in
    back.application.ports. No database setup required.
    """

    def __init__(self) -> None:
        self._store: dict[str, Negotiation] = {}

    def get(self, negotiation_id: str) -> Negotiation:
        """Return negotiation by ID.

        Raises:
            KeyError: if no negotiation with the given ID exists.
        """
        return self._store[negotiation_id]

    def save(self, negotiation: Negotiation) -> None:
        """Persist (overwrite) a negotiation by its ID."""
        self._store[negotiation.id] = negotiation
