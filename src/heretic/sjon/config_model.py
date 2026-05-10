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

v0.5.2: SjonWebcamConfig fields activated (was stub). WebcamCaptureBackend
and OpenCvBackend live in webcam.py. This file owns the config types only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal, Optional

from heretic.sjon.privacy import PrivacyMaskRegion


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

    privacy_masks: list[PrivacyMaskRegion] = field(default_factory=list)
    """v0.5.3 — list of privacy mask regions applied to captured screen frames.

    Each region is a PrivacyMaskRegion specifying (x, y, w, h, mode) in source
    pixel space. Default is `[]` (empty) — opt-in. When non-empty, masks are
    applied inside FrameEncoder.encode() after PIL decode and before resize,
    so unmasked frame bytes never reach disk or the agent.

    Independent from sjon.webcam.privacy_masks — the two senses have different
    privacy concerns and may have different region sets.

    Ref: docs/vision/BLAEJA.md, src/heretic/sjon/privacy.py."""

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
    """Webcam capture settings for L3 Sjón (v0.5.2 — activated).

    Previously a forward-compatibility stub (v0.5). As of v0.5.2 these fields
    drive the WebcamCaptureBackend selection and OpenCvBackend lifecycle declared
    in webcam.py.

    Privacy invariant (stronger than screen capture):
        - enabled defaults to False. Webcam captures the user's physical presence.
          Operators must explicitly opt in. A WARNING is logged at construction
          time when enabled is True to ensure the choice is visible in the log stream.
        - Frames are NEVER written to disk in v0.5.2 (on-demand only).
        - No ring buffer, no continuous mode in v0.5.2. Those are v0.5.x backlog.

    attach_policy governs how webcam frames combine with screen frames in the
    user-message payload. Default "screen_only" preserves backward compatibility
    exactly — the webcam backend may be active but contributes no frames unless
    the policy is changed.

    Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
         src/heretic/sjon/webcam.py (WebcamCaptureBackend ABC + OpenCvBackend).
    """

    enabled: bool = False
    """False by default — webcam captures the user's physical presence.
    Operator must explicitly set to True. A WARNING is logged at construction
    time when True (matching the save_frames pattern in SjonScreenConfig)."""

    device_index: int = 0
    """Zero-based OS device index for cv2.VideoCapture(device_index).
    0 = first available camera (default). Must be >= 0.
    Multi-camera enumeration is deferred to v0.5.x."""

    max_width: int = 1280
    """Maximum output width in pixels. Frame is scaled down proportionally if wider.
    Balances detail vs. vision-API token cost. Must be >= 1."""

    max_height: int = 720
    """Maximum output height in pixels. Frame is scaled down proportionally if taller.
    Must be >= 1."""

    format: Literal["jpeg", "png"] = "jpeg"  # noqa: A003 — field name mirrors YAML key
    """Encoding format for webcam frames delivered to the agent.
    "jpeg" (default) — smaller payload (~5-10x vs PNG); acceptable quality for
    vision API use. "png" — lossless; larger payload; use when visual accuracy
    is more important than token cost.
    Valid values: "jpeg" | "png"."""

    jpeg_quality: int = 85
    """JPEG encoding quality (1–100). Ignored when format is "png".
    85 is a good balance between size and visual fidelity for vision-API use.
    Must be in [1, 100]."""

    attach_policy: Literal["screen_only", "webcam_only", "alongside", "alternate"] = "screen_only"
    """Per-turn frame attachment policy — controls how webcam frames combine with
    screen frames when building the user-message image_url content blocks.

    Values:
        "screen_only"  — default; webcam backend may be active but contributes
                          no frames. Backward-compatible with v0.5.
        "webcam_only"  — send webcam frame; suppress screen frame even if
                          sjon.screen.enabled is True.
        "alongside"    — send BOTH screen and webcam frames in the same turn.
                          Higher token cost; gives the agent the most context.
        "alternate"    — odd turns send screen frame; even turns send webcam frame.
                          Moderate token cost; provides temporal variety.

    Valid values: "screen_only" | "webcam_only" | "alongside" | "alternate".
    Any other value raises SjonConfigError at construction time."""

    privacy_masks: list[PrivacyMaskRegion] = field(default_factory=list)
    """v0.5.3 — list of privacy mask regions applied to captured webcam frames.

    Each region is a PrivacyMaskRegion specifying (x, y, w, h, mode) in source
    pixel space (the webcam's native resolution before resize). Default is `[]`
    (empty) — opt-in. When non-empty, masks are applied inside FrameEncoder
    after decode and before resize, so unmasked webcam bytes never reach disk
    or the agent.

    Independent from sjon.screen.privacy_masks — webcam privacy concerns
    (background, roommate, identity) often differ from screen-capture concerns
    (password manager, private chat).

    Ref: docs/vision/BLAEJA.md, src/heretic/sjon/privacy.py."""

    def __post_init__(self) -> None:
        """Validate field ranges and log privacy notice when enabled is True."""
        _valid_formats = ("jpeg", "png")
        if self.format not in _valid_formats:
            raise ValueError(
                f"SjonWebcamConfig.format must be one of {_valid_formats!r}, "
                f"got {self.format!r}"
            )

        _valid_policies = ("screen_only", "webcam_only", "alongside", "alternate")
        if self.attach_policy not in _valid_policies:
            raise ValueError(
                f"SjonWebcamConfig.attach_policy must be one of {_valid_policies!r}, "
                f"got {self.attach_policy!r}"
            )

        if self.jpeg_quality < 1 or self.jpeg_quality > 100:
            raise ValueError(
                f"SjonWebcamConfig.jpeg_quality must be in [1, 100], "
                f"got {self.jpeg_quality}"
            )

        if self.max_width < 1:
            raise ValueError(
                f"SjonWebcamConfig.max_width must be >= 1, got {self.max_width}"
            )

        if self.max_height < 1:
            raise ValueError(
                f"SjonWebcamConfig.max_height must be >= 1, got {self.max_height}"
            )

        if self.device_index < 0:
            raise ValueError(
                f"SjonWebcamConfig.device_index must be >= 0, got {self.device_index}"
            )

        if self.enabled:
            _LOG.warning(
                "SjonWebcamConfig: enabled is True. Webcam capture will include "
                "the user's physical presence in agent context. "
                "Ensure this is intentional — the privacy invariant requires explicit opt-in. "
                "Ref: src/heretic/sjon/INTERFACE.md §Webcam capture."
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
