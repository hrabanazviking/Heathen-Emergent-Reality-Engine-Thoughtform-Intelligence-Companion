"""
Placeholder tests — ToolDispatcher routing.

Forge Wave 2 implements the bodies. Each test documents the invariant Forge must uphold.

Ref: src/heretic/skilningr/dispatcher.py
     docs/architecture/SENSE_CONTRACTS.md §3 (error format)
"""

import json

import pytest

from heretic.skilningr.dispatcher import ToolDispatcher, _error_result


# ---------------------------------------------------------------------------
# _error_result helper (no NotImplementedError — pure function)
# ---------------------------------------------------------------------------

def test_error_result_structure():
    """_error_result returns a dict with tool_call_id, role='tool', content (JSON)."""
    result = _error_result("call-1", "smidja.screenshot", "SENSE_UNAVAILABLE", "down")
    assert result["tool_call_id"] == "call-1"
    assert result["role"] == "tool"
    payload = json.loads(result["content"])
    assert payload["error"] is True
    assert payload["code"] == "SENSE_UNAVAILABLE"
    assert payload["sense"] == "smidja"
    assert payload["tool"] == "smidja.screenshot"


def test_error_result_derives_sense_from_tool_name():
    """_error_result derives sense from tool_name prefix when sense='' ."""
    result = _error_result("x", "filesystem.read_file", "NOT_FOUND", "missing")
    payload = json.loads(result["content"])
    assert payload["sense"] == "filesystem"


def test_error_result_explicit_sense_overrides_prefix():
    """Explicit sense argument takes precedence over tool_name prefix derivation."""
    result = _error_result("x", "smidja.click", "PERMISSION_DENIED", "no", sense="custom")
    payload = json.loads(result["content"])
    assert payload["sense"] == "custom"


def test_error_result_detail_included_when_given():
    """Optional detail field appears in content JSON when non-empty."""
    result = _error_result("x", "smidja.hotkey", "SENSE_TIMEOUT", "timed out", detail="30s")
    payload = json.loads(result["content"])
    assert payload["detail"] == "30s"


def test_error_result_detail_absent_when_empty():
    """detail field must be absent from content JSON when not provided."""
    result = _error_result("x", "smidja.hotkey", "SENSE_TIMEOUT", "timed out")
    payload = json.loads(result["content"])
    assert "detail" not in payload


# ---------------------------------------------------------------------------
# ToolDispatcher — NotImplementedError skeleton tests
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: ToolDispatcher.register_sense not implemented")
def test_register_sense_stores_sense():
    """register_sense("smidja", mock_sense) → mock_sense retrievable; no exception."""


@pytest.mark.skip(reason="Forge Wave 2: ToolDispatcher.dispatch not implemented")
async def test_dispatch_routes_to_registered_sense():
    """dispatch with a registered prefix calls sense.dispatch_tool_call."""


@pytest.mark.skip(reason="Forge Wave 2: ToolDispatcher.dispatch not implemented")
async def test_dispatch_unknown_prefix_returns_error_json():
    """dispatch with unknown prefix returns tool_result with TOOL_NOT_FOUND error."""


@pytest.mark.skip(reason="Forge Wave 2: ToolDispatcher.dispatch not implemented")
async def test_dispatch_unavailable_sense_returns_error_json():
    """dispatch when sense.is_available=False returns SENSE_UNAVAILABLE tool_result."""


@pytest.mark.skip(reason="Forge Wave 2: ToolDispatcher.dispatch not implemented")
async def test_dispatch_never_raises():
    """dispatch catches all exceptions and returns tool_result — never raises."""


@pytest.mark.skip(reason="Forge Wave 2: ToolDispatcher.all_tool_definitions not implemented")
def test_all_tool_definitions_aggregates_senses():
    """all_tool_definitions returns flat list of tool dicts from all registered senses."""


@pytest.mark.skip(reason="Forge Wave 2: ToolDispatcher.register_sense not implemented")
def test_register_sense_rejects_dotted_prefix():
    """register_sense raises ValueError if prefix contains a dot."""


@pytest.mark.skip(reason="Forge Wave 2: ToolDispatcher.register_sense not implemented")
def test_register_sense_rejects_empty_prefix():
    """register_sense raises ValueError if prefix is empty string."""
