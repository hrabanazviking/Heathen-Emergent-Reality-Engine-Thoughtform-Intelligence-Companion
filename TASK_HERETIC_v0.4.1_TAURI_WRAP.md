# TASK — HERETIC v0.4.1 TAURI WRAP (PRE-STAGED)

> **Operational task resumption file** — per Volmarr's session-resume protocol. If a session breaks, the next session reads this first.

> **Started: 2026-05-07** (immediately after v0.4.0 Eldahús Substrate shipped + audited; HEAD at `9e9a5aa`)

> **Mode: PRE-STAGED + RUST INSTALLED + LINKER BLOCKED.** Original choice 2026-05-07: scaffold only; Volmarr installs Rust. **Update 2026-05-08:** Volmarr authorized autonomous Rust install. Rust 1.95.0 (MSVC + GNU toolchains) installed at `%USERPROFILE%\.cargo\bin\` and added to user PATH persistently. **First-compile blocked at link stage:** MSVC `link.exe` not present (would need Visual Studio Build Tools — `winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools"`, ~5GB + UAC). GNU toolchain's bundled MinGW `dlltool.exe` fails on child-process spawn (incomplete `--profile minimal` MinGW; would need full MinGW-w64 via scoop/choco). Volmarr's call which path: MSVC (Tauri canonical) or MinGW-w64 (lighter). Either resolves the linker; nothing else in the scaffold needs touching until first `cargo tauri dev` succeeds.

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

**Phase:** v0.4.1 SCAFFOLD PRE-STAGED + AUDITED 2026-05-07; awaits Rust install for first compile.

v0.4.0 substrate shipped at `9e9a5aa`. v0.4.1 full scaffold completed and audited this session (HEAD `df4807f`). Rust toolchain absent — no compilation was possible. All scaffolding is logically complete and structurally sound by Tauri 2 documentation review. First compile happens when Volmarr installs Rust.

Audit verdict: **PASS WITH CONCERNS** — 0 blockers, 1 SERIOUS (resolved in Wave 3), 0 open findings.

### v0.4.1 deliverables (pre-stage status as of 2026-05-07)
- ~~⏳~~ **Done 2026-05-07** `src-tauri/` directory:
  - `Cargo.toml` — Tauri 2.x deps with pinned versions — **Done 2026-05-07** (`230205e`); TOML valid
  - `tauri.conf.json` — window config matching AESTHETIC.md (dark theme, `#0a0c10` background, `withGlobalTauri: false`), bundle config, window label `summoning-circle` — **Done 2026-05-07** (`230205e`); JSON valid, full Tauri 2 schema compliance
  - `src/main.rs` — entry point, window creation, sidecar lifecycle, three Tauri commands, `RunEvent::ExitRequested` handler — **Done 2026-05-07** (`6ceffc5`, `df4807f`)
  - `src/sidecar.rs` — Python sidecar spawn, health probe, kill, Drop safety net — **Done 2026-05-07** (`6ceffc5`)
  - `src/error.rs` — `TauriError` + `SidecarError` with `From` impls — **Done 2026-05-07** (`6ceffc5`)
  - `src/lib.rs` — minimal; reserved for cdylib — **Done 2026-05-07** (`230205e`)
  - `build.rs` — standard Tauri build script — **Done 2026-05-07** (`230205e`)
  - `icons/` — 5 placeholder icon files — **Done 2026-05-07** (`230205e`)
  - `capabilities/default.json` — Tauri 2 capabilities, principle of least privilege — **Done 2026-05-07** (`6ceffc5`); JSON valid
  - `Tauri.toml` (legacy v1) — NOT created; v2 uses `tauri.conf.json` only — correct
- ~~⏳~~ **Done 2026-05-07** Root `package.json` — `tauri dev` + `tauri build` scripts, `@tauri-apps/cli ^2` devDependency (`230205e`)
- ~~⏳~~ **Done 2026-05-07** Frontend `vite.config.ts` — `clearScreen: false`, `strictPort`, `port: 1420` on Tauri dev, `TAURI_DEV_HOST` host var (`230205e`)
- ~~⏳~~ **Done 2026-05-07** Frontend `package.json` — `@tauri-apps/api ^2`, `@types/node` (`6ceffc5`)
- ~~⏳~~ **Done 2026-05-07** `docs/architecture/TAURI_SHELL.md` — complete architecture doc: lifecycle, sidecar approach, IPC delineation, capabilities, first-compile gotchas (`230205e`)
- ~~⏳~~ **Done 2026-05-07** `README_DEV.md` — full Rust install path: `winget install Rustlang.Rust.MSVC`, `cargo install tauri-cli --version "^2" --locked`, `cargo tauri dev`, `cargo tauri build` (`230205e`)
- ~~⏳~~ **Done 2026-05-07** Validation:
  - Cargo.toml valid TOML — **VERIFIED** (`5d0624b`)
  - tauri.conf.json valid JSON, Tauri 2 schema — **VERIFIED** (`5d0624b`)
  - main.rs uses Tauri 2.x APIs only — **VERIFIED** (37 audit checks, `5d0624b`)
  - No `unwrap()` in production paths — **VERIFIED** (`5d0624b`)
- ~~⏳~~ **Noted 2026-05-07** Tests: 3 Rust unit test stubs present in `sidecar.rs`; compile-gated; execute only after Rust install

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

### Wave 1 — parallel (no inter-dependencies) — **COMPLETE 2026-05-07**

> Note: First dispatch was interrupted by the Anthropic usage cap mid-session. Tree cleaned at `2b2ad99` (`.gitignore` update) and re-dispatched cleanly. Both roles delivered full deliverables on the second run.

- **Cartographer** (Védis Eikleið) — **COMPLETE 2026-05-07, HEAD `6570a21`**. DATA_FLOW.md §4.9 (Tauri shell flow, pre-staged) + §14 (Tauri shell wrapper diagram) + SYSTEM_OVERVIEW.md §7 (pre-staged inventory). Three architectural threads flagged for first-compile session: PyInstaller deferral makes "Python on PATH" visible; `/health` `lifecycle_state` opens latent stale-ceremony detection path; `cargo tauri dev` is a distinct hybrid mode worth naming.
- **Architect** (Rúnhild Svartdóttir) — **COMPLETE 2026-05-07, HEAD `230205e`**. Full `src-tauri/` 18-file scaffold: Cargo.toml, tauri.conf.json, build.rs, main.rs (stubs), sidecar.rs (stubs), error.rs (stubs), lib.rs, capabilities/default.json, 5 icon placeholders. `docs/architecture/TAURI_SHELL.md` (complete architecture doc). Frontend: vite.config.ts Tauri-friendly, package.json @tauri-apps/api, root package.json tauri scripts. README_DEV.md install path.

### Wave 2 — sequential — **COMPLETE 2026-05-07**
- **Forge** (Eldra Járnsdóttir) — **COMPLETE 2026-05-07, HEAD `6ceffc5`**. All `todo!()` bodies replaced in main.rs, sidecar.rs, error.rs. Deps added to Cargo.toml: ureq, tauri-plugin-dialog, dirs, which. `capabilities/default.json` updated with `dialog:default`. `frontend/package.json` @types/node added. FORGE-NOTE items documented inline for first-compile session. Frontend 59/59 green, build clean. TASK file updated at `86d6a6e`.
- **Auditor** (Sólrún Hvítmynd) — **COMPLETE 2026-05-07, HEAD `5d0624b`**. Full audit of pre-staged scaffold. Verdict: **PASS WITH CONCERNS, 0 blockers**. 37 items verified. 1 SERIOUS (S-1), 2 NOTABLE (N-1/N-2), 3 NITs (X-1/X-2/X-3). B-3 (--pid-file) RESOLVED — Rust does not pass `--pid-file` to Python. B-4/B-5 VERIFIED CLEAN. See `docs/audit/AUDIT_v0.4.1_TAURI_WRAP.md`.

### Wave 3 — cleanup — **COMPLETE 2026-05-07, HEAD `df4807f`**
Single fix: S-1 comment alignment in `main.rs` — Forge aligned the FORGE-NOTE comment with the actual `blocking_show()` call site. Comment-only change; no code path modified. All audit findings now closed.

### Close-out — **COMPLETE 2026-05-07**
- **Scribe** (Eirwyn Rúnblóm) — DEVLOG entry 6 + this TASK file update + memory refresh. 2026-05-07.

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

- v0.4.1.x: PyInstaller bundling of `heretic-serve` so the .msi is fully self-contained (carries forward from PyInstaller deferral; documented in §4 and `TAURI_SHELL.md §10`)
- v0.4.1.x: Code-signing setup for Windows MSI and macOS DMG (requires Volmarr's signing certs)
- v0.4.1.x: Auto-updater wiring
- v0.4.1.x: Tauri tray icon for "background presence" mode (carefully — manifesto warns against always-on)
- v0.4.1.x: `CTRL_BREAK_EVENT` graceful shutdown on Windows — currently `sidecar.kill()` calls `TerminateProcess` (hard kill); graceful `CTRL_BREAK_EVENT` path requires `windows`/`winapi` crate; deferred from v0.4.1 per `sidecar.rs` FORGE-NOTE at line 136 (Audit X-3, now tracked here)
- v0.4.1.x: `--pid-file` Python CLI alignment — Python `heretic serve` should accept `--pid-file <path>` so both sides agree on the crash-recovery file location; Rust currently writes the PID file unilaterally; Python is not consulted (Audit X-3, now tracked here; documented in `sidecar.rs` lines 73-77)

---

## 10. How to resume this task in a future session

**Post-audit state (2026-05-07):** Scaffold complete. Audit closed with 0 open findings (HEAD `df4807f`). Python 424 + frontend 59 = 483 tests passing. First compile deferred pending Rust install.

### Path A — Rust NOT yet installed (still pre-staged)

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read this file from top to bottom
3. Run `rustc --version` — if command not found, you are still pre-staged; do not attempt `cargo build`
4. Read `docs/audit/AUDIT_v0.4.1_TAURI_WRAP.md` for the full first-compile checklist (§Final Verdict)
5. Run `git log --oneline -10` and `git status` to confirm clean state
6. Read `~/.claude/projects/C--Users-volma/memory/project_heretic_status.md`
7. Either install Rust (see Path B) or proceed to v0.5 First Sight on the existing Python + Node stack

### Path B — Rust IS installed (first-compile session)

1. Read `docs/BODY_MANIFESTO.md` — sealed vision
2. Read this file from top to bottom
3. Read `docs/audit/AUDIT_v0.4.1_TAURI_WRAP.md` — especially §Final Verdict and the recommended first-compile checklist
4. Run `rustc --version` and `cargo --version` to confirm toolchain present
5. Run `cd src-tauri && cargo check` — surface latent type errors; fix before proceeding
6. **Watch for S-1:** if `blocking_show()` does not compile, apply the safe fallback documented in `main.rs` FORGE-NOTE (use `.show(|_| {})` async variant; `app.exit(1)` fires regardless)
7. **Watch for N-2:** if `single-instance:default` generates a capability warning, remove it from `capabilities/default.json`
8. Run `cargo tauri dev` — observe sidecar spawn log, health probe log, window open
9. Manually test double-launch (single-instance lock) and clean exit (no orphaned Python process)
10. Commit any compile fixes: `forge(v0.4.1): first-compile fixes (Eldra Járnsdóttir)`
11. Invoke Scribe to close the v0.4.1 milestone properly in DEVLOG once compiled and verified

---

*Task file authored by Runa Gridweaver Freyjasdottir, 2026-05-07.*
*v0.4.1 Tauri Wrap — when the longhouse becomes a cabin around the fire.*
