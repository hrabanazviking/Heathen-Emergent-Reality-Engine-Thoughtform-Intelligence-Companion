// error.rs — Typed error hierarchy for the HERETIC Tauri shell.
//
// All public-facing Tauri command errors must implement serde::Serialize so
// they can be returned to the WebView as structured JSON. The `#[serde(tag = "kind")]`
// pattern gives the frontend a discriminated union it can switch on.
//
// Usage pattern:
//   #[tauri::command]
//   fn my_command() -> Result<SomeReturn, TauriError> { ... }
//
// The error is serialized by Tauri's IPC layer before crossing into the WebView.

use serde::Serialize;
use thiserror::Error;

/// Top-level error type for all Tauri IPC commands.
/// Returned as JSON to the WebView on command failure.
#[derive(Debug, Error, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum TauriError {
    /// The Python sidecar process could not be started or managed.
    #[error("sidecar error: {message}")]
    Sidecar { message: String },

    /// A Tauri window API call failed.
    #[error("window error: {message}")]
    Window { message: String },

    /// A command was invoked when the system was in an invalid state.
    #[error("invalid state: {message}")]
    InvalidState { message: String },

    /// An unexpected internal error — wraps anyhow chains.
    #[error("internal error: {message}")]
    Internal { message: String },
}

impl From<SidecarError> for TauriError {
    fn from(e: SidecarError) -> Self {
        TauriError::Sidecar {
            message: e.to_string(),
        }
    }
}

impl From<anyhow::Error> for TauriError {
    fn from(e: anyhow::Error) -> Self {
        TauriError::Internal {
            message: format!("{:#}", e),
        }
    }
}

/// Errors specific to Python sidecar lifecycle management.
#[derive(Debug, Error)]
pub enum SidecarError {
    /// The sidecar process failed to start.
    #[error("failed to spawn sidecar process: {source}")]
    SpawnFailed {
        #[source]
        source: std::io::Error,
    },

    /// The sidecar started but did not pass the health probe within the timeout.
    #[error("sidecar health probe timed out after {timeout_secs}s on port {port}")]
    HealthTimeout { timeout_secs: u64, port: u16 },

    /// The sidecar health endpoint returned an unexpected response.
    #[error("sidecar health probe returned unexpected status: {status}")]
    HealthUnexpected { status: u16 },

    /// The sidecar process could not be killed cleanly.
    #[error("failed to kill sidecar process (pid {pid}): {source}")]
    KillFailed {
        pid: u32,
        #[source]
        source: std::io::Error,
    },

    /// The sidecar is not running; a lifecycle call was made against a None child.
    #[error("sidecar is not running")]
    NotRunning,

    /// Port resolution failed (e.g. config read error).
    #[error("could not determine sidecar port: {message}")]
    PortResolution { message: String },
}
