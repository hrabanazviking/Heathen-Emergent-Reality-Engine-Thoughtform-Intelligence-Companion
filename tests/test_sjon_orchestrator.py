"""
Placeholder tests for heretic.sjon.sjon.Sjón orchestrator.

These tests are skip-marked during the v0.5 scaffold phase. Forge implements
the full test suite in Wave 2 after the stubs in sjon.py are filled.

Coverage targets (Forge):
    - Sjón.is_available returns False when config.screen.enabled is False
    - Sjón.is_available returns False when backend.available() is False
    - Sjón.is_available returns True when both conditions are met
    - Sjón.snapshot() returns [] when is_available is False (no capture)
    - Sjón.snapshot() returns [] when throttle rejects (within min_interval_ms)
    - Sjón.snapshot() returns [] when backend.capture() raises ScreenCaptureError
    - Sjón.snapshot() returns [] when backend.capture() raises PermissionDeniedError
    - Sjón.snapshot() returns [] when encoder.encode_to_data_url() raises FrameEncodingError
    - Sjón.snapshot() returns [] on unexpected exception (never propagates)
    - Sjón.snapshot() returns ["data:image/png;base64,..."] on success (mock backend + encoder)
    - Sjón.snapshot() respects throttle: two rapid calls return [data_url, []]
    - Sjón.snapshot() does NOT raise under any error condition
    - Sjón.close() calls backend.close() exactly once
    - Sjón.close() is idempotent (safe to call twice)
    - SjonActivity events are emitted at capturing / encoding / idle milestones
      (verify via EventBus mock when Forge wires the event bus integration)
"""

from __future__ import annotations

import asyncio

import pytest


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
async def test_sjon_snapshot_returns_empty_when_unavailable() -> None:
    """snapshot() returns [] immediately when backend is unavailable."""
    from unittest.mock import MagicMock, AsyncMock
    from heretic.sjon.capture import NullBackend
    from heretic.sjon.config_model import SjonConfig, SjonScreenConfig
    from heretic.sjon.encoder import FrameEncoder
    from heretic.sjon.sjon import Sjón
    import logging

    config = SjonConfig(screen=SjonScreenConfig(enabled=True))
    backend = NullBackend()  # available() is always False
    encoder = MagicMock(spec=FrameEncoder)
    sjon = Sjón(config=config, capture_backend=backend, encoder=encoder,
                logger=logging.getLogger("test"))
    result = await sjon.snapshot()
    assert result == []


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
async def test_sjon_snapshot_returns_empty_when_screen_disabled() -> None:
    """snapshot() returns [] when config.screen.enabled is False."""
    from unittest.mock import MagicMock
    from heretic.sjon.capture import NullBackend
    from heretic.sjon.config_model import SjonConfig, SjonScreenConfig
    from heretic.sjon.encoder import FrameEncoder
    from heretic.sjon.sjon import Sjón
    import logging

    config = SjonConfig(screen=SjonScreenConfig(enabled=False))
    backend = MagicMock()
    backend.available.return_value = True
    encoder = MagicMock(spec=FrameEncoder)
    sjon = Sjón(config=config, capture_backend=backend, encoder=encoder,
                logger=logging.getLogger("test"))
    result = await sjon.snapshot()
    assert result == []
    backend.capture.assert_not_called()


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
async def test_sjon_snapshot_never_raises() -> None:
    """snapshot() returns [] and never raises, even on unexpected errors."""
    from unittest.mock import MagicMock
    from heretic.sjon.config_model import SjonConfig, SjonScreenConfig
    from heretic.sjon.encoder import FrameEncoder
    from heretic.sjon.sjon import Sjón
    import logging

    config = SjonConfig(screen=SjonScreenConfig(enabled=True))
    backend = MagicMock()
    backend.available.return_value = True
    backend.capture.side_effect = RuntimeError("unexpected backend explosion")
    encoder = MagicMock(spec=FrameEncoder)
    sjon = Sjón(config=config, capture_backend=backend, encoder=encoder,
                logger=logging.getLogger("test"))
    # Must not raise
    result = await sjon.snapshot()
    assert result == []


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
async def test_sjon_snapshot_throttle() -> None:
    """Second snapshot() within min_interval_ms returns [] (throttled)."""
    from unittest.mock import MagicMock, patch
    from heretic.sjon.config_model import SjonConfig, SjonScreenConfig
    from heretic.sjon.encoder import FrameEncoder
    from heretic.sjon.sjon import Sjón
    import logging

    screen_cfg = SjonScreenConfig(enabled=True, min_interval_ms=5000)
    config = SjonConfig(screen=screen_cfg)
    backend = MagicMock()
    backend.available.return_value = True
    backend.capture.return_value = (b"\x00" * 4, 1, 1)
    encoder = MagicMock(spec=FrameEncoder)
    encoder.encode_to_data_url.return_value = "data:image/png;base64,abc"
    sjon = Sjón(config=config, capture_backend=backend, encoder=encoder,
                logger=logging.getLogger("test"))

    # First call — should succeed
    result1 = await sjon.snapshot()
    assert result1 == ["data:image/png;base64,abc"]

    # Immediate second call — within throttle window; should return []
    result2 = await sjon.snapshot()
    assert result2 == []
    assert backend.capture.call_count == 1  # only one actual capture


@pytest.mark.skip(reason="v0.5 scaffold placeholder — Forge implements in Wave 2")
async def test_sjon_close_calls_backend_close() -> None:
    """close() calls backend.close() and is idempotent."""
    from unittest.mock import MagicMock
    from heretic.sjon.config_model import SjonConfig
    from heretic.sjon.encoder import FrameEncoder
    from heretic.sjon.sjon import Sjón
    import logging

    backend = MagicMock()
    backend.available.return_value = False
    encoder = MagicMock(spec=FrameEncoder)
    sjon = Sjón(config=SjonConfig(), capture_backend=backend, encoder=encoder,
                logger=logging.getLogger("test"))
    await sjon.close()
    await sjon.close()  # idempotent — must not raise
    assert backend.close.call_count >= 1
