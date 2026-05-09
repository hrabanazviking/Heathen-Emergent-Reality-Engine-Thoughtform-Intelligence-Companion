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

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Store
     src/heretic/skilningr/senses/library/config_model.py (LibraryConfig)
"""

from __future__ import annotations

from pathlib import Path


def resolve_source_path(data_dir: Path, source_id: str) -> Path:
    """Return the expected on-disk path for a downloaded source file.

    This is a pure path computation — no I/O is performed.

    Args:
        data_dir:  The Mímisbrunnr data directory (from LibraryConfig).
        source_id: The stable source identifier (e.g. 'prose_edda_brodeur').

    Returns:
        The absolute Path where the source's .txt file should live.

    Raises:
        NotImplementedError: Forge implements the body.
    """
    raise NotImplementedError(
        "resolve_source_path is a Forge implementation target. "
        "Body: return data_dir / f'{source_id}.txt'"
    )


def ensure_storage_directory(data_dir: Path) -> None:
    """Create the Mímisbrunnr data directory if it does not already exist.

    This is the only store function that mutates the filesystem. It uses
    Path.mkdir(parents=True, exist_ok=True) — idempotent.

    Args:
        data_dir: The Mímisbrunnr data directory to create.

    Raises:
        OSError: if the directory cannot be created (permission denied, etc.).
    """
    # This function IS implemented — it is trivial and needed by tests.
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

    Raises:
        NotImplementedError: Forge implements the body.
        ManifestError: if the manifest file is corrupt or schema-invalid.
    """
    raise NotImplementedError(
        "load_local_manifest is a Forge implementation target. "
        "Body: load data_dir / 'mimisbrunnr_manifest.json'; parse JSON; "
        "validate schema; return dict. If file absent, return {}."
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
        NotImplementedError: Forge implements the body.
    """
    raise NotImplementedError(
        "is_source_downloaded is a Forge implementation target. "
        "Body: p = resolve_source_path(data_dir, source_id); "
        "return p.exists() and p.stat().st_size > 0"
    )
