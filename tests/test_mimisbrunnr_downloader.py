"""
Tests for Mímisbrunnr downloader — Downloader class.

All HTTP is mocked via unittest.mock — no real network calls.

Covers:
    - download writes file + returns correct sha256
    - consent gate called before any network activity (ConsentRefused propagates)
    - sha256 mismatch raises IntegrityError and deletes .heretic_tmp
    - sha256 is None (placeholder): accepts download, returns computed hash
    - size cap exceeded raises IntegrityError and deletes .heretic_tmp
    - HTTP non-200 raises LibraryDownloadError
    - network transport error raises LibraryDownloadError
    - atomic rename: final file exists, no .heretic_tmp left after success
    - download with auto_yes=True bypasses consent prompt

Ref: src/heretic/skilningr/mimisbrunnr/downloader.py
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from heretic.skilningr.mimisbrunnr.downloader import Downloader
from heretic.skilningr.mimisbrunnr.errors import (
    ConsentRefused,
    IntegrityError,
    LibraryDownloadError,
)
from heretic.skilningr.mimisbrunnr.manifest import LibrarySource


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_content() -> bytes:
    """Deterministic test content — 500 bytes of repeated ASCII."""
    return b"In the beginning was the Word, and the Word was Odin. " * 10


@pytest.fixture
def sample_content_sha256(sample_content: bytes) -> str:
    return hashlib.sha256(sample_content).hexdigest()


@pytest.fixture
def source_without_sha256(sample_content: bytes) -> LibrarySource:
    """LibrarySource with sha256=None (placeholder — first download)."""
    return LibrarySource(
        id="prose_edda_brodeur",
        title="The Prose Edda",
        url="https://www.gutenberg.org/files/18947/18947-0.txt",
        license="Public Domain",
        expected_size_bytes=len(sample_content),
        sha256=None,
    )


@pytest.fixture
def source_with_correct_sha256(
    sample_content: bytes, sample_content_sha256: str
) -> LibrarySource:
    """LibrarySource with a matching sha256 hash."""
    return LibrarySource(
        id="prose_edda_brodeur",
        title="The Prose Edda",
        url="https://www.gutenberg.org/files/18947/18947-0.txt",
        license="Public Domain",
        expected_size_bytes=len(sample_content),
        sha256=sample_content_sha256,
    )


@pytest.fixture
def source_with_wrong_sha256(sample_content: bytes) -> LibrarySource:
    """LibrarySource with an incorrect sha256 hash."""
    return LibrarySource(
        id="prose_edda_brodeur",
        title="The Prose Edda",
        url="https://www.gutenberg.org/files/18947/18947-0.txt",
        license="Public Domain",
        expected_size_bytes=len(sample_content),
        sha256="0" * 64,  # deliberate wrong hash
    )


def _make_mock_httpx_response(content: bytes, status_code: int = 200):
    """Build an AsyncMock httpx response that yields content in chunks."""
    async def _aiter_bytes(chunk_size: int = 65536):
        # Yield in two chunks to exercise the streaming loop
        half = len(content) // 2 or len(content)
        if content:
            yield content[:half]
            if content[half:]:
                yield content[half:]

    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.aiter_bytes = _aiter_bytes
    # Make it work as an async context manager
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)
    return mock_response


def _make_mock_client(response):
    """Build an AsyncMock httpx.AsyncClient that returns a given response."""
    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ---------------------------------------------------------------------------
# Successful downloads
# ---------------------------------------------------------------------------

class TestDownloaderSuccess:
    """Successful download cases."""

    @pytest.mark.asyncio
    async def test_download_writes_file_content(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(sample_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            returned_sha = await downloader.download(
                source_without_sha256, dest, auto_yes=True
            )

        assert dest.exists()
        assert dest.read_bytes() == sample_content

    @pytest.mark.asyncio
    async def test_download_returns_correct_sha256(
        self,
        tmp_path: Path,
        sample_content: bytes,
        sample_content_sha256: str,
        source_without_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(sample_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            returned_sha = await downloader.download(
                source_without_sha256, dest, auto_yes=True
            )

        assert returned_sha == sample_content_sha256

    @pytest.mark.asyncio
    async def test_download_with_correct_sha256_passes_verification(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_with_correct_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(sample_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            # Must not raise
            await downloader.download(
                source_with_correct_sha256, dest, auto_yes=True
            )

        assert dest.exists()

    @pytest.mark.asyncio
    async def test_no_heretic_tmp_left_after_success(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(sample_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            await downloader.download(
                source_without_sha256, dest, auto_yes=True
            )

        tmp_files = list(tmp_path.glob("*.heretic_tmp"))
        assert tmp_files == [], f"Temp file(s) left on disk: {tmp_files}"

    @pytest.mark.asyncio
    async def test_auto_yes_true_bypasses_consent_prompt(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        """With auto_yes=True, no stdin interaction should occur."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(sample_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            with patch(
                "builtins.input",
                side_effect=AssertionError("input() called unexpectedly")
            ):
                downloader = Downloader()
                await downloader.download(
                    source_without_sha256, dest, auto_yes=True
                )

        assert dest.exists()


# ---------------------------------------------------------------------------
# SHA-256 mismatch
# ---------------------------------------------------------------------------

class TestDownloaderIntegrityError:
    """SHA-256 mismatch must raise IntegrityError and clean up."""

    @pytest.mark.asyncio
    async def test_sha256_mismatch_raises_integrity_error(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_with_wrong_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(sample_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(IntegrityError, match="SHA-256 mismatch"):
                await downloader.download(
                    source_with_wrong_sha256, dest, auto_yes=True
                )

    @pytest.mark.asyncio
    async def test_sha256_mismatch_does_not_write_final_file(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_with_wrong_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(sample_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(IntegrityError):
                await downloader.download(
                    source_with_wrong_sha256, dest, auto_yes=True
                )

        # The final destination file must NOT exist after a mismatch
        assert not dest.exists()

    @pytest.mark.asyncio
    async def test_sha256_mismatch_cleans_up_heretic_tmp(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_with_wrong_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(sample_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(IntegrityError):
                await downloader.download(
                    source_with_wrong_sha256, dest, auto_yes=True
                )

        tmp_files = list(tmp_path.glob("*.heretic_tmp"))
        assert tmp_files == [], f"Temp file(s) left on disk: {tmp_files}"


# ---------------------------------------------------------------------------
# Consent gate
# ---------------------------------------------------------------------------

class TestDownloaderConsentGate:
    """Consent gate must fire before any network activity."""

    @pytest.mark.asyncio
    async def test_consent_refused_propagates_before_network_call(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"

        # Patch consent to raise ConsentRefused immediately
        with patch(
            "heretic.skilningr.mimisbrunnr.downloader.prompt_for_download",
            side_effect=ConsentRefused("Operator declined"),
        ):
            # httpx.AsyncClient must never be called
            with patch(
                "httpx.AsyncClient",
                side_effect=AssertionError("httpx.AsyncClient called after ConsentRefused"),
            ):
                downloader = Downloader()
                with pytest.raises(ConsentRefused):
                    await downloader.download(
                        source_without_sha256, dest, auto_yes=False
                    )

        # No file written
        assert not dest.exists()


# ---------------------------------------------------------------------------
# Size cap enforcement
# ---------------------------------------------------------------------------

class TestDownloaderSizeCap:
    """Size cap must abort oversized downloads before writing the final file."""

    @pytest.mark.asyncio
    async def test_size_cap_raises_integrity_error(
        self,
        tmp_path: Path,
    ) -> None:
        # Source says expected_size is 10 bytes; content is 10000 bytes
        # cap = 10 * 1.5 = 15 bytes — 10000 bytes exceeds cap
        oversized_content = b"X" * 10_000
        source = LibrarySource(
            id="prose_edda_brodeur",
            title="Test",
            url="https://example.com/test.txt",
            license="PD",
            expected_size_bytes=10,
            sha256=None,
        )
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(oversized_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(IntegrityError, match="safety cap"):
                await downloader.download(source, dest, auto_yes=True)

    @pytest.mark.asyncio
    async def test_size_cap_cleans_up_tmp(
        self,
        tmp_path: Path,
    ) -> None:
        oversized_content = b"X" * 10_000
        source = LibrarySource(
            id="prose_edda_brodeur",
            title="Test",
            url="https://example.com/test.txt",
            license="PD",
            expected_size_bytes=10,
            sha256=None,
        )
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(oversized_content)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(IntegrityError):
                await downloader.download(source, dest, auto_yes=True)

        assert not dest.exists()
        tmp_files = list(tmp_path.glob("*.heretic_tmp"))
        assert tmp_files == []


# ---------------------------------------------------------------------------
# HTTP failure modes
# ---------------------------------------------------------------------------

class TestDownloaderHttpFailures:
    """Network-layer failures must produce LibraryDownloadError."""

    @pytest.mark.asyncio
    async def test_http_non_200_raises_library_download_error(
        self,
        tmp_path: Path,
        source_without_sha256: LibrarySource,
    ) -> None:
        dest = tmp_path / "prose_edda_brodeur.txt"
        response = _make_mock_httpx_response(b"Not Found", status_code=404)
        mock_client = _make_mock_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(LibraryDownloadError, match="HTTP 404"):
                await downloader.download(
                    source_without_sha256, dest, auto_yes=True
                )

    @pytest.mark.asyncio
    async def test_transport_error_raises_library_download_error(
        self,
        tmp_path: Path,
        source_without_sha256: LibrarySource,
    ) -> None:
        import httpx

        dest = tmp_path / "prose_edda_brodeur.txt"

        mock_client = MagicMock()
        mock_client.stream = MagicMock(
            side_effect=httpx.TransportError("Connection refused")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(LibraryDownloadError):
                await downloader.download(
                    source_without_sha256, dest, auto_yes=True
                )
