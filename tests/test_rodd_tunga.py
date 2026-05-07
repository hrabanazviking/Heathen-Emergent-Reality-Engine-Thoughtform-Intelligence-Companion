"""
Tests — heretic.rodd.tunga (Tunga orchestrator).

All ChatterboxClient and AudioPlayback calls are mocked — no real HTTP or
audio in the test suite. Tests cover initialisation, sentence-boundary chunking,
fault tolerance, and the close() idempotency contract.

NOTE: feed_chunk() and flush() are async def in the implemented Tunga — they must
be awaited. Tests use pytest-asyncio (asyncio_mode=auto from pyproject.toml).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from heretic.rodd.config_model import RoddConfig, RoddTtsConfig
from heretic.rodd.errors import ChatterboxConnectionError, ChatterboxError, PlaybackError
from heretic.rodd.tunga import Tunga


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(chunk_min_chars: int = 80) -> RoddConfig:
    return RoddConfig(
        tts=RoddTtsConfig(
            endpoint="http://test:7851",
            chunk_min_chars=chunk_min_chars,
            sentence_terminators=(". ", "! ", "? ", "\n\n"),
        )
    )


def _make_logger():
    import logging
    log = logging.getLogger("test.rodd.tunga")
    log.setLevel(logging.CRITICAL)
    return log


def _mock_client(open_raises=None):
    """Return a mock ChatterboxClient."""
    client = MagicMock()
    if open_raises:
        client.open = AsyncMock(side_effect=open_raises)
    else:
        client.open = AsyncMock()
    client.close = AsyncMock()
    # synthesize returns a minimal non-empty bytes by default
    client.synthesize = AsyncMock(return_value=b"RIFF" + b"\x00" * 40)
    return client


def _mock_playback(available: bool = True):
    """Return a mock AudioPlayback backend."""
    pb = MagicMock()
    pb.available = MagicMock(return_value=available)
    pb.play = MagicMock()
    pb.close = MagicMock()
    return pb


async def _build_tunga(config=None, open_raises=None, playback_available=True):
    """Build and open a Tunga for testing."""
    if config is None:
        config = _make_config()
    logger = _make_logger()
    client = _mock_client(open_raises=open_raises)
    playback = _mock_playback(available=playback_available)
    tunga = Tunga(config, client, playback, logger)
    await tunga.open()
    return tunga, client, playback


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

async def test_tunga_not_degraded_on_successful_init() -> None:
    """Tunga.is_degraded is False when playback is available and client opens."""
    tunga, _, _ = await _build_tunga()
    assert tunga.is_degraded is False
    assert tunga.is_closed is False
    await tunga.close()


async def test_tunga_degraded_when_playback_unavailable() -> None:
    """Tunga.is_degraded is True immediately when playback.available() returns False."""
    tunga, _, _ = await _build_tunga(playback_available=False)
    assert tunga.is_degraded is True
    await tunga.close()


async def test_tunga_degraded_when_client_open_raises_connection_error() -> None:
    """Tunga.is_degraded is True when client.open() raises ChatterboxConnectionError."""
    tunga, _, _ = await _build_tunga(open_raises=ChatterboxConnectionError("unreachable"))
    assert tunga.is_degraded is True
    await tunga.close()


async def test_tunga_degraded_when_client_open_raises_any_chatterbox_error() -> None:
    """Tunga.is_degraded is True when client.open() raises any ChatterboxError subclass."""
    from heretic.rodd.errors import ChatterboxApiError
    tunga, _, _ = await _build_tunga(open_raises=ChatterboxApiError("500", status_code=500))
    assert tunga.is_degraded is True
    await tunga.close()


# ---------------------------------------------------------------------------
# feed_chunk() — happy path
# ---------------------------------------------------------------------------

async def test_feed_chunk_accumulates_below_min_chars() -> None:
    """feed_chunk() does not call synthesize() when buffer is below chunk_min_chars."""
    config = _make_config(chunk_min_chars=80)
    tunga, client, playback = await _build_tunga(config=config)

    # Feed a short chunk — well below 80 chars
    await tunga.feed_chunk("Hello. ")
    client.synthesize.assert_not_called()
    await tunga.close()


async def test_feed_chunk_flushes_on_sentence_boundary() -> None:
    """feed_chunk() calls synthesize() when buffer >= chunk_min_chars and terminator found."""
    config = _make_config(chunk_min_chars=10)
    tunga, client, playback = await _build_tunga(config=config)

    # Feed a chunk that exceeds min_chars and ends with '. '
    text = "This is a sentence. "
    await tunga.feed_chunk(text)
    client.synthesize.assert_called_once()
    await tunga.close()


async def test_feed_chunk_retains_remainder_after_terminator() -> None:
    """feed_chunk() retains text after the last terminator in the buffer."""
    config = _make_config(chunk_min_chars=10)
    tunga, client, playback = await _build_tunga(config=config)

    text = "First sentence. Second"
    await tunga.feed_chunk(text)
    # First sentence should have been spoken; "Second" is retained
    assert tunga._buffer == "Second"
    await tunga.close()


async def test_feed_chunk_calls_playback_play() -> None:
    """feed_chunk() calls playback.play() with the bytes returned by synthesize()."""
    config = _make_config(chunk_min_chars=10)
    tunga, client, playback = await _build_tunga(config=config)

    await tunga.feed_chunk("This fires synthesis. ")
    playback.play.assert_called_once()
    await tunga.close()


async def test_feed_chunk_handles_multiple_terminators_in_one_delta() -> None:
    """feed_chunk() with 'last terminator' policy correctly extracts up to the last boundary."""
    config = _make_config(chunk_min_chars=5)
    tunga, client, playback = await _build_tunga(config=config)

    text = "One sentence. Two sentence. Partial"
    await tunga.feed_chunk(text)
    # Should speak up to the LAST '. ' and retain "Partial"
    assert tunga._buffer == "Partial"
    # synthesize should have been called once (one chunk covering both sentences)
    client.synthesize.assert_called_once()
    await tunga.close()


# ---------------------------------------------------------------------------
# feed_chunk() — degraded / fault paths
# ---------------------------------------------------------------------------

async def test_feed_chunk_noop_when_degraded() -> None:
    """feed_chunk() does nothing when is_degraded is True."""
    config = _make_config(chunk_min_chars=5)
    tunga, client, playback = await _build_tunga(config=config)
    tunga._degraded = True

    await tunga.feed_chunk("This sentence should not be spoken. ")
    client.synthesize.assert_not_called()
    await tunga.close()


async def test_feed_chunk_noop_when_closed() -> None:
    """feed_chunk() does nothing when is_closed is True."""
    config = _make_config(chunk_min_chars=5)
    tunga, client, playback = await _build_tunga(config=config)
    tunga._closed = True

    await tunga.feed_chunk("This sentence. ")
    client.synthesize.assert_not_called()


async def test_feed_chunk_sets_degraded_on_synthesize_error() -> None:
    """feed_chunk() sets is_degraded=True and does not raise when synthesize() fails.

    After _MAX_CONSECUTIVE_FAILURES consecutive failures, Tunga enters degraded mode.
    """
    config = _make_config(chunk_min_chars=5)
    from heretic.rodd.tunga import _MAX_CONSECUTIVE_FAILURES
    logger = _make_logger()
    client = _mock_client()
    client.synthesize = AsyncMock(side_effect=ChatterboxConnectionError("gone"))
    playback = _mock_playback()
    tunga = Tunga(config, client, playback, logger)
    await tunga.open()

    # Feed enough failing chunks to trip the consecutive failure counter
    for _ in range(_MAX_CONSECUTIVE_FAILURES):
        await tunga.feed_chunk("A failing sentence. ")
        if tunga.is_degraded:
            break

    assert tunga.is_degraded is True
    await tunga.close()


async def test_feed_chunk_sets_degraded_on_playback_error() -> None:
    """feed_chunk() does not raise when play() raises PlaybackError.

    Playback errors alone do not degrade Tunga (ChatterBox is still reachable),
    but the call should complete without raising.
    """
    config = _make_config(chunk_min_chars=5)
    logger = _make_logger()
    client = _mock_client()
    client.synthesize = AsyncMock(return_value=b"RIFF" + b"\x00" * 40)
    playback = _mock_playback()
    playback.play = MagicMock(side_effect=PlaybackError("device gone"))
    tunga = Tunga(config, client, playback, logger)
    await tunga.open()

    # Should not raise
    await tunga.feed_chunk("Audio fails to play. ")
    # Tunga should still be running (playback failure alone doesn't trip consecutive counter)
    # and most importantly it did not raise
    await tunga.close()


async def test_feed_chunk_does_not_raise_on_any_failure() -> None:
    """feed_chunk() must never propagate exceptions — fault tolerance is absolute."""
    config = _make_config(chunk_min_chars=5)
    logger = _make_logger()
    client = _mock_client()
    client.synthesize = AsyncMock(side_effect=RuntimeError("unexpected boom"))
    playback = _mock_playback()
    tunga = Tunga(config, client, playback, logger)
    await tunga.open()

    # Must not raise
    await tunga.feed_chunk("Unexpected error sentence. ")
    await tunga.close()


# ---------------------------------------------------------------------------
# flush()
# ---------------------------------------------------------------------------

async def test_flush_speaks_remaining_buffer() -> None:
    """flush() calls synthesize() with the full remaining buffer and clears it."""
    config = _make_config(chunk_min_chars=500)  # High min — buffer won't auto-flush
    tunga, client, playback = await _build_tunga(config=config)

    tunga._buffer = "This is still in the buffer"
    await tunga.flush()

    client.synthesize.assert_called_once_with("This is still in the buffer")
    assert tunga._buffer == ""
    await tunga.close()


async def test_flush_noop_on_empty_buffer() -> None:
    """flush() does not call synthesize() when buffer is empty or whitespace-only."""
    tunga, client, playback = await _build_tunga()

    tunga._buffer = "   "
    await tunga.flush()
    client.synthesize.assert_not_called()
    await tunga.close()


async def test_flush_noop_when_degraded() -> None:
    """flush() does nothing when is_degraded is True."""
    tunga, client, playback = await _build_tunga()
    tunga._degraded = True
    tunga._buffer = "Something in the buffer"

    await tunga.flush()
    client.synthesize.assert_not_called()
    await tunga.close()


async def test_flush_noop_when_closed() -> None:
    """flush() does nothing when is_closed is True."""
    tunga, client, playback = await _build_tunga()
    tunga._closed = True
    tunga._buffer = "Something"

    await tunga.flush()
    client.synthesize.assert_not_called()


async def test_flush_does_not_raise_on_synthesize_failure() -> None:
    """flush() does not raise when synthesize() fails during the final flush."""
    config = _make_config(chunk_min_chars=500)
    logger = _make_logger()
    client = _mock_client()
    client.synthesize = AsyncMock(side_effect=ChatterboxConnectionError("gone"))
    playback = _mock_playback()
    tunga = Tunga(config, client, playback, logger)
    await tunga.open()

    tunga._buffer = "Last words"
    await tunga.flush()  # Must not raise


# ---------------------------------------------------------------------------
# close()
# ---------------------------------------------------------------------------

async def test_close_calls_client_and_playback_close() -> None:
    """close() calls client.close() and playback.close()."""
    tunga, client, playback = await _build_tunga()
    tunga._buffer = ""  # Ensure no final flush attempt
    await tunga.close()
    client.close.assert_called_once()
    playback.close.assert_called_once()


async def test_close_sets_is_closed() -> None:
    """close() sets is_closed to True."""
    tunga, client, playback = await _build_tunga()
    await tunga.close()
    assert tunga.is_closed is True


async def test_close_is_idempotent() -> None:
    """close() can be called multiple times without raising or double-closing."""
    tunga, client, playback = await _build_tunga()
    await tunga.close()
    await tunga.close()
    await tunga.close()
    # client.close should only have been called ONCE despite three close() calls
    client.close.assert_called_once()


async def test_close_does_not_raise_when_client_close_raises() -> None:
    """close() does not raise when client.close() raises an exception."""
    tunga, client, playback = await _build_tunga()
    client.close = AsyncMock(side_effect=RuntimeError("close explosion"))

    await tunga.close()  # Must not raise
    assert tunga.is_closed is True


async def test_close_does_not_raise_when_playback_close_raises() -> None:
    """close() does not raise when playback.close() raises an exception."""
    tunga, client, playback = await _build_tunga()
    playback.close = MagicMock(side_effect=RuntimeError("playback close boom"))

    await tunga.close()  # Must not raise
    assert tunga.is_closed is True


# ---------------------------------------------------------------------------
# Sentence chunking logic (detailed boundary tests)
# ---------------------------------------------------------------------------

async def test_chunking_splits_on_period() -> None:
    """Sentence chunking correctly splits on '. ' boundary."""
    config = _make_config(chunk_min_chars=5)
    tunga, client, _ = await _build_tunga(config=config)

    await tunga.feed_chunk("A sentence. ")
    client.synthesize.assert_called()
    await tunga.close()


async def test_chunking_splits_on_exclamation() -> None:
    """Sentence chunking correctly splits on '! ' boundary."""
    config = _make_config(chunk_min_chars=5)
    tunga, client, _ = await _build_tunga(config=config)

    await tunga.feed_chunk("A sentence! ")
    client.synthesize.assert_called()
    await tunga.close()


async def test_chunking_splits_on_question() -> None:
    """Sentence chunking correctly splits on '? ' boundary."""
    config = _make_config(chunk_min_chars=5)
    tunga, client, _ = await _build_tunga(config=config)

    await tunga.feed_chunk("A sentence? ")
    client.synthesize.assert_called()
    await tunga.close()


async def test_chunking_splits_on_double_newline() -> None:
    """Sentence chunking correctly splits on '\\n\\n' boundary."""
    config = _make_config(chunk_min_chars=5)
    tunga, client, _ = await _build_tunga(config=config)

    await tunga.feed_chunk("A paragraph\n\nStarting here")
    client.synthesize.assert_called()
    await tunga.close()


async def test_chunking_no_split_without_terminator() -> None:
    """Chunking does not split even when buffer is long if no terminator is present."""
    config = _make_config(chunk_min_chars=5)
    tunga, client, _ = await _build_tunga(config=config)

    # Very long text but no terminator character
    await tunga.feed_chunk("A" * 500)
    client.synthesize.assert_not_called()
    # Buffer should hold all of it
    assert len(tunga._buffer) == 500
    await tunga.close()


async def test_chunking_respects_min_chars_threshold() -> None:
    """Chunking does not fire when buffer has a terminator but is below min_chars."""
    config = _make_config(chunk_min_chars=80)
    tunga, client, _ = await _build_tunga(config=config)

    # This has a terminator but total text is under 80 chars
    await tunga.feed_chunk("Short. ")
    client.synthesize.assert_not_called()
    await tunga.close()
