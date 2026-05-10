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

ENDURDRYKKR — RESUMABLE DOWNLOADS (v0.7.2):

    - When `.heretic_tmp` exists with size > 0 from a prior interrupted
      download, the next call hashes the existing partial bytes, sends
      a `Range: bytes=N-` header, and continues from offset N.
    - 206 Partial Content → server honoured Range; append to existing tmp.
    - 200 OK on resume attempt → server didn't honour Range; reset hasher,
      truncate tmp, restart fresh (M-9).
    - 416 Range Not Satisfiable → partial bytes don't align with current
      source; delete tmp; raise LibraryDownloadError (operator retries).
    - Network-level errors during streaming preserve `.heretic_tmp` for
      the next call's resume attempt (M-8 — resumable failures).
    - SHA-256 mismatch / size-cap exceeded delete `.heretic_tmp` because
      the partial bytes are poisoned (M-8 — non-resumable failures).
    - Full-file SHA-256 after resume equals SHA-256 of the bytes that
      would have been written by a single uninterrupted download (M-7).

INVARIANT (Cartographer thread #1):
    LibraryClient and all other modules MUST NOT import httpx.
    Downloader is the ONLY module in this codebase that imports httpx.
    This ensures the offline invariant is structurally enforced: you
    cannot accidentally trigger a network call by importing client.py.

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Downloader
     src/heretic/skilningr/mimisbrunnr/manifest.py (LibrarySource)
     src/heretic/skilningr/mimisbrunnr/errors.py
     docs/cartography/DATA_FLOW.md §4.14.1.1
     docs/vision/ENDURDRYKKR.md
     TASK_HERETIC_v0.7.2_ENDURDRYKKR.md
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
        # 1. Consent gate — MUST be first, before any network activity (M-1)
        # -------------------------------------------------------------------
        prompt_for_download(source, auto_yes=auto_yes)

        # -------------------------------------------------------------------
        # 2. Compute safety cap (bytes) + tmp path
        # -------------------------------------------------------------------
        size_cap = int(source.expected_size_bytes * _SIZE_CAP_MULTIPLIER)
        tmp_path = dest_path.with_suffix(".heretic_tmp")

        # -------------------------------------------------------------------
        # 2a. Endurdrykkr — resume detection (v0.7.2)
        #
        # If a .heretic_tmp file exists with non-zero size, hash its bytes
        # into the running SHA-256 BEFORE issuing the Range request. This
        # makes the final hasher.hexdigest() correct across the resume seam
        # (M-7).
        # -------------------------------------------------------------------
        hasher = hashlib.sha256()
        total_bytes = 0
        request_headers: dict[str, str] = {}
        write_mode = "wb"  # default: fresh write
        partial_size = 0

        if tmp_path.exists():
            try:
                partial_size = tmp_path.stat().st_size
            except OSError:
                partial_size = 0

        if partial_size > 0:
            try:
                with tmp_path.open("rb") as fh:
                    while True:
                        chunk = fh.read(_CHUNK_SIZE)
                        if not chunk:
                            break
                        hasher.update(chunk)
                total_bytes = partial_size
                request_headers = {"Range": f"bytes={partial_size}-"}
                write_mode = "ab"  # append to preserve partial bytes
                logger.info(
                    "Endurdrykkr: resuming %r from byte %d (partial tmp file present)",
                    source.id, partial_size,
                )
            except OSError as exc:
                # Couldn't read the partial — best-effort fallback to fresh.
                logger.warning(
                    "Endurdrykkr: could not read partial tmp for %r (%s); "
                    "starting fresh download",
                    source.id, exc,
                )
                hasher = hashlib.sha256()
                total_bytes = 0
                request_headers = {}
                write_mode = "wb"
                partial_size = 0

        # -------------------------------------------------------------------
        # 3. Stream download + SHA-256 + size guard + status dispatch
        # -------------------------------------------------------------------
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=120.0) as client:
                try:
                    async with client.stream(
                        "GET", source.url, headers=request_headers,
                    ) as response:
                        # Status dispatch: 206 = resume; 200 = fresh (or
                        # restart-from-fresh if we asked for a Range);
                        # 416 = partial bytes don't align — delete + raise.
                        if response.status_code == 206:
                            # Server honoured Range. write_mode already "ab".
                            logger.info(
                                "Endurdrykkr: server confirmed resume for %r "
                                "(206 Partial Content); appending from byte %d",
                                source.id, partial_size,
                            )
                        elif response.status_code == 200:
                            if partial_size > 0:
                                # Server ignored our Range. Reset and restart.
                                logger.info(
                                    "Endurdrykkr: resume requested for %r but "
                                    "server returned 200; restarting fresh "
                                    "(M-9)",
                                    source.id,
                                )
                                hasher = hashlib.sha256()
                                total_bytes = 0
                                write_mode = "wb"  # truncate on next open
                            else:
                                # Normal fresh download.
                                logger.info(
                                    "Downloading %r from %s "
                                    "(~%d bytes expected)...",
                                    source.id, source.url,
                                    source.expected_size_bytes,
                                )
                        elif response.status_code == 416:
                            # Range Not Satisfiable — partial doesn't align
                            # with current source. NON-RESUMABLE: delete tmp.
                            self._cleanup_tmp(tmp_path)
                            raise LibraryDownloadError(
                                f"Endurdrykkr: range not satisfiable for "
                                f"{source.id!r} (HTTP 416); partial bytes did "
                                f"not align with current source. Partial file "
                                f"removed. Run download again to start fresh."
                            )
                        else:
                            raise LibraryDownloadError(
                                f"Download of {source.id!r} failed: "
                                f"HTTP {response.status_code} from {source.url}"
                            )

                        # Stream body — append/write per write_mode
                        try:
                            with tmp_path.open(write_mode) as fh:
                                async for chunk in response.aiter_bytes(
                                    chunk_size=_CHUNK_SIZE
                                ):
                                    total_bytes += len(chunk)

                                    # Safety size cap: cumulative across
                                    # resumed + new bytes. NON-RESUMABLE.
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
                            # Disk-write failure during streaming — RESUMABLE
                            # in principle, but this branch typically signals
                            # a serious disk problem; preserve tmp anyway so
                            # the operator can investigate before retrying.
                            raise LibraryDownloadError(
                                f"Disk write failed for {source.id!r}: {exc}. "
                                f"Partial file preserved at {tmp_path} for "
                                f"possible resume."
                            ) from exc

                except httpx.HTTPStatusError as exc:
                    # 4xx/5xx outside our explicit dispatch — RESUMABLE.
                    # Preserve tmp so a subsequent call can attempt resume.
                    raise LibraryDownloadError(
                        f"HTTP error downloading {source.id!r} from "
                        f"{source.url}: {exc}. Partial file (if any) "
                        f"preserved for resume."
                    ) from exc

                except httpx.TransportError as exc:
                    # Network-level error (DNS / TCP / TLS) — RESUMABLE.
                    raise LibraryDownloadError(
                        f"Network transport error downloading {source.id!r}: "
                        f"{exc}. Partial file (if any) preserved for resume."
                    ) from exc

                except httpx.TimeoutException as exc:
                    # Timeout — RESUMABLE.
                    raise LibraryDownloadError(
                        f"Download of {source.id!r} timed out: {exc}. "
                        f"Partial file (if any) preserved for resume."
                    ) from exc

                except httpx.RequestError as exc:
                    # Other request-level error — RESUMABLE.
                    raise LibraryDownloadError(
                        f"Request error downloading {source.id!r}: {exc}. "
                        f"Partial file (if any) preserved for resume."
                    ) from exc

        except (IntegrityError, LibraryDownloadError):
            # Already have typed errors — re-raise without wrapping.
            # Tmp-file disposition was decided at the raise site:
            #   IntegrityError + 416 LibraryDownloadError → tmp deleted (M-8)
            #   other LibraryDownloadError                → tmp preserved (M-8)
            raise

        except Exception as exc:
            # Unexpected — preserve tmp for inspection rather than auto-deleting.
            # The operator can manually delete .heretic_tmp if they want a
            # clean slate.
            raise LibraryDownloadError(
                f"Unexpected error downloading {source.id!r}: "
                f"{type(exc).__name__}: {exc}. Partial file (if any) "
                f"preserved at {tmp_path}."
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
