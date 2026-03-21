"""Section 17 — UI presentation: page structure and action hierarchy.

All scenarios in this section are frontend concerns requiring browser tests.
They are marked skip so they appear in the test collection but don't run.
"""

from __future__ import annotations

import pytest
from pytest_bdd import scenario

FEATURE = "../features/core-loop.feature"


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Page title reads \"Review your negotiated offers\"")
def test_page_title() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(FEATURE, "Improve terms is styled as a text link, not a button")
def test_improve_styled_as_link() -> None:
    pass


@pytest.mark.skip(reason="Frontend concern — requires browser test")
@scenario(
    FEATURE,
    "Maria has not secured any offer and clicks Improve on the penultimate round",
)
def test_nudge_on_penultimate_round() -> None:
    pass
