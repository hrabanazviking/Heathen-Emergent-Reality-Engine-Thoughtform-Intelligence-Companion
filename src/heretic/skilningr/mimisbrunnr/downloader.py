"""
Mímisbrunnr downloader — async HTTP download of LibrarySource texts.

Downloader is responsible for fetching a single LibrarySource from its
canonical URL and writing the content to disk atomically. It does NOT
build indexes or verify consent — those responsibilities belong to
consent.py and index.py respectively.

DESIGN CONTRACT:

    - Uses httpx.AsyncClient for async HTTP.
    - Streams the response body to avoid loading multi-MB texts fully
      into memory before writing.
    - Writes to a .heretic_tmp file first, then os.replace() atomically —
      no partial file is ever visible at the final path.
    - Computes SHA-256 incrementally during the streaming write.
    - Safety size cap: if total bytes received exceeds
      source.expected_size_bytes * 1.5, the download is aborted and
      IntegrityError is raised. The .heretic_tmp file is deleted.
    - If LibrarySource.sha256 is not None, compares the computed hash
      against the manifest hash and raises IntegrityError on mismatch
      (deletes .heretic_tmp before raising).
    - If LibrarySource.sha256 is None (placeholder), logs the computed
      hash at INFO level so the operator can record it for the manifest.
    - Raises LibraryDownloadError on any network failure.
    - The consent gate is called FIRST, before any network activity.
      A ConsentRefused exception propagates out immediately.

INVARIANT (Cartographer thread #1):
    LibraryClient and all other modules MUST NOT import httpx.
    Downloader is the ONLY module in this codebase that imports httpx.
    This ensures the offline invariant is structurally enforced: you
    cannot accidentally trigger a network call by importing client.py.

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Downloader
     src/heretic/skilningr/mimisbrunnr/manifest.py (LibrarySource)
     src/heretic/skilningr/mimisbrunnr/errors.py
"""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

import httpx

from heretic.skilningr.mimisbrunnr.consent import prompt_for_download
from heretic.skilningr.mimisbrunnr.errors import IntegrityError, LibraryDownloadError
from heretic.skilningr.mimisbrunnr.manifest import LibrarySource

logger = logging.getLogger(__name__)

# Download chunk size — 64 KB per chunk keeps memory usage low
_CHUNK_SIZE = 65_536

# Safety cap multiplier: abort if downloaded bytes exceed expected * cap
_SIZE_CAP_MULTIPLIER = 1.5


class Downloader:
    """Async downloader for Mímisbrunnr library sources.

    Usage:
        downloader = Downloader()
        sha256 = await downloader.download(source, dest_path)
        # dest_path now contains the downloaded UTF-8 text; sha256 is
        # the hex digest of the written bytes.

    After a successful call, dest_path contains the UTF-8 text of the
    source and the SHA-256 of the file has been verified (if the
    manifest entry carries a non-None sha256).
    """

    async def download(
        self,
        source: LibrarySource,
        dest_path: Path,
        auto_yes: bool = False,
    ) -> str:
        """Download a LibrarySource and write it to dest_path atomically.

        Downloads source.url, writes the content atomically to dest_path,
        computes the SHA-256 of the downloaded bytes, and validates it
        against source.sha256 if that field is not None.

        Args:
            source:    The LibrarySource entry from NORSE_STARTER_PACK.
            dest_path: Absolute path where the downloaded text will be
                       written. Parent directory must already exist.
            auto_yes:  If True, skip the consent prompt (operator pre-approved).
                       Default False (interactive consent required).

        Returns:
            Hex SHA-256 digest string of the successfully downloaded file.

        Raises:
            ConsentRefused: if the operator declines the consent prompt.
            LibraryDownloadError: on any network-level failure (DNS,
                TCP, TLS, HTTP non-200, oversize response).
            IntegrityError: if source.sha256 is set and the downloaded
                file's hash does not match, OR if the response body
                exceeds the safety size cap.
        """
        # -------------------------------------------------------------------
        # 1. Consent gate — MUST be first, before any network activity
        # -------------------------------------------------------------------
        prompt_for_download(source, auto_yes=auto_yes)

        # -------------------------------------------------------------------
        # 2. Compute safety cap (bytes)
        # -------------------------------------------------------------------
        size_cap = int(source.expected_size_bytes * _SIZE_CAP_MULTIPLIER)
        tmp_path = dest_path.with_suffix(".heretic_tmp")

        # -------------------------------------------------------------------
        # 3. Stream download + SHA-256 + size guard
        # -------------------------------------------------------------------
        hasher = hashlib.sha256()
        total_bytes = 0

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                try:
                    async with client.stream("GET", source.url) as response:
                        if response.status_code != 200:
                            raise LibraryDownloadError(
                                f"Download of {source.id!r} failed: "
                                f"HTTP {response.status_code} from {source.url}"
                            )

                        logger.info(
                            "Downloading %r from %s (~%d bytes expected)...",
                            source.id,
                            source.url,
                            source.expected_size_bytes,
                        )

                        try:
                            with tmp_path.open("wb") as fh:
                                async for chunk in response.aiter_bytes(
                                    chunk_size=_CHUNK_SIZE
                                ):
                                    total_bytes += len(chunk)

                                    # Safety size cap: abort on oversize response
                                    if total_bytes > size_cap:
                                        fh.close()
                                        self._cleanup_tmp(tmp_path)
                                        raise IntegrityError(
                                            f"Download of {source.id!r} aborted: "
                                            f"received {total_bytes:,} bytes which "
                                            f"exceeds the safety cap of "
                                            f"{size_cap:,} bytes "
                                            f"({_SIZE_CAP_MULTIPLIER}x expected size "
                                            f"{source.expected_size_bytes:,})."
                                        )

                                    hasher.update(chunk)
                                    fh.write(chunk)

                        except (IntegrityError, LibraryDownloadError):
                            raise

                        except OSError as exc:
                            self._cleanup_tmp(tmp_path)
                            raise LibraryDownloadError(
                                f"Disk write failed for {source.id!r}: {exc}"
                            ) from exc

                except httpx.HTTPStatusError as exc:
                    self._cleanup_tmp(tmp_path)
                    raise LibraryDownloadError(
                        f"HTTP error downloading {source.id!r} from {source.url}: {exc}"
                    ) from exc

                except httpx.TransportError as exc:
                    self._cleanup_tmp(tmp_path)
                    raise LibraryDownloadError(
                        f"Network transport error downloading {source.id!r}: {exc}"
                    ) from exc

                except httpx.TimeoutException as exc:
                    self._cleanup_tmp(tmp_path)
                    raise LibraryDownloadError(
                        f"Download of {source.id!r} timed out: {exc}"
                    ) from exc

                except httpx.RequestError as exc:
                    self._cleanup_tmp(tmp_path)
                    raise LibraryDownloadError(
                        f"Request error downloading {source.id!r}: {exc}"
                    ) from exc

        except (IntegrityError, LibraryDownloadError):
            # Already have typed errors — re-raise without wrapping
            raise

        except Exception as exc:
            self._cleanup_tmp(tmp_path)
            raise LibraryDownloadError(
                f"Unexpected error downloading {source.id!r}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        # -------------------------------------------------------------------
        # 4. SHA-256 verification
        # -------------------------------------------------------------------
        computed_sha256 = hasher.hexdigest()

        if source.sha256 is not None:
            if computed_sha256 != source.sha256:
                self._cleanup_tmp(tmp_path)
                raise IntegrityError(
                    f"SHA-256 mismatch for {source.id!r}. "
                    f"Expected: {source.sha256}. "
                    f"Got:      {computed_sha256}. "
                    "The file at the source URL may have changed. "
                    "The partially-downloaded .heretic_tmp file has been deleted."
                )
        else:
            # Placeholder sha256 — log it so operator can record in manifest
            logger.info(
                "Source %r downloaded successfully. "
                "SHA-256 (record in manifest): %s  bytes: %d",
                source.id,
                computed_sha256,
                total_bytes,
            )

        # -------------------------------------------------------------------
        # 5. Atomic rename — tmp -> final
        # -------------------------------------------------------------------
        try:
            os.replace(str(tmp_path), str(dest_path))
        except OSError as exc:
            self._cleanup_tmp(tmp_path)
            raise LibraryDownloadError(
                f"Atomic rename failed for {source.id!r}: {exc}"
            ) from exc

        logger.info(
            "Source %r written to %s (%d bytes, sha256=%s...)",
            source.id,
            dest_path,
            total_bytes,
            computed_sha256[:12],
        )

        return computed_sha256

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _cleanup_tmp(tmp_path: Path) -> None:
        """Delete the .heretic_tmp file if it exists — failure is non-fatal."""
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning(
                "Could not delete temporary file %s: %s", tmp_path, exc
            )
