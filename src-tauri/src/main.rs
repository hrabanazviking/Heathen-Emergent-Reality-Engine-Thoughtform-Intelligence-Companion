// main.rs — HERETIC Tauri 2.x shell entry point.
//
// TAURI VERSION: 2.x — do NOT apply Tauri 1.x patterns here.
//
// Key Tauri 2 vs 1 differences honored in this file:
//   - `.plugin()` is used for single-instance and log (v1 had these built-in)
//   - `generate_context!()` is the v2 macro (same name, different internals)
//   - `RunEvent` variants are accessed from `tauri::RunEvent` (same in v2)
//   - `WindowBuilder` v2 API is at `tauri::WebviewWindowBuilder` (changed from v1)
//   - Capabilities are in capabilities/default.json, NOT in tauri.conf.json allowlist
//
// FORGE: implement all todo!() bodies. Priority order:
//   1. setup() — sidecar spawn + health probe
//   2. RunEvent::ExitRequested handler — sidecar kill
//   3. quit command — graceful window close
//   4. focus_window command — bring window to foreground
//   5. get_sidecar_port command — return the active port
//
// FORGE: verify Tauri 2 AppHandle API:
//   https://docs.rs/tauri/2/tauri/struct.AppHandle.html
// FORGE: verify Tauri 2 WebviewWindowBuilder:
//   https://docs.rs/tauri/2/tauri/webview/struct.WebviewWindowBuilder.html
// FORGE: verify tauri-plugin-single-instance v2 usage:
//   https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/single-instance

// Prevent a console window from appearing on Windows release builds.
// Remove this if you need the console during development.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use heretic_lib::error::TauriError;
use heretic_lib::sidecar::PythonSidecar;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tauri::{AppHandle, Manager, RunEvent, State};

// ---------------------------------------------------------------------------
// Shared application state
// ---------------------------------------------------------------------------

/// Thread-safe wrapper around the Python sidecar handle.
/// Stored in Tauri managed state so all commands and event handlers can reach it.
type SidecarState = Arc<Mutex<Option<PythonSidecar>>>;

// ---------------------------------------------------------------------------
// Tauri commands — minimal surface (v0.4.1)
//
// The IPC_PROTOCOL.md makes clear that MOST IPC is WebSocket (ws://localhost:8642/ws).
// These Tauri commands handle only what only-native can do:
//   - quit:             confirm-and-close the window
//   - focus_window:     bring the window to the foreground (single-instance redirect)
//   - get_sidecar_port: let the WebView know the bound port (avoids hardcoding in TS)
// ---------------------------------------------------------------------------

/// Quit the application.
///
/// The sidecar is killed in the RunEvent::ExitRequested handler; this command
/// triggers the exit which causes that event to fire.
///
/// Called from the WebView when the user confirms a close action.
/// In v0.4.1, no confirmation dialog is shown by the shell — the frontend may
/// show one via its own React modal before invoking this command.
#[tauri::command]
async fn quit(app: AppHandle) -> Result<(), TauriError> {
    // FORGE: implement this body.
    // Pattern:
    //   app.exit(0);
    //   Ok(())
    //
    // Note: app.exit() is the Tauri 2 way to request clean shutdown.
    // Do NOT call std::process::exit() here — Tauri must run its cleanup path.
    let _ = app; // suppress unused warning until Forge implements
    todo!("Forge implements: app.exit(0) — trigger graceful Tauri shutdown")
}

/// Bring the main window to the foreground.
///
/// Called by the single-instance plugin when a second launch attempt is detected.
/// Tauri's single-instance plugin fires a callback on the first instance;
/// that callback should invoke this command (or call the window API directly).
#[tauri::command]
async fn focus_window(app: AppHandle) -> Result<(), TauriError> {
    // FORGE: implement this body.
    // Pattern (Tauri 2 WebviewWindow API):
    //   let window = app.get_webview_window("summoning-circle")
    //     .ok_or(TauriError::Window { message: "summoning-circle window not found".into() })?;
    //   window.set_focus().map_err(|e| TauriError::Window { message: e.to_string() })?;
    //   Ok(())
    //
    // FORGE: verify Tauri 2 API: AppHandle::get_webview_window
    //   https://docs.rs/tauri/2/tauri/struct.AppHandle.html#method.get_webview_window
    let _ = app;
    todo!("Forge implements: get_webview_window(\"summoning-circle\").set_focus()")
}

/// Return the port the Python sidecar is bound to.
///
/// The WebView JS layer calls this on startup to confirm the WebSocket port
/// rather than hardcoding `8642`. If the sidecar is not running, returns an error.
#[tauri::command]
async fn get_sidecar_port(state: State<'_, SidecarState>) -> Result<u16, TauriError> {
    // FORGE: implement this body.
    // Pattern:
    //   let guard = state.lock().map_err(|e| TauriError::Internal { message: e.to_string() })?;
    //   match guard.as_ref() {
    //     Some(sidecar) => Ok(sidecar.port()),
    //     None => Err(TauriError::Sidecar { message: "sidecar not running".into() }),
    //   }
    let _ = state;
    todo!("Forge implements: lock SidecarState and return sidecar.port()")
}

// ---------------------------------------------------------------------------
// Application setup
// ---------------------------------------------------------------------------

/// Called once during `tauri::Builder::default().setup(...)`.
///
/// Responsibilities:
///   1. Read the sidecar port from managed state (or heretic.yaml via Tauri config).
///   2. Spawn the Python sidecar.
///   3. Probe the /health endpoint (with a 30 s timeout).
///   4. Store the sidecar handle in managed state.
///
/// If setup fails, the app should surface a user-facing error dialog and exit.
/// In v0.4.1 we log the error and continue (the WebView will show a connection-
/// error state via its normal WebSocket error handling).
fn setup_app(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    // FORGE: implement this body.
    //
    // Steps:
    //   1. Determine sidecar port.
    //      The port is read from heretic.yaml at Python startup. For Tauri's purposes,
    //      we default to 8642 (the heretic.yaml default `vebond.ws_port`) and allow it
    //      to be overridden via a HERETIC_PORT environment variable.
    //      Do NOT hardcode 8642 in production paths — read from env or config file.
    //      See RULES.AI.md: "Never hardcode settings in the code, always use data files."
    //
    //   2. pid_file path: use Tauri's app_local_data_dir() for cross-platform portability.
    //      let pid_file = app.path().app_local_data_dir()?.join("heretic-serve.pid");
    //
    //   3. Spawn:
    //      let sidecar = PythonSidecar::spawn(port, pid_file)
    //        .map_err(|e| format!("Failed to spawn sidecar: {}", e))?;
    //
    //   4. Probe:
    //      sidecar.health_probe(Duration::from_secs(30))
    //        .map_err(|e| format!("Sidecar health probe failed: {}", e))?;
    //
    //   5. Store in managed state:
    //      let state = app.state::<SidecarState>();
    //      *state.lock().unwrap() = Some(sidecar);
    //
    // FORGE: verify Tauri 2 API: App::path()
    //   https://docs.rs/tauri/2/tauri/struct.App.html#method.path
    // FORGE: verify Tauri 2 API: PathResolver::app_local_data_dir()
    //   https://docs.rs/tauri/2/tauri/path/struct.PathResolver.html
    let _ = app;
    log::info!("HERETIC shell setup: sidecar spawn deferred to Forge implementation");
    Ok(())
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
        // Single-instance lock: if a second launch attempt occurs, focus the
        // existing window instead of opening a second one.
        // FORGE: verify the v2 single-instance plugin callback API:
        //   https://github.com/tauri-apps/plugins-workspace/tree/v2/plugins/single-instance
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            // FORGE: implement this callback.
            // When a second instance is launched, focus the existing window:
            //   let _ = tauri::async_runtime::block_on(focus_window(app.clone()));
            log::info!("Second instance detected; focusing existing window");
            let _ = app; // suppress unused warning
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
                // app.exit() is called. Kill the sidecar here.
                RunEvent::ExitRequested { code, .. } => {
                    log::info!("RunEvent::ExitRequested (code: {:?}); killing sidecar", code);
                    // FORGE: implement sidecar kill here.
                    // Pattern:
                    //   let state = app_handle.state::<SidecarState>();
                    //   if let Ok(mut guard) = state.lock() {
                    //     if let Some(ref mut sidecar) = *guard {
                    //       if let Err(e) = sidecar.kill() {
                    //         log::error!("Failed to kill sidecar: {}", e);
                    //       }
                    //     }
                    //   }
                    let _ = app_handle;
                }
                RunEvent::Ready => {
                    log::info!("HERETIC shell ready — Summoning Circle window open");
                }
                _ => {}
            }
        });
}
