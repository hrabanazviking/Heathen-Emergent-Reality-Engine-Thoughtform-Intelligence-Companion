"""
Mímisbrunnr store — local storage layout and source path resolution.

The store module owns the mapping between source_ids and on-disk paths
within the operator-configured data_dir. It does not perform I/O beyond
what is necessary to establish or verify the directory structure.

Storage layout:
    <data_dir>/
        <source_id>.txt           — downloaded plain-text source files
        mimisbrunnr_manifest.json — local manifest tracking download
                                    state, sha256 hashes, download dates

The data_dir itself is configured in LibraryConfig.storage_path.
If storage_path is empty, the Library sense resolves it at init time
via platformdirs.user_data_dir (Forge implements that resolution).

DESIGN CONTRACT:
    - resolve_source_path: pure path computation — no I/O.
    - ensure_storage_directory: creates the data_dir if it does not
      exist; the only store function permitted to mutate the filesystem.
    - load_local_manifest: reads and deserialises the on-disk JSON
      manifest that tracks which sources have been downloaded and their
      verified sha256 hashes.
    - is_source_downloaded: returns True if the source file exists and
      is non-empty at the expected path.
    - update_local_manifest: writes/merges a single source entry into
      the local manifest atomically via .tmp + os.replace.

source_id validation invariant (Cartographer thread #2):
    source_id must match ^[a-z0-9_]+$ — only lowercase alphanumerics
    and underscores, no dots, no slashes, no path characters. Any
    attempt to pass a traversal string is rejected with ValueError.
    The allowed_sources list from NORSE_STARTER_PACK is fully
    compliant with this pattern.

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Store
     src/heretic/skilningr/senses/library/config_model.py (LibraryConfig)
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from heretic.skilningr.mimisbrunnr.errors import ManifestError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# source_id validation
# ---------------------------------------------------------------------------

_SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")
"""Valid source_id: lowercase alphanumerics and underscores only.
No dots, no slashes, no hyphens — prevents path traversal entirely."""

_LOCAL_MANIFEST_FILENAME = "mimisbrunnr_manifest.json"
"""Filename for the local download-state manifest within data_dir."""


def _validate_source_id(source_id: str) -> None:
    """Raise ValueError if source_id contains any unsafe characters.

    Called by resolve_source_path and is_source_downloaded before any
    path construction. This is the structural traversal guard.

    Args:
        source_id: The identifier to validate.

    Raises:
        ValueError: if source_id does not match ^[a-z0-9_]+$
    """
    if not _SOURCE_ID_PATTERN.match(source_id):
        raise ValueError(
            f"Invalid source_id {source_id!r}: must match ^[a-z0-9_]+$ "
            "(only lowercase letters, digits, underscores — no dots, slashes, "
            "hyphens, or other characters). This is a traversal prevention guard."
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_source_path(data_dir: Path, source_id: str) -> Path:
    """Return the expected on-disk path for a downloaded source file.

    This is a pure path computation — no I/O is performed.

    Args:
        data_dir:  The Mímisbrunnr data directory (from LibraryConfig).
        source_id: The stable source identifier (e.g. 'prose_edda_brodeur').
                   Must match ^[a-z0-9_]+$.

    Returns:
        The absolute Path where the source's .txt file should live.

    Raises:
        ValueError: if source_id does not match the safe-identifier pattern.
    """
    _validate_source_id(source_id)
    return data_dir / f"{source_id}.txt"


def ensure_storage_directory(data_dir: Path) -> None:
    """Create the Mímisbrunnr data directory if it does not already exist.

    This is the only store function that mutates the filesystem. It uses
    Path.mkdir(parents=True, exist_ok=True) — idempotent.

    Args:
        data_dir: The Mímisbrunnr data directory to create.

    Raises:
        OSError: if the directory cannot be created (permission denied, etc.).
    """
    data_dir.mkdir(parents=True, exist_ok=True)


def load_local_manifest(data_dir: Path) -> dict[str, dict]:
    """Load the local download-state manifest from disk.

    The local manifest records which sources have been downloaded,
    their verified SHA-256 hashes, and the download timestamp.

    Args:
        data_dir: The Mímisbrunnr data directory.

    Returns:
        A dict mapping source_id (str) to a metadata dict with keys:
            sha256 (str | None): verified hash, or None if not yet verified
            downloaded_at (str | None): ISO 8601 UTC timestamp, or None
            size_bytes (int | None): actual downloaded file size

        Returns {} if the manifest file does not exist yet.

    Raises:
        ManifestError: if the manifest file exists but is corrupt or
            schema-invalid (invalid JSON, unexpected top-level type).
    """
    manifest_path = data_dir / _LOCAL_MANIFEST_FILENAME

    if not manifest_path.exists():
        return {}

    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(
            f"Could not read local manifest at {manifest_path}: {exc}"
        ) from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ManifestError(
            f"Local manifest at {manifest_path} is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ManifestError(
            f"Local manifest at {manifest_path} must be a JSON object "
            f"(dict), got {type(data).__name__!r}."
        )

    return data  # type: ignore[return-value]


def update_local_manifest(
    data_dir: Path,
    source_id: str,
    sha256: str,
    downloaded_at: str | None = None,
    size_bytes: int | None = None,
) -> None:
    """Write or merge a single source entry into the local manifest.

    The write is atomic: data is written to a .tmp file then os.replace()d
    to the final path, so no partial manifest is ever visible.

    Args:
        data_dir:      The Mímisbrunnr data directory.
        source_id:     The source identifier to update. Must match ^[a-z0-9_]+$.
        sha256:        The verified SHA-256 hex digest of the downloaded file.
        downloaded_at: ISO 8601 UTC timestamp string (optional). Defaults to
                       now if not provided.
        size_bytes:    Actual size of the downloaded file in bytes (optional).

    Raises:
        ValueError: if source_id does not match the safe-identifier pattern.
        ManifestError: if the existing manifest is corrupt.
        OSError: if the atomic write fails.
    """
    _validate_source_id(source_id)

    if downloaded_at is None:
        downloaded_at = datetime.now(timezone.utc).isoformat()

    # Load existing manifest (or start fresh)
    try:
        data = load_local_manifest(data_dir)
    except ManifestError:
        logger.warning(
            "Corrupt local manifest in %s — resetting to empty dict before update.",
            data_dir,
        )
        data = {}

    # Merge the new entry
    data[source_id] = {
        "sha256": sha256,
        "downloaded_at": downloaded_at,
        "size_bytes": size_bytes,
    }

    # Atomic write
    manifest_path = data_dir / _LOCAL_MANIFEST_FILENAME
    tmp_path = manifest_path.with_suffix(".heretic_tmp")

    try:
        tmp_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(str(tmp_path), str(manifest_path))
    except OSError as exc:
        # Clean up .heretic_tmp on failure
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise OSError(
            f"Failed to write local manifest to {manifest_path}: {exc}"
        ) from exc

    logger.info(
        "Local manifest updated — source %r sha256=%s", source_id, sha256[:12]
    )


def is_source_downloaded(data_dir: Path, source_id: str) -> bool:
    """Return True if the source file exists and is non-empty on disk.

    Does NOT verify SHA-256 — this is a quick existence check. Use
    load_local_manifest() for integrity state.

    Args:
        data_dir:  The Mímisbrunnr data directory.
        source_id: The source identifier to check.

    Returns:
        True if the .txt file exists and has size > 0, False otherwise.

    Raises:
        ValueError: if source_id does not match the safe-identifier pattern.
    """
    path = resolve_source_path(data_dir, source_id)
    try:
        return path.exists() and path.stat().st_size > 0
    except OSError:
        return False
