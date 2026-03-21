"""Section 11 — UI states: loading, error, first-time, and resume.

All scenarios in this section are frontend concerns requiring browser tests.
They are marked skip so they appear in the test collection but don't run.
"""

from __future__ import annotations

import pytest
from pytest_bdd import scenario

FEATURE = "../features/core-loop.feature"


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Maria sees a loading state while the engine generates new offers")
def test_loading_state_generating_offers() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Maria sees a loading state while the deal is being finalized")
def test_loading_state_finalizing_deal() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Maria clicks Agree and uses the undo window")
def test_agree_undo_window() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Engine fails to generate new offers after Improve")
def test_engine_error_after_improve() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Network drops during Agree")
def test_network_drops_during_agree() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Maria sees the MESO card format for the first time")
def test_first_time_meso_format() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Offers have not yet loaded when Maria opens the negotiation link")
def test_offers_loading_on_open() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Maria closes the browser mid-negotiation and returns")
def test_resume_mid_negotiation() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Maria returns to a negotiation that has already been completed")
def test_return_to_completed_negotiation() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Maria double-clicks Improve terms rapidly")
def test_double_click_improve() -> None:
    pass
