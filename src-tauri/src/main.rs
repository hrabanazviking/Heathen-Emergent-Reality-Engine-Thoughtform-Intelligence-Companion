// main.rs — HERETIC Tauri 2.x shell entry point.
//
// TAURI VERSION: 2.x — do NOT apply Tauri 1.x patterns here.
//
// Key Tauri 2 vs 1 differences honored in this file:
//   - `.plugin()` is used for single-instance, log, and dialog (v1 had none of these built-in)
//   - `generate_context!()` is the v2 macro (same name, different internals)
//   - `RunEvent` variants are accessed from `tauri::RunEvent` (same in v2)
//   - `WindowBuilder` v2 API is at `tauri::WebviewWindowBuilder` (changed from v1)
//   - Capabilities are in capabilities/default.json, NOT in tauri.conf.json allowlist
//   - `app.get_webview_window()` replaces v1 `app.get_window()`
//
// Forge Worker: Eldra Járnsdóttir — all todo!() macros replaced with live bodies (v0.4.1).

// Prevent a console window from appearing on Windows release builds.
// Remove this if you need the console output during development.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use heretic_lib::error::{SidecarError, TauriError};
use heretic_lib::sidecar::PythonSidecar;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{AppHandle, Manager, RunEvent, State};

// ---------------------------------------------------------------------------
// Shared application state
// ---------------------------------------------------------------------------

/// Thread-safe wrapper around the Python sidecar handle.
/// Stored in Tauri managed state so all commands and event handlers can reach it.
///
/// The `Option<PythonSidecar>` is None if:
///   a) spawn has not yet been called (before setup_app completes), or
///   b) the sidecar was explicitly killed and the slot cleared.
type SidecarState = Arc<Mutex<Option<PythonSidecar>>>;

// ---------------------------------------------------------------------------
// Tauri commands — minimal surface (v0.4.1)
// ---------------------------------------------------------------------------

/// Quit the application.
///
/// Triggers `app.exit(0)` which causes `RunEvent::ExitRequested` to fire,
/// where the sidecar kill path lives. Do NOT kill the sidecar here — the
/// RunEvent handler is the single authoritative kill site.
///
/// Called from the WebView when the user confirms a close action.
/// In v0.4.1 no shell-level confirmation dialog is shown — the frontend
/// may show a React modal before invoking this command.
#[tauri::command]
async fn quit(app: AppHandle) -> Result<(), TauriError> {
    log::info!("quit command received — calling app.exit(0)");
    app.exit(0);
    Ok(())
}

/// Bring the main window to the foreground.
///
/// Called by the single-instance plugin callback when a second launch is
/// detected. Retrieves the "summoning-circle" WebviewWindow and calls
/// `set_focus()`. Returns an error if the window is not found.
#[tauri::command]
async fn focus_window(app: AppHandle) -> Result<(), TauriError> {
    // Odin's eye turns to the summoning circle and brings it to the fore.
    app.get_webview_window("summoning-circle")
        .ok_or_else(|| TauriError::Window {
            message: "summoning-circle window not found".into(),
        })?
        .set_focus()
        .map_err(|e| TauriError::Window {
            message: e.to_string(),
        })?;
    Ok(())
}

/// Return the port the Python sidecar is bound to.
///
/// The WebView JS layer calls this on startup to confirm the WebSocket port
/// rather than hardcoding 8642. Returns an error if the sidecar is not running.
#[tauri::command]
async fn get_sidecar_port(state: State<'_, SidecarState>) -> Result<u16, TauriError> {
    // Heimdall checks the portcullis — what gate does the sidecar guard?
    let guard = state
        .lock()
        .map_err(|e| TauriError::Internal { message: e.to_string() })?;
    match guard.as_ref() {
        Some(sidecar) => Ok(sidecar.port()),
        None => Err(TauriError::Sidecar {
            message: "sidecar is not running — cannot return port".into(),
        }),
    }
}

// ---------------------------------------------------------------------------
// Application setup
// ---------------------------------------------------------------------------

/// Show a blocking error dialog and exit the application.
///
/// Used when the sidecar fails to spawn or fails the health probe. Tauri
/// `tauri_plugin_dialog` is used for the native message box. This function
/// does NOT return — it calls `app.exit(1)` after the user dismisses the dialog.
///
/// FORGE-NOTE: `tauri_plugin_dialog::blocking::MessageDialogBuilder` is the
/// synchronous API (Tauri 2 dialog plugin). In Tauri 2.x the blocking builder
/// is available from `tauri_plugin_dialog::blocking`. If the dialog plugin
/// version does not expose `.blocking()`, fall back to `MessageDialogBuilder`
/// from the root of the crate and call `.show(|_| {})` (async fire-and-forget).
/// The exit() call below runs regardless, so the dialog is best-effort UX.
fn show_fatal_error_and_exit(app: &tauri::App, title: &str, message: &str) {
    log::error!("Fatal startup error — {}: {}", title, message);

    // Show a blocking native message dialog.
    // FORGE-NOTE: tauri_plugin_dialog 2.x API —
    //   `tauri_plugin_dialog::blocking::MessageDialogBuilder::new(app, title, message).show()`
    // This call blocks the current thread until the user clicks OK.
    // If the blocking API is unavailable in the installed version, remove the
    // `.blocking()` call and use the async `.show(|_| {})` form instead — the
    // exit() call below will still run after the closure is enqueued.
    use tauri_plugin_dialog::DialogExt;
    let _ = app
        .dialog()
        .message(message)
        .title(title)
        .blocking_show();

    // Terminate the application with a non-zero exit code.
    app.handle().exit(1);
}

/// Called once during `tauri::Builder::default().setup(...)`.
///
/// Responsibilities:
///   1. Read the sidecar port from HERETIC_PORT env (default 8642).
///   2. Resolve the pid_file path via Tauri's app_local_data_dir().
///   3. Spawn the Python sidecar.
///   4. Probe /health (30 s timeout).
///   5. Store the sidecar handle in managed state.
///
/// On any failure, a user-facing error dialog is shown and the app exits.
fn setup_app(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    log::info!("HERETIC shell setup: beginning sidecar spawn sequence");

    // --- Step 1: Determine sidecar port from environment ---------------------
    // Per RULES.AI.md: never hardcode settings. Port comes from env first,
    // then falls back to the heretic.yaml default (8642).
    let port: u16 = std::env::var("HERETIC_PORT")
        .ok()
        .and_then(|s| s.parse::<u16>().ok())
        .unwrap_or(8642);

    log::info!("HERETIC shell: sidecar port resolved to {}", port);

    // --- Step 2: Resolve pid_file path via Tauri PathResolver ---------------
    // Tauri's app_local_data_dir() returns:
    //   Windows: %LOCALAPPDATA%\io.heretic.app\
    //   macOS:   ~/Library/Application Support/io.heretic.app/
    //   Linux:   ~/.local/share/io.heretic.app/ (or $XDG_DATA_HOME/io.heretic.app/)
    //
    // This is cross-platform and location-agnostic (RULES.AI.md).
    //
    // FORGE-NOTE: Tauri 2 API — app.path().app_local_data_dir()
    //   Returns Result<PathBuf, tauri::Error>
    let pid_file: std::path::PathBuf = match app.path().app_local_data_dir() {
        Ok(data_dir) => data_dir.join("heretic-serve.pid"),
        Err(e) => {
            // Non-fatal: if we cannot resolve the data dir, skip PID tracking.
            log::warn!(
                "HERETIC shell: could not resolve app_local_data_dir: {}; pid_file disabled",
                e
            );
            std::path::PathBuf::new()
        }
    };

    // --- Step 3: Spawn the Python sidecar ------------------------------------
    // The runes are carved — we breathe life into the Python daemon.
    let sidecar = match PythonSidecar::spawn(port, pid_file) {
        Ok(s) => s,
        Err(ref e @ SidecarError::PythonNotFound { .. }) => {
            show_fatal_error_and_exit(
                app,
                "H.E.R.E.T.I.C. — Python Not Found",
                &format!(
                    "Python 3.10+ was not found on your system PATH.\n\n\
                    Please install Python 3.10 or later from https://python.org \
                    and ensure it is available on the PATH, then restart H.E.R.E.T.I.C.\n\n\
                    Technical detail: {}",
                    e
                ),
            );
            // show_fatal_error_and_exit calls app.exit(1) — this line is unreachable
            // but Rust needs a value here; the process will have exited.
            return Ok(());
        }
        Err(e) => {
            show_fatal_error_and_exit(
                app,
                "H.E.R.E.T.I.C. — Startup Error",
                &format!(
                    "H.E.R.E.T.I.C. could not start its background service.\n\n\
                    Technical detail: {}\n\n\
                    Check that 'heretic[serve]' is installed (pip install -e .[serve]) \
                    and try again.",
                    e
                ),
            );
            return Ok(());
        }
    };

    // --- Step 4: Health probe ------------------------------------------------
    // The völva reads the wyrd — we wait for the sidecar's heartbeat.
    if let Err(e) = sidecar.health_probe(Duration::from_secs(30)) {
        show_fatal_error_and_exit(
            app,
            "H.E.R.E.T.I.C. — Sidecar Not Responding",
            &format!(
                "H.E.R.E.T.I.C. started its background service but it did not become \
                ready within 30 seconds.\n\n\
                Technical detail: {}\n\n\
                Check the application logs for further information.",
                e
            ),
        );
        return Ok(());
    }

    // --- Step 5: Store in managed state -------------------------------------
    // The sidecar rune is sealed in Yggdrasil's bark.
    let state = app.state::<SidecarState>();
    match state.lock() {
        Ok(mut guard) => {
            *guard = Some(sidecar);
            log::info!("HERETIC shell: sidecar running and healthy — setup complete");
        }
        Err(e) => {
            // Mutex poisoned — extremely unlikely during setup.
            log::error!("HERETIC shell: SidecarState mutex poisoned: {}", e);
            show_fatal_error_and_exit(
                app,
                "H.E.R.E.T.I.C. — Internal Error",
                "An internal state error occurred during startup. Please restart the application.",
            );
        }
    }

    Ok(())
}

// ---------------------------------------------------------------------------
// RunEvent handler — sidecar kill on exit
// ---------------------------------------------------------------------------

/// Kill the sidecar when the application is exiting.
///
/// Called from the `RunEvent::ExitRequested` arm in the run() event loop.
/// This is the authoritative kill site — do not kill the sidecar from command
/// handlers or window-close handlers.
///
/// TAURI NOTE: Do NOT call `app_handle.exit()` inside this handler — that would
/// recursively re-fire ExitRequested. The exit was already triggered by the
/// `quit` command or window close; we are merely cleaning up.
fn on_exit_requested(app_handle: &AppHandle) {
    log::info!("RunEvent::ExitRequested: initiating sidecar shutdown");
    match app_handle.try_state::<SidecarState>() {
        Some(state) => {
            match state.lock() {
                Ok(mut guard) => {
                    if let Some(ref mut sidecar) = *guard {
                        match sidecar.kill() {
                            Ok(()) => log::info!("RunEvent::ExitRequested: sidecar killed cleanly"),
                            Err(SidecarError::NotRunning) => {
                                log::debug!("RunEvent::ExitRequested: sidecar was already stopped")
                            }
                            Err(e) => {
                                log::error!("RunEvent::ExitRequested: kill failed: {}", e)
                            }
                        }
                    } else {
                        log::debug!("RunEvent::ExitRequested: no sidecar in state (was not started)")
                    }
                }
                Err(e) => {
                    // Mutex poisoned — process is exiting anyway; log and continue.
                    log::error!("RunEvent::ExitRequested: mutex poisoned: {}", e);
                }
            }
        }
        None => {
            // State was not yet managed (failed very early in setup).
            log::warn!("RunEvent::ExitRequested: SidecarState not managed — nothing to kill");
        }
    }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

fn main() {
    // Tauri 2.x builder pattern.
    //
    // Plugins must be registered via .plugin() — they are no longer auto-included.
    // The invoke_handler macro registers all #[tauri::command] functions.
    // generate_context!() reads tauri.conf.json at compile time.
    tauri::Builder::default()
        // Dialog plugin — required for show_fatal_error_and_exit() native dialogs.
        // Must be registered before setup() runs.
        .plugin(tauri_plugin_dialog::init())
        // Single-instance lock: if a second launch attempt occurs, focus the
        // existing window instead of opening a second one.
        //
        // FORGE-NOTE: the callback receives &AppHandle. We cannot call the
        // async `focus_window` command from here (no async context), so we
        // call the window API directly. If the window is not yet ready (early
        // re-launch during startup), the set_focus() call will log a warning
        // and the user will need to click the taskbar icon.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            log::info!("second instance detected — focusing existing summoning-circle window");
            if let Some(window) = app.get_webview_window("summoning-circle") {
                if let Err(e) = window.set_focus() {
                    log::warn!("single-instance focus failed: {}", e);
                }
            }
        }))
        // Structured logging: routes Rust log:: calls to the Tauri log plugin.
        // Log level and targets are configured in tauri.conf.json plugins.log.
        .plugin(tauri_plugin_log::Builder::new().build())
        // Register managed state: the sidecar handle, wrapped for thread safety.
        .manage(SidecarState::new(Mutex::new(None)))
        // Application setup: spawn sidecar, probe health, store handle.
        .setup(|app| setup_app(app))
        // Register Tauri IPC commands.
        .invoke_handler(tauri::generate_handler![quit, focus_window, get_sidecar_port])
        // Run event loop and handle lifecycle events.
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            match event {
                // ExitRequested fires when the last window is closed OR when
                // app.exit() is called from the `quit` command.
                // Kill the sidecar here — single authoritative kill site.
                //
                // ARCHITECTURE NOTE (TAURI_SHELL.md §9 gotcha 4):
                //   Do NOT call app_handle.exit() here — that would recurse.
                //   The exit was already triggered; we are only cleaning up.
                RunEvent::ExitRequested { code, .. } => {
                    log::info!("RunEvent::ExitRequested (code: {:?})", code);
                    on_exit_requested(app_handle);
                }
                RunEvent::Ready => {
                    log::info!("HERETIC shell ready — Summoning Circle window open");
                }
                _ => {}
            }
        });
}
