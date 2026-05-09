# Library Sense — Interface Contract

**Last updated:** 2026-05-08 (v0.7 scaffold — Rúnhild Svartdóttir)
**Scope:** L5.9 Library sense — Mímisbrunnr Norse text corpus access
**Authority:** Architect (Rúnhild Svartdóttir)

---

## 1. Identity

| Field       | Value                                               |
|-------------|-----------------------------------------------------|
| True Name   | Mímisbrunnr ("Mímir's well")                        |
| sense_id    | `library`                                           |
| Layer       | L5.9 Skilningr sense hub                            |
| Prefix      | `library.*`                                         |
| Config key  | `skilningr.library.*` in `heretic.yaml`             |
| Module      | `heretic.skilningr.senses.library`                  |
| Client      | `LibraryClient` (corpus accessor)                   |
| Backend     | `heretic.skilningr.mimisbrunnr` (data layer)        |

---

## 2. Purpose

The Library sense gives the agent keyword-search access to the Norse text
corpus downloaded by the Mímisbrunnr subsystem. The agent can search for
terms across all downloaded sources, retrieve line ranges from specific texts,
and inspect which sources are available locally.

The Library sense does NOT download texts — that is an operator action via
the `heretic library download` CLI command or the Mímisbrunnr downloader.

---

## 3. Tools (LOCKED at v0.7)

| Tool name              | Action                        | Required params    | Optional params                          |
|------------------------|-------------------------------|---------------------|------------------------------------------|
| `library.search`       | Keyword search over corpus    | `query` (string)   | `max_results` (integer, default 20)      |
| `library.get_text`     | Retrieve line range from source | `source_id` (string) | `start_line` (integer, default 1), `num_lines` (integer, default 50) |
| `library.list_sources` | List all sources + download status | — | — |

Tool names are stable identifiers. Renaming is a breaking change per
SENSE_CONTRACTS.md §2 rule 4.

---

## 4. Success Response Shapes

### library.search
```json
[
  {
    "source_id": "prose_edda_brodeur",
    "line_number": 1234,
    "context_text": "...And Odin said to the ravens...",
    "match_position": 14
  }
]
```

### library.get_text
```json
{
  "source_id": "prose_edda_brodeur",
  "start_line": 1,
  "num_lines": 50,
  "text": "THE PROSE EDDA\n\nPROLOGUE\n..."
}
```

### library.list_sources
```json
[
  {
    "id": "prose_edda_brodeur",
    "title": "The Younger Edda (Prose Edda) — Snorri Sturluson, trans. Brodeur (1916)",
    "url": "https://www.gutenberg.org/files/18947/18947-0.txt",
    "license": "Project Gutenberg License — public domain in the USA",
    "expected_size_bytes": 387653,
    "downloaded": true,
    "sha256": "abc123..."
  }
]
```

---

## 5. Failure Modes

| Condition                          | Error class            | SENSE_CONTRACTS code   |
|------------------------------------|------------------------|------------------------|
| Index not built / no sources       | `LibraryIndexError`    | `SENSE_INTERNAL_ERROR` |
| Source not downloaded              | `LibraryError`         | `INVALID_ARGUMENTS`    |
| Unknown source_id                  | `LibraryError`         | `INVALID_ARGUMENTS`    |
| start_line out of range            | `LibraryError`         | `INVALID_ARGUMENTS`    |
| Consent refused for download       | `ConsentRefused`       | `PERMISSION_DENIED`    |
| Download network failure           | `LibraryDownloadError` | `EXTERNAL_APP_UNAVAILABLE` |
| SHA-256 mismatch after download    | `IntegrityError`       | `SENSE_INTERNAL_ERROR` |
| Sense disabled or not open         | `SenseUnavailableError`| `SENSE_UNAVAILABLE`    |

All failures are translated into structured tool_result error JSON at the
LibrarySense dispatch boundary. None propagate to L1 Bifröst.

---

## 6. Lifecycle

1. **Kynding (open):** `LibrarySense.open()` resolves `storage_path` (via
   platformdirs if empty), calls `ensure_storage_directory()`, optionally
   rebuilds the keyword index if `autoindex_on_open=True` and index is stale.
2. **Tengsl (tool calls):** `dispatch_tool_call()` routes to `LibraryClient`
   which delegates to Mímisbrunnr subsystem functions.
3. **Slokna (close):** `LibrarySense.close()` marks `_is_open=False`.
   No persistent connection in v0.7.

---

## 7. Configuration Reference

```yaml
skilningr:
  library:
    enabled: false                    # opt-in; must be true to expose tools
    storage_path: ""                  # empty = platformdirs resolution at startup
    max_results: 20                   # max hits per library.search call
    autoindex_on_open: true           # rebuild index at startup if stale
    sources:                          # pre-approved source ids for auto-download
      []                              # empty = interactive consent required
      # - prose_edda_brodeur
      # - poetic_edda_bellows
      # - heimskringla_laing
      # - volsunga_saga_morris
      # - erik_red_saga
```

---

## 8. Dependency Law

```
LibrarySense → LibraryClient → mimisbrunnr.{store, index, manifest}
                              → mimisbrunnr.downloader (on download)
                              → mimisbrunnr.consent (on download)
```

The Library sense never imports from other senses. The Mímisbrunnr subsystem
never imports from senses. This is a strict one-way dependency.

---

## 9. What Callers Must Not Assume

- Callers MUST NOT assume any sources are downloaded at startup.
  Call `library.list_sources` to check before calling `library.search`.
- Callers MUST NOT attempt to download sources via tool calls —
  downloads are an operator CLI action, not an agent-triggered action.
- The `library.*` tool prefix is stable. Do not use `mimisbrunnr.*`.

---

## 10. Forge Implementation Targets (v0.7 Wave 1)

| Target | Notes |
|--------|-------|
| `LibraryClient.search` | Delegate to KeywordIndex.search; convert SearchHit to dict |
| `LibraryClient.get_text` | Validate source downloaded; slice line range from .txt file |
| `LibraryClient.list_sources` | Annotate NORSE_STARTER_PACK sources with download state |
| `LibrarySense.open` | Resolve path; ensure dir; optional index rebuild |
| `LibrarySense.close` | Set `_is_open = False` |
| `LibrarySense.dispatch_tool_call` | Full dispatch body (mirrors MinniSense pattern) |
