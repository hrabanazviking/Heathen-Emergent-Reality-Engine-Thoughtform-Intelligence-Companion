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

    def encode(
        self,
        frame_bytes: bytes,
        width: int,
        height: int,
        pixel_format: str = "BGRA",
    ) -> bytes:
        """Convert raw pixel bytes to compressed PNG bytes.

        Steps:
            1. Construct a PIL.Image from frame_bytes using Pillow's raw decoder.
               For BGRA (mss output), use "BGRX" raw mode which reads B,G,R and
               discards the 4th byte — cleanest channel-order fix in one pass.
               For other formats, use frombuffer directly.
            2. Resize proportionally if larger than max_width x max_height.
            3. Save to an in-memory BytesIO buffer as PNG with compress_level=6.
            4. Return the raw PNG bytes.

        Args:
            frame_bytes: Raw pixel data as bytes. Format matches pixel_format.
            width: Frame width in pixels (must match the data in frame_bytes).
            height: Frame height in pixels (must match the data in frame_bytes).
            pixel_format: PIL mode string for the raw bytes. Default 'BGRA'
                (mss raw output). Other values: 'RGB', 'RGBA'.

        Returns:
            Compressed PNG bytes.

        Raises:
            FrameEncodingError: if Pillow is not installed or encoding fails.
        """
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

            img = self.resize_if_needed(img)

            buf = io.BytesIO()
            img.save(buf, format="PNG", compress_level=6)
            return buf.getvalue()

        except FrameEncodingError:
            raise  # re-raise typed errors
        except Exception as exc:
            raise FrameEncodingError(
                f"Frame encoding failed: {exc}"
            ) from exc

    def resize_if_needed(self, image: object) -> object:
        """Downscale a PIL.Image if it exceeds max_width or max_height.

        Proportional scaling is preserved — the image is scaled by the minimum
        ratio needed so that neither dimension exceeds the configured maximum.
        If the image fits within max_width x max_height it is returned unchanged
        (no copy, no re-encode).

        Uses Image.thumbnail() which modifies in-place and preserves aspect ratio.

        Args:
            image: A PIL.Image object. Type annotated as object here because
                Pillow is an optional dep and PIL.Image is not importable at
                module load time without it.

        Returns:
            A PIL.Image object, possibly downscaled in-place.

        Raises:
            FrameEncodingError: if Pillow is not installed or resizing fails.
        """
        try:
            from PIL import Image
            # Type assertion: callers always pass PIL.Image here.
            img: Image.Image = image  # type: ignore[assignment]
            w, h = img.size
            if w <= self._max_width and h <= self._max_height:
                # Within bounds — return as-is, no copy needed.
                return img
            # thumbnail() modifies in-place and preserves aspect ratio.
            # It scales to fit within the given box — exactly what we need.
            img.thumbnail((self._max_width, self._max_height), Image.Resampling.LANCZOS)
            return img
        except FrameEncodingError:
            raise
        except Exception as exc:
            raise FrameEncodingError(
                f"Frame resize failed: {exc}"
            ) from exc

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
    ) -> str:
        """Convenience method: encode raw bytes directly to a data URL string.

        Equivalent to: self.to_data_url(self.encode(frame_bytes, width, height, pixel_format))

        Args:
            frame_bytes: Raw pixel data.
            width: Frame width in pixels.
            height: Frame height in pixels.
            pixel_format: PIL mode string. Default 'BGRA'.

        Returns:
            Inline base64 PNG data URL string.

        Raises:
            FrameEncodingError: if any encoding step fails.
        """
        png = self.encode(frame_bytes, width, height, pixel_format)
        return self.to_data_url(png)
