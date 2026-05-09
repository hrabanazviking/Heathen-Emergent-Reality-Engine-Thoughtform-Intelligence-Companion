"""
Mímisbrunnr manifest — Norse starter pack source registry.

NorseStarterPackManifest is the authoritative record of the five
public-domain Norse texts that constitute the Mímisbrunnr starter
corpus. It is a module-level constant: NORSE_STARTER_PACK.

The five texts are all UTF-8 plain text served from Project Gutenberg
under the Project Gutenberg License (no cost, public domain in the USA).
SHA-256 hashes are None at scaffold time — Forge computes and locks
them after the first verified download.

URL VERIFICATION RECORD (Rúnhild Svartdóttir, 2026-05-08):
    All five URLs were verified via HTTP HEAD requests before being
    committed to this manifest. Two of the originally proposed URLs
    returned HTTP 404; canonical replacements were located via the
    Gutendex API (https://gutendex.com/) and content-verified.

    prose_edda_brodeur    OK  387,653 bytes   text/plain; charset=utf-8
    poetic_edda_bellows   OK  977,831 bytes   text/plain; charset=utf-8
    heimskringla_laing    OK  1,748,862 bytes text/plain; charset=utf-8
    volsunga_saga_morris  OK  330,843 bytes   text/plain; charset=utf-8
    erik_red_saga         OK   79,340 bytes   text/plain; charset=utf-8

    Dead URLs replaced:
        gutenberg.org/files/598/598-0.txt     (404) →
            gutenberg.org/ebooks/598.txt.utf-8  (Gutendex canonical)
        gutenberg.org/files/38722/38722-0.txt (404) →
            gutenberg.org/ebooks/73533.txt.utf-8 (Gutendex — Bellows
            translation confirmed by content snippet and translator field)

SHA-256 hashes are PLACEHOLDER (None) until Forge computes them from
the first successful download. They must be filled before v0.7 release.
Do NOT remove the None values without replacing them with the actual
hash strings.

Ref: src/heretic/skilningr/mimisbrunnr/INTERFACE.md §Manifest
     TASK_HERETIC_v0.7_MIMISBRUNNR.md §URL Verification
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LibrarySource:
    """A single text source entry in the Mímisbrunnr manifest.

    Attributes:
        id (str):
            Stable machine identifier. Used as the filename stem under
            the Mímisbrunnr data_dir (e.g. 'prose_edda_brodeur.txt').
            Never changes after the manifest is sealed.

        title (str):
            Human-readable title, including translator where relevant.

        url (str):
            Canonical plain-text download URL. Must be a verified,
            reachable URL serving UTF-8 content. Do not change without
            re-running the verification protocol.

        license (str):
            License statement. All starter-pack sources are Project
            Gutenberg public-domain texts.

        expected_size_bytes (int):
            Content-Length reported by the server at manifest-seal time.
            Used as a sanity check during download — if the actual
            downloaded size differs by more than 5%, Forge logs a
            warning and records the discrepancy in the local manifest.
            This is NOT a security check; sha256 is the integrity gate.

        sha256 (str | None):
            Hex SHA-256 digest of the downloaded plain-text file.
            None at scaffold time — Forge fills this in after the first
            verified download. MUST be set before v0.7 release.
    """

    id: str
    title: str
    url: str
    license: str
    expected_size_bytes: int
    sha256: str | None = None


@dataclass(frozen=True)
class NorseStarterPackManifest:
    """The Mímisbrunnr Norse starter pack — five public-domain texts.

    sources is an ordered list. The ordering is stable and must not
    change once the manifest is sealed, because source indices may be
    embedded in persistent index structures on disk.

    The module-level constant NORSE_STARTER_PACK is the single
    authoritative instance of this class. Do NOT construct additional
    instances — reference the constant directly.
    """

    sources: list[LibrarySource] = field(default_factory=list)

    def get_source(self, source_id: str) -> LibrarySource | None:
        """Return the LibrarySource with the given id, or None if absent."""
        for source in self.sources:
            if source.id == source_id:
                return source
        return None

    @property
    def source_ids(self) -> list[str]:
        """Ordered list of all source identifiers."""
        return [s.id for s in self.sources]


# ---------------------------------------------------------------------------
# The sealed manifest constant
# ---------------------------------------------------------------------------

NORSE_STARTER_PACK: NorseStarterPackManifest = NorseStarterPackManifest(
    sources=[
        # ----------------------------------------------------------------
        # 1. Prose Edda — Snorri Sturluson, trans. Arthur Gilchrist Brodeur
        # ----------------------------------------------------------------
        LibrarySource(
            id="prose_edda_brodeur",
            title="The Younger Edda (Prose Edda) — Snorri Sturluson, trans. Brodeur (1916)",
            url="https://www.gutenberg.org/files/18947/18947-0.txt",
            license="Project Gutenberg License — public domain in the USA",
            expected_size_bytes=387_653,
            sha256="a46fb8abc9e96c4bf757571f25cf55a1d2999d780271765b9dd54f09f70f8f32",  # locked 2026-05-08
        ),

        # ----------------------------------------------------------------
        # 2. Poetic Edda — trans. Henry Adams Bellows (1923)
        #    PG #73533 — gutendex canonical; content-verified 2026-05-08
        # ----------------------------------------------------------------
        LibrarySource(
            id="poetic_edda_bellows",
            title="The Poetic Edda — trans. Henry Adams Bellows (1923)",
            url="https://www.gutenberg.org/ebooks/73533.txt.utf-8",
            license="Project Gutenberg License — public domain in the USA",
            expected_size_bytes=977_831,
            sha256="50710042c87eb3075c74a9f36cd7dd0ffdc7bd7ba3bb7d5dee0f62db88b28e3c",  # locked 2026-05-08
        ),

        # ----------------------------------------------------------------
        # 3. Heimskringla — Snorri Sturluson, trans. Samuel Laing (1844)
        #    PG #598 — gutendex canonical; replaces dead 598-0.txt URL
        # ----------------------------------------------------------------
        LibrarySource(
            id="heimskringla_laing",
            title="Heimskringla: The Chronicle of the Kings of Norway — trans. Laing (1844)",
            url="https://www.gutenberg.org/ebooks/598.txt.utf-8",
            license="Project Gutenberg License — public domain in the USA",
            expected_size_bytes=1_748_862,
            sha256="dc794ff1dbaf88a9fee5172e5594adcb3de79316c4f281508fc3b8a6dd83d6a1",  # locked 2026-05-08
        ),

        # ----------------------------------------------------------------
        # 4. Volsunga Saga — trans. William Morris and Eiríkr Magnússon (1888)
        # ----------------------------------------------------------------
        LibrarySource(
            id="volsunga_saga_morris",
            title="The Story of the Volsungs (Volsunga Saga) — trans. Morris & Magnusson (1888)",
            url="https://www.gutenberg.org/files/1152/1152-0.txt",
            license="Project Gutenberg License — public domain in the USA",
            expected_size_bytes=330_843,
            sha256="b6ecaf400f47608c7497465fe5029268fb57c1a456c5bb99a1633fd6fc04053b",  # locked 2026-05-08
        ),

        # ----------------------------------------------------------------
        # 5. The Saga of Erik the Red — trans. J. Sephton (1880)
        # ----------------------------------------------------------------
        LibrarySource(
            id="erik_red_saga",
            title="The Saga of Erik the Red — trans. J. Sephton (1880)",
            url="https://www.gutenberg.org/files/17946/17946-0.txt",
            license="Project Gutenberg License — public domain in the USA",
            expected_size_bytes=79_340,
            sha256="6232afa6e0c384eb51d8a32df92fce7ba25cc15382cc9df45e2b0b2edb2b9c42",  # locked 2026-05-08
        ),
    ]
)
"""The authoritative Mímisbrunnr Norse starter pack manifest.

Five public-domain texts: Prose Edda (Brodeur), Poetic Edda (Bellows),
Heimskringla (Laing), Volsunga Saga (Morris/Magnusson), Erik the Red Saga
(Sephton). All sourced from Project Gutenberg, UTF-8 plain text.

All URLs verified reachable via HTTP HEAD, 2026-05-08 (Rúnhild Svartdóttir).
SHA-256 hashes are None — Forge fills them after the first successful download.
"""
