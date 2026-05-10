"""
Frame encoder — L3 Sjón (Vision).

Converts raw captured pixel bytes into an inline base64 PNG data URL
suitable for injection into an OpenAI /v1/chat/completions message as:

    {"type": "image_url", "image_url": {"url": "data:image/png;base64,<bytes>"}}

This format is sealed by audit C-Q-C3 (AUDIT_v0.0_INITIAL_DOC_SET.md).
No URL references — frames are always inline. This avoids any file-server
dependency and keeps frames within the Tailscale trust boundary.

The FrameEncoder class handles:
    - BGRA -> RGB conversion via Pillow's BGRX raw decoder mode.
      mss returns BGRA (Blue, Green, Red, Alpha in memory order).
      Pillow's "BGRX" raw decoder reads BGR then discards the 4th byte —
      exactly matching BGRA with alpha ignored. This is the cleanest path
      because it avoids splitting and re-merging channels.
    - Proportional downscale to max_width x max_height if the frame is larger.
    - PNG encoding with compression level 6 (good ratio / fast encode).
    - Base64 encoding to a data URL string.

Channel order decision (documented here for the Auditor):
    mss stores pixels as BGRA in memory. PIL.Image.frombytes("RGBA", ...) would
    interpret this as RGBA, giving wrong colours (B and R channels swapped).
    The correct approach is PIL.Image.frombytes("RGB", (w,h), raw, "raw", "BGRX")
    which uses Pillow's raw decoder in BGRX mode — reads B, G, R, skips X.
    This produces a correct RGB image in one step with no channel splitting.
    Cartographer flagged this in §4.10 note; BGRX path chosen here.

Pillow is required (in the [vision] extra).

Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
    docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md C-Q-C3 (RESOLVED).
"""

from __future__ import annotations

import base64
import io
import logging

from heretic.sjon.errors import FrameEncodingError


# ---------------------------------------------------------------------------
# FrameEncoder
# ---------------------------------------------------------------------------

class FrameEncoder:
    """Encode raw captured pixel bytes to an inline base64 PNG data URL.

    Typical usage:

        encoder = FrameEncoder(max_width=1280, max_height=720, logger=log)
        data_url = encoder.encode_to_data_url(raw_bgra, width, height)
        # data_url = "data:image/png;base64,iVBORw0K..."

    Ref: docs/architecture/AGENT_AGNOSTIC_PROTOCOL.md §8 item 7 (Bifrost Covenant).
    """

    def __init__(
        self,
        max_width: int = 1280,
        max_height: int = 720,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialise FrameEncoder.

        Args:
            max_width: Maximum output width in pixels. Frames wider than this
                are scaled down proportionally.
            max_height: Maximum output height in pixels. Frames taller than
                this are scaled down proportionally.
            logger: Optional logger for encoding diagnostics.
        """
        self._max_width = max_width
        self._max_height = max_height
        self._logger = logger or logging.getLogger(__name__)
        # v0.5.3 Blæja — per-encoder state dict consumed by apply_privacy_masks
        # to throttle clamp/no-op debug logs to one per encoder lifetime.
        self._privacy_state: dict = {}

    def encode(
        self,
        frame_bytes: bytes,
        width: int,
        height: int,
        pixel_format: str = "BGRA",
        max_width_override: int | None = None,
        max_height_override: int | None = None,
        privacy_masks: list | None = None,
    ) -> bytes:
        """Convert raw pixel bytes to compressed PNG bytes.

        Steps:
            1. Construct a PIL.Image from frame_bytes using Pillow's raw decoder.
               For BGRA (mss output), use "BGRX" raw mode which reads B,G,R and
               discards the 4th byte — cleanest channel-order fix in one pass.
               For other formats, use frombuffer directly.
            2. Resize proportionally if larger than the effective max dimensions.
               max_width_override / max_height_override, when provided, replace
               self._max_width / self._max_height for this call only.
               This is used by the Sjón oversize-retry path to force a lower
               resolution cap without constructing a second encoder instance.
            3. Save to an in-memory BytesIO buffer as PNG with compress_level=6.
            4. Return the raw PNG bytes.

        Args:
            frame_bytes: Raw pixel data as bytes. Format matches pixel_format.
            width: Frame width in pixels (must match the data in frame_bytes).
            height: Frame height in pixels (must match the data in frame_bytes).
            pixel_format: PIL mode string for the raw bytes. Default 'BGRA'
                (mss raw output). Other values: 'RGB', 'RGBA'.
            max_width_override: When provided, overrides self._max_width for this
                call. Useful for the oversize-retry path which passes half_w.
            max_height_override: When provided, overrides self._max_height for this
                call. Useful for the oversize-retry path which passes half_h.

        Returns:
            Compressed PNG bytes.

        Raises:
            FrameEncodingError: if Pillow is not installed or encoding fails.
        """
        # Resolve effective max dimensions — override wins if supplied.
        effective_max_w = max_width_override if max_width_override is not None else self._max_width
        effective_max_h = max_height_override if max_height_override is not None else self._max_height

        try:
            from PIL import Image
        except ImportError as exc:
            raise FrameEncodingError(
                "Pillow is required for frame encoding. "
                "Install heretic[vision] to enable screen capture."
            ) from exc

        try:
            if pixel_format == "BGRA":
                # BGRX raw decoder: reads B, G, R, skips X (= the alpha byte).
                # This produces a correct RGB image in one step without channel splitting.
                # 'BGRX' is Pillow's built-in raw decoder mode — see Pillow docs §Decoders.
                img = Image.frombytes("RGB", (width, height), frame_bytes, "raw", "BGRX")
            elif pixel_format == "RGBA":
                img = Image.frombytes("RGBA", (width, height), frame_bytes).convert("RGB")
            elif pixel_format == "RGB":
                img = Image.frombytes("RGB", (width, height), frame_bytes)
            else:
                # Generic fallback: let Pillow try to interpret the format.
                img = Image.frombuffer(pixel_format, (width, height), frame_bytes)
                if img.mode != "RGB":
                    img = img.convert("RGB")

            # v0.5.3 Blæja — privacy masks applied here, AFTER decode and
            # BEFORE resize / encode / save. There is no codepath in which
            # an unmasked frame can reach the rest of the pipeline.
            if privacy_masks:
                from heretic.sjon.privacy import apply_privacy_masks
                img = apply_privacy_masks(
                    img, privacy_masks,
                    log=self._logger,
                    _state=self._privacy_state,
                )

            img = self._resize_to_bounds(img, effective_max_w, effective_max_h)

            buf = io.BytesIO()
            img.save(buf, format="PNG", compress_level=6)
            return buf.getvalue()

        except FrameEncodingError:
            raise  # re-raise typed errors
        except Exception as exc:
            raise FrameEncodingError(
                f"Frame encoding failed: {exc}"
            ) from exc

    def _resize_to_bounds(self, image: object, max_w: int, max_h: int) -> object:
        """Internal: downscale a PIL.Image if it exceeds the given bounds.

        Parametric version used by encode() so that both the normal path
        (self._max_width / self._max_height) and the oversize-retry path
        (half_w / half_h override) share a single resize implementation.

        Args:
            image: A PIL.Image object.
            max_w: Maximum allowed width in pixels.
            max_h: Maximum allowed height in pixels.

        Returns:
            A PIL.Image object, possibly downscaled in-place.

        Raises:
            FrameEncodingError: if resizing fails.
        """
        try:
            from PIL import Image
            # Type assertion: callers always pass PIL.Image here.
            img: Image.Image = image  # type: ignore[assignment]
            w, h = img.size
            if w <= max_w and h <= max_h:
                # Within bounds — return as-is, no copy needed.
                return img
            # thumbnail() modifies in-place and preserves aspect ratio.
            # It scales to fit within the given box — exactly what we need.
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            return img
        except FrameEncodingError:
            raise
        except Exception as exc:
            raise FrameEncodingError(
                f"Frame resize failed: {exc}"
            ) from exc

    def resize_if_needed(self, image: object) -> object:
        """Downscale a PIL.Image if it exceeds max_width or max_height.

        Proportional scaling is preserved — the image is scaled by the minimum
        ratio needed so that neither dimension exceeds the configured maximum.
        If the image fits within max_width x max_height it is returned unchanged
        (no copy, no re-encode).

        Uses Image.thumbnail() which modifies in-place and preserves aspect ratio.

        This public method uses the instance's configured max_width/max_height.
        For a parametric version (used by the oversize-retry path), see
        _resize_to_bounds().

        Args:
            image: A PIL.Image object. Type annotated as object here because
                Pillow is an optional dep and PIL.Image is not importable at
                module load time without it.

        Returns:
            A PIL.Image object, possibly downscaled in-place.

        Raises:
            FrameEncodingError: if Pillow is not installed or resizing fails.
        """
        return self._resize_to_bounds(image, self._max_width, self._max_height)

    def to_data_url(self, png_bytes: bytes) -> str:
        """Encode PNG bytes as an inline base64 data URL string.

        Produces the exact format required by the OpenAI vision API:
            data:image/png;base64,<base64_encoded_png>

        This format is sealed by audit C-Q-C3 (AUDIT_v0.0_INITIAL_DOC_SET.md).

        Args:
            png_bytes: Compressed PNG bytes (output of encode()).

        Returns:
            A string of the form 'data:image/png;base64,<encoded>'.
            The returned string is safe to embed directly in a JSON content block.
        """
        # base64.standard_b64encode uses the standard alphabet (not URL-safe).
        # This is what the OpenAI API expects for inline image data.
        encoded = base64.standard_b64encode(png_bytes).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def encode_to_data_url(
        self,
        frame_bytes: bytes,
        width: int,
        height: int,
        pixel_format: str = "BGRA",
        privacy_masks: list | None = None,
    ) -> str:
        """Convenience method: encode raw bytes directly to a data URL string.

        Equivalent to:
            self.to_data_url(self.encode(frame_bytes, width, height, pixel_format,
                                         privacy_masks=privacy_masks))

        Args:
            frame_bytes: Raw pixel data.
            width: Frame width in pixels.
            height: Frame height in pixels.
            pixel_format: PIL mode string. Default 'BGRA'.
            privacy_masks: Optional list of PrivacyMaskRegion (v0.5.3 Blæja).
                When provided and non-empty, masks are applied after decode
                and before resize / encode / save — i.e., the unmasked frame
                bytes never reach the encoded output or any save path.

        Returns:
            Inline base64 PNG data URL string.

        Raises:
            FrameEncodingError: if any encoding step fails.
        """
        png = self.encode(
            frame_bytes, width, height, pixel_format,
            privacy_masks=privacy_masks,
        )
        return self.to_data_url(png)
