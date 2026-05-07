# Mímisbrunnr — The Well of Wisdom

> *"From there come the dews that drop in the dales — / it stands ever green over Urd's well." — Voluspá*
>
> *Mímisbrunnr — Mímir's Well — was the well of wisdom under the second root of Yggdrasil. Odin sacrificed an eye to drink from it once. Mímir himself drank from it daily, and so was the wisest of beings.*
>
> Volmarr drinks bandwidth and disk. The agents who inhabit H.E.R.E.T.I.C. drink whatever wisdom we ladle into the well.

---

## Status

**Specification phase.** No implementation yet. Slot in the roadmap: v0.7.5 → v0.10. See `docs/ROADMAP.md` (TBD) and `TASK_HERETIC_v0.1_BOOTSTRAP.md`.

This file documents the design intent. Implementation lives at `heretic/mimisbrunnr/` (not yet created).

---

## What it is

Mímisbrunnr is H.E.R.E.T.I.C.'s **optional offline knowledge subsystem**. It downloads, ingests, indexes, and serves massive freely-available open-licensed corpora so that any agent inhabiting the H.E.R.E.T.I.C. body can *drink* from a well of curated human knowledge during a session — without a network call to a cloud service.

It plugs into H.E.R.E.T.I.C.'s **L5.9 Library MCP** as one of several library backends. The agent doesn't see Mímisbrunnr directly; it calls `library.search(...)`, and Mímisbrunnr (when enabled) is one of the wells that may answer.

It is **opt-in**. Disabled by default. Mímisbrunnr requires explicit user consent, explicit disk-budget acknowledgement, and explicit per-source download confirmation. No source is ever fetched without the user saying yes.

---

## What it is not

- ❌ Not the agent's memory. The spirit brings its mind; this is a bookshelf in the longhouse.
- ❌ Not a training corpus. We do not fine-tune on Mímisbrunnr contents — we serve them at retrieval time.
- ❌ Not a chatbot frontend. It is plumbing for L5.9.
- ❌ Not always-on. Like the rest of H.E.R.E.T.I.C., it activates only during a ceremony.
- ❌ Not a CommonCrawl-style firehose. We curate sources by quality, license clarity, and relevance.

---

## Sources we plan to support (v0.7.5 → v0.10)

All free, all open-licensed, all attributed in `THIRD_PARTY_NOTICES.md`.

### Tier 1 — light starters (seeded in v0.7.5)

| Source | Size | License | Format |
|---|---|---|---|
| Norse sagas (public domain) | ~50 MB | Public domain | EPUB / TXT |
| Wiktionary (en) | ~2 GB ZIM | CC BY-SA 4.0 | ZIM |
| Wikiquote (en) | ~250 MB ZIM | CC BY-SA 4.0 | ZIM |
| Project Gutenberg — curated Norse subset | ~3 GB | Public domain | EPUB |

### Tier 2 — medium (v0.8)

| Source | Size | License | Format |
|---|---|---|---|
| Wikipedia — Norse / mythology subset | ~3 GB | CC BY-SA 4.0 | custom ZIM |
| arXiv abstracts only | ~5 GB | CC0 / various | JSONL |
| Stack Exchange — selected sites (math, philosophy, mythology, English, etc.) | ~10–100 GB | CC BY-SA 4.0 | XML / ZIM |
| Project Gutenberg — full | ~30 GB | Public domain | EPUB |

### Tier 3 — heavy (v0.9 → v0.10)

| Source | Size | License | Format |
|---|---|---|---|
| Wikipedia — full English | ~25 GB ZIM / ~85 GB raw | CC BY-SA 4.0 | ZIM (recommended) |
| Wikipedia — multi-language full (NO, IS, SE, OE, DE) | 200+ GB | CC BY-SA 4.0 | ZIM each |
| PubMed Central OA subset | ~30 GB | CC BY / CC0 | XML |
| Internet Archive — public domain books (selected categories) | TB-scale | Public domain | varies |
| OpenStreetMap planet | ~80 GB | ODbL | PBF |

### Tier 4 — explicitly excluded by default

- **CommonCrawl** — TB scale, mostly low-quality web text, dubious training-data ethics
- **GitHub source dumps** — license is messy across millions of repos
- **Reddit** — license unclear since 2024
- **Anything behind a paywall**

May be reconsidered in v2.x by user request only.

---

## Architecture

```
heretic/mimisbrunnr/
├── README.md                          # this file's implementation companion
├── manifests/                         # one YAML per source
│   ├── norse_sagas_public_domain.yaml
│   ├── wiktionary_en.yaml
│   ├── wikiquote_en.yaml
│   ├── gutenberg_curated_norse.yaml
│   ├── wikipedia_norse_subset.yaml
│   ├── wikipedia_en.yaml
│   ├── stackexchange_selected.yaml
│   ├── arxiv_abstracts.yaml
│   ├── pubmed_oa.yaml
│   └── custom_user.yaml
├── downloaders/
│   ├── http_resumable.py              # generic, resumable, hash-verified
│   ├── torrent.py                     # for big stuff offered via BT
│   ├── kiwix.py                       # ZIM file fetcher
│   └── archive_org.py                 # IA API client
├── ingestion/                         # post-download processing
│   ├── parser_zim.py                  # libzim — Kiwix-format reader
│   ├── parser_xml_wikipedia.py        # raw XML dumps
│   ├── parser_epub.py
│   ├── parser_pdf.py
│   ├── parser_jsonl.py
│   └── parser_text.py
├── indexer.py                         # builds vector index over ingested
├── cli.py                             # heretic library subcommands
└── status.py                          # disk + progress tracking
```

Each manifest YAML records: source URL(s), expected size, SHA-256 (where available), license, attribution string, recommended format, parse strategy. License-tracked end-to-end so `THIRD_PARTY_NOTICES.md` updates automatically when a corpus is added.

---

## CLI workflow — the well-tending ritual

```bash
heretic library list                          # all available sources
heretic library inspect wikipedia_en          # size, license, format, est. time
heretic library download wikipedia_en --confirm
heretic library status                        # progress + disk usage
heretic library index wikipedia_en --backend faiss
heretic library remove wikipedia_en
heretic library reindex --all
heretic library serve                         # mount as MCP server (L5.9 backend)
```

User MUST confirm disk usage before any download — never auto-fetches anything large. Default behavior:

```
$ heretic library download wikipedia_en
Source: Wikipedia English (full)
  Format:        ZIM (Kiwix)
  Download size: 25 GB
  Disk after:    25 GB (compressed) — ZIM stays compressed at rest
  License:       CC BY-SA 4.0
  Attribution:   Wikimedia Foundation contributors
  Estimated:     ~30 min on 100 Mbps

Confirm? [y/N]
```

Resumable. Hash-verified. Can pause / resume across sessions. Failed or partial downloads do not corrupt state.

---

## ZIM vs raw

Where ZIMs exist, **prefer ZIMs**:

- Already compressed (3–4× smaller than raw)
- Mountable — agent queries via `libzim`, no ingestion needed for keyword search
- Maintained by Kiwix (active, MIT-licensed Python bindings)
- Supports browser-style article retrieval via title or full-text search

Raw dumps only when ZIM unavailable (Gutenberg, custom-curated subsets).

For semantic retrieval: build a vector index *over* the ZIM contents on demand. User's choice via config. Default retrieval mode is **keyword** (cheaper, faster, works without GPU); **vector** mode is opt-in per source.

---

## How it plugs into L5.9 Library MCP

The Library MCP server has multiple backends. Mímisbrunnr is one. Others can coexist:

```yaml
senses:
  library:
    enabled: true
    backends:
      - type: file_index
        path: ./library/curated         # your hand-curated notes
      - type: mimisbrunnr
        sources:
          - norse_sagas_public_domain
          - wikipedia_norse_subset
          - gutenberg_curated_norse
        retrieval: keyword              # keyword | vector | hybrid
      - type: mindspark                 # plug in MindSpark ThoughtForge
        endpoint: http://localhost:7777
```

Agent calls `library.search(query)` — the L5.9 server routes across all enabled backends, returns ranked results. The agent does not need to know which corpus answered.

---

## License hygiene (per Volmarr's plunder rules)

Every source's manifest YAML records:

```yaml
license: "CC BY-SA 4.0"
license_url: "https://creativecommons.org/licenses/by-sa/4.0/"
attribution: "Wikimedia Foundation contributors"
attribution_required: true
share_alike_required: true
notice_file_entry: true
```

On download, an entry is appended to `THIRD_PARTY_NOTICES.md` declaring source, version, license, and attribution. On removal, the entry is removed. The notice file is always honest about what's currently sitting in the well.

When the agent retrieves and the response is shown to the user, attribution travels with the citation — the agent sees source metadata and can cite properly.

---

## v0.7.5 starter pack — the Norse seed

The default first download (small, curated, on-theme): **`norse_sagas_public_domain`** + **`wiktionary_en`** + **`gutenberg_curated_norse`**. About 5 GB total. This gives any inhabiting spirit immediate access to the Norse cultural depth that H.E.R.E.T.I.C. is built around — without committing to the larger downloads.

Includes (subject to license verification per work):

- Heimskringla (Snorri Sturluson) — Hollander, Laing translations
- Prose Edda — multiple translations
- Poetic Edda — Bellows, Hollander, Larrington translations
- Volsunga Saga
- Njál's Saga
- Egil's Saga
- Laxdæla Saga
- Eyrbyggja Saga
- Saga of the Greenlanders, Saga of Erik the Red
- Cleasby–Vigfusson Old Norse dictionary
- Volmarr's existing `data/Poetic_Edda_Translation.json` — folded in as a known-good starter

---

*Mímisbrunnr is a name, a vision, and a placeholder. The well does not yet exist as code. When it is built, it will be built from this design.*
