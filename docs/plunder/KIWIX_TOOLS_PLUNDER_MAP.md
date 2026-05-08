# Kiwix Tools and python-libzim — Plunder Map

**Map authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding
**Status:** studying — no code adapted yet; relevant for v0.7.5 First Drink at the Well (L5.9 Mímisbrunnr)

---

## Upstream Identity — Two Distinct Projects

This map covers two related Kiwix projects that are both relevant to Mímisbrunnr's ZIM download and serving infrastructure. They have different licenses and different usage patterns.

### Project A: kiwix-tools

| Field | Value |
|---|---|
| Project name | kiwix-tools |
| Repository | https://github.com/kiwix/kiwix-tools |
| Contains | `kiwix-serve` (HTTP server), `kiwix-manage`, `kiwix-search` CLI tools |
| Version as of write | latest release — verify at build time |
| Primary maintainer | Kiwix team |
| License | **GPL-3.0** |
| License URL | https://github.com/kiwix/kiwix-tools/blob/main/COPYING |
| License verification status | **Verified GPL-3.0 2026-05-07** (COPYING file confirms GPL version 3) |

### Project B: python-libzim

| Field | Value |
|---|---|
| Project name | python-libzim |
| Repository | https://github.com/openzim/python-libzim |
| PyPI package | `libzim` |
| Contains | Python bindings for libzim C++ library |
| Version as of write | verify at https://pypi.org/project/libzim/ |
| Primary maintainer | openZIM project (Kiwix Foundation) |
| License | **GPL-3.0** |
| License URL | https://github.com/openzim/python-libzim/blob/main/LICENSE |
| License verification status | **License verification TBD** — the repository states GPL-3.0, but the exact license of the installed pip package must be confirmed at the SPDX level before implementation. **Auditor action required before v0.7.5.** |

---

## Upstream License

### kiwix-tools
**GPL-3.0 (GNU General Public License, version 3).**
Copyleft license. Stricter than GPL-2.0 in certain respects (no "GPL-2.0-or-later" compatibility unless the receiving code is also GPLv3-compatible). Stronger patent termination clause.

### python-libzim
**GPL-3.0** (claimed; **License verification TBD** — confirm at SPDX level before implementation).

---

## Compatibility Verdict

### kiwix-tools
**CONDITIONAL — same dynamic-link / external-process compliance pattern as libzim. GPL code is never vendored or bundled.**

kiwix-tools are CLI binaries. HERETIC's Mímisbrunnr does not use kiwix-tools at runtime in the standard workflow — it uses libzim Python bindings directly for ZIM reading. However, kiwix-tools may be useful to a user as companion tools (e.g., `kiwix-serve` to serve ZIM files via HTTP as an alternative backend, `kiwix-manage` for ZIM catalog management). If HERETIC ever calls `kiwix-serve` as a subprocess, that subprocess is an external GPL binary — no code integration occurs. The same dynamic-dependency pattern applies.

**HERETIC must never bundle kiwix-tools binaries in its distribution package.** Users install kiwix-tools independently via their package manager.

### python-libzim
**CONDITIONAL — same GPL compliance pattern as libzim.** The Python bindings are consumed at runtime via `pip install libzim`. The `libzim` pip package is the python-libzim project. All GPL boundary constraints from the `LIBZIM_PLUNDER_MAP.md` apply here identically.

**Additional concern:** python-libzim is listed as GPL-3.0, while the underlying C++ libzim is GPL-2.0-or-later. These are compatible (GPL-3 is one of the "later versions" allowed by GPL-2.0-or-later). No conflict between the two. However, this means that consuming the Python bindings makes the installed environment GPL-3.0 (not merely GPL-2.0), which is the stricter bound. HERETIC's compliance posture is unchanged — dynamic runtime dep, never bundled, user installs.

---

## What We Plunder

**No source is plundered from either project.** Both are consumed exclusively as installed runtime dependencies called through their documented APIs.

### kiwix-tools (if used at all)
- Optional: `kiwix-serve` may be used as a subprocess by Mímisbrunnr to serve ZIM files via HTTP (as an alternative to direct libzim binding access). This is architectural reference only — not yet decided for v0.7.5.
- If used: HERETIC calls `kiwix-serve` as an external subprocess; it serves ZIM content over localhost HTTP; HERETIC's library sense queries that HTTP endpoint. No GPL code crosses into HERETIC.

### python-libzim
- The `libzim` PyPI package — same usage as described in `LIBZIM_PLUNDER_MAP.md`. This map adds the note that the Python binding is its own project (python-libzim / openzim/python-libzim) with its own GPL-3.0 license.
- `libzim.Archive`, `libzim.Archive.get_entry_by_path()`, `libzim.Archive.get_search_results()` — API surface only. HERETIC's `parser_zim.py` calls these at runtime.

---

## What We DO NOT Plunder

- Any kiwix-tools source code — **forbidden** (GPL-3.0).
- Any python-libzim binding source code — **forbidden** (GPL-3.0).
- The kiwix-serve HTTP server implementation — we consume its HTTP interface if used, but the binary is external.
- The kiwix-manage catalog format details — referenced from documentation only.

---

## Local Domain Ownership

| HERETIC layer | True Name | Owns this integration |
|---|---|---|
| L5.9 Mímisbrunnr | Mímisbrunnr (mimisbrunnr) — Mímir's Well | ZIM file reading (python-libzim runtime dep); optional kiwix-serve subprocess invocation (if HTTP backend chosen) |
| L0 Grunnr | Grunnr (grunnr) | Config: kiwix-serve endpoint (if used) configured in `heretic.yaml` — never a hardcoded path |

kiwix-tools and python-libzim are exclusively within `heretic/sense_hub/library/mimisbrunnr/`. They are strictly optional — Mímisbrunnr degrades gracefully if neither is installed.

---

## Attribution Requirements

| Requirement | Status |
|---|---|
| Preserve LICENSE file | Neither project is distributed by HERETIC — no LICENSE files in repo. Disclose in `THIRD_PARTY_NOTICES.md`. |
| NOTICE file required | Not required — no code copied |
| In-source headers required | Not required — no source adapted |
| THIRD_PARTY_NOTICES.md entry | **Yes — both projects must appear in THIRD_PARTY_NOTICES.md, both clearly labeled GPL-3.0, both marked as external runtime deps user installs separately** |
| User disclosure | Yes — `heretic library` CLI help and installation docs must inform users of GPL dependency status for ZIM features |

---

## Verification Status

### kiwix-tools
- License re-verified: **2026-05-07** — GPL-3.0 confirmed at https://github.com/kiwix/kiwix-tools/blob/main/COPYING

### python-libzim
- License: **License verification TBD** — repository claims GPL-3.0; must confirm the installed PyPI package's SPDX identifier before v0.7.5. Check: `pip show libzim` after install, or `cat $(pip show libzim | grep Location | awk '{print $2}')/libzim-*.dist-info/LICENSE`.
- **Auditor action required before v0.7.5 build phase.**

---

## Vendor Path

**External runtime dependencies — user installs separately. NEVER vendored.**

- kiwix-tools: user installs via `apt install kiwix-tools`, `brew install kiwix-tools`, or from https://github.com/kiwix/kiwix-tools/releases. Never bundled by HERETIC.
- python-libzim: `pip install libzim`. Declared in `requirements-optional.txt`.

**The GPL exclusion boundary is absolute. Zero GPL code enters `vendor/`. Zero GPL binaries are bundled in HERETIC distributions. Violation of this rule requires immediate removal and legal review.**

---

## kiwix-serve Architectural Note (if HTTP backend chosen)

If Mímisbrunnr uses `kiwix-serve` as a local HTTP ZIM server rather than direct libzim bindings:

```
heretic/sense_hub/library/mimisbrunnr/ingestion/parser_zim.py
  ↓ (if http backend)
kiwix-serve (external subprocess, user-installed, GPL-3.0)
  ↓ HTTP (localhost)
heretic/sense_hub/library/mimisbrunnr/
  ↓ fetches article HTML/text via HTTP
```

This pattern is even cleaner from a GPL perspective: HERETIC talks to kiwix-serve over HTTP, which is an ordinary communication channel that does not create a derivative work. No GPL code is linked or imported. The subprocess is a black box accessed via a standard network protocol.

Whether to use direct libzim Python bindings vs kiwix-serve HTTP backend is an open architectural question for the Mímisbrunnr build phase. Both are legally acceptable under the external-runtime-dep pattern.

---

*Plunder map authored by Eirwyn Rúnblóm, 2026-05-07.*
*The Kiwix project builds excellent wells. We draw from them from the outside — their walls remain theirs.*
