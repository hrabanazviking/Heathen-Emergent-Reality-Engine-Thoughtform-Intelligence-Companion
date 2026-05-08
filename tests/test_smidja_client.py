"""
Placeholder tests — BrunhandHttpClient.

Forge Wave 2 implements the bodies. Each test documents the exact behaviour
Forge must produce. Assertions use mocked httpx responses (respx or pytest-httpx).

Ref: src/heretic/skilningr/senses/smidja/client.py
     src/seidr_smidja/brunhand/daemon/INTERFACE.md
"""

import pytest

from heretic.skilningr.config_model import SmidjaConfig
from heretic.skilningr.senses.smidja.client import BrunhandHttpClient
from heretic.skilningr.senses.smidja.errors import (
    BrunhandAuthError,
    BrunhandSessionLockedError,
    BrunhandTimeoutError,
    BrunhandUnreachableError,
)


def make_config(**kwargs) -> SmidjaConfig:
    """Return a SmidjaConfig with enabled=False so __post_init__ does not warn."""
    defaults = dict(
        enabled=False,
        host="127.0.0.1",
        port=8848,
        token_env="BRUNHAND_TOKEN_HERETIC",
        require_https=False,  # allow http in test contexts
        request_timeout_seconds=5,
    )
    defaults.update(kwargs)
    return SmidjaConfig(**defaults)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.__init__ not implemented")
def test_client_init_resolves_token_from_env(monkeypatch):
    """__init__ reads token from os.environ[config.token_env].
    If enabled=True and env var is set, no AuthError is raised."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.__init__ not implemented")
def test_client_init_raises_auth_error_if_enabled_and_token_missing(monkeypatch):
    """__init__ raises BrunhandAuthError when enabled=True and env var is unset."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.__init__ not implemented")
def test_client_init_token_not_in_repr():
    """The bearer token value must not appear in __repr__ or __str__ output."""


# ---------------------------------------------------------------------------
# open / health
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.open not implemented")
async def test_open_success_probes_health():
    """open() calls GET /v1/brunhand/health; on 200 with status='ok', completes without error."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.open not implemented")
async def test_open_raises_unreachable_on_connect_error():
    """open() raises BrunhandUnreachableError if httpx.ConnectError occurs."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.open not implemented")
async def test_open_raises_timeout_on_timeout():
    """open() raises BrunhandTimeoutError if httpx.TimeoutException occurs."""


# ---------------------------------------------------------------------------
# screenshot
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.screenshot not implemented")
async def test_screenshot_returns_decoded_png_bytes():
    """screenshot() decodes png_bytes_b64 from daemon response and returns raw bytes."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.screenshot not implemented")
async def test_screenshot_sends_request_envelope():
    """screenshot() POST body includes request_id, session_id, agent_id fields."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.screenshot not implemented")
async def test_screenshot_raises_auth_error_on_401():
    """screenshot() raises BrunhandAuthError when daemon returns HTTP 401."""


# ---------------------------------------------------------------------------
# click
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.click not implemented")
async def test_click_sends_correct_body():
    """click(100, 200, button='right') sends x=100, y=200, button='right' in body."""


# ---------------------------------------------------------------------------
# type_text
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.type_text not implemented")
async def test_type_text_posts_to_brunhand_type():
    """type_text() POSTs to /v1/brunhand/type (not /v1/brunhand/type_text)."""


# ---------------------------------------------------------------------------
# hotkey
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.hotkey not implemented")
async def test_hotkey_sends_keys_list():
    """hotkey(['ctrl', 's']) sends keys=['ctrl', 's'] in request body."""


# ---------------------------------------------------------------------------
# vroid_open / vroid_export — path correctness
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.vroid_open not implemented")
async def test_vroid_open_posts_to_correct_path():
    """vroid_open() POSTs to /v1/brunhand/vroid/open_project (NOT /vroid-open)."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient.vroid_export not implemented")
async def test_vroid_export_posts_to_correct_path():
    """vroid_export() POSTs to /v1/brunhand/vroid/export_vrm (NOT /vroid-export)."""


# ---------------------------------------------------------------------------
# Session lock
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient._raise_for_auth not implemented")
async def test_any_request_raises_session_locked_on_423():
    """Any request that receives HTTP 423 raises BrunhandSessionLockedError."""


# ---------------------------------------------------------------------------
# _build_envelope
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient._build_envelope not implemented")
def test_build_envelope_includes_required_fields():
    """_build_envelope returns dict with request_id, session_id, agent_id."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient._build_envelope not implemented")
def test_build_envelope_request_id_is_uuid_string():
    """_build_envelope generates a new UUID string for request_id per call."""


@pytest.mark.skip(reason="Forge Wave 2: BrunhandHttpClient._build_envelope not implemented")
def test_build_envelope_session_id_stable_across_calls():
    """_build_envelope uses the same session_id for all calls in a client lifetime."""
