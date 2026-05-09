"""
Tests for the Mímisbrunnr Norse starter pack manifest.

These tests verify the structure and integrity of NORSE_STARTER_PACK
at the module-import level — no network access, no disk I/O.

Covers:
    - NORSE_STARTER_PACK is a NorseStarterPackManifest instance
    - Exactly 5 sources in the starter pack
    - Each source has a non-empty id, title, url, license
    - All URLs are HTTPS (no HTTP)
    - expected_size_bytes is a positive integer for each source
    - sha256 is a sealed 64-character hex string for all sources (locked 2026-05-08)
    - source_ids are unique (no duplicates)
    - get_source() returns the correct LibrarySource or None
    - NorseStarterPackManifest is frozen (immutable)
    - LibrarySource is frozen (immutable)

Ref: src/heretic/skilningr/mimisbrunnr/manifest.py
"""

from __future__ import annotations

import re

import pytest

from heretic.skilningr.mimisbrunnr.manifest import (
    LibrarySource,
    NORSE_STARTER_PACK,
    NorseStarterPackManifest,
)


EXPECTED_SOURCE_IDS = [
    "prose_edda_brodeur",
    "poetic_edda_bellows",
    "heimskringla_laing",
    "volsunga_saga_morris",
    "erik_red_saga",
]


class TestNorseStarterPackManifest:
    """Tests for the NORSE_STARTER_PACK module-level constant."""

    def test_constant_is_manifest_instance(self) -> None:
        """NORSE_STARTER_PACK must be a NorseStarterPackManifest."""
        assert isinstance(NORSE_STARTER_PACK, NorseStarterPackManifest)

    def test_exactly_five_sources(self) -> None:
        """The starter pack must contain exactly 5 sources."""
        assert len(NORSE_STARTER_PACK.sources) == 5

    def test_source_ids_match_expected(self) -> None:
        """Source ids must match the known set in order."""
        assert NORSE_STARTER_PACK.source_ids == EXPECTED_SOURCE_IDS

    def test_source_ids_unique(self) -> None:
        """No duplicate source ids."""
        ids = NORSE_STARTER_PACK.source_ids
        assert len(ids) == len(set(ids))

    @pytest.mark.parametrize("source_id", EXPECTED_SOURCE_IDS)
    def test_each_source_has_non_empty_id(self, source_id: str) -> None:
        source = NORSE_STARTER_PACK.get_source(source_id)
        assert source is not None
        assert source.id == source_id
        assert len(source.id) > 0

    @pytest.mark.parametrize("source_id", EXPECTED_SOURCE_IDS)
    def test_each_source_has_non_empty_title(self, source_id: str) -> None:
        source = NORSE_STARTER_PACK.get_source(source_id)
        assert source is not None
        assert len(source.title) > 0

    @pytest.mark.parametrize("source_id", EXPECTED_SOURCE_IDS)
    def test_each_source_url_is_https(self, source_id: str) -> None:
        """All starter pack URLs must use HTTPS."""
        source = NORSE_STARTER_PACK.get_source(source_id)
        assert source is not None
        assert source.url.startswith("https://"), (
            f"Source {source_id!r} URL must use HTTPS: {source.url!r}"
        )

    @pytest.mark.parametrize("source_id", EXPECTED_SOURCE_IDS)
    def test_each_source_has_non_empty_license(self, source_id: str) -> None:
        source = NORSE_STARTER_PACK.get_source(source_id)
        assert source is not None
        assert len(source.license) > 0

    @pytest.mark.parametrize("source_id", EXPECTED_SOURCE_IDS)
    def test_each_source_expected_size_is_positive(self, source_id: str) -> None:
        source = NORSE_STARTER_PACK.get_source(source_id)
        assert source is not None
        assert isinstance(source.expected_size_bytes, int)
        assert source.expected_size_bytes > 0

    _SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

    @pytest.mark.parametrize("source_id", EXPECTED_SOURCE_IDS)
    def test_sha256_is_sealed_hex_string(self, source_id: str) -> None:
        """SHA-256 hashes are sealed 64-char lowercase hex strings (locked 2026-05-08).

        The manifest was originally scaffolded with sha256=None. Forge computed
        and locked the hashes from real downloads on 2026-05-08 via
        scripts/lock_hashes.py. All five hashes must now be present and valid.

        If you see this test fail after a URL replacement: re-run
        scripts/lock_hashes.py, capture the new digests, update manifest.py,
        and update the expected values below.
        """
        source = NORSE_STARTER_PACK.get_source(source_id)
        assert source is not None
        assert source.sha256 is not None, (
            f"Source {source_id!r} sha256 is None — manifest hashes should be "
            "locked. Run scripts/lock_hashes.py and update manifest.py."
        )
        assert self._SHA256_PATTERN.match(source.sha256), (
            f"Source {source_id!r} sha256 {source.sha256!r} does not match "
            "the expected format ^[0-9a-f]{64}$."
        )

    def test_get_source_returns_none_for_unknown(self) -> None:
        """get_source must return None for an unknown id."""
        result = NORSE_STARTER_PACK.get_source("does_not_exist")
        assert result is None

    def test_manifest_is_frozen(self) -> None:
        """NorseStarterPackManifest must be frozen — normal attribute assignment raises."""
        with pytest.raises((AttributeError, TypeError)):
            # frozen=True dataclass raises FrozenInstanceError (subclass of AttributeError)
            # when normal attribute assignment is attempted.
            NORSE_STARTER_PACK.sources = []  # type: ignore[misc]

    def test_library_source_is_frozen(self) -> None:
        """LibrarySource must be frozen — normal attribute assignment raises."""
        source = NORSE_STARTER_PACK.sources[0]
        with pytest.raises((AttributeError, TypeError)):
            source.id = "mutated"  # type: ignore[misc]
