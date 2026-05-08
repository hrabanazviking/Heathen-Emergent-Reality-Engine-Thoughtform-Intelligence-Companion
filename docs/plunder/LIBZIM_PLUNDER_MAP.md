# libzim — Plunder Map

**Map authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding
**Status:** studying — no code adapted yet; required for v0.7.5 First Drink at the Well (L5.9 Mímisbrunnr ZIM reading)

---

## Upstream Identity

| Field | Value |
|---|---|
| Project name | libzim |
| Repository | https://github.com/openzim/libzim |
| PyPI binding | `libzim` (Kiwix-maintained Python bindings — separate package) |
| Version as of write | libzim C++ library: 9.x (verify at time of Mímisbrunnr build) |
| Primary maintainer | openZIM project (Kiwix Foundation) |
| License | **GPL-2.0-or-later** |
| License URL | https://github.com/openzim/libzim/blob/main/COPYING |
| License verification status | **Verified GPL-2.0-or-later 2026-05-07** (COPYING file in repo confirms GPL version 2 or later, copyright Kiwix team) |

---

## Upstream License

**GPL-2.0-or-later (GNU General Public License, version 2 or any later version).**

This is a **copyleft license**. The GPL requires that any work that is a derivative of GPL-licensed code, or that links with it at compile time, must itself be distributed under the GPL. This imposes a critical architectural constraint on how HERETIC may use libzim.

---

## Compatibility Verdict

**CONDITIONAL — GPL copyleft requires dynamic-link / external-process compliance pattern. Never vendor. Never statically link.**

### The GPL Boundary Problem

HERETIC is MIT-licensed. If libzim were vendored into `vendor/libzim/` or statically linked into a HERETIC binary, the resulting binary would be a derivative work of GPL-licensed code and would need to be distributed under the GPL — which conflicts with HERETIC's MIT grant. This is legally unacceptable.

### The Correct Architecture Pattern: Dynamic Runtime Dependency

The lawful pattern is:
1. **libzim is an installed runtime dependency** — the user installs it via their OS package manager (`apt install libzim-dev`, `brew install libzim`, etc.) or via pip (`pip install libzim`).
2. **HERETIC's Mímisbrunnr code imports libzim via the Python bindings at runtime** — Python's dynamic import is a runtime call to a separately-installed library, not a compile-time link. This is the same pattern used by many MIT-licensed tools that call GPL-licensed libraries at runtime (e.g., ffmpeg, GPL libraries called via subprocess).
3. **libzim's GPL code does not enter HERETIC's source or distribution archive.** The user acquires and installs libzim separately; HERETIC merely calls it through a defined API.
4. **HERETIC declares the dependency clearly** in `THIRD_PARTY_NOTICES.md`, instructs users to install libzim themselves, and does not bundle or redistribute any libzim source or binary.

This pattern is legally well-established and is how tools like `youtube-dl`, MkDocs plugins, and many scientific Python packages consume GPL libraries without becoming GPL themselves.

### What HERETIC MAY do
- Import `libzim` in `heretic/sense_hub/library/mimisbrunnr/ingestion/parser_zim.py` at runtime.
- Call `libzim`'s Python API to open and read `.zim` files from disk.
- Instruct users to `pip install libzim` or install via their package manager.
- Declare libzim as a runtime dependency in documentation without distributing its code.

### What HERETIC MUST NOT do
- Vendor libzim source into `vendor/` — **forbidden, absolutely**.
- Include libzim binaries in HERETIC's distribution package.
- Statically compile libzim into any HERETIC binary.
- Re-export or wrap libzim's API in a way that creates a derivative work.
- Fail to disclose the GPL dependency to users (transparency required; see Attribution below).

---

## What We Plunder

**No source is plundered.** libzim is used exclusively as an installed runtime dependency, called through its documented Python API.

### Runtime API usage (not code plunder)
- `libzim.Archive` — opens a `.zim` file from disk and provides iteration over articles.
- `libzim.Archive.get_entry_by_path(path)` — retrieve specific articles.
- `libzim.Archive.get_metadata(key)` — read ZIM metadata (title, description, language, etc.).
- Full-text search index if the ZIM includes one: `libzim.Archive.get_search_results(query)`.
- Attribution metadata extraction from ZIM manifests.

### What we design locally against the API (not copied from libzim)
- `heretic/sense_hub/library/mimisbrunnr/ingestion/parser_zim.py` — HERETIC's own ZIM parser class that wraps libzim calls, handles errors gracefully, extracts attribution metadata, and produces results in HERETIC's internal format.
- The attribution-with-result pattern (`THIRD_PARTY_NOTICES.md` entry generated automatically on corpus download) — HERETIC-native.

---

## What We DO NOT Plunder

- Any libzim C++ source code — **forbidden entirely** (GPL).
- Any libzim Python binding source code — these are also GPL; only the installed package's API surface is consumed.
- The libzim test suite or build system.
- The ZIM format specification is documented by openZIM — we read the spec but implement against it only through the libzim API, not by reimplementing the format.

---

## Local Domain Ownership

| HERETIC layer | True Name | Owns this integration |
|---|---|---|
| L5.9 Mímisbrunnr | Mímisbrunnr (mimisbrunnr) — Mímir's Well | ZIM file reading: `parser_zim.py` calls libzim at runtime; libzim is declared as an optional runtime dep for this sense |
| L0 Grunnr | Grunnr (grunnr) | Config: `senses.library.backends[type=mimisbrunnr].data_dir` (where ZIM files live) |

libzim is **exclusively used within** `heretic/sense_hub/library/mimisbrunnr/ingestion/parser_zim.py`. No other module imports it. If libzim is absent, Mímisbrunnr's ZIM backend gracefully degrades to `UNAVAILABLE` status — the sense still functions for file-index and MindSpark backends.

---

## Public Interface

Inside HERETIC, libzim is surfaced as follows:

- `heretic/sense_hub/library/mimisbrunnr/ingestion/parser_zim.py` is the one file that imports libzim.
- Import is wrapped in a `try/except ImportError` guard: if libzim is not installed, the ZIM backend reports `status: unavailable` and `entry_count: 0` in `library.list_sources()`. The sense does not crash.
- No libzim types or classes escape `parser_zim.py` — results are converted to HERETIC-internal dicts before being returned to Skilningr.
- The `library.search()` tool result always carries attribution strings derived from ZIM metadata — this is the sense-level attribution contract.

---

## Attribution Requirements

| Requirement | Status |
|---|---|
| Preserve LICENSE file | libzim is not distributed by HERETIC — no LICENSE file to preserve in repo. Disclose in `THIRD_PARTY_NOTICES.md`. |
| NOTICE file required | Not required for GPL when used as an external runtime dep (no code copied) |
| In-source headers required | Not required — no libzim source is copied or adapted |
| THIRD_PARTY_NOTICES.md entry | **Yes — required, and must clearly state: GPL-2.0-or-later, external runtime dep, user installs separately, HERETIC does not bundle or redistribute** |
| User disclosure | Yes — the installation documentation and `heretic library` CLI help text must tell users that the ZIM feature requires installing libzim, which is GPL-licensed |
| Trademark / branding | No trademark concerns |

---

## Verification Status

- License re-verified: **2026-05-07** — GPL-2.0-or-later confirmed at https://github.com/openzim/libzim/blob/main/COPYING
- Python binding package: `libzim` on PyPI — **License verification TBD** for the Python bindings specifically. The C++ library is GPL; the Python bindings are maintained by Kiwix. Verify whether `pip install libzim` installs GPL-licensed binding code or an LGPL/MIT wrapper. This distinction matters for the compliance analysis. **Auditor action required before v0.7.5 implementation.**
- Current version: verify at build time (https://pypi.org/project/libzim/)
- ZIM format specification: https://wiki.openzim.org/wiki/ZIM_file_format — public documentation, no license concern.

---

## Vendor Path

**External runtime dependency — user installs separately. NEVER vendored.**

Declared as an optional runtime dependency:
- Documentation: "To use the ZIM-format library backend, install libzim: `pip install libzim` or via your OS package manager."
- `requirements-optional.txt` or equivalent: `libzim>=3.0` (verify minimum version at build time).
- `heretic.yaml` documentation: `senses.library.backends[type=mimisbrunnr]` is only available when libzim is installed.

**Zero GPL code enters the HERETIC repository. Zero GPL code enters HERETIC's distribution packages. Zero GPL binaries are bundled. This boundary is absolute and inviolable.**

---

## GPL Risk Register

| Risk | Mitigation |
|---|---|
| Developer accidentally vendors libzim | `DOMAIN_MAP.md` §vendor/ explicitly states: no GPL code enters vendor/. `RULES.AI.md` carried forward. Code review gate. |
| Distribution pipeline bundles libzim binary | Release build scripts must include an explicit GPL-exclusion check. CI gate: scan distribution archive for GPL files. |
| Python binding turns out to have GPL obligations beyond the C++ library | **License verification TBD (Auditor action required)** — see Verification Status above. |
| User confusion about why ZIM doesn't work | `heretic library status` CLI command must explain clearly when libzim is absent and how to install it. |

---

*Plunder map authored by Eirwyn Rúnblóm, 2026-05-07.*
*The well of wisdom calls from behind a GPL wall. We drink from outside it, through the proper channel, without crossing the threshold.*
