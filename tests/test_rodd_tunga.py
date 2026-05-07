"""
Placeholder tests — heretic.rodd.tunga (Tunga orchestrator).

All tests are skip-marked. Forge (Eldra Járnsdóttir) replaces the skip markers
and ``pass`` bodies with real assertions in Wave 2.

All ChatterboxClient and AudioPlayback calls must be mocked — no real HTTP or
audio in the test suite. Use pytest-mock (mocker fixture) or unittest.mock.AsyncMock.

Coverage targets (Forge):

    Initialisation:
        - Tunga.is_degraded is False when playback is available and client opens successfully.
        - Tunga.is_degraded is True immediately when playback.available() returns False.
        - Tunga.is_degraded is True if client.open() raises ChatterboxConnectionError.
        - Tunga.is_degraded is True if client.open() raises ChatterboxError (any subclass).

    feed_chunk() happy path:
        - Accumulates text without speaking when buffer < chunk_min_chars.
        - Flushes a sentence chunk when buffer >= chunk_min_chars and contains a terminator.
        - Retains the remainder after the last terminator in the buffer.
        - Calls client.synthesize() with the correct chunk text.
        - Calls playback.play() with the WAV bytes returned by synthesize().

    feed_chunk() degraded / fault paths:
        - Does nothing when is_degraded is True.
        - Does nothing when is_closed is True.
        - Sets is_degraded and does not raise when synthesize() raises ChatterboxError.
        - Sets is_degraded and does not raise when play() raises PlaybackError.

    flush():
        - Speaks the remaining buffer text and clears the buffer.
        - Does nothing when buffer is empty (or whitespace-only).
        - Does nothing when is_degraded is True.
        - Does nothing when is_closed is True.
        - Does not raise when synthesize() fails during flush.

    close():
        - Calls client.close() and playback.close().
        - Sets is_closed to True.
        - Is safe to call multiple times (idempotent).
        - Does not raise when client.close() raises.
        - Does not raise when playback.close() raises.

    Sentence chunking logic:
        - Splits on '. ' boundary correctly.
        - Splits on '! ' boundary correctly.
        - Splits on '? ' boundary correctly.
        - Splits on '\n\n' boundary correctly.
        - Retains partial sentence after the last terminator.
        - Does not split when no terminator present regardless of length.
"""

import pytest


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_tunga_not_degraded_on_successful_init(mocker) -> None:
    """Tunga.is_degraded is False when playback is available and client opens."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_tunga_degraded_when_playback_unavailable(mocker) -> None:
    """Tunga.is_degraded is True when playback.available() returns False."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_tunga_degraded_when_client_open_raises(mocker) -> None:
    """Tunga.is_degraded is True when client.open() raises ChatterboxConnectionError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_feed_chunk_accumulates_below_min_chars(mocker) -> None:
    """feed_chunk() does not call synthesize() when buffer is below chunk_min_chars."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_feed_chunk_flushes_on_sentence_boundary(mocker) -> None:
    """feed_chunk() calls synthesize() when buffer >= chunk_min_chars and terminator found."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_feed_chunk_retains_remainder_after_terminator(mocker) -> None:
    """feed_chunk() retains text after the last terminator in the buffer."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_feed_chunk_calls_playback_play(mocker) -> None:
    """feed_chunk() calls playback.play() with the bytes returned by synthesize()."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_feed_chunk_noop_when_degraded(mocker) -> None:
    """feed_chunk() does nothing when is_degraded is True."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_feed_chunk_noop_when_closed(mocker) -> None:
    """feed_chunk() does nothing when is_closed is True."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_feed_chunk_sets_degraded_on_synthesize_error(mocker) -> None:
    """feed_chunk() sets is_degraded=True and does not raise when synthesize() fails."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_feed_chunk_sets_degraded_on_playback_error(mocker) -> None:
    """feed_chunk() sets is_degraded=True and does not raise when play() raises PlaybackError."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_flush_speaks_remaining_buffer(mocker) -> None:
    """flush() calls synthesize() with the full remaining buffer and clears it."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_flush_noop_on_empty_buffer(mocker) -> None:
    """flush() does not call synthesize() when buffer is empty or whitespace-only."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_flush_noop_when_degraded(mocker) -> None:
    """flush() does nothing when is_degraded is True."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_flush_does_not_raise_on_synthesize_failure(mocker) -> None:
    """flush() does not raise when synthesize() fails during the final flush."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_close_calls_client_and_playback_close(mocker) -> None:
    """close() calls client.close() and playback.close()."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_close_sets_is_closed(mocker) -> None:
    """close() sets is_closed to True."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_close_is_idempotent(mocker) -> None:
    """close() can be called multiple times without raising or double-closing."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_close_does_not_raise_when_client_close_raises(mocker) -> None:
    """close() does not raise when client.close() raises an exception."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_chunking_splits_on_period(mocker) -> None:
    """Sentence chunking correctly splits on '. ' boundary."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_chunking_splits_on_exclamation(mocker) -> None:
    """Sentence chunking correctly splits on '! ' boundary."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_chunking_splits_on_question(mocker) -> None:
    """Sentence chunking correctly splits on '? ' boundary."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_chunking_splits_on_double_newline(mocker) -> None:
    """Sentence chunking correctly splits on '\\n\\n' boundary."""
    pass


@pytest.mark.skip(reason="Scaffold placeholder — Forge will implement in Wave 2")
async def test_chunking_no_split_without_terminator(mocker) -> None:
    """Chunking does not split even when buffer is long if no terminator is present."""
    pass
