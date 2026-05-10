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


# ---------------------------------------------------------------------------
# v0.7.2 Endurdrykkr — resumable downloads
# ---------------------------------------------------------------------------

def _make_mock_streaming_response(
    body_chunks: list[bytes],
    status_code: int = 200,
):
    """Build a mock httpx response that yields specific chunks in order.

    Differs from the v0.7 helper by allowing explicit chunk control — for
    resume tests we need to assert exactly which bytes are sent (e.g.,
    only the resumed portion).
    """
    async def _aiter_bytes(chunk_size: int = 65536):
        for chunk in body_chunks:
            yield chunk

    mock = MagicMock()
    mock.status_code = status_code
    mock.aiter_bytes = _aiter_bytes
    mock.__aenter__ = AsyncMock(return_value=mock)
    mock.__aexit__ = AsyncMock(return_value=False)
    return mock


def _make_capturing_client(response):
    """A mock httpx.AsyncClient whose .stream() captures the kwargs passed."""
    captured = {"headers": None, "url": None}

    def stream_call(method, url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers", {})
        return response

    mock_client = MagicMock()
    mock_client.stream = MagicMock(side_effect=stream_call)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client, captured


class TestDownloaderResumeDetection:
    """Resume detection: when .heretic_tmp exists, send Range header."""

    @pytest.mark.asyncio
    async def test_resume_detects_existing_tmp_and_sends_range(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        """When .heretic_tmp exists with size N, Range: bytes=N- is sent."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        # Pre-create a partial file with the FIRST half of the content
        partial_size = len(sample_content) // 2
        tmp_file.write_bytes(sample_content[:partial_size])

        # Server returns 206 with the REMAINING bytes
        response = _make_mock_streaming_response(
            body_chunks=[sample_content[partial_size:]],
            status_code=206,
        )
        mock_client, captured = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            await downloader.download(
                source_without_sha256, dest, auto_yes=True
            )

        # Range header was sent with the correct offset
        assert captured["headers"] == {"Range": f"bytes={partial_size}-"}

    @pytest.mark.asyncio
    async def test_resume_206_appends_to_partial_tmp(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        """206 Partial Content → final file equals expected full content."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        partial_size = len(sample_content) // 3
        tmp_file.write_bytes(sample_content[:partial_size])

        response = _make_mock_streaming_response(
            body_chunks=[sample_content[partial_size:]],
            status_code=206,
        )
        mock_client, _ = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            await downloader.download(
                source_without_sha256, dest, auto_yes=True
            )

        assert dest.exists()
        assert dest.read_bytes() == sample_content
        assert not tmp_file.exists()  # atomic rename consumed it

    @pytest.mark.asyncio
    async def test_resume_full_sha256_matches_after_seam(
        self,
        tmp_path: Path,
        sample_content: bytes,
        sample_content_sha256: str,
        source_with_correct_sha256: LibrarySource,
    ) -> None:
        """SHA-256 of resumed file matches the SHA-256 of the full content (M-7)."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        partial_size = len(sample_content) // 4
        tmp_file.write_bytes(sample_content[:partial_size])

        response = _make_mock_streaming_response(
            body_chunks=[sample_content[partial_size:]],
            status_code=206,
        )
        mock_client, _ = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            returned_sha = await downloader.download(
                source_with_correct_sha256, dest, auto_yes=True
            )

        # The hash returned must equal the full-content hash
        assert returned_sha == sample_content_sha256
        # And the file on disk must equal the full content
        assert dest.read_bytes() == sample_content

    @pytest.mark.asyncio
    async def test_no_resume_when_tmp_does_not_exist(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        """No tmp → no Range header, fresh download."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        # No tmp file pre-created
        response = _make_mock_streaming_response(
            body_chunks=[sample_content],
            status_code=200,
        )
        mock_client, captured = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            await downloader.download(
                source_without_sha256, dest, auto_yes=True
            )

        # No Range header
        assert captured["headers"] == {}

    @pytest.mark.asyncio
    async def test_no_resume_when_tmp_is_empty(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        """Empty (zero-byte) tmp file → treated as no tmp, no Range sent."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        tmp_file.write_bytes(b"")  # zero bytes
        assert tmp_file.stat().st_size == 0

        response = _make_mock_streaming_response(
            body_chunks=[sample_content],
            status_code=200,
        )
        mock_client, captured = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            await downloader.download(
                source_without_sha256, dest, auto_yes=True
            )

        assert captured["headers"] == {}
        assert dest.read_bytes() == sample_content


class TestDownloaderResumeStatusDispatch:
    """Resume status dispatch: 206, 200, 416."""

    @pytest.mark.asyncio
    async def test_server_returns_200_on_resume_request_restarts_fresh(
        self,
        tmp_path: Path,
        sample_content: bytes,
        sample_content_sha256: str,
        source_with_correct_sha256: LibrarySource,
    ) -> None:
        """Server ignored Range and returned 200 → reset hasher, full download
        from server (M-9). Final file content matches the full body."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        # Pre-create with WRONG bytes (will be discarded on M-9 restart)
        tmp_file.write_bytes(b"this is wrong partial content")

        # Server returns 200 + the full correct content
        response = _make_mock_streaming_response(
            body_chunks=[sample_content],
            status_code=200,
        )
        mock_client, _ = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            returned_sha = await downloader.download(
                source_with_correct_sha256, dest, auto_yes=True
            )

        # SHA matches the full-content hash (the wrong partial was discarded)
        assert returned_sha == sample_content_sha256
        assert dest.read_bytes() == sample_content

    @pytest.mark.asyncio
    async def test_server_returns_416_deletes_tmp_and_raises(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        """416 Range Not Satisfiable → tmp deleted, LibraryDownloadError raised."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        tmp_file.write_bytes(sample_content[:100])
        assert tmp_file.exists()

        response = _make_mock_streaming_response(
            body_chunks=[],  # 416 has no body relevant to us
            status_code=416,
        )
        mock_client, _ = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(LibraryDownloadError) as exc_info:
                await downloader.download(
                    source_without_sha256, dest, auto_yes=True
                )

        assert "416" in str(exc_info.value) or "satisfiable" in str(exc_info.value).lower()
        # Tmp must be deleted (non-resumable failure)
        assert not tmp_file.exists()
        # Final file must NOT exist (atomic rename never happened)
        assert not dest.exists()


class TestDownloaderResumeIntegrity:
    """Resume preserves integrity guarantees (M-7, M-8)."""

    @pytest.mark.asyncio
    async def test_size_cap_counts_resumed_plus_new_bytes(
        self,
        tmp_path: Path,
    ) -> None:
        """Cumulative size cap applies across resumed + new bytes (M-8 non-resumable).

        Pre-fill .heretic_tmp with bytes near the cap. The server's response
        bytes push us over → IntegrityError + tmp deleted.
        """
        # Source expects 100 bytes; cap = 150 bytes (1.5x).
        source = LibrarySource(
            id="test_source",
            title="Test",
            url="https://example.com/test.txt",
            license="Public Domain",
            expected_size_bytes=100,
            sha256=None,
        )
        dest = tmp_path / "test.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        # Pre-fill with 140 bytes (under 150 cap)
        tmp_file.write_bytes(b"x" * 140)

        # Server returns 206 with another 50 bytes → total 190 > 150 cap
        response = _make_mock_streaming_response(
            body_chunks=[b"y" * 50],
            status_code=206,
        )
        mock_client, _ = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(IntegrityError):
                await downloader.download(source, dest, auto_yes=True)

        # NON-RESUMABLE failure: tmp deleted (M-8)
        assert not tmp_file.exists()
        assert not dest.exists()

    @pytest.mark.asyncio
    async def test_sha256_mismatch_after_resume_deletes_tmp(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_with_wrong_sha256: LibrarySource,
    ) -> None:
        """Final SHA-256 mismatch after resume → tmp deleted (M-8 non-resumable)."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        partial_size = len(sample_content) // 2
        tmp_file.write_bytes(sample_content[:partial_size])

        response = _make_mock_streaming_response(
            body_chunks=[sample_content[partial_size:]],
            status_code=206,
        )
        mock_client, _ = _make_capturing_client(response)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(IntegrityError):
                await downloader.download(
                    source_with_wrong_sha256, dest, auto_yes=True
                )

        # NON-RESUMABLE: tmp deleted because SHA-256 mismatch poisons it
        assert not tmp_file.exists()
        assert not dest.exists()

    @pytest.mark.asyncio
    async def test_network_error_during_resume_preserves_tmp(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        """Transport error during resumed stream → .heretic_tmp PRESERVED (M-8 resumable)."""
        import httpx
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        partial_size = len(sample_content) // 2
        tmp_file.write_bytes(sample_content[:partial_size])
        original_partial_size = tmp_file.stat().st_size

        # Mock a transport error at stream creation time
        mock_client = MagicMock()
        mock_client.stream = MagicMock(
            side_effect=httpx.TransportError("Connection lost mid-resume")
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            downloader = Downloader()
            with pytest.raises(LibraryDownloadError):
                await downloader.download(
                    source_without_sha256, dest, auto_yes=True
                )

        # RESUMABLE failure: tmp file PRESERVED for next call
        assert tmp_file.exists()
        # The bytes are unchanged (partial_size intact for next resume)
        assert tmp_file.stat().st_size == original_partial_size
        assert tmp_file.read_bytes() == sample_content[:partial_size]


class TestDownloaderResumeConsentGate:

    @pytest.mark.asyncio
    async def test_consent_runs_before_resume_detection(
        self,
        tmp_path: Path,
        sample_content: bytes,
        source_without_sha256: LibrarySource,
    ) -> None:
        """Consent refused → tmp file is NOT inspected, NOT modified (M-1)."""
        dest = tmp_path / "prose_edda_brodeur.txt"
        tmp_file = dest.with_suffix(".heretic_tmp")
        tmp_file.write_bytes(sample_content[:100])
        original_bytes = tmp_file.read_bytes()

        # Patch consent to refuse
        with patch(
            "heretic.skilningr.mimisbrunnr.downloader.prompt_for_download",
            side_effect=ConsentRefused("denied"),
        ):
            downloader = Downloader()
            with pytest.raises(ConsentRefused):
                await downloader.download(
                    source_without_sha256, dest, auto_yes=False
                )

        # Tmp file unchanged — consent gate ran first
        assert tmp_file.read_bytes() == original_bytes
