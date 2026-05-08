# TASK — HERETIC v0.4.1 TAURI WRAP (PRE-STAGED)

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-07** (immediately after v0.4.0 Eldahús Substrate shipped + audited; HEAD at `9e9a5aa`)

> **Mode: PRE-STAGED.** Volmarr explicitly chose: scaffold the Tauri shell + supporting code now; he installs Rust himself before running `cargo tauri build`. No autonomous installation of system toolchains.

---

## 1. Task scope

Wrap the v0.4.0 React frontend in a Tauri 2.x native shell so the Summoning Circle runs as a real desktop application (not a browser tab). The Tauri shell:

- Hosts the existing React+Vite frontend in a WebView2 (Windows) / WebKit (macOS) / WebKitGTK (Linux) window
- Spawns the Python `heretic serve` backend as a sidecar child process when the window opens
- Cleanly terminates the sidecar when the window closes
- Surfaces a Norse-aesthetic native window chrome (dark, frameless or near-frameless, no light flashes)
- Builds platform-native installers (`.msi` for Windows, `.dmg` for macOS, `.deb`/`.AppImage` for Linux)

The frontend code itself does NOT change. Tauri merely hosts what already works in the browser.

---

## 2. Current status — 2026-05-07

**Phase:** v0.4.0 substrate shipped at `9e9a5aa`. v0.4.1 is **pre-staged only** in this session — Rust toolchain absent, so no compilation is possible. All scaffolding is logical/structural; first compile happens when Volmarr installs Rust.

### v0.4.1 deliverables (pre-stage only)
- ⏳ `src-tauri/` directory:
  - `Cargo.toml` — Tauri 2.x deps with pinned versions
  - `tauri.conf.json` — window config matching AESTHETIC.md (dark theme, modest size, transparent if supported), bundle config, sidecar bin reference
  - `src/main.rs` — entry point, window creation, sidecar lifecycle (spawn at startup, kill on `RunEvent::Exit`)
  - `src/sidecar.rs` — Python sidecar process management (port discovery, health probe, graceful kill)
  - `src/error.rs` — Tauri-side error types
  - `build.rs` — standard Tauri build script
  - `icons/` — placeholder icons (.ico, .png, .icns) — Forge generates simple geometric placeholders
  - `Tauri.toml` (legacy v1) — NOT created; v2 uses tauri.conf.json
- ⏳ Root `package.json` updates — add `tauri` script targets (`tauri dev`, `tauri build`) and `@tauri-apps/cli` devDependency
- ⏳ Frontend `vite.config.ts` updates — `clearScreen: false`, `server.strictPort: true`, `server.port: 1420` (Tauri convention) — to play nicely with `cargo tauri dev`
- ⏳ Frontend `package.json` — add `@tauri-apps/api` dependency (used in WebView for Tauri command invocation if needed; v0.4.1 minimal usage)
- ⏳ `docs/architecture/TAURI_SHELL.md` — architecture doc: window lifecycle, sidecar lifecycle, IPC delineation (note: most IPC is the existing WebSocket; Tauri commands used only for native-only concerns like quit-confirmation, focus-restore, single-instance lock)
- ⏳ `README_DEV.md` updates — full install path: install Rust (`winget install Rustlang.Rust.MSVC` OR `rustup-init.exe`), `cargo install tauri-cli@2`, `cargo tauri dev`, `cargo tauri build`
- ⏳ Validation:
  - Cargo.toml is valid TOML
  - tauri.conf.json is valid JSON and matches Tauri 2 schema (cross-reference against `https://schema.tauri.app/config/2` if reachable)
  - main.rs uses Tauri 2.x APIs (NOT 1.x — they differ significantly)
  - No `unwrap()` in production paths — proper error handling throughout
- ⏳ Tests: minimal Rust unit test stubs (since `cargo test` cannot run, write the test files but mark them with comments noting they execute only after Rust install)

### Constraints carried from v0.4.0
- Frontend code does NOT change (no breaking modifications to `frontend/src/`)
- WebSocket protocol does NOT change (Tauri shell connects to Python sidecar over the same `ws://localhost:8642/ws` IPC)
- Norse aesthetic — window chrome should match the AESTHETIC.md dark theme; no jarring native chrome flash on startup
- No emoji
- No absolute paths

---

## 3. Architectural decisions for v0.4.1

| Decision | Choice | Rationale |
|---|---|---|
| Tauri version | **Tauri 2.x** (latest stable) | v2 stable since Oct 2024; v1 is sunsetted. New work uses v2. |
| Sidecar approach | Tauri's `externalBin` sidecar pattern | Tauri spawns a bundled binary; we point it at Python script wrapped via PyInstaller (deferred — see §4) OR directly at the system Python interpreter for development |
| Sidecar binary | **Dev: system Python**; **prod: PyInstaller bundle (deferred)** | Dev mode runs `python -m heretic serve`; production .msi bundles a PyInstaller'd `heretic-serve.exe`. PyInstaller config is documented but the actual one-file build is v0.4.1.x. |
| Window config | Frameless, dark, fixed-aspect, no menu | Per AESTHETIC.md: dim by default, no clinical browser chrome |
| Single-instance | Yes (Tauri plugin `single-instance`) | Prevents multiple summonings |
| Auto-updater | NO for v0.4.1 | Add in v1.x; release infra comes later |
| Tauri commands | Minimal — only: `quit`, `focus_window`, `get_sidecar_port` | Most IPC is WebSocket; Tauri commands cover only what only-native can do |
| Logging | Tauri stderr → host stderr; Rust `log` + `env_logger` | Match the Python logging philosophy |
| Icons | Geometric placeholder for v0.4.1; proper sigil in v1.x | Vector design needs Skald + designer pass; Forge ships placeholder |

---

## 4. PyInstaller / sidecar bundling — decision

**v0.4.1 ships sidecar-via-system-Python only.** The reasoning:

- Bundling Python via PyInstaller adds 30-60 MB to the installer and a complex build step
- v0.4.1 is the minimum viable wrap — get the window working, get the sidecar lifecycle right
- v0.4.1.x (a follow-up small milestone) adds PyInstaller bundling
- Until then, the .msi installer requires Python 3.10+ on PATH; document this clearly in README_DEV.md and the installer's prerequisite check

If the sidecar pattern proves fragile when the user's Python differs from the development Python, we revisit. v0.4.1 documents this and accepts the risk.

---

## 5. Mythic Engineering wave plan

Slimmer than v0.1-v0.4 (this is a wrap milestone, not a new faculty):

### Wave 1 — parallel (no inter-dependencies)
- **Cartographer** (Védis Eikleið) — map the Tauri shell ↔ React frontend ↔ Python sidecar lifecycle. Add `docs/cartography/DATA_FLOW.md §4.9 "Tauri shell flow (v0.4.1 — pre-staged)"` showing: Tauri startup → spawn Python sidecar → wait for /health 200 → load WebView pointed at React build → user interacts → Tauri shutdown → kill sidecar. Note the IPC remains WebSocket (already mapped in §4.8); Tauri commands are minimal.
- **Architect** (Rúnhild Svartdóttir) — scaffold `src-tauri/`: Cargo.toml (Tauri 2.x deps + plugins), tauri.conf.json (Tauri 2 schema, window config, sidecar reference, bundle config), src/main.rs skeleton, src/sidecar.rs skeleton, src/error.rs, build.rs, placeholder icons (text-based generation OK for v0.4.1), `docs/architecture/TAURI_SHELL.md` architecture doc, README_DEV.md updates with install path. Update root `package.json` with tauri script targets and devDeps. Update `frontend/vite.config.ts` for Tauri-friendly defaults. Update `frontend/package.json` with @tauri-apps/api dependency.

### Wave 2 — sequential
- **Forge** (Eldra Járnsdóttir) — COMPLETE (2026-05-07, HEAD `6ceffc5`). All `todo!()` bodies replaced. See commit for full inventory. FORGE-NOTE items documented for first-compile session. Frontend 59/59 green, build clean.
- **Auditor** (Sólrún Hvítmynd) — audit the pre-staged scaffold against:
  - Tauri 2 config schema (validate `tauri.conf.json` field names + types)
  - Tauri 2 Rust API (`tauri::Builder`, `RunEvent`, `WindowBuilder` — verify no v1 holdovers)
  - Cargo.toml dep version coherence (Tauri 2.x compatible plugin versions)
  - Sidecar safety (the kill path must be reliable; no zombie Python on Tauri crash)
  - Icon files exist
  - README_DEV.md install path is complete and correct
  - All file paths are relative and cross-platform
  - The frontend continues to build and test cleanly (no regression)
  - Audit can RUN: cargo, javascript, frontend tests; CANNOT RUN: cargo build (no Rust), tauri build

### Wave 3 — cleanup (only if Auditor finds notables)
Per-finding dispatch.

### Close-out
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 6 + update this TASK file + memory refresh.

---

## 6. Files to be created (Forge target list)

```
src-tauri/
  Cargo.toml
  tauri.conf.json
  build.rs
  src/
    main.rs
    sidecar.rs
    error.rs
    lib.rs              # for cdylib if mobile targets later; keep minimal
  icons/
    32x32.png
    128x128.png
    128x128@2x.png
    icon.ico
    icon.icns           # macOS placeholder; can be generated from PNG later
  capabilities/
    default.json        # Tauri 2 capabilities config
docs/architecture/
  TAURI_SHELL.md        # architecture doc
docs/cartography/
  DATA_FLOW.md          # §4.9 Tauri shell flow appended (Cartographer)
README_DEV.md           # updated install/build path
package.json            # tauri script targets at root (or stays in frontend; pick cleanest)
frontend/package.json   # add @tauri-apps/api
frontend/vite.config.ts # Tauri-friendly tweaks
```

---

## 7. Operational rules (carried, immutable)

- Branch: `development` only
- Push frequently
- No absolute paths (especially in tauri.conf.json paths — use Tauri's `$RESOURCE` and `$APPDATA` placeholders)
- No hardcoded settings in Rust — sidecar port comes from Python config (see §3 `get_sidecar_port` Tauri command)
- Modular, fault-tolerant
- No emoji in code or docs
- Type hints (Python) + types (TypeScript) everywhere; idiomatic Rust (Result types, ?, no unwrap in non-test paths)
- Each subagent commits with their own attribution line
- After EVERY completed phase: update this TASK file + memory immediately

---

## 8. v0.4.0 backlog (carried; some closed by v0.4.1 pre-stage)

- v0.4.0 backlog: Tauri wrap (THIS TASK, pre-staged)
- v0.4.x: sense-toggle implementation (still backlog after v0.4.1)
- v0.4.x: voice waveform widget (still backlog)
- v0.4.x: light/dark theme switch (still backlog)

---

## 9. v0.4.1.x backlog (forward-looking)

- v0.4.1.x: PyInstaller bundling of `heretic-serve` so the .msi is fully self-contained
- v0.4.1.x: Code-signing setup for Windows MSI and macOS DMG (requires Volmarr's signing certs)
- v0.4.1.x: Auto-updater wiring
- v0.4.1.x: Tauri tray icon for "background presence" mode (carefully — manifesto warns against always-on)

---

## 10. How to resume this task in a future session

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read this file from top to bottom
3. **Critical: check Rust install state.** If `rustc --version` works, you can compile. If not, you're still pre-staged — do not attempt `cargo build`.
4. If Rust is installed: run `cd src-tauri && cargo check` to surface any latent errors from the pre-staged code; fix them; then `cargo tauri dev` to verify the window opens and the sidecar spawns
5. Read `docs/audit/AUDIT_v0.4.1_TAURI_WRAP.md` if it exists
6. Run `git log --oneline -15` and `git status`
7. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*v0.4.1 Tauri Wrap — when the longhouse becomes a cabin around the fire.*
