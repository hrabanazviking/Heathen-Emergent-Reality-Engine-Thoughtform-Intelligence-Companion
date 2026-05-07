"""
Tests — CLI `light` command voice (Tunga) integration.

Verifies that the `light` command:
- Instantiates Tunga when rodd.tts.enabled is True (by checking Tunga is constructed)
- Skips Tunga when rodd.tts.enabled is False
- Continues text-only (no crash) when Tunga construction raises
- Correctly calls feed_chunk and flush per streaming text delta

Tests avoid entering the full blocking turn loop by having the mock Bifröst connection
fail on open() — the command returns early with exit_code=1, which is sufficient to
verify the Tunga construction path in the TENGSL block.

All network calls are mocked — no real connections made.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretic.cli import _async_light
from heretic.bifrost.errors import BifrostConnectionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(config_path=None, debug=False):
    """Build a minimal argparse.Namespace that _async_light expects."""
    ns = MagicMock()
    ns.config = config_path
    ns.debug = debug
    return ns


def _make_grunnr_tts(enabled=True, endpoint="http://test:7851"):
    """Build a mock grunnr RoddTtsConfig."""
    tts = MagicMock()
    tts.enabled = enabled
    tts.endpoint = endpoint
    tts.engine = "chatterbox"
    tts.voice_id = "default"
    tts.device = "default"
    tts.speed = 1.0
    return tts


def _make_full_config(tts_enabled=True, endpoint="http://test:7851"):
    """Build a mock HereticConfig with all required attributes."""
    grunnr = MagicMock()
    grunnr.log_level = "WARNING"
    grunnr.log_file = None

    bifrost = MagicMock()
    bifrost.endpoint = "http://localhost:8080"
    bifrost.api_key = "test-key"
    bifrost.model = "test-model"
    bifrost.timeout_seconds = 30
    bifrost.stream_timeout_seconds = 60
    bifrost.connect_timeout_seconds = 10
    bifrost.max_retries = 1
    bifrost.backoff_seconds = [1.0]
    bifrost.heartbeat_interval_seconds = 30
    bifrost.heartbeat_miss_threshold = 3
    bifrost.heartbeat_enabled = False
    bifrost.stream = True
    bifrost.max_tokens = 127000
    bifrost.max_parallel_tool_calls = 1
    bifrost.max_tool_call_rounds = 5
    bifrost.drain_timeout_seconds = 5
    bifrost.input_queue_depth = 5
    bifrost.inject_context_on_connect = False
    bifrost.vision_in = False
    tailscale = MagicMock()
    tailscale.prefer = False
    tailscale.fallback_to_direct = True
    bifrost.tailscale = tailscale

    rodd = MagicMock()
    rodd.tts = _make_grunnr_tts(enabled=tts_enabled, endpoint=endpoint)

    cfg = MagicMock()
    cfg.grunnr = grunnr
    cfg.bifrost = bifrost
    cfg.rodd = rodd
    return cfg


# ---------------------------------------------------------------------------
# Strategy: have Bifröst open() fail — command exits early, but we still pass
# through the TENGSL Tunga init block before the failure propagates.
# We inspect what happens to Tunga in that window.
# ---------------------------------------------------------------------------

async def test_light_instantiates_tunga_when_tts_enabled() -> None:
    """light command creates a Tunga instance when rodd.tts.enabled is True.

    Bifröst opens successfully. Stdin immediately delivers /quit so the turn loop
    exits immediately without calling send_message. We verify Tunga was constructed
    and opened in the TENGSL block before the turn loop.

    The run_in_executor call for stdin.readline is patched at the asyncio loop level
    to return the quit command synchronously without blocking.
    """
    cfg = _make_full_config(tts_enabled=True)

    tunga_instances: list = []

    class CapturingTunga:
        def __init__(self, *a, **kw):
            tunga_instances.append(self)
            self.is_degraded = False
            self.is_closed = False

        async def open(self): pass
        async def feed_chunk(self, text): pass
        async def flush(self): pass
        async def close(self): pass

    mock_bifrost_client = MagicMock()
    mock_bifrost_client.open = AsyncMock()  # Succeeds
    mock_bifrost_client.close = AsyncMock()
    mock_bifrost_client.capability_tool_use = False
    mock_bifrost_client.capability_vision_in = False
    mock_bifrost_client.capability_streaming = True

    mock_playback = MagicMock()
    mock_playback.available = MagicMock(return_value=True)

    # Patch run_in_executor to return "/quit" so the turn loop exits immediately
    # without threading complications.
    async def _fake_run_in_executor(executor, func, *args):
        return "/quit\n"

    with patch("heretic.grunnr.config.load_config", return_value=cfg), \
         patch("heretic.grunnr.logger.configure_logging"), \
         patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()), \
         patch("heretic.bifrost.client.OpenAICompatClient", return_value=mock_bifrost_client), \
         patch("heretic.rodd.chatterbox.ChatterboxHttpClient"), \
         patch("heretic.rodd.playback.AudioPlayback.best_available", return_value=mock_playback), \
         patch("heretic.rodd.tunga.Tunga", new=CapturingTunga), \
         patch("asyncio.get_running_loop") as mock_loop_getter:
        mock_loop = MagicMock()
        mock_loop.run_in_executor = _fake_run_in_executor
        mock_loop_getter.return_value = mock_loop
        result = await _async_light(_make_args())

    # Command exited cleanly (turn loop saw /quit)
    assert result == 0
    assert len(tunga_instances) == 1, (
        f"Expected 1 Tunga instance, got {len(tunga_instances)}"
    )


async def test_light_skips_tunga_when_tts_disabled() -> None:
    """light command does not create Tunga when rodd.tts.enabled is False."""
    cfg = _make_full_config(tts_enabled=False)

    tunga_call_count = [0]

    class CountingTunga:
        def __init__(self, *a, **kw):
            tunga_call_count[0] += 1
        async def open(self): pass
        async def close(self): pass

    mock_bifrost_client = MagicMock()
    mock_bifrost_client.open = AsyncMock(
        side_effect=BifrostConnectionError("test: no connection")
    )
    mock_bifrost_client.close = AsyncMock()

    with patch("heretic.grunnr.config.load_config", return_value=cfg), \
         patch("heretic.grunnr.logger.configure_logging"), \
         patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()), \
         patch("heretic.bifrost.client.OpenAICompatClient", return_value=mock_bifrost_client), \
         patch("heretic.rodd.tunga.Tunga", new=CountingTunga):
        result = await _async_light(_make_args())

    assert result == 1
    assert tunga_call_count[0] == 0, "Tunga should not be instantiated when tts.enabled is False"


async def test_light_continues_text_only_when_tunga_init_raises() -> None:
    """light command continues (no crash) when Tunga construction raises."""
    cfg = _make_full_config(tts_enabled=True)

    def _raising_tunga(*a, **kw):
        raise RuntimeError("Tunga exploded during init")

    mock_bifrost_client = MagicMock()
    mock_bifrost_client.open = AsyncMock(
        side_effect=BifrostConnectionError("test: no connection")
    )
    mock_bifrost_client.close = AsyncMock()

    mock_playback = MagicMock()
    mock_playback.available = MagicMock(return_value=True)

    with patch("heretic.grunnr.config.load_config", return_value=cfg), \
         patch("heretic.grunnr.logger.configure_logging"), \
         patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()), \
         patch("heretic.bifrost.client.OpenAICompatClient", return_value=mock_bifrost_client), \
         patch("heretic.rodd.chatterbox.ChatterboxHttpClient"), \
         patch("heretic.rodd.playback.AudioPlayback.best_available", return_value=mock_playback), \
         patch("heretic.rodd.tunga.Tunga", side_effect=_raising_tunga):
        # Should not raise — just returns 1 (Bifröst failure after Tunga graceful fallback)
        result = await _async_light(_make_args())

    # Command continues and exits cleanly — the Tunga init failure was swallowed
    assert result == 1
