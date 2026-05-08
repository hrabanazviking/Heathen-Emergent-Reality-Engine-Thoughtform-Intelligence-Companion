# HERETIC — Tauri Shell Architecture (L-1 Skál)

**Last updated:** 2026-05-07 (v0.4.1 pre-stage — Rúnhild Svartdóttir)
**Scope:** The Tauri 2.x native desktop shell that wraps the React frontend and manages
the Python sidecar lifecycle. This layer sits *outside* the HERETIC Python layer stack
(L0 Grunnr through L5 Skilningr) and is designated **L-1 Skál** (the Longhouse Shell).
**Authority:** Architect (Rúnhild Svartdóttir)

---

## 1. What This Layer Owns

L-1 Skál owns exactly three responsibilities:

| Responsibility | Implementation location | Notes |
|---|---|---|
| Native window creation and chrome | `src-tauri/tauri.conf.json` window config | Dark theme, 1280x800 default, 960x600 min |
| Python sidecar lifecycle | `src-tauri/src/sidecar.rs` + `main.rs` setup/RunEvent | Spawn on start, kill on exit |
| Native-only IPC commands | `src-tauri/src/main.rs` `#[tauri::command]` | quit, focus_window, get_sidecar_port |

Everything else — agent communication, voice I/O, WebSocket protocol, ceremony lifecycle —
belongs to the Python layer stack. Skál does not interpret IPC messages; it merely hosts
the WebView that does.

---

## 2. Window Lifecycle

```
OS Launch
    |
    v
tauri::Builder::default()
    .plugin(single-instance)   <- prevent double-summonings
    .plugin(log)               <- structured Rust log output
    .manage(SidecarState)      <- thread-safe sidecar handle
    .setup(setup_app)          <- spawn Python sidecar, health probe
    .invoke_handler(...)       <- register Tauri commands
    .build(generate_context!())
    |
    v
setup_app() {
    1. Read sidecar port from env HERETIC_PORT (default 8642)
    2. Resolve pid_file path via Tauri PathResolver (app_local_data_dir)
    3. PythonSidecar::spawn(port, pid_file)  <- std::process::Command
    4. sidecar.health_probe(30s)             <- HTTP GET /health with retry
    5. Store in SidecarState managed state
}
    |
    v
RunEvent::Ready
    |
    v
[USER INTERACTS WITH WEBVIEW]
    |
    v
RunEvent::ExitRequested
    |
    v
sidecar.kill()   <- terminates Python child process
    |
    v
Tauri exits
```

The WebView connects directly to `ws://127.0.0.1:8642/ws` after the window opens.
Skál does not proxy, intercept, or re-serialize any WebSocket traffic. See
`IPC_PROTOCOL.md` for the full WebSocket schema.

---

## 3. Sidecar Approach — externalBin vs shell-spawn

**Decision: system Python via `std::process::Command` (not Tauri externalBin).**

Rationale:

- Tauri's `externalBin` sidecar pattern bundles a pre-compiled binary declared
  under `bundle.externalBin` in `tauri.conf.json`. That binary must exist at build
  time. For v0.4.1, we have no compiled `heretic-serve.exe` — the Python package
  is installed via `pip install -e .` on the developer's machine.

- PyInstaller bundling (which would produce that binary) is deferred to v0.4.1.x.
  See `TASK_HERETIC_v0.4.1_TAURI_WRAP.md §4` for the full rationale.

- For v0.4.1, `PythonSidecar::spawn()` calls `std::process::Command::new("python")`
  with args `["-m", "heretic", "serve", "--port", "<port>"]`. This requires Python
  3.10+ on PATH with the `heretic[serve]` extras installed.

- The `externalBin` key is intentionally absent from `tauri.conf.json` in v0.4.1.
  When v0.4.1.x introduces PyInstaller bundling, the sidecar.rs spawn method will
  be replaced by Tauri's sidecar API, and `externalBin` will be added.

**Platform note:** On Windows, `python` resolves correctly via PATH (the Microsoft
Store Python stub is bypassed when the real interpreter is on PATH). On POSIX, try
`python3` first. Forge handles the platform branch in `sidecar.rs::spawn()`.

---

## 4. IPC Delineation

### What crosses the Tauri command boundary (minimal)

| Command | Direction | Purpose |
|---|---|---|
| `quit` | JS -> Rust | Trigger graceful app exit (Rust calls `app.exit(0)`) |
| `focus_window` | Rust -> Rust / JS -> Rust | Single-instance: bring window forward |
| `get_sidecar_port` | JS -> Rust | Read the active sidecar port (avoids TS hardcode) |

### What does NOT cross the Tauri command boundary

Everything in `IPC_PROTOCOL.md` (WebSocket, ceremony states, Bifrost health,
agent tokens, voice indicators) travels directly between the WebView's WebSocket
client and the Python Vebond server. Skál is transparent to all of it.

The `withGlobalTauri: false` setting in `tauri.conf.json` means the `__TAURI__`
global is NOT injected. The frontend accesses Tauri commands via the
`@tauri-apps/api` package (`invoke()` call). This is the v2-idiomatic pattern.

---

## 5. Single-Instance Lock

The `tauri-plugin-single-instance` plugin prevents two summonings. When a second
launch is detected, the plugin fires a callback in the first instance's process.
That callback calls `focus_window` to bring the existing window to the foreground
and then exits the second process. See `main.rs` for the callback stub.

---

## 6. Capabilities (Tauri 2 Permission System)

Tauri 2 replaces v1's `allowlist` with a capabilities file system at
`src-tauri/capabilities/`. The `default.json` file grants the `summoning-circle`
window access to:

- `core:default` — standard window operations
- `core:window:allow-close`, `allow-set-focus`, `allow-show`, `allow-hide`,
  `allow-minimize`, `allow-unminimize` — required for native window management
- `log:default` — Tauri log plugin
- `single-instance:default` — single-instance plugin

No filesystem, shell-execute, HTTP client, or clipboard permissions are granted.
All network communication is handled by the Python sidecar and the WebView's
native WebSocket — not via Tauri shell APIs.

---

## 7. Window Configuration Rationale

| Setting | Value | Source |
|---|---|---|
| `backgroundColor` | `#0a0c10` | AESTHETIC.md "Void" color — prevents white flash during WebView load |
| `theme` | `"Dark"` | Forces OS dark chrome (title bar, scrollbars) to match Void |
| `decorations` | `true` | Native title bar retained for v0.4.1; frameless is v1.x |
| `transparent` | `false` | Transparent windows require `macos-private-api` + alpha compositing; deferred |
| `minWidth/minHeight` | 960x600 | Minimum viable Summoning Circle without layout collapse |
| `defaultWidth/defaultHeight` | 1280x800 | Comfortable default per AESTHETIC.md "modest size" guidance |
| `center` | `true` | Opens centered on the primary display |

Setting `backgroundColor` to the Void color is the most important anti-flash measure.
It ensures the window frame shows the correct background before the WebView's React
bundle has loaded and painted.

---

## 8. Tauri 2 vs Tauri 1 — Differences Honored in This Scaffold

| Area | Tauri 1 | Tauri 2 (this scaffold) |
|---|---|---|
| Config schema | `tauri.conf.json` v1 | `tauri.conf.json` v2 with `$schema` pointing to `https://schema.tauri.app/config/2` |
| Plugins | Built-in (single-instance, log) | External: `tauri-plugin-single-instance = "2"`, `tauri-plugin-log = "2"` |
| Allowlist | `tauri.conf.json` `[tauri.allowlist]` | `capabilities/default.json` permission grants |
| Window builder | `WindowBuilder` | `WebviewWindowBuilder` (Tauri 2 renamed) |
| Global Tauri object | Injected by default | `withGlobalTauri: false`; use `@tauri-apps/api` package |
| Build deps | `tauri-build = "1"` | `tauri-build = "2"` |
| Window URL in conf | `"url": "tauri://localhost"` | `"url": "index.html"` (relative to `frontendDist`) |
| App setup | `.setup(Box<dyn Fn(...)>)` | `.setup(|app| ...)` closure or fn pointer |
| Mobile support | Absent | `crate-type = ["staticlib", "cdylib", "rlib"]` in lib.rs |

---

## 9. First-Compile Gotchas for Forge

1. **`tauri::generate_context!()`** reads `tauri.conf.json` at compile time via the build
   script. If `tauri.conf.json` has a schema error, the build fails with a cryptic message.
   Run `python -c "import json; json.load(open('src-tauri/tauri.conf.json'))"` first.

2. **`withGlobalTauri: false`** means `window.__TAURI__` does not exist. Any TS code
   that accesses it directly will fail. Always use `import { invoke } from "@tauri-apps/api/core"`.

3. **`tauri_plugin_single_instance::init(|app, args, cwd| {...})`** — the closure receives
   `&AppHandle`, not `App`. You cannot call `app.state()` inside this closure during early
   startup if state is not yet managed. Defer state access to after `RunEvent::Ready`.

4. **`RunEvent::ExitRequested`** fires before the process exits. Do NOT call `app.exit()`
   inside the `ExitRequested` handler — it will recurse. Call it from a command or from
   a window `on_window_event` listener instead.

5. **`process.env.TAURI_DEV_HOST`** — Tauri 2 injects this env var during `cargo tauri dev`
   to tell Vite which host to bind on (important for mobile targets). The vite.config.ts
   in this scaffold reads it to switch between port 1420 (Tauri dev) and 5173 (standalone).

6. **Icon sizes** — Tauri's bundler validates that all icons listed in `tauri.conf.json`
   actually exist before building. The placeholder icons in `src-tauri/icons/` satisfy
   this requirement. Replace with final artwork before v1.x.

---

## 10. v0.4.1.x Forward Path

- **PyInstaller sidecar bundling:** Replace `std::process::Command` spawn with Tauri's
  `tauri::process::Command` sidecar API. Add `externalBin: ["binaries/heretic-serve"]` to
  `tauri.conf.json`. The binary name must be platform-suffixed (Tauri handles this).

- **Frameless window:** Set `decorations: false`, add draggable regions in the React layer
  via `-webkit-app-region: drag` CSS. Blocked on Forge implementing the drag region overlay.

- **Code signing:** Add `bundle.windows.certificateThumbprint` and `bundle.macOS.signingIdentity`
  in `tauri.conf.json`. Blocked on Volmarr supplying signing certificates.

- **Auto-updater:** Add `tauri-plugin-updater = "2"` and `updater` capability permissions.
  Blocked on release infrastructure milestone.

---

*Architecture law: Skál wraps; it does not think. All cognition belongs to Python. All
ceremony belongs to the WebSocket. The shell is a longhouse around a fire that someone
else lit.*
