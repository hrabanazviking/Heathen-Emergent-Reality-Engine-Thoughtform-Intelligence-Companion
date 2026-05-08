"""
Frame encoder — L3 Sjón (Vision).

Converts raw captured pixel bytes into an inline base64 PNG data URL
suitable for injection into an OpenAI /v1/chat/completions message as:

    {"type": "image_url", "image_url": {"url": "data:image/png;base64,<bytes>"}}

This format is sealed by audit C-Q-C3 (AUDIT_v0.0_INITIAL_DOC_SET.md).
No URL references — frames are always inline. This avoids any file-server
dependency and keeps frames within the Tailscale trust boundary.

The FrameEncoder class handles:
    - BGRA -> RGB conversion (mss returns BGRA; PNG expects RGB or RGBA)
    - Proportional downscale to max_width x max_height if the frame is larger
    - Optional crop (applied before resize when both are specified)
    - PNG encoding with compression level 6 (good ratio / fast encode)
    - Base64 encoding to a data URL string

Pillow is required (in the [vision] extra). All public methods are
NotImplementedError stubs — Forge implements the full Pillow integration.

Ref: docs/architecture/LAYER_INTERFACES.md §L3 Sjón.
    docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md C-Q-C3 (RESOLVED).
"""

from __future__ import annotations

import base64
import io
import logging
from typing import TYPE_CHECKING

from heretic.sjon.errors import FrameEncodingError

if TYPE_CHECKING:
    # Pillow is an optional dep; only used in type annotations here so the
    # module remains importable even when Pillow is not installed.
    # Forge: import PIL.Image directly in the method bodies, wrapped in try/except.
    pass


# ---------------------------------------------------------------------------
# FrameEncoder
# ---------------------------------------------------------------------------

class FrameEncoder:
    """Encode raw captured pixel bytes to an inline base64 PNG data URL.

    Typical usage (after Forge implements the stubs):

        encoder = FrameEncoder(max_width=1280, max_height=720, logger=log)
        data_url = encoder.encode_to_data_url(raw_bgra, width, height)
        # data_url = "data:image/png;base64,iVBORw0K..."

    All methods are NotImplementedError stubs in this scaffold.

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
            1. Construct a PIL.Image from frame_bytes using the given dimensions
               and pixel_format (e.g. 'BGRA' for mss output).
            2. Convert to 'RGB' (discard alpha channel — PNG alpha is not needed
               for vision model injection and reduces file size).
            3. Call resize_if_needed() to downscale if larger than max dimensions.
            4. Save to an in-memory BytesIO buffer as PNG with compress_level=6.
            5. Return the raw PNG bytes.

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
        raise NotImplementedError(
            "FrameEncoder.encode(): "
            "1. Try: from PIL import Image. "
            "2. img = Image.frombuffer(pixel_format, (width, height), frame_bytes). "
            "   If pixel_format is 'BGRA', convert to RGB first: "
            "   img = img.convert('RGBA'); r, g, b, a = img.split(); img = Image.merge('RGB', (b, g, r)). "
            "   Actually for BGRA use: img_rgba = Image.frombuffer('RGBA', (w,h), raw); "
            "   b, g, r, a = img_rgba.split(); img = Image.merge('RGB', (r, g, b)). "
            "3. img = self.resize_if_needed(img). "
            "4. buf = io.BytesIO(); img.save(buf, format='PNG', compress_level=6); return buf.getvalue(). "
            "5. Wrap ImportError and PIL exceptions -> FrameEncodingError."
        )

    def resize_if_needed(self, image: object) -> object:
        """Downscale a PIL.Image if it exceeds max_width or max_height.

        Proportional scaling is preserved — the image is scaled by the minimum
        ratio needed so that neither dimension exceeds the configured maximum.
        If the image fits within max_width x max_height it is returned unchanged
        (no copy, no re-encode).

        Args:
            image: A PIL.Image object. Type annotated as object here because
                Pillow is an optional dep and PIL.Image is not importable at
                module load time without it.

        Returns:
            A PIL.Image object, possibly downscaled in-place.

        Raises:
            FrameEncodingError: if Pillow is not installed or resizing fails.
        """
        raise NotImplementedError(
            "FrameEncoder.resize_if_needed(): "
            "from PIL import Image. "
            "w, h = image.size. "
            "ratio = min(self._max_width / w, self._max_height / h, 1.0). "
            "if ratio >= 1.0: return image (no resize needed). "
            "new_w = int(w * ratio); new_h = int(h * ratio). "
            "return image.resize((new_w, new_h), Image.LANCZOS). "
            "Wrap PIL exceptions -> FrameEncodingError."
        )

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
        raise NotImplementedError(
            "FrameEncoder.to_data_url(): "
            "encoded = base64.b64encode(png_bytes).decode('ascii'). "
            "return f'data:image/png;base64,{encoded}'. "
            "(base64 is stdlib — no optional dep needed here.)"
        )

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
        raise NotImplementedError(
            "FrameEncoder.encode_to_data_url(): "
            "png = self.encode(frame_bytes, width, height, pixel_format). "
            "return self.to_data_url(png)."
        )
