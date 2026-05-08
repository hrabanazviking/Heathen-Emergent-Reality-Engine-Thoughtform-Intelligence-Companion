"""
Tests — CLI `light` command Hlust (STT) integration.

Verifies that the `light` command:
- Instantiates Hlust when rodd.stt.enabled is True
- Does NOT instantiate Hlust when rodd.stt.enabled is False (regression for v0.2 stdin path)
- Falls back to stdin when Hlust construction raises
- Falls back to stdin when Hlust.is_available is False
- Uses Hlust.capture_one_utterance() for voice input when available + isatty
- Falls back to stdin when Hlust.capture_one_utterance() raises
- Closes Hlust during Slokna teardown

All network calls are mocked. Bifröst opens successfully; the turn loop receives
a single turn (via mock input) and exits when it sees /quit.
"""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretic.cli import _async_light
from heretic.bifrost.errors import BifrostConnectionError
from heretic.rodd.errors import HlustConfigError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(config_path=None, debug=False):
    ns = MagicMock()
    ns.config = config_path
    ns.debug = debug
    return ns


def _make_grunnr_tts(enabled=False):
    """Minimal TTS config (disabled by default for STT-focused tests)."""
    tts = MagicMock()
    tts.enabled = enabled
    tts.endpoint = "http://test:7851"
    tts.engine = "chatterbox"
    tts.voice_id = "default"
    tts.device = "default"
    tts.speed = 1.0
    return tts


def _make_grunnr_stt(
    enabled: bool = True,
    model_path: str = "models/test.bin",
    device: str = "default",
    vad_threshold: float = 0.6,
    language: str = "en",
    load_strategy: str = "lazy",
    engine: str = "whisper_cpp",
):
    stt = MagicMock()
    stt.enabled = enabled
    stt.engine = engine
    stt.model_path = model_path
    stt.device = device
    stt.vad_threshold = vad_threshold
    stt.language = language
    stt.load_strategy = load_strategy
    return stt


def _make_full_config(stt_enabled: bool = True, tts_enabled: bool = False):
    """Build a minimal mock HereticConfig for STT testing."""
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
    rodd.tts = _make_grunnr_tts(enabled=tts_enabled)
    rodd.stt = _make_grunnr_stt(enabled=stt_enabled)

    cfg = MagicMock()
    cfg.grunnr = grunnr
    cfg.bifrost = bifrost
    cfg.rodd = rodd
    return cfg


def _make_mock_client(chunks: list[str] | None = None):
    """Build a mock OpenAICompatClient that emits /quit-triggering input on first turn."""
    client = AsyncMock()
    client.open = AsyncMock()
    client.close = AsyncMock()
    client.capability_tool_use = False
    client.capability_vision_in = False
    client.capability_streaming = True

    async def _fake_send(messages, **kwargs):
        for chunk in (chunks or ["ok"]):
            yield chunk

    client.send_message = _fake_send
    return client


# ---------------------------------------------------------------------------
# Test: Hlust instantiated when stt.enabled
# ---------------------------------------------------------------------------

async def test_light_instantiates_hlust_when_stt_enabled() -> None:
    """light command creates a Hlust instance when rodd.stt.enabled is True."""
    cfg = _make_full_config(stt_enabled=True)

    hlust_instances: list = []

    class CapturingHlust:
        def __init__(self, *a, **kw):
            hlust_instances.append(self)
            self.is_available = True
            self.is_closed = False

        async def open(self):
            pass

        async def capture_one_utterance(self):
            return "/quit"

        async def close(self):
            self.is_closed = True

    client = _make_mock_client()

    with (
        patch("heretic.grunnr.config.load_config", return_value=cfg),
        patch("heretic.grunnr.logger.configure_logging"),
        patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()),
        patch("heretic.bifrost.client.OpenAICompatClient", return_value=client),
        patch("heretic.rodd.hlust.Hlust", CapturingHlust),
        patch("heretic.rodd.microphone.MicrophoneCapture.best_available", return_value=MagicMock()),
        patch("heretic.rodd.vad.VadDetector.best_available", return_value=MagicMock()),
        patch("heretic.rodd.whisper_engine.WhisperEngine.best_available", return_value=MagicMock()),
        patch("sys.stdin.isatty", return_value=True),
    ):
        await _async_light(_make_args())

    assert len(hlust_instances) == 1


# ---------------------------------------------------------------------------
# Test: Hlust not instantiated when stt.enabled is False
# ---------------------------------------------------------------------------

async def test_light_skips_hlust_when_stt_disabled() -> None:
    """light command does not create Hlust when rodd.stt.enabled is False."""
    cfg = _make_full_config(stt_enabled=False)

    hlust_instances: list = []

    class CapturingHlust:
        def __init__(self, *a, **kw):
            hlust_instances.append(self)
            self.is_available = True
            self.is_closed = False
        async def open(self): pass
        async def capture_one_utterance(self): return "/quit"
        async def close(self): pass

    # Patch readline to return /quit immediately
    stdin_readline_calls = ["/quit\n"]

    def _fake_readline():
        return stdin_readline_calls.pop(0) if stdin_readline_calls else ""

    client = _make_mock_client()

    with (
        patch("heretic.grunnr.config.load_config", return_value=cfg),
        patch("heretic.grunnr.logger.configure_logging"),
        patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()),
        patch("heretic.bifrost.client.OpenAICompatClient", return_value=client),
        patch("heretic.rodd.hlust.Hlust", CapturingHlust),
        patch("sys.stdin.isatty", return_value=False),
        patch("sys.stdin.readline", side_effect=_fake_readline),
    ):
        await _async_light(_make_args())

    # Hlust should NOT have been instantiated because stt.enabled is False
    assert len(hlust_instances) == 0


# ---------------------------------------------------------------------------
# Test: Hlust init failure falls back to stdin
# ---------------------------------------------------------------------------

async def test_light_falls_back_to_stdin_when_hlust_init_fails() -> None:
    """light command falls back to stdin when Hlust construction raises."""
    cfg = _make_full_config(stt_enabled=True)

    stdin_readline_calls = ["/quit\n"]
    def _fake_readline():
        return stdin_readline_calls.pop(0) if stdin_readline_calls else ""

    def _raising_hlust(*a, **kw):
        raise RuntimeError("Hlust init exploded")

    client = _make_mock_client()

    with (
        patch("heretic.grunnr.config.load_config", return_value=cfg),
        patch("heretic.grunnr.logger.configure_logging"),
        patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()),
        patch("heretic.bifrost.client.OpenAICompatClient", return_value=client),
        patch("heretic.rodd.hlust.Hlust", side_effect=_raising_hlust),
        patch("heretic.rodd.microphone.MicrophoneCapture.best_available", return_value=MagicMock()),
        patch("heretic.rodd.vad.VadDetector.best_available", return_value=MagicMock()),
        patch("heretic.rodd.whisper_engine.WhisperEngine.best_available", return_value=MagicMock()),
        patch("sys.stdin.isatty", return_value=False),
        patch("sys.stdin.readline", side_effect=_fake_readline),
    ):
        result = await _async_light(_make_args())

    # Should complete normally (fallback to stdin, not crash)
    assert result == 0


# ---------------------------------------------------------------------------
# Test: Hlust.is_available=False falls back to stdin
# ---------------------------------------------------------------------------

async def test_light_falls_back_to_stdin_when_hlust_unavailable() -> None:
    """light command uses stdin when Hlust.is_available is False."""
    cfg = _make_full_config(stt_enabled=True)

    stdin_readline_calls = ["/quit\n"]
    def _fake_readline():
        return stdin_readline_calls.pop(0) if stdin_readline_calls else ""

    class UnavailableHlust:
        def __init__(self, *a, **kw):
            self.is_available = False
            self.is_closed = False
        async def open(self): pass
        async def capture_one_utterance(self): raise HlustConfigError("unavailable")
        async def close(self): pass

    client = _make_mock_client()

    with (
        patch("heretic.grunnr.config.load_config", return_value=cfg),
        patch("heretic.grunnr.logger.configure_logging"),
        patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()),
        patch("heretic.bifrost.client.OpenAICompatClient", return_value=client),
        patch("heretic.rodd.hlust.Hlust", UnavailableHlust),
        patch("heretic.rodd.microphone.MicrophoneCapture.best_available", return_value=MagicMock()),
        patch("heretic.rodd.vad.VadDetector.best_available", return_value=MagicMock()),
        patch("heretic.rodd.whisper_engine.WhisperEngine.best_available", return_value=MagicMock()),
        patch("sys.stdin.isatty", return_value=False),
        patch("sys.stdin.readline", side_effect=_fake_readline),
    ):
        result = await _async_light(_make_args())

    assert result == 0


# ---------------------------------------------------------------------------
# Test: Capture failure falls back to stdin for that turn
# ---------------------------------------------------------------------------

async def test_light_falls_back_stdin_on_capture_exception() -> None:
    """light falls back to stdin readline when capture_one_utterance raises."""
    cfg = _make_full_config(stt_enabled=True)

    capture_call_count = [0]
    stdin_calls = ["/quit\n"]

    def _fake_readline():
        return stdin_calls.pop(0) if stdin_calls else ""

    class ExplodingHlust:
        def __init__(self, *a, **kw):
            self.is_available = True
            self.is_closed = False

        async def open(self): pass

        async def capture_one_utterance(self):
            capture_call_count[0] += 1
            raise Exception("mic exploded")

        async def close(self): pass

    client = _make_mock_client()

    with (
        patch("heretic.grunnr.config.load_config", return_value=cfg),
        patch("heretic.grunnr.logger.configure_logging"),
        patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()),
        patch("heretic.bifrost.client.OpenAICompatClient", return_value=client),
        patch("heretic.rodd.hlust.Hlust", ExplodingHlust),
        patch("heretic.rodd.microphone.MicrophoneCapture.best_available", return_value=MagicMock()),
        patch("heretic.rodd.vad.VadDetector.best_available", return_value=MagicMock()),
        patch("heretic.rodd.whisper_engine.WhisperEngine.best_available", return_value=MagicMock()),
        patch("sys.stdin.isatty", return_value=True),
        patch("sys.stdin.readline", side_effect=_fake_readline),
    ):
        result = await _async_light(_make_args())

    # Should complete normally — fallback to stdin after capture failure
    assert result == 0
    assert capture_call_count[0] >= 1


# ---------------------------------------------------------------------------
# Test: Hlust.close() called during Slokna
# ---------------------------------------------------------------------------

async def test_light_closes_hlust_during_slokna() -> None:
    """light command calls Hlust.close() during the Slokna teardown phase."""
    cfg = _make_full_config(stt_enabled=True)

    hlust_close_calls = [0]

    class TrackingHlust:
        def __init__(self, *a, **kw):
            self.is_available = True
            self.is_closed = False

        async def open(self): pass

        async def capture_one_utterance(self):
            return "/quit"

        async def close(self):
            hlust_close_calls[0] += 1

    client = _make_mock_client()

    with (
        patch("heretic.grunnr.config.load_config", return_value=cfg),
        patch("heretic.grunnr.logger.configure_logging"),
        patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()),
        patch("heretic.bifrost.client.OpenAICompatClient", return_value=client),
        patch("heretic.rodd.hlust.Hlust", TrackingHlust),
        patch("heretic.rodd.microphone.MicrophoneCapture.best_available", return_value=MagicMock()),
        patch("heretic.rodd.vad.VadDetector.best_available", return_value=MagicMock()),
        patch("heretic.rodd.whisper_engine.WhisperEngine.best_available", return_value=MagicMock()),
        patch("sys.stdin.isatty", return_value=True),
    ):
        await _async_light(_make_args())

    assert hlust_close_calls[0] == 1


# ---------------------------------------------------------------------------
# Test: Stdin path still works when stt.enabled is False (v0.2 regression)
# ---------------------------------------------------------------------------

async def test_stdin_path_unaffected_when_stt_disabled() -> None:
    """Stdin input still functions normally when rodd.stt.enabled is False (v0.2 path)."""
    cfg = _make_full_config(stt_enabled=False)

    # Feed one non-quit turn followed by /quit
    readline_responses = ["hello\n", "/quit\n"]
    send_message_calls = [0]

    def _fake_readline():
        return readline_responses.pop(0) if readline_responses else ""

    async def _fake_send(messages, **kwargs):
        send_message_calls[0] += 1
        yield "response text"

    client = _make_mock_client()
    client.send_message = _fake_send

    with (
        patch("heretic.grunnr.config.load_config", return_value=cfg),
        patch("heretic.grunnr.logger.configure_logging"),
        patch("heretic.grunnr.logger.get_logger", return_value=MagicMock()),
        patch("heretic.bifrost.client.OpenAICompatClient", return_value=client),
        patch("sys.stdin.isatty", return_value=False),
        patch("sys.stdin.readline", side_effect=_fake_readline),
    ):
        result = await _async_light(_make_args())

    assert result == 0
    # send_message should have been called once for the "hello" turn
    assert send_message_calls[0] == 1
