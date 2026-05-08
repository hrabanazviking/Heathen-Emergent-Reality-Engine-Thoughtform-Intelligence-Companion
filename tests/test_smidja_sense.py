"""
Placeholder tests — SmidjaSense orchestrator.

Forge Wave 2 implements the bodies. Tests use mocked BrunhandHttpClient
and a mock event emitter.

Ref: src/heretic/skilningr/senses/smidja/sense.py
     docs/architecture/SENSE_CONTRACTS.md §1 (lifecycle) §3 (error format)
"""

import json

import pytest

from heretic.skilningr.config_model import SmidjaConfig
from heretic.skilningr.senses.smidja.tools import SMIDJA_TOOL_DEFINITIONS


# ---------------------------------------------------------------------------
# tool_definitions property
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense.__init__ not implemented")
def test_tool_definitions_returns_smidja_tool_definitions_when_enabled():
    """tool_definitions returns SMIDJA_TOOL_DEFINITIONS when config.enabled=True."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense.__init__ not implemented")
def test_tool_definitions_returns_empty_when_disabled():
    """tool_definitions returns [] when config.enabled=False."""


# ---------------------------------------------------------------------------
# is_available property
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_is_available_false_before_open():
    """is_available is False before open() is called."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_is_available_true_after_successful_open():
    """is_available is True after open() completes without error."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_is_available_false_after_close():
    """is_available is False after close() is called."""


# ---------------------------------------------------------------------------
# open / close fault tolerance
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_open_degrades_gracefully_on_unreachable_daemon():
    """open() catches BrunhandUnreachableError and sets is_available=False without raising."""


# ---------------------------------------------------------------------------
# dispatch_tool_call — never raises
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_dispatch_screenshot_returns_tool_result():
    """dispatch_tool_call for smidja.screenshot returns dict with tool_call_id, role, content."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_dispatch_click_returns_tool_result():
    """dispatch_tool_call for smidja.click returns tool_result with click payload."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_dispatch_screenshot_encodes_png_as_data_url():
    """smidja.screenshot result content contains a base64 data URL for the PNG."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_dispatch_never_raises_on_client_error():
    """dispatch_tool_call catches all client errors and returns error tool_result."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_dispatch_emits_started_and_completed_events():
    """dispatch_tool_call calls event_emitter with STARTED then COMPLETED events."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_dispatch_emits_failed_event_on_error():
    """dispatch_tool_call calls event_emitter with FAILED event when client raises."""


@pytest.mark.skip(reason="Forge Wave 2: SmidjaSense not implemented")
async def test_dispatch_unknown_tool_name_returns_error():
    """dispatch_tool_call with unknown smidja.* name returns INVALID_ARGUMENTS error."""
