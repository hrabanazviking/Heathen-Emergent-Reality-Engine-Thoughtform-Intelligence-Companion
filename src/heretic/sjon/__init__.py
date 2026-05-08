"""
heretic.sjon — L3 Sjón (Vision) module.

Exports all public types needed by other layers:

Configuration:
    SjonConfig          — root config struct (screen + webcam)
    SjonScreenConfig    — screen capture settings (Approach B source of truth)
    SjonWebcamConfig    — webcam settings (declared; not implemented in v0.5)

Capture backends:
    ScreenCaptureBackend  — abstract base class
    MssBackend            — mss-based cross-platform backend (mss in [vision] extra)
    NullBackend           — always-unavailable silent stub
    best_available        — factory function (module-level, mirrors rodd.playback pattern)

Encoder:
    FrameEncoder          — BGRA -> resize -> PNG -> base64 data URL

Orchestrator:
    Sjon                  — async on-demand snapshot coordinator
    (True Name: Sjón — use ascii alias Sjon in code; the Unicode class name is also
     exported for operators who prefer the diacritics form)

Errors:
    SjonError               — root
    ScreenCaptureError      — capture operation failure
    PermissionDeniedError   — OS denied screen capture permission
    BackendUnavailableError — no backend available on this machine
    FrameEncodingError      — encoding failure (Pillow, resize, base64)
    ThrottleRejectedError   — snapshot rejected within min_interval_ms window

Importing this package from heretic.grunnr.config is safe: the import chain is
    heretic.sjon.config_model -> (stdlib only)
which introduces no circular dependency.

Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
    src/heretic/sjon/INTERFACE.md — full module contract.
"""

from __future__ import annotations

from heretic.sjon.capture import (
    MssBackend,
    NullBackend,
    ScreenCaptureBackend,
    best_available,
)
from heretic.sjon.config_model import SjonConfig, SjonScreenConfig, SjonWebcamConfig
from heretic.sjon.encoder import FrameEncoder
from heretic.sjon.errors import (
    BackendUnavailableError,
    FrameEncodingError,
    PermissionDeniedError,
    ScreenCaptureError,
    SjonError,
    ThrottleRejectedError,
)
from heretic.sjon.sjon import Sjón

# ASCII alias for callers who do not use Unicode identifiers.
Sjon = Sjón

__all__ = [
    # Config
    "SjonConfig",
    "SjonScreenConfig",
    "SjonWebcamConfig",
    # Capture
    "ScreenCaptureBackend",
    "MssBackend",
    "NullBackend",
    "best_available",
    # Encoder
    "FrameEncoder",
    # Orchestrator
    "Sjón",
    "Sjon",
    # Errors
    "SjonError",
    "ScreenCaptureError",
    "PermissionDeniedError",
    "BackendUnavailableError",
    "FrameEncodingError",
    "ThrottleRejectedError",
]
