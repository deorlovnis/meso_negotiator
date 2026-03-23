"""Domain exception hierarchy for the MESO negotiation engine.

All domain exceptions are defined here so they can be imported by any layer
without creating circular dependencies. No HTTP or framework imports.
"""


class NegotiationError(Exception):
    """Raised when a state transition or action is invalid."""
