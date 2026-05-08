"""
Tests for heretic.sjon.sjon.Sjón orchestrator.

All external I/O (capture backend, encoder) is mocked. Tests verify:
    - is_available gating
    - throttle behaviour (Cartographer F-5: returns [] not stale, within min_interval_ms)
    - snapshot() happy path returns ["data:image/png;base64,..."]
    - failure modes return [] and never raise
    - close() is idempotent
    - event_emitter receives correct SjonActivity state sequence
"""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import MagicMock, patch

import pytest

from heretic.sjon.config_model import SjonConfig, SjonScreenConfig
from heretic.sjon.encoder import FrameEncoder
from heretic.sjon.errors import (
    BackendUnavailableError,
    FrameEncodingError,
    PermissionDeniedError,
    ScreenCaptureError,
)


def _make_sjon(
    enabled: bool = True,
    backend_available: bool = True,
    min_interval_ms: int = 0,
    event_emitter=None,
    max_width: int = 64,
    max_height: int = 64,
):
    """Helper: build a Sjón orchestrator with controlled mock backend/encoder."""
    from heretic.sjon.sjon import Sjón

    screen_cfg = SjonScreenConfig(
        enabled=enabled,
        min_interval_ms=min_interval_ms,
        max_width=max_width,
        max_height=max_height,
    )
    config = SjonConfig(screen=screen_cfg)

    mock_backend = MagicMock()
    mock_backend.available.return_value = backend_available
    # Default happy-path: returns a 1x1 BGRA frame
    mock_backend.capture.return_value = (bytes(4), 1, 1)

    mock_encoder = MagicMock(spec=FrameEncoder)
    mock_encoder.encode.return_value = b"\x89PNG" + b"\x00" * 32
    mock_encoder.to_data_url.return_value = "data:image/png;base64,AAAA"

    sjon = Sjón(
        config=config,
        capture_backend=mock_backend,
        encoder=mock_encoder,
        logger=logging.getLogger("test.sjon"),
        event_emitter=event_emitter,
    )
    return sjon, mock_backend, mock_encoder


# ---------------------------------------------------------------------------
# is_available property
# ---------------------------------------------------------------------------

class TestSjonIsAvailable:
    def test_false_when_screen_disabled(self) -> None:
        sjon, _, _ = _make_sjon(enabled=False, backend_available=True)
        assert sjon.is_available is False

    def test_false_when_backend_unavailable(self) -> None:
        sjon, _, _ = _make_sjon(enabled=True, backend_available=False)
        assert sjon.is_available is False

    def test_true_when_both_conditions_met(self) -> None:
        sjon, _, _ = _make_sjon(enabled=True, backend_available=True)
        assert sjon.is_available is True


# ---------------------------------------------------------------------------
# snapshot() — gating
# ---------------------------------------------------------------------------

class TestSjonSnapshotGating:
    @pytest.mark.asyncio
    async def test_returns_empty_when_unavailable(self) -> None:
        """snapshot() returns [] when backend is unavailable."""
        sjon, mock_backend, _ = _make_sjon(backend_available=False)
        result = await sjon.snapshot()
        assert result == []
        mock_backend.capture.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_when_screen_disabled(self) -> None:
        """snapshot() returns [] when config.screen.enabled is False."""
        sjon, mock_backend, _ = _make_sjon(enabled=False)
        result = await sjon.snapshot()
        assert result == []
        mock_backend.capture.assert_not_called()


# ---------------------------------------------------------------------------
# snapshot() — happy path
# ---------------------------------------------------------------------------

class TestSjonSnapshotHappyPath:
    @pytest.mark.asyncio
    async def test_returns_data_url_list_on_success(self) -> None:
        """snapshot() returns a list with one data URL string on success."""
        sjon, _, _ = _make_sjon()
        result = await sjon.snapshot()
        assert len(result) == 1
        assert result[0] == "data:image/png;base64,AAAA"

    @pytest.mark.asyncio
    async def test_calls_capture_then_encode_then_data_url(self) -> None:
        """snapshot() calls backend.capture, encoder.encode, encoder.to_data_url in order."""
        sjon, mock_backend, mock_encoder = _make_sjon()
        await sjon.snapshot()
        mock_backend.capture.assert_called_once()
        mock_encoder.encode.assert_called_once()
        mock_encoder.to_data_url.assert_called_once()


# ---------------------------------------------------------------------------
# snapshot() — throttle (Cartographer F-5: returns [] not stale)
# ---------------------------------------------------------------------------

class TestSjonSnapshotThrottle:
    @pytest.mark.asyncio
    async def test_first_call_succeeds(self) -> None:
        sjon, _, _ = _make_sjon(min_interval_ms=0)
        result = await sjon.snapshot()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_second_call_within_throttle_returns_empty(self) -> None:
        """Second snapshot() within min_interval_ms returns [] (empty, not stale)."""
        sjon, mock_backend, _ = _make_sjon(min_interval_ms=60000)  # 60s throttle

        result1 = await sjon.snapshot()
        assert len(result1) == 1  # first call succeeds

        result2 = await sjon.snapshot()
        assert result2 == []  # throttled — empty list, not stale frame
        assert mock_backend.capture.call_count == 1  # only one actual capture occurred

    @pytest.mark.asyncio
    async def test_throttle_zero_allows_rapid_calls(self) -> None:
        """When min_interval_ms=0 there is no throttle and calls always proceed."""
        sjon, mock_backend, _ = _make_sjon(min_interval_ms=0)
        await sjon.snapshot()
        await sjon.snapshot()
        assert mock_backend.capture.call_count == 2


# ---------------------------------------------------------------------------
# snapshot() — failure modes (all must return [] and never raise)
# ---------------------------------------------------------------------------

class TestSjonSnapshotFailureModes:
    @pytest.mark.asyncio
    async def test_returns_empty_on_screen_capture_error(self) -> None:
        sjon, mock_backend, _ = _make_sjon()
        mock_backend.capture.side_effect = ScreenCaptureError("capture failed")
        result = await sjon.snapshot()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_permission_denied(self) -> None:
        sjon, mock_backend, _ = _make_sjon()
        mock_backend.capture.side_effect = PermissionDeniedError("permission denied")
        result = await sjon.snapshot()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_backend_unavailable_at_capture_time(self) -> None:
        sjon, mock_backend, _ = _make_sjon()
        mock_backend.capture.side_effect = BackendUnavailableError("backend gone")
        result = await sjon.snapshot()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_frame_encoding_error(self) -> None:
        sjon, _, mock_encoder = _make_sjon()
        mock_encoder.encode.side_effect = FrameEncodingError("encode failed")
        result = await sjon.snapshot()
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_unexpected_exception(self) -> None:
        """snapshot() never raises even on completely unexpected exceptions."""
        sjon, mock_backend, _ = _make_sjon()
        mock_backend.capture.side_effect = RuntimeError("something exploded")
        result = await sjon.snapshot()
        assert result == []

    @pytest.mark.asyncio
    async def test_does_not_raise_on_any_error(self) -> None:
        """Verify the no-raise contract: snapshot() must be safe to call unconditionally."""
        sjon, mock_backend, _ = _make_sjon()
        mock_backend.capture.side_effect = ValueError("very unexpected")
        # Must not raise — call should complete cleanly
        try:
            result = await sjon.snapshot()
            assert result == []
        except Exception as exc:
            pytest.fail(f"snapshot() raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# snapshot() — oversize guard (F-4)
# ---------------------------------------------------------------------------

class TestSjonSnapshotOversizeGuard:
    @pytest.mark.asyncio
    async def test_oversized_png_triggers_retry_at_half_resolution(self) -> None:
        """When encoded PNG exceeds 4 MB, retry encodes with halved max dimensions.

        N-1 fix: previously only asserted call_count == 2, which passed even when
        the retry used the same (un-halved) dimensions. Now we also verify that
        the second call carries max_width_override and max_height_override set to
        exactly half of the configured max_width / max_height.
        """
        from heretic.sjon.sjon import _OVERSIZE_BYTES

        # _make_sjon defaults: max_width=64, max_height=64
        # So expected half dims: max_width_override=32, max_height_override=32
        sjon, _, mock_encoder = _make_sjon(max_width=64, max_height=64)
        # First encode: oversized. Second encode (half res): acceptable size.
        oversized_png = b"\x89PNG" + b"\x00" * (_OVERSIZE_BYTES + 1)
        small_png = b"\x89PNG" + b"\x00" * 32
        mock_encoder.encode.side_effect = [oversized_png, small_png]
        mock_encoder.to_data_url.return_value = "data:image/png;base64,RETRY"

        result = await sjon.snapshot()
        # Should succeed with the retry result
        assert result == ["data:image/png;base64,RETRY"]
        assert mock_encoder.encode.call_count == 2  # original + retry

        # N-1 fix: verify the SECOND call actually passed halved override dimensions.
        # call_args_list[0] = first call (no overrides), [1] = retry (with overrides).
        first_call = mock_encoder.encode.call_args_list[0]
        retry_call = mock_encoder.encode.call_args_list[1]

        # First call must NOT carry the oversize overrides (clean baseline).
        assert first_call.kwargs.get("max_width_override") is None
        assert first_call.kwargs.get("max_height_override") is None

        # Retry call MUST carry exactly half the configured max dimensions.
        assert retry_call.kwargs.get("max_width_override") == 32   # 64 // 2
        assert retry_call.kwargs.get("max_height_override") == 32  # 64 // 2

    @pytest.mark.asyncio
    async def test_oversized_retry_also_oversized_returns_empty(self) -> None:
        """When both original and retry encode are oversized, return []."""
        from heretic.sjon.sjon import _OVERSIZE_BYTES

        sjon, _, mock_encoder = _make_sjon()
        oversized_png = b"\x89PNG" + b"\x00" * (_OVERSIZE_BYTES + 1)
        mock_encoder.encode.side_effect = [oversized_png, oversized_png]

        result = await sjon.snapshot()
        assert result == []


# ---------------------------------------------------------------------------
# close() — idempotency and resource cleanup
# ---------------------------------------------------------------------------

class TestSjonClose:
    @pytest.mark.asyncio
    async def test_close_calls_backend_close(self) -> None:
        sjon, mock_backend, _ = _make_sjon()
        await sjon.close()
        mock_backend.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self) -> None:
        """close() can be called multiple times without error."""
        sjon, mock_backend, _ = _make_sjon()
        await sjon.close()
        await sjon.close()
        # Must not raise — backend.close() may be called once or twice, both fine

    @pytest.mark.asyncio
    async def test_close_ignores_backend_exception(self) -> None:
        """close() must not propagate errors from backend.close()."""
        sjon, mock_backend, _ = _make_sjon()
        mock_backend.close.side_effect = RuntimeError("close failed")
        # Must not raise
        await sjon.close()


# ---------------------------------------------------------------------------
# event_emitter — SjonActivity state sequence
# ---------------------------------------------------------------------------

class TestSjonEventEmitter:
    @pytest.mark.asyncio
    async def test_emits_capturing_encoding_idle_on_success(self) -> None:
        """Happy-path snapshot emits: capturing -> encoding -> idle."""
        emitted_states = []

        def _emitter(event):
            try:
                emitted_states.append(event.state.value)
            except AttributeError:
                emitted_states.append(str(event))

        sjon, _, _ = _make_sjon(event_emitter=_emitter)
        result = await sjon.snapshot()
        assert len(result) == 1
        # States must appear in the correct order
        assert "capturing" in emitted_states
        assert "encoding" in emitted_states
        assert "idle" in emitted_states
        # capturing must precede encoding, encoding must precede idle
        assert emitted_states.index("capturing") < emitted_states.index("encoding")
        assert emitted_states.index("encoding") < emitted_states.index("idle")

    @pytest.mark.asyncio
    async def test_emits_failed_on_capture_error(self) -> None:
        """Capture error triggers a 'failed' event emission."""
        emitted_states = []

        def _emitter(event):
            try:
                emitted_states.append(event.state.value)
            except AttributeError:
                emitted_states.append(str(event))

        sjon, mock_backend, _ = _make_sjon(event_emitter=_emitter)
        mock_backend.capture.side_effect = ScreenCaptureError("boom")
        await sjon.snapshot()
        assert "failed" in emitted_states

    @pytest.mark.asyncio
    async def test_no_event_emitter_does_not_crash(self) -> None:
        """When event_emitter is None, snapshot() proceeds without error."""
        sjon, _, _ = _make_sjon(event_emitter=None)
        result = await sjon.snapshot()
        assert len(result) == 1


# ---------------------------------------------------------------------------
# v0.5.1 placeholder tests — continuous task lifecycle + ring buffer
# Forge implements the logic; these stubs mark the scaffold complete.
# ---------------------------------------------------------------------------

class TestSjonContinuousCapture:
    """start_continuous_capture / stop_continuous_capture — v0.5.1. (Placeholders.)"""

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: task starts and emits CONTINUOUS_RUNNING"
    )
    @pytest.mark.asyncio
    async def test_start_continuous_capture_launches_task(self) -> None:
        sjon, _, _ = _make_sjon()
        await sjon.start_continuous_capture()
        assert sjon._continuous_task is not None
        assert not sjon._continuous_task.done()
        await sjon.stop_continuous_capture()

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: stop cancels task cleanly"
    )
    @pytest.mark.asyncio
    async def test_stop_continuous_capture_cancels_task(self) -> None:
        sjon, _, _ = _make_sjon()
        await sjon.start_continuous_capture()
        await sjon.stop_continuous_capture()
        assert sjon._continuous_task is None

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: start is idempotent (no double-task)"
    )
    @pytest.mark.asyncio
    async def test_start_continuous_capture_idempotent(self) -> None:
        sjon, _, _ = _make_sjon()
        await sjon.start_continuous_capture()
        first_task = sjon._continuous_task
        await sjon.start_continuous_capture()  # second call — must not spawn a new task
        assert sjon._continuous_task is first_task
        await sjon.stop_continuous_capture()

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: stop is idempotent (no-op if not running)"
    )
    @pytest.mark.asyncio
    async def test_stop_continuous_capture_idempotent(self) -> None:
        sjon, _, _ = _make_sjon()
        await sjon.stop_continuous_capture()  # must not raise when no task running


class TestSjonRingBuffer:
    """recent_frames() and ring buffer semantics — v0.5.1. (Placeholders.)"""

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: recent_frames returns [] on empty buffer"
    )
    def test_recent_frames_empty_when_no_capture(self) -> None:
        sjon, _, _ = _make_sjon()
        assert sjon.recent_frames() == []

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: recent_frames(n) returns last n entries"
    )
    def test_recent_frames_returns_last_n(self) -> None:
        sjon, _, _ = _make_sjon()
        # Manually populate buffer to simulate continuous mode
        sjon._buffer.extend(["url1", "url2", "url3"])
        result = sjon.recent_frames(n=2)
        assert result == ["url2", "url3"]

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: recent_frames(None) returns all"
    )
    def test_recent_frames_none_returns_all(self) -> None:
        sjon, _, _ = _make_sjon()
        sjon._buffer.extend(["url1", "url2", "url3"])
        result = sjon.recent_frames()
        assert result == ["url1", "url2", "url3"]

    @pytest.mark.skip(
        reason="v0.5.1 placeholder — Forge implements: buffer cleared on close (privacy invariant)"
    )
    @pytest.mark.asyncio
    async def test_close_clears_buffer(self) -> None:
        sjon, _, _ = _make_sjon()
        sjon._buffer.extend(["url1", "url2"])
        await sjon.close()
        assert list(sjon._buffer) == []
