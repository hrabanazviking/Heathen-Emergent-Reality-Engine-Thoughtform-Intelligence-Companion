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
    log = log if log is not None else _LOG

    # Empty list is the early-return fast path. No Pillow imports happen here.
    if not masks:
        return image

    # Lazy import — Pillow is an optional dep but here is required because we
    # already have a PIL.Image in hand from upstream decode.
    from PIL import Image, ImageDraw, ImageFilter

    img: "Image.Image" = image  # type: ignore[assignment]
    w_img, h_img = img.size

    for region in masks:
        # Clamp region to image bounds. Returns (x, y, w, h) of effective
        # region. If w_eff or h_eff is 0, region is wholly off-frame.
        x_eff = max(0, min(region.x, w_img))
        y_eff = max(0, min(region.y, h_img))
        x_end = max(x_eff, min(region.x + region.w, w_img))
        y_end = max(y_eff, min(region.y + region.h, h_img))
        w_eff = x_end - x_eff
        h_eff = y_end - y_eff

        if w_eff <= 0 or h_eff <= 0:
            _maybe_log_clamp_once(
                log, _state,
                "wholly off-frame", region, w_img, h_img,
            )
            continue

        clamped = (w_eff != region.w) or (h_eff != region.h) or (
            x_eff != region.x or y_eff != region.y
        )
        if clamped:
            _maybe_log_clamp_once(
                log, _state,
                "partially off-frame (clamped)", region, w_img, h_img,
            )

        try:
            _apply_one_region(img, region, x_eff, y_eff, w_eff, h_eff)
        except Exception as exc:
            # Fail-safe: if any Pillow primitive raises during the mask
            # application, fall back to SOLID-fill so the unmasked region
            # never propagates downstream.
            log.warning(
                "Blæja: mask application raised for region "
                "(x=%d, y=%d, w=%d, h=%d, mode=%r): %s — falling back to SOLID",
                region.x, region.y, region.w, region.h, region.mode, exc,
            )
            try:
                draw = ImageDraw.Draw(img)
                draw.rectangle(
                    (x_eff, y_eff, x_eff + w_eff - 1, y_eff + h_eff - 1),
                    fill=region.solid_color,
                )
            except Exception as exc2:
                # If even SOLID-fill fails, the whole encoder fails — but
                # we never let an unmasked region pass downstream silently.
                # This branch should be unreachable in practice because
                # ImageDraw.rectangle on a valid PIL image cannot fail given
                # validated inputs.
                raise RuntimeError(
                    f"Blæja: SOLID-fill fallback failed for region "
                    f"({region.x}, {region.y}, {region.w}, {region.h}): {exc2}"
                ) from exc2

    return img


def _maybe_log_clamp_once(
    log: logging.Logger,
    state: Optional[dict],
    kind: str,
    region: PrivacyMaskRegion,
    w_img: int,
    h_img: int,
) -> None:
    """Emit one-time-per-encoder debug log on clamp / no-op events.

    `state` is the encoder's persistent state dict (passed by the caller).
    When `state["clamp_logged"]` is already True, this is a no-op.
    Without a `state` dict, the log fires every time (used in pure-function
    tests where there's no encoder lifetime).
    """
    if state is not None and state.get("clamp_logged"):
        return
    log.debug(
        "Blæja: privacy mask region %s on %dx%d image: "
        "x=%d, y=%d, w=%d, h=%d, mode=%r. Subsequent clamp events suppressed.",
        kind, w_img, h_img,
        region.x, region.y, region.w, region.h, region.mode,
    )
    if state is not None:
        state["clamp_logged"] = True


def _apply_one_region(
    img: object,
    region: PrivacyMaskRegion,
    x: int,
    y: int,
    w: int,
    h: int,
) -> None:
    """Apply a single mask region in place on the given PIL.Image.

    Uses the post-clamp coordinates (x, y, w, h). Dispatches by mode.
    """
    from PIL import Image, ImageDraw, ImageFilter

    image: "Image.Image" = img  # type: ignore[assignment]

    if region.mode == "solid":
        draw = ImageDraw.Draw(image)
        # Pillow rectangle uses inclusive (x0, y0, x1, y1) coords — the
        # bottom-right point IS painted, so we use w-1 / h-1 as the offset.
        draw.rectangle(
            (x, y, x + w - 1, y + h - 1),
            fill=region.solid_color,
        )
        return

    if region.mode == "blur":
        radius = (
            region.blur_radius
            if region.blur_radius is not None
            else max(8, min(w, h) // 8)
        )
        # Crop region, blur the crop, paste back at (x, y).
        crop = image.crop((x, y, x + w, y + h))
        blurred = crop.filter(ImageFilter.GaussianBlur(radius=radius))
        image.paste(blurred, (x, y))
        return

    if region.mode == "pixelate":
        factor = (
            region.pixelate_factor
            if region.pixelate_factor is not None
            else max(8, min(w, h) // 12)
        )
        small_w = max(1, w // factor)
        small_h = max(1, h // factor)
        crop = image.crop((x, y, x + w, y + h))
        # Down-sample to coarse grid, then up-sample with NEAREST so the
        # pixelation blocks are crisp.
        small = crop.resize((small_w, small_h), Image.Resampling.NEAREST)
        pixelated = small.resize((w, h), Image.Resampling.NEAREST)
        image.paste(pixelated, (x, y))
        return

    # Should be unreachable — mode is validated at PrivacyMaskRegion.__post_init__.
    raise ValueError(f"Blæja: unknown mask mode {region.mode!r}")
