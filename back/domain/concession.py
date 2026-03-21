"""Boulware concession curve for target utility per round.

Pure function with no side effects. Implements the Boulware strategy:
hold firm early, concede more near deadline.

Formula (Faratin 1998 time-dependent tactic):
    target(r) = walk_away + (opening - walk_away) * (1 - (r-1) / (R-1)) ^ (1/beta)

Parameters:
- beta > 1 produces Boulware behavior (recommended 2.0-4.0)
- beta = 1 produces linear concession
- beta < 1 produces conceder behavior (not recommended)
"""

from __future__ import annotations


def target_utility(
    round: int,
    max_rounds: int,
    opening_utility: float,
    walkaway_utility: float,
    beta: float,
) -> float:
    """Compute target operator utility for a given round.

    Args:
        round: Current round number (1-indexed). Round 1 is the first round.
        max_rounds: Total number of rounds allowed.
        opening_utility: Utility target at round 1 (near the operator ideal).
        walkaway_utility: Utility floor (minimum acceptable; typically 0.0).
        beta: Curve exponent. Use > 1 for Boulware (hold firm, concede late).

    Returns:
        Target utility in [walkaway_utility, opening_utility].

    Notes:
        At round 1:   target equals opening_utility (no concession)
        At round R:   target equals walkaway_utility (maximum concession)
    """
    progress = (round - 1) / (max_rounds - 1) if max_rounds > 1 else 1.0
    return walkaway_utility + (opening_utility - walkaway_utility) * (
        (1.0 - progress) ** (1.0 / beta)
    )
