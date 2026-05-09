"""
Mímisbrunnr downloader — async HTTP download of LibrarySource texts.

Downloader is responsible for fetching a single LibrarySource from its
canonical URL and writing the content to disk atomically. It does NOT
build indexes or verify consent — those responsibilities belong to
consent.py and index.py respectively.

DESIGN CONTRACT (enforced at scaffold level, implemented by Forge):

    - Uses httpx.AsyncClient for async HTTP.
    - Streams the response body to avoid loading multi-MB texts fully
      into memory before writing.
    - Writes to a .tmp file first, then os.replace() atomically —
      no partial file is ever visible at the final path.
    - After the write, computes SHA-256 of the written bytes.
    - If LibrarySource.sha256 is not None, compares the computed hash
      against the manifest hash and raises IntegrityError on mismatch.
    - If LibrarySource.sha256 is None (placeholder), logs the computed
      hash at INFO level so the operator can record it.
    - Raises LibraryDownloadError on any network failure.

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Downloader
     src/heretic/skilningr/mimisbrunnr/manifest.py (LibrarySource)
     src/heretic/skilningr/mimisbrunnr/errors.py
"""

from __future__ import annotations

import logging
from pathlib import Path

from heretic.skilningr.mimisbrunnr.errors import LibraryDownloadError, IntegrityError
from heretic.skilningr.mimisbrunnr.manifest import LibrarySource

logger = logging.getLogger(__name__)


class Downloader:
    """Async downloader for Mímisbrunnr library sources.

    Usage (Forge implements the body):
        downloader = Downloader()
        await downloader.download(source, dest_path)

    After a successful call, dest_path contains the UTF-8 text of the
    source and the SHA-256 of the file has been verified (if the
    manifest entry carries a non-None sha256).
    """

    async def download(self, source: LibrarySource, dest_path: Path) -> None:
        """Download a LibrarySource and write it to dest_path.

        Downloads source.url, writes the content atomically to dest_path,
        computes the SHA-256 of the downloaded bytes, and validates it
        against source.sha256 if that field is not None.

        Args:
            source:    The LibrarySource entry from NORSE_STARTER_PACK.
            dest_path: Absolute path where the downloaded text will be
                       written. Parent directory must already exist.

        Raises:
            LibraryDownloadError: on any network-level failure (DNS,
                TCP, TLS, HTTP non-200).
            IntegrityError: if source.sha256 is set and the downloaded
                file's hash does not match.

        Note:
            sha256 in the manifest is currently None (scaffold placeholder).
            Forge records the computed hash after the first download so
            that future downloads can be integrity-checked.
        """
        raise NotImplementedError(
            "Downloader.download is a Forge implementation target. "
            "The body will stream source.url via httpx.AsyncClient, "
            "write atomically to dest_path, compute SHA-256, and "
            "validate against source.sha256 if not None."
        )
