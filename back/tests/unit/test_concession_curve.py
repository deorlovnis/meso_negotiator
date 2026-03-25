"""Unit tests for Boulware concession curve.

Error categories targeted:
- Computation errors: exponentiation, monotonicity, off-by-one on round index
- Boundary errors: round 1 near opening, final round near walk-away, round 0, round > max

Source spec: core-loop.feature section 15.
Architecture ref: ARCHITECTURE.md domain/concession.py contract.

Formula under test (Faratin 1998):
    target(r) = walkaway + (opening - walkaway) * (1 - (r-1)/(R-1))^(1/beta)

Where:
    r = current round (1-indexed)
    R = max rounds
    beta > 1 gives Boulware (hold firm early, concede late)

Round 1 yields opening utility (no concession); round R yields walk-away.
"""

from __future__ import annotations

from back.domain.concession import target_utility

# ---------------------------------------------------------------------------
# Standard test parameters from the Background spec
# ---------------------------------------------------------------------------
OPENING_UTILITY = 1.0
WALKAWAY_UTILITY = 0.0
MAX_ROUNDS = 5
BOULWARE_BETA = 3.0  # Recommended range: 2.5-4.0 per ARCHITECTURE.md


class TestConcessionCurveBoundaries:
    """Falsifiable claims from section 15:
    - Round 1 target is near opening utility
    - Final round target is near walk-away utility
    """

    def test_round_one_equals_opening_utility(self):
        """section 15: 'target utility is close to the opening utility value'

        At round 1 of 5: progress = (1-1)/(5-1) = 0, so target = opening.
        Round 1 means no concession yet.
        """
        result = target_utility(
            round=1,
            max_rounds=MAX_ROUNDS,
            opening_utility=OPENING_UTILITY,
            walkaway_utility=WALKAWAY_UTILITY,
            beta=BOULWARE_BETA,
        )
        assert abs(result - OPENING_UTILITY) < 1e-9, (
            f"Round 1 should equal opening utility {OPENING_UTILITY}, got {result}"
        )

    def test_final_round_near_walkaway_utility(self):
        """section 15: 'target utility is close to the walk-away utility value'

        At round 5 of 5: target = 0.0 + (1.0 - 0.0) * (1 - 5/5)^3
                                     = (0.0)^3 = 0.0
        Final round should equal walk-away exactly.
        """
        result = target_utility(
            round=MAX_ROUNDS,
            max_rounds=MAX_ROUNDS,
            opening_utility=OPENING_UTILITY,
            walkaway_utility=WALKAWAY_UTILITY,
            beta=BOULWARE_BETA,
        )
        assert result == WALKAWAY_UTILITY, (
            f"Final round should equal walk-away {WALKAWAY_UTILITY}, got {result}"
        )

    def test_round_zero_above_opening_utility(self):
        """Adversarial: round 0 (before negotiation starts).

        At round 0: progress = (0-1)/(5-1) = -0.25, so (1 - (-0.25))^3 = 1.25^3 > 1.
        Round 0 is outside the intended range; result exceeds opening utility.
        """
        result = target_utility(
            round=0,
            max_rounds=MAX_ROUNDS,
            opening_utility=OPENING_UTILITY,
            walkaway_utility=WALKAWAY_UTILITY,
            beta=BOULWARE_BETA,
        )
        assert result >= OPENING_UTILITY, (
            f"Round 0 should be at or above opening utility {OPENING_UTILITY}, got {result}"
        )


class TestConcessionCurveMonotonicity:
    """Falsifiable claim: target utility decreases monotonically with round number.

    section 6: 'the concession rate follows the Boulware curve with diminishing concessions'
    """

    def test_monotonic_decrease_across_all_rounds(self):
        """Target utility at round r should be >= target at round r+1."""
        previous = OPENING_UTILITY + 1  # Start above any possible utility
        for r in range(1, MAX_ROUNDS + 1):
            current = target_utility(
                round=r,
                max_rounds=MAX_ROUNDS,
                opening_utility=OPENING_UTILITY,
                walkaway_utility=WALKAWAY_UTILITY,
                beta=BOULWARE_BETA,
            )
            assert current < previous, (
                f"Not monotonically decreasing: round {r} ({current}) >= "
                f"round {r - 1} ({previous})"
            )
            previous = current

    def test_boulware_concedes_less_early_more_late(self):
        """Verify the Boulware curve shape with beta > 1.

        With the formula target(r) = walkaway + (opening - walkaway) * (1 - p)^(1/beta),
        beta > 1 makes (1 - p)^(1/beta) concave: the utility holds firm in
        early rounds and drops steeply near the deadline. This means the *absolute
        concession* (utility drop per round) is smaller early and larger late.

        Boulware strategy: hold firm early, concede near deadline.
        """
        targets = [
            target_utility(
                round=r,
                max_rounds=MAX_ROUNDS,
                opening_utility=OPENING_UTILITY,
                walkaway_utility=WALKAWAY_UTILITY,
                beta=BOULWARE_BETA,
            )
            for r in range(1, MAX_ROUNDS + 1)
        ]
        # Drop = targets[r] - targets[r+1] (positive number = concession)
        drop_early = targets[0] - targets[1]  # round 1 -> round 2
        drop_late = targets[3] - targets[4]  # round 4 -> round 5

        assert drop_early < drop_late, (
            f"Boulware (beta>1) holds firm early, concedes late: "
            f"early drop {drop_early:.4f} vs late drop {drop_late:.4f}"
        )


class TestConcessionCurveBetaVariants:
    """Test different beta values to verify the Boulware shape parameter.

    Error category: Computation errors (exponentiation behavior).
    """

    def test_beta_one_gives_linear_concession(self):
        """Beta = 1 should produce a linear curve: target = opening * (1 - (r-1)/(R-1))."""
        for r in range(1, MAX_ROUNDS + 1):
            result = target_utility(
                round=r,
                max_rounds=MAX_ROUNDS,
                opening_utility=OPENING_UTILITY,
                walkaway_utility=WALKAWAY_UTILITY,
                beta=1.0,
            )
            progress = (r - 1) / (MAX_ROUNDS - 1)
            expected = WALKAWAY_UTILITY + (OPENING_UTILITY - WALKAWAY_UTILITY) * (
                1 - progress
            )
            assert abs(result - expected) < 1e-9, (
                f"Beta=1 at round {r}: expected {expected}, got {result}"
            )

    def test_high_beta_holds_firm_longer(self):
        """Beta = 10 (extreme Boulware): higher beta holds firm longer.

        With 1/beta exponent, higher beta → smaller exponent → curve stays
        closer to opening utility longer. Compare at round 2.
        """
        result_high_beta = target_utility(
            round=2,
            max_rounds=MAX_ROUNDS,
            opening_utility=OPENING_UTILITY,
            walkaway_utility=WALKAWAY_UTILITY,
            beta=10.0,
        )
        result_low_beta = target_utility(
            round=2,
            max_rounds=MAX_ROUNDS,
            opening_utility=OPENING_UTILITY,
            walkaway_utility=WALKAWAY_UTILITY,
            beta=1.0,
        )
        # Higher beta should give higher utility at round 2 (holds firm)
        assert result_high_beta > result_low_beta, (
            f"High beta ({result_high_beta}) should be higher than low beta "
            f"({result_low_beta}) at round 2 (holds firm longer)"
        )

    def test_beta_less_than_one_gives_conceder_curve(self):
        """Beta < 1 should produce Conceder behavior (concede early, hold late).

        With 1/beta exponent, beta=0.5 → exponent=2 → convex curve that
        drops faster early. At round 2 with beta=0.5: (0.75)^2 = 0.5625,
        which is lower than linear (0.75).
        """
        result = target_utility(
            round=2,
            max_rounds=MAX_ROUNDS,
            opening_utility=OPENING_UTILITY,
            walkaway_utility=WALKAWAY_UTILITY,
            beta=0.5,
        )
        linear_result = target_utility(
            round=2,
            max_rounds=MAX_ROUNDS,
            opening_utility=OPENING_UTILITY,
            walkaway_utility=WALKAWAY_UTILITY,
            beta=1.0,
        )
        assert result < linear_result, (
            f"Conceder (beta<1) at round 2 should yield lower utility than "
            f"linear: {result} vs {linear_result}"
        )


class TestConcessionCurveWithNonZeroWalkaway:
    """Test with walkaway_utility != 0 to verify the offset term works."""

    def test_nonzero_walkaway_at_final_round(self):
        """Final round should equal walk-away even when walk-away is not zero."""
        result = target_utility(
            round=5,
            max_rounds=5,
            opening_utility=0.95,
            walkaway_utility=0.30,
            beta=BOULWARE_BETA,
        )
        assert abs(result - 0.30) < 1e-9, (
            f"Final round should reach walk-away 0.30, got {result}"
        )

    def test_nonzero_walkaway_at_round_one(self):
        """Round 1 should equal opening utility regardless of walk-away."""
        result = target_utility(
            round=1,
            max_rounds=5,
            opening_utility=0.95,
            walkaway_utility=0.30,
            beta=BOULWARE_BETA,
        )
        assert abs(result - 0.95) < 1e-9, (
            f"Round 1 should equal opening 0.95, got {result}"
        )

    def test_nonzero_walkaway_monotonic(self):
        """Monotonic decrease should hold regardless of walk-away offset."""
        previous = 1.0
        for r in range(1, 6):
            current = target_utility(
                round=r,
                max_rounds=5,
                opening_utility=0.95,
                walkaway_utility=0.30,
                beta=BOULWARE_BETA,
            )
            assert current < previous, (
                f"Not monotonic at round {r}: {current} >= {previous}"
            )
            assert current >= 0.30, f"Should not go below walk-away 0.30: got {current}"
            previous = current
