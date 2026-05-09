# Mímisbrunnr Subsystem — Interface Contract

**Last updated:** 2026-05-08 (v0.7 scaffold — Rúnhild Svartdóttir)
**Scope:** heretic.skilningr.mimisbrunnr — Norse text corpus backend
**Authority:** Architect (Rúnhild Svartdóttir)

---

## 1. Identity

| Field      | Value                                                |
|------------|------------------------------------------------------|
| True Name  | Mímisbrunnr ("Mímir's well")                         |
| Layer      | Backend subsystem — NOT a sense; serves L5.9 Library sense |
| Module     | `heretic.skilningr.mimisbrunnr`                      |
| Config key | `skilningr.library.*` in `heretic.yaml`              |

---

## 2. Purpose

Mímisbrunnr is the corpus layer beneath the Library sense. It owns:

- The **manifest** of verified public-domain Norse texts (5 sources, starter pack)
- The **download gate** — async download with SHA-256 integrity verification
- The **storage layout** — local path resolution and directory management
- The **keyword index** — build and search over downloaded plain-text sources
- The **consent gate** — operator approval before any download occurs

The Library sense (senses/library/) calls into Mímisbrunnr. Mímisbrunnr
does not call into any sense or into the ToolDispatcher.

---

## 3. Module Responsibilities

| Module        | Owns                                             | Does NOT own               |
|---------------|--------------------------------------------------|----------------------------|
| `manifest.py` | NORSE_STARTER_PACK constant, LibrarySource type  | Disk I/O, network          |
| `downloader.py`| Async HTTP download, atomic write, SHA-256 verify | Consent, index, path layout |
| `store.py`    | Path resolution, dir creation, local manifest JSON | Download, index, agent tools |
| `index.py`    | Build and search keyword index (JSONL)           | Download, consent, path resolution |
| `consent.py`  | Operator approval prompt                         | Download, index, config    |
| `errors.py`   | LibraryError hierarchy                           | Nothing else               |

---

## 4. The Norse Starter Pack (LOCKED at v0.7)

Five public-domain texts. All URLs verified 2026-05-08 via HTTP HEAD.

| source_id              | Title (translator, year)                         | URL                                              | Size (bytes) |
|------------------------|--------------------------------------------------|--------------------------------------------------|--------------|
| `prose_edda_brodeur`   | Prose Edda — Brodeur (1916)                      | gutenberg.org/files/18947/18947-0.txt            | 387,653      |
| `poetic_edda_bellows`  | Poetic Edda — Bellows (1923)                     | gutenberg.org/ebooks/73533.txt.utf-8             | 977,831      |
| `heimskringla_laing`   | Heimskringla — Laing (1844)                      | gutenberg.org/ebooks/598.txt.utf-8               | 1,748,862    |
| `volsunga_saga_morris` | Volsunga Saga — Morris/Magnusson (1888)          | gutenberg.org/files/1152/1152-0.txt              | 330,843      |
| `erik_red_saga`        | Saga of Erik the Red — Sephton (1880)            | gutenberg.org/files/17946/17946-0.txt            | 79,340       |

**URL verification record:** Two originally proposed URLs returned HTTP 404 at
scaffold time. They were replaced with canonical Gutendex API equivalents
(Heimskringla: 598-0.txt → ebooks/598.txt.utf-8; Poetic Edda Bellows: 38722-0.txt
→ ebooks/73533.txt.utf-8, PG book #73533). Content was verified by snippet check.

**SHA-256 hashes:** All `None` at scaffold time. Forge computes and locks them
after the first successful download. Must be set before v0.7 release.

---

## 5. Storage Layout

```
<storage_path>/                     ← resolved from LibraryConfig.storage_path
    prose_edda_brodeur.txt          ← downloaded plain-text files (source_id + .txt)
    poetic_edda_bellows.txt
    heimskringla_laing.txt
    volsunga_saga_morris.txt
    erik_red_saga.txt
    keyword_index.jsonl             ← built by KeywordIndex.build()
    mimisbrunnr_manifest.json       ← local download-state manifest
```

`storage_path` defaults to platformdirs.user_data_dir("heretic") / "library" /
"mimisbrunnr" when LibraryConfig.storage_path is empty. Forge implements this
resolution inside LibrarySense.open().

---

## 6. Download Protocol

1. **Consent gate:** `consent.prompt_for_download(source, auto_yes)` — returns
   True or raises ConsentRefused. No network access before consent.
2. **Download:** `Downloader.download(source, dest_path)` — streams the URL,
   writes atomically to `<storage_path>/<source_id>.txt`.
3. **Integrity:** After write, compute SHA-256. If `source.sha256` is not None,
   compare — raise `IntegrityError` on mismatch. If None, log the computed hash.
4. **Record:** Update `mimisbrunnr_manifest.json` with sha256, download timestamp,
   and actual file size.

---

## 7. Keyword Index

- **Build:** `KeywordIndex.build(data_dir)` — iterates all `*.txt` files; records
  `(source_id, line_number, line_text)` tuples; serialises to `keyword_index.jsonl`.
- **Search:** `KeywordIndex.search(query, max_results)` — loads (or reuses cached)
  index; case-folded substring match; returns list of `SearchHit` dataclasses.
- **SearchHit fields:** `source_id`, `line_number`, `context_text`, `match_position`.
- Index is rebuilt by `heretic library rebuild-index` or by LibrarySense.open()
  when `autoindex_on_open=True` and the index is stale.

---

## 8. Error Hierarchy

```
SkilningrError
    LibraryError                    — root; catch this for any Mímisbrunnr failure
        LibraryDownloadError        — network transport failure
        IntegrityError              — SHA-256 hash mismatch on downloaded file
        ManifestError               — local manifest corrupt or schema-invalid
        ConsentRefused              — operator declined the download prompt
        LibraryIndexError           — index build or search failure
```

All errors caught at LibrarySense dispatch boundary; never re-raised to L1 Bifröst.

---

## 9. What Callers Must Not Assume

- Callers MUST NOT assume sources are downloaded — always check
  `store.is_source_downloaded()` or `client.list_sources()` first.
- Callers MUST NOT call `Downloader.download()` without calling
  `consent.prompt_for_download()` first.
- Callers MUST NOT call `KeywordIndex.search()` before `build()` or
  before checking that a pre-built `keyword_index.jsonl` exists.
- The `sha256` field in NORSE_STARTER_PACK is None at scaffold — do NOT
  treat None as "no verification required". Forge fills this in.

---

## 10. Forge Implementation Targets (v0.7 Wave 1)

| Target | Module | Notes |
|--------|--------|-------|
| `resolve_source_path` | store.py | Pure path computation: `data_dir / f'{source_id}.txt'` |
| `load_local_manifest` | store.py | Load/parse JSON; return {} if absent |
| `is_source_downloaded` | store.py | `p.exists() and p.stat().st_size > 0` |
| `Downloader.download` | downloader.py | httpx stream; atomic write; SHA-256 |
| `KeywordIndex.build` | index.py | Iterate *.txt; write keyword_index.jsonl |
| `KeywordIndex.search` | index.py | Load index; case-fold match; return SearchHit list |
| `prompt_for_download` interactive | consent.py | Read stdin; 'y'/'Y' → True; else ConsentRefused |
