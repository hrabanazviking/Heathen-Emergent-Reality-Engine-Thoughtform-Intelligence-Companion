"""
Sjón config — SjonConfig, SjonScreenConfig, SjonWebcamConfig dataclasses.

These are the canonical type definitions for L3 Sjón (Vision). They were
previously inlined in heretic.grunnr.config; they now live here so the sjon
layer is self-contained, mirroring the pattern established by rodd.config_model
and vebond.config_model (Approach B, audit S-1).

heretic.grunnr.config imports from this module and re-exports the types.
This module has no imports from heretic.grunnr, so the import direction is safe
and introduces no circular dependency.

Canonical key reference: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal, Optional


_LOG = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SjonScreenConfig
# ---------------------------------------------------------------------------

@dataclass
class SjonScreenConfig:
    """Screen capture settings for L3 Sjón.

    All fields correspond to the sjon.screen.* YAML block documented in
    LAYER_INTERFACES.md §L3 Sjón config keys.

    Privacy invariant: save_frames defaults to False.  Auto-saving captured
    frames to disk is NEVER permitted without explicit operator opt-in.
    When save_frames is True a non-fatal warning is logged at construction
    time to ensure the choice is visible in the log stream.

    Ref: docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md C-Q-C3 (sealed).
    """

    enabled: bool = True
    """True = screen capture active when L3 Sjón starts."""

    interval_ms: int = 5000
    """Milliseconds between periodic captures (v0.5.x — not used in v0.5 on-demand mode)."""

    max_width: int = 1280
    """Maximum output width in pixels. Frame is scaled down if the captured screen
    is wider; aspect ratio is preserved. Balances detail vs. token cost."""

    max_height: int = 720
    """Maximum output height in pixels. Frame is scaled down if the captured screen
    is taller; aspect ratio is preserved."""

    crop: Optional[dict[str, int]] = None
    """None = full screen. Dict with keys {x, y, w, h} to capture a sub-region.
    Coordinates in pixels on the source monitor. Validation: x,y,w,h must all be
    non-negative integers. Forge validates bounds against monitor geometry at capture time."""

    buffer_depth: int = 5
    """Number of frames to retain in the ring buffer (v0.5.x — not used in v0.5 on-demand mode).
    Must be >= 1."""

    save_frames: bool = False
    """Opt-in only. When True, captured frames may be written to an ephemeral
    session-scoped temp directory (never a permanent location). A log warning is
    emitted at construction time when this is True. NEVER set True by default.
    Privacy invariant: see docs/architecture/LAYER_INTERFACES.md §L3 Error model."""

    monitor_index: int = 0
    """Zero-based index of the monitor to capture. 0 = primary monitor (default).
    Must be >= 0. Out-of-range values are handled gracefully at capture time by
    clamping to the highest available monitor index with a warning.

    Monitor-index mapping asymmetry (v0.5.1):
        In on-demand mode (continuous=False), monitor_index=0 maps to the primary
        single screen (mss index 1).  In continuous mode (continuous=True),
        monitor_index=0 maps to the all-monitors composite (mss index 0).
        For monitor_index>=1, direct mss index mapping applies in both modes.
    """

    continuous: bool = False
    """Opt-in periodic capture; v0.5.1+. When True, Sjón starts a background
    asyncio.Task at TENGSL that captures every interval_ms milliseconds and
    populates a ring buffer of depth buffer_depth. When False (default), Sjón
    operates in on-demand mode: one frame per snapshot() call, no background task.

    Requires interval_ms > 0. Sub-500ms intervals emit a warning at config
    construction time because they stress the host system under continuous load.
    """

    attach_policy: Literal["latest", "all_buffered", "none"] = "latest"
    """Per-turn frame-attach policy for continuous mode; v0.5.1+.
    Governs which buffered frames are attached to a user message when continuous=True.

    Values:
        "latest"       — attach the single most-recent frame from the ring buffer
                         (default; mirrors v0.5 on-demand behaviour: one frame per turn).
        "all_buffered" — attach every frame currently in the ring buffer (up to
                         buffer_depth frames); higher token cost, richer temporal context.
        "none"         — do not attach any frames from the buffer; continuous capture
                         runs but frames are not injected into agent turns.

    Ignored when continuous=False (on-demand mode uses snapshot() directly).
    Valid values: "latest" | "all_buffered" | "none". Any other value raises
    SjonConfigError at config construction time.
    """

    min_interval_ms: int = 1000
    """Minimum milliseconds between any two captures (throttle guard). No capture
    will be initiated within this window of the previous one, regardless of trigger.
    Must be >= 0. Default 1000 ms prevents rapid-fire spam."""

    def __post_init__(self) -> None:
        """Validate field ranges. Non-fatal warnings for unsafe opt-ins."""
        if self.interval_ms < 0:
            raise ValueError(
                f"SjonScreenConfig.interval_ms must be >= 0, got {self.interval_ms}"
            )
        if self.max_width < 1:
            raise ValueError(
                f"SjonScreenConfig.max_width must be >= 1, got {self.max_width}"
            )
        if self.max_height < 1:
            raise ValueError(
                f"SjonScreenConfig.max_height must be >= 1, got {self.max_height}"
            )
        if self.buffer_depth < 1:
            raise ValueError(
                f"SjonScreenConfig.buffer_depth must be >= 1, got {self.buffer_depth}"
            )
        if self.monitor_index < 0:
            raise ValueError(
                f"SjonScreenConfig.monitor_index must be >= 0, got {self.monitor_index}"
            )
        if self.min_interval_ms < 0:
            raise ValueError(
                f"SjonScreenConfig.min_interval_ms must be >= 0, got {self.min_interval_ms}"
            )
        if self.crop is not None:
            for key in ("x", "y", "w", "h"):
                val = self.crop.get(key, 0)
                if not isinstance(val, int) or val < 0:
                    raise ValueError(
                        f"SjonScreenConfig.crop.{key} must be a non-negative integer, "
                        f"got {val!r}"
                    )
        if self.save_frames:
            _LOG.warning(
                "SjonScreenConfig: save_frames is True. Captured screen frames WILL be "
                "written to disk. Ensure this is intentional — the privacy invariant "
                "requires opt-in. Ref: LAYER_INTERFACES.md §L3 Error model."
            )
        if self.continuous and self.interval_ms < 500:
            _LOG.warning(
                "SjonScreenConfig: continuous=True with interval_ms=%d. "
                "Sub-500ms capture intervals stress the host system under sustained load. "
                "Consider increasing interval_ms to 500 or higher.",
                self.interval_ms,
            )
        _valid_attach_policies = ("latest", "all_buffered", "none")
        if self.attach_policy not in _valid_attach_policies:
            raise ValueError(
                f"SjonScreenConfig.attach_policy must be one of "
                f"{_valid_attach_policies!r}, got {self.attach_policy!r}"
            )


# ---------------------------------------------------------------------------
# SjonWebcamConfig
# ---------------------------------------------------------------------------

@dataclass
class SjonWebcamConfig:
    """Webcam capture settings for L3 Sjón.

    Declared here for forward compatibility. Webcam support is NOT implemented
    in v0.5 — this mirrors the RoddSttConfig pattern where Hlust was declared
    in v0.2 but implemented in v0.3.

    Implementation target: v1.x.
    """

    enabled: bool = False
    """False by default — webcam capture not implemented in v0.5."""

    device: str = "default"
    """OS device identifier or 'default'. Interpretation is backend-specific."""

    interval_ms: int = 10000
    """Milliseconds between periodic webcam captures. Must be >= 0."""

    def __post_init__(self) -> None:
        if self.interval_ms < 0:
            raise ValueError(
                f"SjonWebcamConfig.interval_ms must be >= 0, got {self.interval_ms}"
            )


# ---------------------------------------------------------------------------
# SjonConfig (root)
# ---------------------------------------------------------------------------

@dataclass
class SjonConfig:
    """L3 Sjón — vision layer root config.

    Groups screen and webcam sub-configs. Corresponds to the sjon: top-level
    YAML block in heretic.yaml.

    Authoritative key reference: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
    """

    screen: SjonScreenConfig = field(default_factory=SjonScreenConfig)
    """Screen capture configuration."""

    webcam: SjonWebcamConfig = field(default_factory=SjonWebcamConfig)
    """Webcam capture configuration (declared; not implemented in v0.5)."""
