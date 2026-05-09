# TASK — HERETIC v0.7 FIRST DRINK AT THE WELL

> **Operational task resumption file** — per Volmarr's session-resume protocol.

> **Started: 2026-05-08** (immediately after v0.6.x MCP Server shipped + audited + cleaned at `f7a85b5`)

> **Codename:** *First Drink at the Well* — Mímisbrunnr opens; the spirit drinks of the Norse starter pack.

---

## 1. Task scope

Activate L5.9 Library — the optional knowledge-well subsystem named **Mímisbrunnr** (Mímir's Well).

The spec at `docs/MIMISBRUNNR.md` (sealed v0.0) describes a download + ingest + query subsystem letting the agent drink from open-licensed offline corpora. The full vision spans ZIMs (Wikipedia/Wiktionary), Project Gutenberg, Stack Exchange dumps, arXiv abstracts. **v0.7 ships the LIGHT TIER ONLY**: file-index backend + a curated Norse starter pack (Eddas + sagas in plain text from Project Gutenberg / Heimskringla.no — public domain).

The library is **opt-in**. A user who never enables it never downloads a byte. Per-source disk-budget confirmation is required before any download. License-tracked end-to-end into THIRD_PARTY_NOTICES.md.

---

## 2. Current status — 2026-05-08

**Phase:** v0.6.x SHIPPED + AUDITED + CLEANED at `f7a85b5`. Test baseline: Python 1012 + 7 skipped + 91 frontend = 1110.

### v0.7 deliverables
- ⏳ `src/heretic/skilningr/mimisbrunnr/` — Mímisbrunnr subsystem (corpus manifest, downloader, file-index, query)
- ⏳ `src/heretic/skilningr/senses/library/` — L5.9 Library sense (the agent-callable surface)
- ⏳ Norse starter pack manifest — list of public-domain texts with URL, license, size, SHA-256
- ⏳ File-index backend — simple line-by-line keyword search; no vector search yet (v0.9)
- ⏳ Download manager — per-source disk budget; user confirmation; resumable download; SHA-256 verify
- ⏳ Tools (3): `library.search`, `library.get_text`, `library.list_sources`
- ⏳ `pyproject.toml` — new `[library]` extra (minimal for v0.7: just stdlib + httpx already present; v0.9 adds sentence-transformers + faiss)
- ⏳ `heretic.example.yaml` — `skilningr.library:` block
- ⏳ Tests — 30+ new Python tests
- ⏳ docs/cartography/DATA_FLOW.md §4.14 — library flow
- ⏳ docs/THIRD_PARTY_NOTICES.md — Norse starter pack license entries

### What v0.7 does NOT add
- Vector search / embeddings (v0.9; `[library-vector]` extra adds sentence-transformers + faiss-cpu)
- ZIM ingest via libzim (v0.8; GPL — runtime-only never vendored)
- Wikipedia/Wiktionary corpus (v0.8 full catalog)
- MindSpark backend integration (v0.10)
- Auto-download on first run (operator must explicitly confirm each source)
- Live web fetches as part of library queries (use Leið for that)

---

## 3. Norse starter pack — proposed manifest (Architect verifies)

| Source | Format | License | URL | Approx size |
|---|---|---|---|---|
| Prose Edda (Brodeur translation) | UTF-8 plain text | Public Domain | gutenberg.org/files/18947/18947-0.txt | ~280 KB |
| Poetic Edda (Bellows translation) | UTF-8 plain text | Public Domain | sacred-texts.com/neu/poe/ (or Gutenberg equivalent) | ~600 KB |
| Heimskringla (Laing 1844 translation) | UTF-8 plain text | Public Domain | gutenberg.org/files/598/598-0.txt | ~1.4 MB |
| Saga of the Volsungs (Morris/Magnusson 1888) | UTF-8 plain text | Public Domain | gutenberg.org/files/1152/1152-0.txt | ~370 KB |
| Saga of Erik the Red | UTF-8 plain text | Public Domain | sacred-texts.com or Gutenberg | ~50 KB |

Total: ~2.7 MB starter pack. Operator confirms per-source before download.

Architect must VERIFY actual URLs + licenses + SHA-256 hashes at scaffold time. Project Gutenberg URLs are stable; sacred-texts.com requires verification of redistribution terms (most translations there are PD because they predate 1928 but verify each).

---

## 4. Architectural decisions

| Decision | Choice | Rationale |
|---|---|---|
| Sense location | `senses/library/` parallel to other 4 senses | Library is an L5 sense from the agent's view; the Mímisbrunnr subsystem is the implementation backend |
| Subsystem location | `mimisbrunnr/` module separate from sense | Sense is the agent-facing API; mimisbrunnr/ is the corpus management. Mirrors how Smiðja delegates to BrunhandHttpClient + ForgeHttpClient. |
| Download lib | httpx (already a dep) | Reuse |
| Index backend (v0.7) | File-line keyword search via stdlib (`re` + iteration) | Simple; deterministic; fast for ~3 MB corpus; no new deps |
| Index backend (v0.9) | sentence-transformers + faiss for vector search | Future; opt-in via `[library-vector]` extra |
| Storage location | `~/.local/share/heretic/library/` (Unix), `%APPDATA%/heretic/library/` (Windows) per `dirs` library (already a dep from v0.6.1) | Cross-platform user-data dir |
| Manifest format | YAML at `~/.local/share/heretic/library/manifest.yaml` (or starter manifest shipped with HERETIC) | Operator-readable; same format as heretic.yaml |
| Per-source consent | First-time download requires explicit operator confirmation (CLI prompt OR config flag) | Privacy + budget |
| SHA-256 verify | Required for downloaded files | Integrity |
| Resumable downloads | v0.7 = no, full re-download on partial; v0.7.x adds resume | Simpler scope |
| Tool naming | `library.<action>` per A-2 sealed convention | Two-part naming |
| Failure mode | Download fail / source missing / index empty → error tool_result; never crash | Per RULES.AI |
| Privacy invariant | Library never leaves the user's machine; queries are LOCAL keyword search | Mímisbrunnr is offline-by-design |

---

## 5. Mímisbrunnr light tier architecture

```
src/heretic/skilningr/mimisbrunnr/
  __init__.py
  INTERFACE.md
  manifest.py           — NorseStarterPackManifest dataclass (sources list)
  downloader.py         — async httpx download with SHA-256 verify
  store.py              — local filesystem layout: <data_dir>/library/sources/<source_id>/
  index.py              — line-by-line keyword search; load/build/query
  consent.py            — operator-confirmation flow (CLI prompt or config flag)
  errors.py
src/heretic/skilningr/senses/library/
  __init__.py
  INTERFACE.md
  config_model.py       — LibraryConfig
  errors.py
  client.py             — wraps mimisbrunnr; provides search / get_text / list_sources methods
  tools.py              — 3 ToolDefinitions
  sense.py              — LibrarySense orchestrator
```

`heretic library` CLI subcommand for management:
- `heretic library list` — show available + downloaded sources
- `heretic library download <source_id>` — confirm + download
- `heretic library remove <source_id>` — delete source
- `heretic library rebuild-index` — refresh keyword index

---

## 6. Mythic Engineering wave plan

### Wave 1 — parallel
- **Cartographer**: `docs/cartography/DATA_FLOW.md §4.14` — Library flow (agent calls library.search → LibrarySense → mimisbrunnr/index → returns matches with source attribution → tool_result). Document download flow + consent flow + storage layout. §16 update with new sense module + mimisbrunnr/ subsystem.
- **Architect**: scaffold `mimisbrunnr/` subsystem (NotImplementedError stubs) + `senses/library/` (mirror layout from existing 4 senses); LibraryConfig with `enabled: false` default + storage path + max_results + sources list; LibraryError hierarchy; 3 locked tool definitions; `[library]` pyproject extra (httpx + dirs already present; PyYAML for manifest); `heretic library` CLI subparser stub; verify the Norse starter pack URLs are reachable (light HEAD request); update IPC_PROTOCOL naming bridge with `library` sense.

### Wave 2
- **Forge**: implement downloader (async httpx with SHA-256 + per-source consent prompt), store (filesystem layout under `dirs.user_data_dir / heretic / library`), index (stdlib re-based keyword search loading lines into memory or scanning file with regex; results return file path + line context), LibraryClient wrapping mimisbrunnr ops, LibrarySense routing 3 tools, CLI library subcommands. Real tests with mocked httpx + in-memory store. 30+ new Python tests. Total target 1042+.
- **Auditor**: AUDIT_v0.7_MIMISBRUNNR.md; verify privacy invariant (no automatic downloads; consent enforced); SHA-256 verify enforced; storage path validation (no traversal); index correctness (matches return correct source attribution); tool schema; failure modes; cross-platform storage path; license attribution.

### Wave 3 — cleanup if needed

### Close-out
- **Scribe**: DEVLOG entry 14 + TASK update + memory refresh + add Norse starter pack license entries to THIRD_PARTY_NOTICES.md.

No Skald — extension milestone (5th sense; not a new faculty triad).

---

## 7. v0.7 exit criteria
- `heretic library list` shows the 5-source Norse starter pack
- Operator can `heretic library download prose_edda` (with confirmation prompt) and SHA-256 verifies; file lands in `~/.local/share/heretic/library/sources/prose_edda/text.txt`
- Agent can call `library.search` with a keyword and receive matches with source attribution
- Agent can call `library.get_text` to retrieve a passage
- Agent can call `library.list_sources` to see what's available locally
- All settings via `heretic.yaml`; opt-in default disabled
- Test count ≥1042 Python; total ≥1140
- Audit verdict PASS or PASS WITH CONCERNS, no blockers
- THIRD_PARTY_NOTICES.md updated with all 5 source attributions

---

## 8. Backlog forward
- v0.5.3 frontend Sjón webcam sub-badge
- v0.5.x periodic webcam, multi-camera, privacy masks
- v0.6.2.1 Leið streaming via aiter_bytes
- v0.6.2.2 Leið headless browser (playwright)
- v0.6.x.1 MCP resources/* hosting
- v0.6.x.2 MCP prompts/* hosting
- v0.7.x download resume + integrity recovery
- v0.8 full catalog: Wikipedia ZIMs (libzim runtime-only), Wiktionary, Wikiquote, Project Gutenberg full catalog
- v0.9 vector index: sentence-transformers + faiss
- v0.10 MindSpark backend
- v0.4.1 first compile (awaits operator linker install)

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-08.*
*v0.7 — when the spirit drinks of the well.*
