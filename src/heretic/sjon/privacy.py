"""
Sjón privacy masks (Blæja v0.5.3 + Margblæja v0.5.4).

This module owns the privacy-mask layer applied to captured frames before any
leak path (encode, save, transport). The mask runs inside
`FrameEncoder.encode()`, after PIL decoding the raw bytes and before resize.
There is no codepath in which an unmasked frame can reach disk or transport
when a non-empty `privacy_masks` list is configured.

Public surface:
    - `PrivacyMaskShape` Protocol — structural type any concrete shape obeys.
      Two methods: `bounding_box()` and `alpha_mask(w, h)`.
    - `PrivacyMaskRegion` dataclass — rectangular shape (v0.5.3 base case).
    - `PrivacyMaskCircle` dataclass — circle shape (v0.5.4).
    - `PrivacyMaskPolygon` dataclass — polygon shape with >= 3 vertices (v0.5.4).
    - `apply_privacy_masks(image, masks)` pure function — applies each shape
      to the image via the shared bbox-clamp / crop / apply-mode / composite /
      paste pipeline.

Privacy invariants:
    P-1: Unmasked frame bytes never reach disk.                    (v0.5.3)
    P-2: Unmasked frame bytes never reach the agent.               (v0.5.3)
    P-3: `privacy_masks` defaults to `[]` — feature is opt-in.     (v0.5.3)
    P-4: Mask coordinates in source pixel space; clamping silent
         except one-time debug log per encoder lifetime.           (v0.5.3)
    P-5: Zero-area regions rejected at config-construction.        (v0.5.3)
    P-6: Existing privacy invariants preserved (save_frames False,
         webcam enabled False, in-memory ring buffer only).        (v0.5.3)
    P-7: Alpha-mask composite preserves shape boundaries pixel-exactly.
                                                                    (v0.5.4)
    P-8: Degenerate polygon (co-linear/coincident vertices) is a
         valid construction. Pillow rasterises whatever it can (a thin
         line for collinear points, a single pixel for coincident ones).
         apply does not raise; mask covers Pillow's output; the rest of
         the image is unchanged.                                     (v0.5.4)
    P-9: A shape whose bounding box is wholly off-frame is a no-op. (v0.5.4)

Ref: src/heretic/sjon/INTERFACE.md §Privacy Masks (Blæja + Margblæja)
     docs/cartography/DATA_FLOW.md §4.10.14, §4.10.14.1
     docs/vision/BLAEJA.md, docs/vision/MARGBLAEJA.md
     TASK_HERETIC_v0.5.3_BLAEJA.md, TASK_HERETIC_v0.5.4_MARGBLAEJA.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal, Optional, Protocol, Tuple, runtime_checkable


_LOG = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared mode + validation helpers
# ---------------------------------------------------------------------------

PrivacyMaskMode = Literal["blur", "solid", "pixelate"]
"""Application modes for a privacy mask region.

- "blur"     — Gaussian blur of the region.
- "solid"    — region replaced with a uniform RGB colour.
- "pixelate" — region downsampled then upsampled with NEAREST resampling.
"""

_VALID_MODES: Tuple[str, ...] = ("blur", "solid", "pixelate")


def _validate_shared_shape_fields(
    cls_name: str,
    mode: str,
    blur_radius: Optional[int],
    solid_color: Tuple[int, int, int],
    pixelate_factor: Optional[int],
) -> None:
    """Shared validation for the mode + mode-param fields across all shapes.

    Each shape's __post_init__ calls this after validating its own
    geometric fields. Raises ValueError on any constraint breach.
    """
    if mode not in _VALID_MODES:
        raise ValueError(
            f"{cls_name}.mode must be one of {_VALID_MODES!r}, got {mode!r}"
        )
    if blur_radius is not None:
        if not isinstance(blur_radius, int) or blur_radius < 1:
            raise ValueError(
                f"{cls_name}.blur_radius must be a positive integer or None, "
                f"got {blur_radius!r}"
            )
    if pixelate_factor is not None:
        if not isinstance(pixelate_factor, int) or pixelate_factor < 2:
            raise ValueError(
                f"{cls_name}.pixelate_factor must be an integer >= 2 or None, "
                f"got {pixelate_factor!r}"
            )
    if not (
        isinstance(solid_color, tuple)
        and len(solid_color) == 3
        and all(isinstance(c, int) and 0 <= c <= 255 for c in solid_color)
    ):
        raise ValueError(
            f"{cls_name}.solid_color must be a 3-tuple of ints in [0, 255], "
            f"got {solid_color!r}"
        )


# ---------------------------------------------------------------------------
# PrivacyMaskShape Protocol (v0.5.4)
# ---------------------------------------------------------------------------

@runtime_checkable
class PrivacyMaskShape(Protocol):
    """Structural type for any privacy-mask shape.

    A shape provides the two pieces of information needed by the unified
    apply pipeline:
        - `bounding_box()` returns the axis-aligned bounding box of the
          shape in source pixel space, as `(x, y, w, h)`. Pre-clamp.
        - `alpha_mask(w, h)` returns a Pillow `"L"` mode image of size
          `(w, h)` whose pixels are 255 inside the shape and 0 outside.
          Coordinate origin is bounding-box-relative, i.e. `(0, 0)` of
          the alpha mask corresponds to `(x, y)` of the bounding box.

    All concrete shape types — `PrivacyMaskRegion`, `PrivacyMaskCircle`,
    `PrivacyMaskPolygon` — implement this Protocol. Mode and mode-specific
    parameter fields (`mode`, `blur_radius`, `solid_color`, `pixelate_factor`)
    are also part of every shape's surface, accessed by name in
    `apply_privacy_masks`.

    Marked `@runtime_checkable` so `isinstance(x, PrivacyMaskShape)` works,
    though the apply pipeline never relies on isinstance — it just calls
    the Protocol methods.
    """

    mode: PrivacyMaskMode

    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (x, y, w, h) — pre-clamp source-pixel bounds of the shape."""
        ...

    def alpha_mask(self, w: int, h: int) -> object:
        """Return a Pillow 'L' mode image (w×h) with shape interior = 255."""
        ...


# ---------------------------------------------------------------------------
# PrivacyMaskRegion (rectangle — v0.5.3 base case)
# ---------------------------------------------------------------------------


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
        _validate_shared_shape_fields(
            "PrivacyMaskRegion",
            self.mode, self.blur_radius, self.solid_color, self.pixelate_factor,
        )

    # ----- PrivacyMaskShape Protocol implementation (v0.5.4) -----

    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (x, y, w, h) — the rectangle is its own bounding box."""
        return (self.x, self.y, self.w, self.h)

    def alpha_mask(self, w: int, h: int) -> object:
        """Return an L-mode image fully opaque — rectangle covers entire bbox.

        For the rectangle case, the bounding box equals the shape, so the
        alpha mask is a uniform 255 (fully opaque). Composite reduces to
        identity replacement of the bbox region — exactly matching v0.5.3
        behaviour.
        """
        from PIL import Image
        return Image.new("L", (w, h), 255)


# ---------------------------------------------------------------------------
# PrivacyMaskCircle (v0.5.4)
# ---------------------------------------------------------------------------


@dataclass
class PrivacyMaskCircle:
    """A circular privacy mask region (v0.5.4 *Margblæja*).

    Defined by centre `(cx, cy)` and `radius` in source pixel space.

    Construction-time validation (raises `ValueError`):
        - `cx`, `cy` non-negative ints
        - `radius` positive int (>= 1)
        - `mode` in {"blur", "solid", "pixelate"}
        - `solid_color` 3-tuple of ints in [0, 255]
        - `blur_radius` positive int or None
        - `pixelate_factor` int >= 2 or None
    """

    cx: int
    cy: int
    radius: int

    mode: PrivacyMaskMode = "blur"
    blur_radius: Optional[int] = None
    solid_color: Tuple[int, int, int] = (0, 0, 0)
    pixelate_factor: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.cx, int) or self.cx < 0:
            raise ValueError(
                f"PrivacyMaskCircle.cx must be a non-negative integer, got {self.cx!r}"
            )
        if not isinstance(self.cy, int) or self.cy < 0:
            raise ValueError(
                f"PrivacyMaskCircle.cy must be a non-negative integer, got {self.cy!r}"
            )
        if not isinstance(self.radius, int) or self.radius < 1:
            raise ValueError(
                f"PrivacyMaskCircle.radius must be a positive integer (>= 1), "
                f"got {self.radius!r}"
            )
        _validate_shared_shape_fields(
            "PrivacyMaskCircle",
            self.mode, self.blur_radius, self.solid_color, self.pixelate_factor,
        )

    # ----- PrivacyMaskShape Protocol implementation -----

    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (cx-radius, cy-radius, 2*radius, 2*radius)."""
        return (
            self.cx - self.radius,
            self.cy - self.radius,
            2 * self.radius,
            2 * self.radius,
        )

    def alpha_mask(self, w: int, h: int) -> object:
        """Draw a filled disc of size (w, h) — fills the bounding box exactly."""
        from PIL import Image, ImageDraw
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        # Pillow's ellipse with the bounding box of the bbox produces the
        # circle (since w == h == 2*radius for a non-clamped circle).
        draw.ellipse((0, 0, w - 1, h - 1), fill=255)
        return mask


# ---------------------------------------------------------------------------
# PrivacyMaskPolygon (v0.5.4)
# ---------------------------------------------------------------------------


@dataclass
class PrivacyMaskPolygon:
    """A polygonal privacy mask region (v0.5.4 *Margblæja*).

    Defined by an ordered list of `(x, y)` vertex tuples in source pixel space,
    with `len(points) >= 3`. Pillow's `ImageDraw.polygon` fills the interior;
    the polygon is closed automatically by Pillow (last vertex connects to
    first).

    Construction-time validation (raises `ValueError`):
        - `len(points) >= 3`
        - each point a 2-tuple of non-negative ints
        - `mode` in {"blur", "solid", "pixelate"}
        - `solid_color` 3-tuple of ints in [0, 255]
        - `blur_radius` positive int or None
        - `pixelate_factor` int >= 2 or None

    A degenerate polygon (co-linear vertices or coincident vertices) is a valid
    construction. Pillow rasterises what it can — a thin line for collinear
    points, a single pixel for coincident vertices. apply does not raise; the
    mask covers Pillow's output exactly (P-8).
    """

    points: list

    mode: PrivacyMaskMode = "blur"
    blur_radius: Optional[int] = None
    solid_color: Tuple[int, int, int] = (0, 0, 0)
    pixelate_factor: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.points, list) or len(self.points) < 3:
            raise ValueError(
                f"PrivacyMaskPolygon.points must be a list of >= 3 (x, y) "
                f"tuples, got {self.points!r}"
            )
        for i, p in enumerate(self.points):
            if not (
                isinstance(p, tuple)
                and len(p) == 2
                and isinstance(p[0], int) and isinstance(p[1], int)
                and p[0] >= 0 and p[1] >= 0
            ):
                raise ValueError(
                    f"PrivacyMaskPolygon.points[{i}] must be a 2-tuple of "
                    f"non-negative ints, got {p!r}"
                )
        _validate_shared_shape_fields(
            "PrivacyMaskPolygon",
            self.mode, self.blur_radius, self.solid_color, self.pixelate_factor,
        )

    # ----- PrivacyMaskShape Protocol implementation -----

    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return the smallest axis-aligned rectangle containing all vertices.

        Returns (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1). The
        +1 includes the max-edge pixel so that `alpha_mask(w, h)` aligns
        with `Image.crop((min_x, min_y, max_x+1, max_y+1))`.
        """
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        min_x = min(xs)
        min_y = min(ys)
        max_x = max(xs)
        max_y = max(ys)
        return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

    def alpha_mask(self, w: int, h: int) -> object:
        """Draw the filled polygon onto an `(w, h)` L mask in bbox-local coords."""
        from PIL import Image, ImageDraw
        # Translate vertices into bounding-box-local coordinates.
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        min_x = min(xs)
        min_y = min(ys)
        local_pts = [(p[0] - min_x, p[1] - min_y) for p in self.points]
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon(local_pts, fill=255)
        return mask


# ---------------------------------------------------------------------------
# PrivacyMaskRoundedRectangle (v0.5.5 — Mjúkblæja)
# ---------------------------------------------------------------------------


@dataclass
class PrivacyMaskRoundedRectangle:
    """A rounded-rectangle privacy mask region (v0.5.5 *Mjúkblæja*).

    Defined by axis-aligned `(x, y, w, h)` plus `corner_radius` — a single
    integer applied to all four corners. The dominant modern UI primitive:
    chat windows, code panels, dialog boxes, browser tabs.

    Construction-time validation (raises `ValueError`):
        - `x`, `y` non-negative ints
        - `w`, `h` positive ints (>= 1)
        - `corner_radius` non-negative int (`0` is valid: degenerate to a
          sharp rectangle)
        - `mode`, `solid_color`, `blur_radius`, `pixelate_factor` validated
          by `_validate_shared_shape_fields`

    Apply-time corner-radius clamp:
        If `corner_radius > min(w, h) // 2`, the effective radius is clamped
        to `min(w, h) // 2`. The operator is not warned; the rendered shape
        is the largest valid rounded rectangle. This honours operator intent
        (cover a soft-cornered region) without erroring on the impossible
        case of overlapping corner arcs.
    """

    x: int
    y: int
    w: int
    h: int
    corner_radius: int

    mode: PrivacyMaskMode = "blur"
    blur_radius: Optional[int] = None
    solid_color: Tuple[int, int, int] = (0, 0, 0)
    pixelate_factor: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.x, int) or self.x < 0:
            raise ValueError(
                f"PrivacyMaskRoundedRectangle.x must be a non-negative integer, "
                f"got {self.x!r}"
            )
        if not isinstance(self.y, int) or self.y < 0:
            raise ValueError(
                f"PrivacyMaskRoundedRectangle.y must be a non-negative integer, "
                f"got {self.y!r}"
            )
        if not isinstance(self.w, int) or self.w < 1:
            raise ValueError(
                f"PrivacyMaskRoundedRectangle.w must be a positive integer (>= 1), "
                f"got {self.w!r}"
            )
        if not isinstance(self.h, int) or self.h < 1:
            raise ValueError(
                f"PrivacyMaskRoundedRectangle.h must be a positive integer (>= 1), "
                f"got {self.h!r}"
            )
        if not isinstance(self.corner_radius, int) or self.corner_radius < 0:
            raise ValueError(
                f"PrivacyMaskRoundedRectangle.corner_radius must be a non-negative "
                f"integer, got {self.corner_radius!r}"
            )
        _validate_shared_shape_fields(
            "PrivacyMaskRoundedRectangle",
            self.mode, self.blur_radius, self.solid_color, self.pixelate_factor,
        )

    # ----- PrivacyMaskShape Protocol implementation -----

    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (x, y, w, h) — the rounded rect's curves are inside the bbox."""
        return (self.x, self.y, self.w, self.h)

    def alpha_mask(self, w: int, h: int) -> object:
        """Draw the rounded rectangle as the alpha mask. Corner radius clamped."""
        from PIL import Image, ImageDraw
        # Apply-time clamp: corner_radius cannot exceed half the shorter side.
        # min(w, h) // 2 is the largest valid corner_radius for which the four
        # corner arcs do not overlap. corner_radius=0 produces a sharp rect.
        eff_radius = min(self.corner_radius, min(w, h) // 2)
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        # Pillow rounded_rectangle: (xy, radius, fill).
        # xy is (x0, y0, x1, y1) inclusive — so we use (0, 0, w-1, h-1).
        draw.rounded_rectangle(
            (0, 0, w - 1, h - 1),
            radius=eff_radius,
            fill=255,
        )
        return mask


# ---------------------------------------------------------------------------
# PrivacyMaskEllipse (v0.5.5 — Mjúkblæja)
# ---------------------------------------------------------------------------


@dataclass
class PrivacyMaskEllipse:
    """An axis-aligned ellipse privacy mask region (v0.5.5 *Mjúkblæja*).

    Defined by centre `(cx, cy)` and two distinct radii `(rx, ry)`. Strict
    generalisation of `PrivacyMaskCircle`: the degenerate case `rx == ry`
    is a valid ellipse and renders identically to the equivalent circle.
    The two are independent dataclasses, not in a subtype relationship —
    operator chooses the type that best names their intent.

    Construction-time validation (raises `ValueError`):
        - `cx`, `cy` non-negative ints
        - `rx`, `ry` positive ints (>= 1)
        - `mode`, `solid_color`, `blur_radius`, `pixelate_factor` validated
          by `_validate_shared_shape_fields`
    """

    cx: int
    cy: int
    rx: int
    ry: int

    mode: PrivacyMaskMode = "blur"
    blur_radius: Optional[int] = None
    solid_color: Tuple[int, int, int] = (0, 0, 0)
    pixelate_factor: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.cx, int) or self.cx < 0:
            raise ValueError(
                f"PrivacyMaskEllipse.cx must be a non-negative integer, "
                f"got {self.cx!r}"
            )
        if not isinstance(self.cy, int) or self.cy < 0:
            raise ValueError(
                f"PrivacyMaskEllipse.cy must be a non-negative integer, "
                f"got {self.cy!r}"
            )
        if not isinstance(self.rx, int) or self.rx < 1:
            raise ValueError(
                f"PrivacyMaskEllipse.rx must be a positive integer (>= 1), "
                f"got {self.rx!r}"
            )
        if not isinstance(self.ry, int) or self.ry < 1:
            raise ValueError(
                f"PrivacyMaskEllipse.ry must be a positive integer (>= 1), "
                f"got {self.ry!r}"
            )
        _validate_shared_shape_fields(
            "PrivacyMaskEllipse",
            self.mode, self.blur_radius, self.solid_color, self.pixelate_factor,
        )

    # ----- PrivacyMaskShape Protocol implementation -----

    def bounding_box(self) -> Tuple[int, int, int, int]:
        """Return (cx-rx, cy-ry, 2*rx, 2*ry) — axis-aligned ellipse bbox."""
        return (
            self.cx - self.rx,
            self.cy - self.ry,
            2 * self.rx,
            2 * self.ry,
        )

    def alpha_mask(self, w: int, h: int) -> object:
        """Draw a filled ellipse of size (w, h). Pillow's ellipse on a non-equal-
        side bounding box produces a true ellipse (rx != ry case).
        """
        from PIL import Image, ImageDraw
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, w - 1, h - 1), fill=255)
        return mask


# ---------------------------------------------------------------------------
# apply_privacy_masks
# ---------------------------------------------------------------------------

def apply_privacy_masks(
    image: object,
    masks: list,  # list[PrivacyMaskShape] — Protocol-typed
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

    for shape in masks:
        # Get pre-clamp bounding box from the shape (Protocol method).
        bx, by, bw, bh = shape.bounding_box()

        # Clamp bounding box to image bounds. Returns (x, y, w, h) of effective
        # region. If w_eff or h_eff is 0, region is wholly off-frame.
        x_eff = max(0, min(bx, w_img))
        y_eff = max(0, min(by, h_img))
        x_end = max(x_eff, min(bx + bw, w_img))
        y_end = max(y_eff, min(by + bh, h_img))
        w_eff = x_end - x_eff
        h_eff = y_end - y_eff

        if w_eff <= 0 or h_eff <= 0:
            _maybe_log_clamp_once(
                log, _state,
                "wholly off-frame", shape, bx, by, bw, bh, w_img, h_img,
            )
            continue

        clamped = (w_eff != bw) or (h_eff != bh) or (x_eff != bx or y_eff != by)
        if clamped:
            _maybe_log_clamp_once(
                log, _state,
                "partially off-frame (clamped)", shape, bx, by, bw, bh, w_img, h_img,
            )

        try:
            _apply_one_shape(img, shape, x_eff, y_eff, w_eff, h_eff, log, _state)
        except Exception as exc:
            # Fail-safe: if any Pillow primitive raises during the mask
            # application, fall back to SOLID-fill of the bounding box so
            # the unmasked region never propagates downstream.
            log.warning(
                "Margblæja: mask application raised for shape %s "
                "(bbox x=%d y=%d w=%d h=%d, mode=%r): %s — falling back to SOLID",
                type(shape).__name__, bx, by, bw, bh, shape.mode, exc,
            )
            try:
                draw = ImageDraw.Draw(img)
                draw.rectangle(
                    (x_eff, y_eff, x_eff + w_eff - 1, y_eff + h_eff - 1),
                    fill=shape.solid_color,
                )
            except Exception as exc2:
                # If even SOLID-fill fails, the whole encoder fails — but
                # we never let an unmasked region pass downstream silently.
                raise RuntimeError(
                    f"Margblæja: SOLID-fill fallback failed for shape "
                    f"{type(shape).__name__} bbox=({bx}, {by}, {bw}, {bh}): {exc2}"
                ) from exc2

    return img


def _maybe_log_clamp_once(
    log: logging.Logger,
    state: Optional[dict],
    kind: str,
    shape,  # PrivacyMaskShape
    bx: int,
    by: int,
    bw: int,
    bh: int,
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
        "Margblæja: privacy mask shape %s %s on %dx%d image: "
        "bbox=(%d, %d, %d, %d), mode=%r. Subsequent clamp events suppressed.",
        type(shape).__name__, kind, w_img, h_img,
        bx, by, bw, bh, shape.mode,
    )
    if state is not None:
        state["clamp_logged"] = True


def _apply_one_shape(
    img: object,
    shape,  # PrivacyMaskShape
    x: int,
    y: int,
    w: int,
    h: int,
    log: logging.Logger,
    state: Optional[dict],
) -> None:
    """Apply a single mask shape in place on the given PIL.Image.

    Uses the post-clamp bounding-box coordinates (x, y, w, h). The mode is
    applied to the bbox crop; the alpha mask carves out the shape from the
    modified crop and composites it over the original.

    Pipeline: crop → apply mode to crop → composite via shape.alpha_mask → paste.
    """
    from PIL import Image, ImageDraw, ImageFilter

    image: "Image.Image" = img  # type: ignore[assignment]

    # Extract the bounding-box crop. This is the canvas the mode is applied
    # to; the alpha mask then carves out the shape's interior.
    crop_original = image.crop((x, y, x + w, y + h))

    # Apply the requested mode to the bbox crop. The crop's full rectangle
    # is treated as the modification surface; the shape selection happens at
    # composite time.
    if shape.mode == "solid":
        modified = Image.new("RGB", (w, h), shape.solid_color)
    elif shape.mode == "blur":
        radius = (
            shape.blur_radius
            if shape.blur_radius is not None
            else max(8, min(w, h) // 8)
        )
        modified = crop_original.filter(ImageFilter.GaussianBlur(radius=radius))
    elif shape.mode == "pixelate":
        factor = (
            shape.pixelate_factor
            if shape.pixelate_factor is not None
            else max(8, min(w, h) // 12)
        )
        small_w = max(1, w // factor)
        small_h = max(1, h // factor)
        small = crop_original.resize((small_w, small_h), Image.Resampling.NEAREST)
        modified = small.resize((w, h), Image.Resampling.NEAREST)
    else:
        # Should be unreachable — mode is validated at construction time.
        raise ValueError(f"Margblæja: unknown mask mode {shape.mode!r}")

    # Get the shape's alpha mask in bbox-local coordinates. The mask is "L"
    # mode: 255 inside the shape, 0 outside. For PrivacyMaskRegion (rectangle),
    # this is fully opaque white — composite reduces to identity replacement
    # (matching the v0.5.3 behaviour exactly).
    alpha = shape.alpha_mask(w, h)

    # P-8 detection: if the alpha mask has zero non-zero pixels, the shape is
    # degenerate (e.g. polygon with co-linear vertices). Skip composite and log.
    # Pillow's getbbox() returns None when the image is entirely zero.
    if alpha.getbbox() is None:
        _maybe_log_clamp_once(
            log, state,
            "degenerate (empty alpha mask)", shape, x, y, w, h, w, h,
        )
        return

    # Composite: pixels where alpha == 255 take from `modified`; pixels where
    # alpha == 0 take from `crop_original`. This is P-7 — boundary preserved.
    composited = Image.composite(modified, crop_original, alpha)

    # Paste back at the clamped coordinates.
    image.paste(composited, (x, y))
