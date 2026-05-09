# THIRD_PARTY_NOTICES.md

**Project:** H.E.R.E.T.I.C. — Host Environment for Realtime Embodiment, Tooling & Interactive Control
**Project license:** MIT
**Copyright:** 2026 Volmarr Wyrd
**Last updated:** 2026-05-08
**Maintained by:** Eirwyn Rúnblóm, Scribe for Vibe Coding

This file records every third-party dependency — whether vendored, runtime-installed, or called as an external service — that HERETIC uses or intends to use. It is organized by the layer of the architecture that owns the dependency. It is updated whenever a new dependency enters the project, and whenever a dependency is removed.

Entries marked **License verification TBD** require Auditor action before the corresponding build phase begins. Entries marked **architectural reference only** indicate that no code was copied or adapted.

---

## Layer L0 — Grunnr (Foundation)

---

### Tauri

**Name:** Tauri
**Repository:** https://github.com/tauri-apps/tauri
**License:** MIT OR Apache-2.0 (dual — HERETIC receives under MIT)
**License URL:** https://github.com/tauri-apps/tauri/blob/dev/LICENSE_MIT
**Attribution requirement:** Preserve MIT copyright notice in distribution NOTICES/
**Usage:** Core desktop application framework. L0 Grunnr (the Tauri Rust backend) and L4 Vébond (the Tauri WebView frontend) are built on Tauri. Provides window management, IPC bridge, subprocess supervisor, and cross-platform native WebView.
**Vendor status:** Build framework — compiled into binary; declared in `Cargo.toml`
**Plunder map:** `docs/plunder/TAURI_PLUNDER_MAP.md`

---

## Layer L1 — Bifröst (Agent Connection)

---

### Hermes Agent (NousResearch)

**Name:** Hermes Agent
**Repository:** https://github.com/NousResearch/hermes-agent
**License:** MIT
**License URL:** https://github.com/NousResearch/hermes-agent/blob/main/LICENSE
**Attribution requirement:** None beyond standard MIT copyright notice; no NOTICE file required
**Usage:** Primary inhabiting spirit. Hermes Agent runs on the Raspberry Pi at `100.101.39.30:8643/v1`. HERETIC's L1 Bifröst connects to it as an OpenAI-compatible HTTP client. No Hermes code is imported, bundled, or distributed by HERETIC. This entry documents the architectural reference relationship and confirms the MIT license.
**Vendor status:** External runtime service (runs on Pi) — architectural reference only. No code plundered.
**Plunder map:** `docs/plunder/HERMES_AGENT_PLUNDER_MAP.md`

---

### OpenClaw

**Name:** OpenClaw
**Repository:** https://github.com/openclaw/openclaw
**License:** MIT
**License URL:** https://github.com/openclaw/openclaw/blob/main/LICENSE
**Attribution requirement:** None beyond standard MIT copyright notice; no NOTICE file required
**Usage:** Tier 1 alternate inhabiting spirit. OpenClaw is a supported agent backend for HERETIC — a user may run OpenClaw instead of or alongside Hermes. HERETIC's L1 Bifröst connects to an OpenClaw endpoint via the same OpenAI-compat protocol. No OpenClaw code is imported, bundled, or distributed by HERETIC.
**Vendor status:** External runtime service — architectural reference only. No code plundered.
**Plunder map:** `docs/plunder/OPENCLAW_PLUNDER_MAP.md`

---

## Layer L2 — Rödd (Voice)

---

### whisper.cpp

**Name:** whisper.cpp
**Repository:** https://github.com/ggerganov/whisper.cpp
**License:** MIT
**License URL:** https://github.com/ggerganov/whisper.cpp/blob/master/LICENSE
**Attribution requirement:** If binary bundled in distribution: include `LICENSE` in distribution `NOTICES/`. If user-installs binary: note in this file only.
**Usage:** Speech-to-text engine for L2 Rödd Hlust (the ear). HERETIC spawns whisper.cpp as a subprocess or uses its Python bindings to transcribe microphone audio. The resulting transcript is emitted as a `voice::transcript` event to L1 Bifröst. Model files (`.gguf`) are downloaded separately by the user; HERETIC does not bundle model weights.
**Vendor status:** External runtime dependency — user installs binary or HERETIC bundles platform binary in release. Not vendored as source.
**Plunder map:** `docs/plunder/WHISPER_CPP_PLUNDER_MAP.md`

---

### ChatterBox TTS

**Name:** ChatterBox TTS
**Repository:** https://github.com/resemble-ai/chatterbox
**License:** MIT — Resemble AI. **Verified 2026-05-07** by Sólrún Hvítmynd (Auditor) via `gh repo view resemble-ai/chatterbox --json name,licenseInfo`.
**License URL:** https://github.com/resemble-ai/chatterbox/blob/main/LICENSE
**Attribution requirement:** Preserve MIT copyright notice in THIRD_PARTY_NOTICES.md. ChatterBox runs as an external service on the Pi; HERETIC holds no ChatterBox source code. No in-source header required.
**Usage:** Text-to-speech engine for L2 Rödd Tunga (the tongue). HERETIC's Tunga MCP server sends HTTP POST requests to the ChatterBox endpoint on the Tailscale network; ChatterBox returns synthesized audio. ChatterBox runs on the Pi; HERETIC does not bundle it.
**Vendor status:** External runtime service (runs on Pi) — HERETIC is a client only
**Plunder map:** No plunder map created — no code plundering planned; MIT license is compatible but no code is used

---

## Layer L3 — Sjón (Vision)

No third-party runtime dependencies. Sjón uses OS native screen capture APIs (DXGI on Windows, CoreGraphics on macOS, X11/Wayland on Linux) through Tauri/Rust platform crates. Those crates (e.g., `xcap`, `scrap`, or equivalent) will be added to this file when the specific crates are selected at v0.5 build time.

---

## Layer L4 — Vébond (UI — Eldahús)

---

### React

**Name:** React (and ReactDOM)
**Repository:** https://github.com/facebook/react
**License:** MIT
**License URL:** https://github.com/facebook/react/blob/main/LICENSE
**Attribution requirement:** Preserve MIT copyright notice in distribution
**Usage:** L4 Vébond / Eldahús frontend component framework. The Summoning Circle UI, ceremony controls, sense status indicators, and voice waveform display are built in React/TypeScript.
**Vendor status:** Build dependency — compiled into the frontend bundle; declared in `package.json`
**Plunder map:** Not required — React is a standard framework dependency with no code adaptation.

---

## Layer L5 — Skilningr (MCP Sense Hub)

---

### MCP Python SDK (Anthropic)

**Name:** Model Context Protocol Python SDK
**Repository:** https://github.com/modelcontextprotocol/python-sdk
**PyPI package:** `mcp`
**License:** MIT
**License URL:** https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE
**Attribution requirement:** Preserve MIT copyright notice in distribution `NOTICES/` (or pip-installed: note here only)
**Usage:** Foundation library for all L5.x sense subprocesses. Every sense MCP server (`heretic-sense-minni`, `heretic-sense-skepja`, etc.) uses the MCP Python SDK to implement the `initialize` / `tools/list` / `tools/call` lifecycle over stdio transport. This is a runtime pip dependency, not vendored source.
**Vendor status:** External runtime dependency via `pip install mcp`. Declared in `requirements.txt`.
**Plunder map:** `docs/plunder/MCP_SDK_PLUNDER_MAP.md`

---

## Layer L5.5 — Smiðja (Blender Sense)

---

### Seidr-Smidja (Brúarhönd v0.1)

**Name:** Seidr-Smidja / Brúarhönd
**Repository:** Local sibling repo at `C:/Users/volma/runa/Seidr-Smidja` (GitHub: `https://github.com/hrabanazviking/Seidr-Smidja`)
**License:** MIT
**License URL:** Seidr-Smidja's own MIT LICENSE file
**Attribution requirement:** Preserve MIT copyright notice; note Volmarr Wyrd as author
**Usage:** L5.5 Smiðja sense server wraps the Seidr-Smidja Brúarhönd daemon. The Brúarhönd daemon runs as an external process; HERETIC's `heretic-sense-smidja` subprocess calls its HTTP REST API to control Blender (screenshot, click, hotkey, vroid_open, vroid_export). Seidr-Smidja is owned by Volmarr — same ecosystem, MIT license, clean for integration.
**Vendor status:** External runtime service (runs as sibling process on laptop) — HERETIC calls its HTTP API. Not vendored.
**Plunder map:** Not a plunder target — first-party Volmarr project in the same ecosystem.

---

### Blender (application)

**Name:** Blender
**Repository:** https://www.blender.org / https://github.com/blender/blender
**License:** GPL-3.0
**License URL:** https://www.blender.org/about/license/
**Attribution requirement:** HERETIC does not bundle or distribute Blender. User installs Blender independently. No GPL code enters HERETIC.
**Usage:** External application controlled via L5.5 Smiðja through Seidr-Smidja Brúarhönd. Blender is a Zone 4 dependency (external application — not HERETIC's code at all, per `ARCHITECTURE.md` §7). HERETIC merely calls its API via MCP; its GPL license has no effect on HERETIC's MIT grant.
**Vendor status:** External application — user installs independently. HERETIC does not bundle.
**Plunder map:** Not required — Zone 4 external application.

---

## Layer L5.9 — Mímisbrunnr (Library Sense)

---

### libzim

**Name:** libzim
**Repository:** https://github.com/openzim/libzim
**PyPI binding:** `libzim`
**License:** GPL-2.0-or-later
**License URL:** https://github.com/openzim/libzim/blob/main/COPYING
**Attribution requirement:** HERETIC does not bundle or distribute libzim. User installs via `pip install libzim` or OS package manager. No GPL code enters HERETIC. This entry discloses the dependency for transparency.
**Usage:** Optional runtime dependency for L5.9 Mímisbrunnr ZIM-format library backend. HERETIC's `parser_zim.py` imports libzim at runtime to read `.zim` files downloaded by the user. If libzim is not installed, the ZIM backend degrades gracefully to `UNAVAILABLE`.
**Vendor status:** External runtime dependency — user installs separately. **NEVER vendored. NEVER bundled. GPL boundary absolute.**
**Plunder map:** `docs/plunder/LIBZIM_PLUNDER_MAP.md`
**GPL compliance note:** Dynamic runtime import pattern only. No libzim source or binary enters HERETIC's distribution archive. Detailed compliance analysis in the plunder map.

---

### python-libzim (kiwix/openzim Python bindings)

**Name:** python-libzim
**Repository:** https://github.com/openzim/python-libzim
**PyPI package:** `libzim` (same pip package as above — python-libzim IS the pip `libzim` package)
**License:** GPL-3.0 — openzim/kiwix. **Verified 2026-05-07** by Sólrún Hvítmynd (Auditor) via `gh repo view openzim/python-libzim --json name,licenseInfo`. See `docs/plunder/KIWIX_TOOLS_PLUNDER_MAP.md`.
**Attribution requirement:** GPL-3.0. Same external-runtime-dep pattern as libzim C++ library — `try/except ImportError` guard in `parser_zim.py`; no GPL code enters HERETIC's distribution archive.
**Usage:** Same as libzim entry above — python-libzim provides the Python API surface used by `parser_zim.py`.
**Vendor status:** External runtime dependency — user installs via `pip install libzim`. **NEVER vendored.**
**Plunder map:** `docs/plunder/KIWIX_TOOLS_PLUNDER_MAP.md`

---

### kiwix-tools

**Name:** kiwix-tools (kiwix-serve, kiwix-manage, kiwix-search)
**Repository:** https://github.com/kiwix/kiwix-tools
**License:** GPL-3.0
**License URL:** https://github.com/kiwix/kiwix-tools/blob/main/COPYING
**Attribution requirement:** HERETIC does not bundle or distribute kiwix-tools. User installs via OS package manager if the kiwix-serve HTTP backend option is used.
**Usage:** Optional companion tooling for L5.9 Mímisbrunnr. If Mímisbrunnr uses the `kiwix-serve` HTTP backend (instead of direct libzim Python binding), kiwix-serve is called as an external subprocess serving ZIM files over localhost HTTP. HERETIC communicates with it over HTTP — no GPL code integration.
**Vendor status:** External runtime dependency — user installs separately (optional). **NEVER vendored. NEVER bundled.**
**Plunder map:** `docs/plunder/KIWIX_TOOLS_PLUNDER_MAP.md`

---

### MindSpark ThoughtForge

**Name:** MindSpark ThoughtForge
**Repository:** https://github.com/hrabanazviking/MindSpark_ThoughtForge (local: `C:/Users/volma/runa/MindSpark_ThoughtForge`)
**License:** MIT
**License URL:** MindSpark's own MIT LICENSE file
**Attribution requirement:** Preserve MIT copyright notice; note Volmarr Wyrd as author
**Usage:** Optional backend for L5.9 Mímisbrunnr library sense. When enabled, HERETIC's library sense sends HTTP POST requests to MindSpark's RAG endpoint at `localhost:7777`. MindSpark provides vector search, document ingestion, and cognitive scaffolding. MindSpark is owned by Volmarr — same ecosystem, MIT license, clean for integration. Status: v1.2.0 shipped, 620 tests.
**Vendor status:** External runtime service (runs as sibling process on laptop). Not vendored.
**Plunder map:** Not a plunder target — first-party Volmarr project.

---

## Optional Dependencies (L5.9 Mímisbrunnr — vector indexing)

---

### faiss-cpu / faiss-gpu

**Name:** FAISS (Facebook AI Similarity Search)
**Repository:** https://github.com/facebookresearch/faiss
**PyPI package:** `faiss-cpu` or `faiss-gpu`
**License:** MIT
**License URL:** https://github.com/facebookresearch/faiss/blob/main/LICENSE
**Attribution requirement:** Preserve MIT copyright notice
**Usage:** Optional vector indexing for L5.9 Mímisbrunnr when `retrieval: vector` is configured. Used to build and query FAISS indices over ZIM/corpus content for semantic search.
**Vendor status:** Optional runtime pip dependency — `faiss-cpu` (or `faiss-gpu` for hardware acceleration). `pip install faiss-cpu`.
**License verification status:** **Verified MIT 2026-05-07** by Sólrún Hvítmynd (Auditor) via `gh repo view facebookresearch/faiss --json name,licenseInfo`. Current FAISS repo is unambiguously MIT.

---

### sentence-transformers

**Name:** sentence-transformers
**Repository:** https://github.com/UKPLab/sentence-transformers
**PyPI package:** `sentence-transformers`
**License:** Apache-2.0
**License URL:** https://github.com/UKPLab/sentence-transformers/blob/master/LICENSE
**Attribution requirement:** Apache-2.0: preserve license, copyright notices, and NOTICE file if present. Mark modified files if any.
**Usage:** Optional embedding library for L5.9 Mímisbrunnr vector retrieval. Used to encode article text into embedding vectors for FAISS indexing.
**Vendor status:** Optional runtime pip dependency — `pip install sentence-transformers`.
**License verification status:** **Verified Apache-2.0 2026-05-07** by Sólrún Hvítmynd (Auditor) via `pip show sentence-transformers` (v5.3.0 installed, `License: Apache 2.0`) and `gh repo view UKPLab/sentence-transformers` (redirects to huggingface/sentence-transformers). Repository has migrated from UKPLab org to huggingface org; license unchanged.

---

## External Services (Not Code — Zone 4)

---

### SillyTavern (architectural reference only — NOT USED)

**Name:** SillyTavern
**Repository:** https://github.com/SillyTavern/SillyTavern
**License:** AGPL-3.0
**License URL:** https://github.com/SillyTavern/SillyTavern/blob/release/LICENSE
**Attribution requirement:** Not applicable — no code copied or adapted. This entry exists to document the explicit decision not to use SillyTavern code due to AGPL incompatibility.
**Usage:** Studied as an architectural reference for AI companion UI patterns, persona/character card design, and plugin architectures. **No code was copied. No code was adapted. No code was derived. HERETIC's MIT license is incompatible with AGPL-3.0.** This entry records the study and the boundary.
**Vendor status:** Not used. Not installed. Not bundled. Not referenced in code.
**Plunder map:** `docs/plunder/SILLYTAVERN_PLUNDER_MAP.md`

---

### WYRD Protocol

**Name:** WYRD Protocol (World-Yielding Realtime Data)
**Repository:** https://github.com/hrabanazviking/WYRD-Protocol-World-Yielding-Real-time-Data-AI-world-model (local: `C:/Users/volma/runa/WYRD-Protocol`)
**License:** MIT
**License URL:** WYRD Protocol's own MIT LICENSE file
**Attribution requirement:** Preserve MIT copyright notice; note Volmarr Wyrd as author
**Usage:** Optional L5.8 Nýr Limr custom MCP plugin. When a user wants world-model access during ceremonies, they run WYRD Protocol as a local MCP server and add it to `heretic.yaml` under `senses.custom.plugins`. HERETIC calls its MCP tool surface. WYRD Protocol is owned by Volmarr — same ecosystem, MIT license, clean for integration. Status: v1.0.0 released, all 19 phases complete.
**Vendor status:** External runtime service (optional, user-configured). Not vendored.
**Plunder map:** Not a plunder target — first-party Volmarr project.

---

## Corpus Data Attribution (L5.9 Mímisbrunnr — downloaded by user)

The following corpus entries are added **automatically** when a user downloads a library source via `heretic library download <source_id> --confirm`. They appear here as a template for what each source's attribution entry will look like when fully populated. At ship time, only entries for corpora that the user has actually downloaded should appear in a running installation's `THIRD_PARTY_NOTICES.md`.

---

### Wikimedia Foundation corpora (Wikipedia, Wiktionary, Wikiquote ZIM files)

**Name:** Wikipedia / Wiktionary / Wikiquote (Wikimedia Foundation)
**License:** CC BY-SA 4.0
**License URL:** https://creativecommons.org/licenses/by-sa/4.0/
**Attribution:** "Wikipedia content is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License. Wikipedia® is a registered trademark of the Wikimedia Foundation, Inc."
**Attribution required:** Yes — must appear in any retrieval result that surfaces Wikipedia content to users. Attribution travels with the result (HERETIC's citation format).
**Share-alike required:** Yes — if Wikipedia content is remixed and distributed, the resulting work must also be CC BY-SA 4.0. HERETIC does not remix or redistribute corpus content; it retrieves and displays it. The share-alike clause does not apply to retrieval.
**Status in repository:** Template only — actual entry populated when user downloads a Wikimedia ZIM.

---

### Project Gutenberg (public domain works)

**Name:** Project Gutenberg
**License:** Public domain (works pre-1928) — no copyright restriction on content
**Attribution:** Works from Project Gutenberg are in the public domain. The Project Gutenberg trademark and branding require that content served as "from Project Gutenberg" links back to the original Project Gutenberg source. HERETIC's attribution field for Gutenberg results will cite the Project Gutenberg item ID.
**Status in repository:** Template for future catalog sources. The v0.7 Norse starter pack entries are named individually below.

---

## Norse Starter Pack — v0.7 Mímisbrunnr (Corpus Data Attribution, Named Entries)

These five texts are the authoritative sources constituting the Norse starter pack shipped in HERETIC v0.7. They are public-domain works translated before 1928 by translators who died more than 70 years ago. The texts were sourced exclusively from Project Gutenberg, which has verified their public-domain status in the United States of America.

No copyright protection attaches to the text content. No license compliance is required beyond attribution. The SHA-256 values below were computed from the canonical UTF-8 text files as served by Project Gutenberg on 2026-05-08 (verified via `scripts/lock_hashes.py`, HERETIC development branch commit `d555397`).

---

### Prose Edda — Snorri Sturluson (~1220 CE) / trans. Arthur Gilchrist Brodeur (1916)

**Source title:** The Prose Edda of Snorri Sturluson
**Original work:** Written ~1220 CE by Snorri Sturluson (1179–1241), Icelandic chieftain, historian, and poet
**Translation:** Arthur Gilchrist Brodeur (1916); Brodeur died 1971 — translation is public domain (pre-1928 publication, author deceased >70 years)
**Project Gutenberg item ID:** #18947
**Project Gutenberg URL:** https://www.gutenberg.org/files/18947/18947-0.txt
**Manifest source ID:** `prose_edda_brodeur`
**Approximate size:** 388 KB (387,653 bytes)
**SHA-256 (UTF-8 text, 2026-05-08):** `a46fb8abc9e96c4bf757571f25cf55a1d2999d780271765b9dd54f09f70f8f32`
**License:** Public domain in the United States of America (and in most jurisdictions). Project Gutenberg License applies to Project Gutenberg's electronic presentation; the text itself is free of copyright.
**Redistribution terms:** Freely redistributable. Attribution to Snorri Sturluson (author) and Arthur Gilchrist Brodeur (translator) is customary and encouraged.
**Notes:** The Prose Edda is the principal source for Norse mythology and Skaldic poetics. It comprises the Gylfaginning (cosmology), Skáldskaparmál (poetic language), and Háttatal (verse forms). Brodeur's 1916 translation is standard in English scholarship.

---

### Poetic Edda — Anonymous (~9th–13th century CE) / trans. Henry Adams Bellows (1923)

**Source title:** The Poetic Edda
**Original work:** Anonymous collection of Old Norse poems, compiled ~13th century in Iceland; individual poems date from the 9th–12th centuries CE
**Translation:** Henry Adams Bellows (1923); Bellows died 1939 — translation is public domain (pre-1928 publication, author deceased >70 years)
**Project Gutenberg item ID:** #73533
**Project Gutenberg URL:** https://www.gutenberg.org/ebooks/73533.txt.utf-8
**Manifest source ID:** `poetic_edda_bellows`
**Approximate size:** 978 KB (977,831 bytes)
**SHA-256 (UTF-8 text, 2026-05-08):** `50710042c87eb3075c74a9f36cd7dd0ffdc7bd7ba3bb7d5dee0f62db88b28e3c`
**License:** Public domain in the United States of America. Project Gutenberg License applies to the electronic presentation.
**Redistribution terms:** Freely redistributable. Attribution to the translator Henry Adams Bellows is customary.
**Notes:** The Poetic Edda (Codex Regius) is the primary source of Norse mythological and heroic poetry, including the Völuspá, Hávamál, Rígsþula, and the Sigurd/Völsung cycle. Bellows's 1923 translation includes extensive scholarly commentary. Note: an earlier proposed URL (`sacred-texts.com/neu/poe/`) was rejected in favor of the canonical Project Gutenberg URL due to unclear redistribution terms on sacred-texts.com. Project Gutenberg's public-domain verification is authoritative.

---

### Heimskringla — Snorri Sturluson (~1230 CE) / trans. Samuel Laing (1844)

**Source title:** Heimskringla, or the Chronicle of the Kings of Norway
**Original work:** Written ~1230 CE by Snorri Sturluson (1179–1241). The Ynglinga Saga opens the collection; it continues through the life of Óláfr Haraldsson and later kings.
**Translation:** Samuel Laing (1844); Laing died 1868 — translation is public domain (pre-1928 publication, author deceased >70 years)
**Project Gutenberg item ID:** #598
**Project Gutenberg URL:** https://www.gutenberg.org/ebooks/598.txt.utf-8
**Manifest source ID:** `heimskringla_laing`
**Approximate size:** 1.75 MB (1,748,862 bytes)
**SHA-256 (UTF-8 text, 2026-05-08):** `dc794ff1dbaf88a9fee5172e5594adcb3de79316c4f281508fc3b8a6dd83d6a1`
**License:** Public domain in the United States of America. Project Gutenberg License applies to the electronic presentation.
**Redistribution terms:** Freely redistributable. Attribution to Snorri Sturluson (author) and Samuel Laing (translator) is customary.
**Notes:** Heimskringla is the most comprehensive history of the Norwegian kings composed in the medieval period, drawing on oral tradition, earlier sagas, and Snorri's own synthesis. Laing's 1844 translation was the standard English text for over a century. The Gutenberg edition is the largest file in the Norse starter pack (~1.75 MB).

---

### Saga of the Volsungs — Anonymous (~1270 CE) / trans. William Morris and Eiríkr Magnússon (1888)

**Source title:** The Story of the Volsungs (Volsunga Saga)
**Original work:** Anonymous Icelandic prose saga, compiled ~1270 CE, drawing on older heroic poetry including the Poetic Edda Sigurd cycle. The foundational source for Wagner's Ring Cycle and Tolkien's Sigurd and Gudrún.
**Translation:** William Morris (1834–1896) and Eiríkr Magnússon (1833–1913), 1888; both translators deceased >70 years — translation is public domain (pre-1928 publication, authors deceased)
**Project Gutenberg item ID:** #1152
**Project Gutenberg URL:** https://www.gutenberg.org/files/1152/1152-0.txt
**Manifest source ID:** `volsunga_saga_morris`
**Approximate size:** 331 KB (330,843 bytes)
**SHA-256 (UTF-8 text, 2026-05-08):** `b6ecaf400f47608c7497465fe5029268fb57c1a456c5bb99a1633fd6fc04053b`
**License:** Public domain in the United States of America. Project Gutenberg License applies to the electronic presentation.
**Redistribution terms:** Freely redistributable. Attribution to William Morris and Eiríkr Magnússon (translators) is customary.
**Notes:** The Morris/Magnússon translation is notable for its deliberately archaic and elevated register, intended to reflect the saga's heroic tone. The Volsunga Saga covers the genealogy of the Volsung clan from Odin through Sigurd Fáfnisbane and the tragedies that follow. This is the earliest and most complete prose account of the Sigurd legend.

---

### Saga of Erik the Red — Anonymous (~1265 CE) / trans. J. Sephton (1880)

**Source title:** The Saga of Erik the Red (Eiríks saga rauða)
**Original work:** Anonymous Icelandic saga, compiled ~1265 CE, one of the two principal Vinland sagas. Narrates the Norse exploration of North America (Vínland) by Leif Eiríksson and Þorfinnr Karlsefni.
**Translation:** J. Sephton (1880); Sephton died 1883 — translation is public domain (pre-1928 publication, author deceased >70 years)
**Project Gutenberg item ID:** #17946
**Project Gutenberg URL:** https://www.gutenberg.org/files/17946/17946-0.txt
**Manifest source ID:** `erik_red_saga`
**Approximate size:** 79 KB (79,340 bytes)
**SHA-256 (UTF-8 text, 2026-05-08):** `6232afa6e0c384eb51d8a32df92fce7ba25cc15382cc9df45e2b0b2edb2b9c42`
**License:** Public domain in the United States of America. Project Gutenberg License applies to the electronic presentation.
**Redistribution terms:** Freely redistributable. Attribution to J. Sephton (translator) is customary.
**Notes:** Eiríks saga rauða is the shorter and more geographically precise of the two Vinland sagas (the other being Grænlendinga saga). It contains the earliest written account of Europeans reaching North America and describes the skræling (indigenous people) encounters. Sephton's 1880 translation is the earliest standard English text. The smallest file in the Norse starter pack (~79 KB).

---

## License Verification TBD — Auditor Action Required

All four previously-TBD entries have been resolved. See audit report `docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md` §B for full evidence.

| Dependency | Required for | Status |
|---|---|---|
| ChatterBox TTS | v0.2 First Voice | **Resolved 2026-05-07 — MIT (resemble-ai/chatterbox)** |
| python-libzim (pip `libzim` SPDX) | v0.7.5 First Drink | **Resolved 2026-05-07 — GPL-3.0 (openzim/python-libzim)** |
| faiss-cpu | v0.7.5 First Drink | **Resolved 2026-05-07 — MIT (facebookresearch/faiss)** |
| sentence-transformers | v0.7.5 First Drink | **Resolved 2026-05-07 — Apache-2.0 (huggingface/sentence-transformers)** |

---

*This file is maintained by Eirwyn Rúnblóm, Scribe for Vibe Coding.*
*Every borrowed thing is named here. Every name carries its lineage.*
*Updated: 2026-05-08 — v0.7 Norse starter pack corpus entries added (L-1 fulfillment)*
