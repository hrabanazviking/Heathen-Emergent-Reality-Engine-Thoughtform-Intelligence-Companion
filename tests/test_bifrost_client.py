"""
Tests for bifrost.client — BifrostClient ABC and OpenAICompatClient skeleton.

Placeholder suite. Forge will implement real tests here covering:
    - OpenAICompatClient.open() connects to a mock SSE endpoint and populates
      capability flags based on the probe response
    - OpenAICompatClient.open() raises BifrostAuthError on HTTP 401
    - OpenAICompatClient.open() raises BifrostConnectionError when endpoint is down
    - OpenAICompatClient.open() raises BifrostProbeError on probe timeout
    - OpenAICompatClient.send_message() yields text deltas from a mock SSE stream
    - OpenAICompatClient.send_message() yields tool_call events as JSON strings
    - OpenAICompatClient.send_message() raises BifrostTimeoutError on timeout
    - OpenAICompatClient.send_message() raises BifrostProtocolError on malformed JSON
    - OpenAICompatClient.close() is safe to call before open() (no-op, no raise)
    - Capability flags default to False before open() is called
    - BifrostConfig.api_key expansion: raw ${VAR} string must not reach HTTP headers

Two structural tests are active now (skeleton-level, no network).
"""

from __future__ import annotations

import pytest

from heretic.bifrost.client import BifrostClient, OpenAICompatClient
from heretic.bifrost.config_model import BifrostConfig
from heretic.bifrost.errors import (
    BifrostError,
    BifrostConnectionError,
    BifrostAuthError,
    BifrostTimeoutError,
)


def test_bifrost_client_is_abstract() -> None:
    """BifrostClient cannot be instantiated directly — it is an ABC."""
    import inspect
    assert inspect.isabstract(BifrostClient)


def test_openai_compat_client_default_capabilities() -> None:
    """OpenAICompatClient starts with all capability flags False before open()."""
    client = OpenAICompatClient(BifrostConfig())
    assert client.capability_tool_use is False
    assert client.capability_vision_in is False
    assert client.capability_streaming is False


def test_error_hierarchy() -> None:
    """All Bifröst error types are subclasses of BifrostError."""
    for cls in (BifrostConnectionError, BifrostAuthError, BifrostTimeoutError):
        assert issubclass(cls, BifrostError)


@pytest.mark.skip(reason="Forge will implement: open() not yet built")
@pytest.mark.asyncio
async def test_open_success_sets_capabilities() -> None:
    """open() against a mock probe endpoint populates capability flags."""
    pass


@pytest.mark.skip(reason="Forge will implement: open() not yet built")
@pytest.mark.asyncio
async def test_open_raises_auth_error_on_401() -> None:
    """open() raises BifrostAuthError when the mock returns HTTP 401."""
    pass


@pytest.mark.skip(reason="Forge will implement: send_message() not yet built")
@pytest.mark.asyncio
async def test_send_message_yields_text_deltas() -> None:
    """send_message() yields text delta strings from a mock SSE stream."""
    pass


@pytest.mark.skip(reason="Forge will implement: send_message() not yet built")
@pytest.mark.asyncio
async def test_send_message_yields_tool_call_event() -> None:
    """send_message() yields a JSON tool_call record when agent requests a tool."""
    pass
