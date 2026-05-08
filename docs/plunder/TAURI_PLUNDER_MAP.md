# Tauri — Plunder Map

**Map authored:** 2026-05-07
**Author:** Eirwyn Rúnblóm, Scribe for Vibe Coding
**Status:** studying — no code adapted yet; Tauri is the L0 Grunnr runtime shell and L4 Vébond UI host; required from v0.4 onward

---

## Upstream Identity

| Field | Value |
|---|---|
| Project name | Tauri |
| Repository | https://github.com/tauri-apps/tauri |
| Version as of write | Tauri v2.x (current stable — verify exact tag at build time) |
| Primary maintainer | Tauri Programme (CrabNebula Ltd. and community) |
| License | MIT OR Apache-2.0 (dual license — recipient chooses) |
| License URL | MIT: https://github.com/tauri-apps/tauri/blob/dev/LICENSE_MIT — Apache-2.0: https://github.com/tauri-apps/tauri/blob/dev/LICENSE_APACHE |
| License verification status | **Verified dual MIT/Apache-2.0 2026-05-07** (confirmed in Tauri repo root — both license files present, SPDX: `MIT OR Apache-2.0`) |

---

## Upstream License

**Dual license: MIT OR Apache-2.0 (recipient's choice).**

HERETIC chooses to receive Tauri under **MIT** — consistent with HERETIC's own MIT license and the simplest path. MIT is a strict superset of the permissions Apache-2.0 grants, so choosing MIT avoids the Apache-2.0 patent grant clause considerations for a project that is itself MIT.

**Tauri's JavaScript frontend crate (`@tauri-apps/api`) is also MIT OR Apache-2.0** — same choice applies.

Both choices are legally clean. The attribution obligation is the standard MIT copyright notice preservation.

---

## Compatibility Verdict

**CLEAN — no caveats.** Dual MIT/Apache-2.0 upstream received under MIT into HERETIC's MIT project. Tauri has no copyleft dependencies in its core Rust crate. The WebView dependency (WebKit2GTK on Linux, WKWebView on macOS, WebView2 on Windows) is the OS's native WebView — installed by the OS or by the user, not bundled by Tauri itself. No GPL or LGPL code enters `vendor/` through Tauri.

**Note on WebView2 (Windows):** Microsoft's WebView2 runtime is proprietary but redistributable under Microsoft's terms. It is not part of HERETIC's source; users install it (it ships pre-installed on Windows 11). No license concern for HERETIC's MIT grant.

---

## What We Plunder

Tauri is used as a **build framework and runtime dependency** — it is the structural scaffolding of the entire application. It is not a source-level plunder; it is the forge itself.

### Framework dependency (Cargo + npm)
- `tauri` Rust crate — the core runtime; manages the OS window, WebView, IPC bridge, subprocess supervisor, app lifecycle.
- `@tauri-apps/api` npm package — TypeScript API for the React frontend (L4 Vébond / Eldahús) to communicate with the Rust backend via Tauri IPC events.
- Tauri's `tauri.conf.json` configuration system — HERETIC's application manifest, permissions, window config.
- Tauri's subprocess spawning API (`tauri::api::process::Command`) — used by L0 Grunnr to spawn and supervise sense subprocesses (Python MCP servers, whisper.cpp).
- Tauri's event system — the IPC bridge between L4 Vébond (React) and the Rust backend layers (L0/L1/L2/L3/L5).
- Tauri's sidecar feature — for bundling whisper.cpp or other binaries alongside the HERETIC app in release builds.

### What we study and implement locally (pattern extraction)
- The Tauri IPC event pattern (`invoke` + `listen`) — HERETIC uses this for all L4 ↔ backend communication. The exact event names and payload shapes are HERETIC-native (`heretic::ui::command::*`, `heretic::lifecycle::*`).
- The subprocess supervisor pattern — HERETIC's Holdvörðr process model (spawn subprocess, watch for crash, restart per policy) is implemented using Tauri's process APIs but the restart policy logic is HERETIC-native.
- The `tauri.conf.json` permission model — HERETIC configures only the permissions it actually needs (filesystem paths, subprocess spawning, network access to localhost).

### What we study but do not copy
- Tauri's example applications — reference only.
- The Tauri plugin ecosystem — HERETIC may use Tauri plugins (e.g., `tauri-plugin-shell`, `tauri-plugin-process`) but does not plunder their source.

---

## What We DO NOT Plunder

- Tauri's Electron-style bundling patterns — HERETIC deliberately avoids anything that increases bundle size; the whole point of choosing Tauri is lightweight native WebView.
- The Tauri updater / autoupdate system — HERETIC follows Volmarr's law against auto-update behaviors without explicit user consent. If HERETIC ships an updater, it will be opt-in only.
- Tauri's telemetry or crash reporting — not used. HERETIC emits its own structured log (session JSONL); no external telemetry.
- Tauri's authentication plugins — HERETIC manages its own token handling (Bearer token via env var, never written to OS keychain by default in v1).

---

## Local Domain Ownership

| HERETIC layer | True Name | Owns this integration |
|---|---|---|
| L0 Grunnr | Grunnr (grunnr) — the foundation | Tauri process lifecycle: app init, config loading, subprocess supervisor, crash guard, logging to session JSONL |
| L4 Vébond / Eldahús | Vébond (vebond), Eldahús | Tauri WebView window: React component tree, Norse dark theme, IPC event consumption/emission for ceremony controls |

**L0 Grunnr IS the Tauri backend.** There is no separation; Grunnr is implemented as the Tauri Rust application. L4 Vébond is the Tauri frontend (React + TypeScript in the WebView).

---

## Public Interface

Inside HERETIC, Tauri is surfaced as follows:

- `heretic/foundation/` (Rust): directly depends on `tauri` crate. This is the one place Tauri APIs are called.
- `heretic/ui/` (TypeScript/React): directly depends on `@tauri-apps/api`. This is the one place Tauri frontend APIs are called.
- All other layers (L1–L3, L5) communicate with L0 via HERETIC's internal event bus (`heretic::lifecycle::*` events), not via Tauri APIs directly.
- Replacing Tauri with another desktop framework (hypothetically, in v3.x) would require rewriting `heretic/foundation/` and `heretic/ui/` only — no other layer would change.

---

## Attribution Requirements

| Requirement | Status |
|---|---|
| Preserve LICENSE file | Yes — Tauri's MIT license notice must appear in HERETIC's distribution (via `THIRD_PARTY_NOTICES.md` and in release `NOTICES/`) |
| NOTICE file required | Apache-2.0 requires a NOTICE file if receiving under Apache-2.0; under MIT, no NOTICE required. HERETIC chooses MIT — no NOTICE obligation. |
| In-source headers required | Not required for MIT; not required unless source is directly adapted |
| THIRD_PARTY_NOTICES.md entry | Yes |
| Trademark / branding | Do not imply Tauri Programme or CrabNebula endorsement. The name "Tauri" may appear in technical documentation as the framework used, but not as a brand association. |

---

## Verification Status

- License re-verified: **2026-05-07** — dual MIT/Apache-2.0 confirmed at https://github.com/tauri-apps/tauri/blob/dev/LICENSE_MIT
- HERETIC chooses to receive under: **MIT**
- Current stable version: Tauri v2.x — **verify exact version at build time** (https://github.com/tauri-apps/tauri/releases)
- Open question: Tauri v2 introduced a new permissions model. Confirm `tauri.conf.json` permission scoping for `fs`, `shell`, `process` capabilities needed by HERETIC at build time. Tauri v2 permissions are more granular than v1.

---

## Vendor Path

**Build framework — declared in `Cargo.toml` and `package.json`.**

Not vendored as source. Consumed via:
- Rust: `Cargo.toml` dependency `tauri = { version = "2", features = [...] }`
- Node: `package.json` devDependency `@tauri-apps/cli` and dependency `@tauri-apps/api`

Tauri is compiled into the HERETIC binary at build time — it is not a separate distributable. The resulting binary contains Tauri's Rust code under MIT license. The MIT attribution appears in `THIRD_PARTY_NOTICES.md`.

---

## Technology Decision Record

The choice of Tauri over Electron is documented in `docs/architecture/ARCHITECTURE.md` §8:

- Tauri uses the OS's native WebView (no bundled Chromium → fast cold-start, small binary, low idle RAM).
- Electron would add ~150 MB Chromium bundle — antithetical to HERETIC's "body rests" philosophy.
- Tauri's Rust core provides native subprocess management for the Holdvörðr process tree.
- Trade-off accepted: native WebView quirks across platforms require defensive CSS. React handles the status-heavy Summoning Circle UI elegantly.

---

*Plunder map authored by Eirwyn Rúnblóm, 2026-05-07.*
*Tauri is the forge-shell that holds the body together. We build inside it, not against it.*
