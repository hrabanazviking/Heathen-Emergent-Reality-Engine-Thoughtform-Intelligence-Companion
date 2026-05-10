"""
Sjón privacy masks (Blæja — v0.5.3).

This module owns the rectangular privacy-mask layer applied to captured frames
before any leak path (encode, save, transport). The mask runs inside
`FrameEncoder.encode()`, after PIL decoding the raw bytes and before resize.
There is no codepath in which an unmasked frame can reach disk or transport
when a non-empty `privacy_masks` list is configured.

Public surface:
    - `PrivacyMaskRegion` dataclass — operator-defined region with mode and
      mode-specific parameters.
    - `apply_privacy_masks(image, masks)` pure function — applies each region
      to the image in order; returns the image (modified in place).

Privacy invariants (cross-checked by Auditor in AUDIT_v0.5.3_BLAEJA.md):
    P-1: Unmasked frame bytes never reach disk if any privacy mask is configured.
    P-2: Unmasked frame bytes never reach the agent.
    P-3: `privacy_masks` defaults to `[]` — feature is opt-in.
    P-4: Mask coordinates in source pixel space; clamping silent except for a
         one-time debug log per encoder lifetime.
    P-5: Zero-area regions rejected at config-construction with `ValueError`.
    P-6: Existing privacy invariants preserved (save_frames False, webcam enabled
         False, in-memory ring buffer only).

Ref: src/heretic/sjon/INTERFACE.md §Privacy Masks (Blæja — v0.5.3)
     docs/cartography/DATA_FLOW.md §4.10.14
     docs/vision/BLAEJA.md
     TASK_HERETIC_v0.5.3_BLAEJA.md §3
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal, Optional, Tuple


_LOG = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PrivacyMaskRegion
# ---------------------------------------------------------------------------

PrivacyMaskMode = Literal["blur", "solid", "pixelate"]
"""Application modes for a privacy mask region.

- "blur"     — Gaussian blur of the region.
- "solid"    — region replaced with a uniform RGB colour.
- "pixelate" — region downsampled then upsampled with NEAREST resampling.
"""

_VALID_MODES: Tuple[str, ...] = ("blur", "solid", "pixelate")


@dataclass
class PrivacyMaskRegion:
    """A rectangular region of a captured frame to be obscured before encoding.

    Coordinates are in **source pixel space** — i.e., the monitor or webcam's
    native resolution before any resize. This keeps operator authoring stable:
    if `max_width` changes from 1280 to 1920 in heretic.yaml, mask coordinates
    remain valid.

    Construction-time validation (raises `ValueError`):
        - `x`, `y` must be non-negative ints
        - `w`, `h` must be positive ints (>= 1)
        - `mode` must be one of {"blur", "solid", "pixelate"}
        - `solid_color` must be a 3-tuple of ints in [0, 255] when present
        - `blur_radius`, when not None, must be >= 1
        - `pixelate_factor`, when not None, must be >= 2

    Out-of-bounds regions (e.g., `x + w > image_width`) are clamped at apply
    time, silently except for a one-time debug log per encoder lifetime.
    A region wholly off the frame becomes a no-op.
    """

    x: int
    """Left edge of the region in source pixels. Must be >= 0."""

    y: int
    """Top edge of the region in source pixels. Must be >= 0."""

    w: int
    """Width of the region in source pixels. Must be >= 1."""

    h: int
    """Height of the region in source pixels. Must be >= 1."""

    mode: PrivacyMaskMode = "blur"
    """Application mode. One of {"blur", "solid", "pixelate"}."""

    blur_radius: Optional[int] = None
    """Optional Gaussian blur radius (used when `mode == "blur"`).
    `None` means auto: `max(8, min(w, h) // 8)`."""

    solid_color: Tuple[int, int, int] = (0, 0, 0)
    """RGB colour used when `mode == "solid"`. Default: black `(0, 0, 0)`."""

    pixelate_factor: Optional[int] = None
    """Optional pixelation factor (used when `mode == "pixelate"`).
    `None` means auto: `max(8, min(w, h) // 12)`."""

    def __post_init__(self) -> None:
        """Validate field ranges and modes. Fail loudly at config construction."""
        if not isinstance(self.x, int) or self.x < 0:
            raise ValueError(
                f"PrivacyMaskRegion.x must be a non-negative integer, got {self.x!r}"
            )
        if not isinstance(self.y, int) or self.y < 0:
            raise ValueError(
                f"PrivacyMaskRegion.y must be a non-negative integer, got {self.y!r}"
            )
        if not isinstance(self.w, int) or self.w < 1:
            raise ValueError(
                f"PrivacyMaskRegion.w must be a positive integer (>= 1), got {self.w!r}"
            )
        if not isinstance(self.h, int) or self.h < 1:
            raise ValueError(
                f"PrivacyMaskRegion.h must be a positive integer (>= 1), got {self.h!r}"
            )
        if self.mode not in _VALID_MODES:
            raise ValueError(
                f"PrivacyMaskRegion.mode must be one of {_VALID_MODES!r}, "
                f"got {self.mode!r}"
            )
        if self.blur_radius is not None:
            if not isinstance(self.blur_radius, int) or self.blur_radius < 1:
                raise ValueError(
                    f"PrivacyMaskRegion.blur_radius must be a positive integer or None, "
                    f"got {self.blur_radius!r}"
                )
        if self.pixelate_factor is not None:
            if not isinstance(self.pixelate_factor, int) or self.pixelate_factor < 2:
                raise ValueError(
                    f"PrivacyMaskRegion.pixelate_factor must be an integer >= 2 or None, "
                    f"got {self.pixelate_factor!r}"
                )
        if not (
            isinstance(self.solid_color, tuple)
            and len(self.solid_color) == 3
            and all(isinstance(c, int) and 0 <= c <= 255 for c in self.solid_color)
        ):
            raise ValueError(
                f"PrivacyMaskRegion.solid_color must be a 3-tuple of ints in [0, 255], "
                f"got {self.solid_color!r}"
            )


# ---------------------------------------------------------------------------
# apply_privacy_masks
# ---------------------------------------------------------------------------

def apply_privacy_masks(
    image: object,
    masks: list[PrivacyMaskRegion],
    *,
    log: Optional[logging.Logger] = None,
    _state: Optional[dict] = None,
) -> object:
    """Apply a list of privacy mask regions to a PIL.Image, in place.

    This is the body of the Blæja step. It runs inside `FrameEncoder.encode()`
    after PIL decoding the raw bytes and before any resize / save / transport.

    Args:
        image: A PIL.Image. Type-annotated as `object` because Pillow is an
            optional dependency and `PIL.Image` is not importable at module
            load time without it. Callers always pass a real PIL.Image.
        masks: List of `PrivacyMaskRegion` to apply, in order. An empty list
            is the early-return fast path: returns the image unchanged.
        log: Optional logger. Defaults to module logger.
        _state: Internal — encoder-instance state dict for one-time debug log
            tracking. When present, `_state["clamp_logged"]` is consulted/set.

    Returns:
        The same PIL.Image, modified in place. Returned for chaining.

    Behaviour:
        - Empty `masks` list: image returned unchanged (no Pillow imports happen).
        - Each region clamped to image bounds:
            x_eff = max(0, min(x, w_img - 1))
            y_eff = max(0, min(y, h_img - 1))
            w_eff = max(0, min(x + w, w_img) - x_eff)
            h_eff = max(0, min(y + h, h_img) - y_eff)
            If w_eff == 0 or h_eff == 0, region is a no-op.
        - First clamp/no-op per encoder lifetime emits a debug log; subsequent
          ones are silent.
        - On Pillow filter exception within a region's mode application, the
          region falls back to SOLID-fill (fail-safe — the unmasked region
          must never propagate downstream).

    Raises:
        Nothing. Exceptions inside the mask step are caught and converted to
        SOLID-fill fallback. The function is total — it always returns an
        image, never raises.

    Forge contract: this signature is final at Wave 3. The Forge implements
    the body in Wave 4 (mask cropping, mode application via Pillow primitives,
    paste-back).
    """
    raise NotImplementedError(
        "Architect scaffold (Wave 3): function signature is sealed; "
        "Forge implements body in Wave 4."
    )
