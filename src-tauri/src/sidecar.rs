// sidecar.rs — Python sidecar lifecycle management for the HERETIC Tauri shell.
//
// Responsibility: spawn `python -m heretic serve`, probe its /health endpoint,
// hold the child handle, and kill cleanly on Drop or explicit request.
//
// DESIGN DECISION (v0.4.1): We use system Python (`python -m heretic serve`)
// rather than a bundled PyInstaller binary. The bundled binary approach (tauri
// `externalBin` with a pre-compiled heretic-serve.exe) is deferred to v0.4.1.x.
// Rationale: bundling adds 30-60 MB and a complex CI build step; for v0.4.1 the
// window-wrapping milestone, system Python is sufficient if documented in
// README_DEV.md. See TASK_HERETIC_v0.4.1_TAURI_WRAP.md §4 for the full rationale.
//
// FORGE: implement the todo!() bodies below. The health probe requires an async
// HTTP GET to `http://127.0.0.1:{port}/health`. Use `tokio::time::timeout` around
// the probe loop. The spawn must find `python` or `python3` on PATH (prefer
// checking for `python3` first on non-Windows, `python` on Windows).
//
// FORGE: verify Tauri 2 API for spawning a Command:
//   https://docs.rs/tauri/2/tauri/process/struct.Command.html
// In v0.4.1 we do NOT use Tauri's sidecar API (which requires the binary to be
// declared under `externalBin` in tauri.conf.json). We use std::process::Command
// directly since we are invoking system Python, not a bundled sidecar binary.

use crate::error::SidecarError;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::time::Duration;

/// Manages the lifecycle of the Python `heretic serve` child process.
///
/// The sidecar is spawned by [`PythonSidecar::spawn`] and terminates either
/// explicitly via [`PythonSidecar::kill`] or automatically when the struct is
/// dropped (via the `Drop` implementation). The Tauri `RunEvent::ExitRequested`
/// handler in `main.rs` calls `kill()` explicitly before the app exits; Drop is
/// the safety net for panics and unclean exits.
pub struct PythonSidecar {
    /// The OS child process handle. `None` after a successful `kill()` call.
    child: Option<Child>,

    /// The TCP port the Python sidecar is listening on.
    /// Used by the `get_sidecar_port` Tauri command.
    pub port: u16,

    /// Path to the pid file written by the sidecar (optional; used for crash recovery).
    /// FORGE: the Python `heretic serve` command should write its PID to this path
    /// at startup if `vebond.pid_file` is set in heretic.yaml.
    pub pid_file: PathBuf,
}

impl PythonSidecar {
    /// Spawn the Python sidecar and return a managed handle.
    ///
    /// This does NOT wait for the health probe — the caller should call
    /// [`health_probe`] after `spawn` to confirm the server is ready.
    ///
    /// # Arguments
    /// - `port`: the TCP port for `heretic serve` to bind on (from heretic.yaml).
    /// - `pid_file`: optional path for the sidecar's pid file; pass an empty path
    ///   if pid file tracking is not needed.
    ///
    /// # Errors
    /// Returns [`SidecarError::SpawnFailed`] if the OS process creation fails.
    pub fn spawn(port: u16, pid_file: PathBuf) -> Result<Self, SidecarError> {
        // FORGE: implement this body.
        // Steps:
        //   1. Locate the Python executable: try `python3` first (POSIX), fall
        //      back to `python` (Windows). Use `which`-style PATH search or
        //      just attempt spawn and let the OS fail cleanly.
        //   2. Build std::process::Command:
        //        Command::new("python")
        //          .args(["-m", "heretic", "serve", "--port", &port.to_string()])
        //          .stdin(Stdio::null())
        //          .stdout(Stdio::inherit())  // heretic uses structured logging; inherit is fine
        //          .stderr(Stdio::inherit())
        //          .spawn()
        //          .map_err(|e| SidecarError::SpawnFailed { source: e })?
        //   3. Return PythonSidecar { child: Some(child), port, pid_file }
        todo!("Forge implements: spawn system Python with `python -m heretic serve --port {port}`")
    }

    /// Probe the sidecar's /health endpoint until it returns HTTP 200 or the
    /// timeout elapses.
    ///
    /// Uses a retry loop with 250 ms sleep between attempts. Suitable for use
    /// inside a `tokio::task::spawn_blocking` or a `tauri::async_runtime::spawn`.
    ///
    /// # Arguments
    /// - `timeout`: maximum time to wait for the sidecar to become healthy.
    ///
    /// # Errors
    /// - [`SidecarError::HealthTimeout`] if the probe does not succeed within `timeout`.
    /// - [`SidecarError::HealthUnexpected`] if the sidecar responds but with a non-200 status.
    pub fn health_probe(&self, timeout: Duration) -> Result<(), SidecarError> {
        // FORGE: implement this body.
        // Use blocking HTTP (reqwest blocking feature, or ureq, or std TcpStream + raw GET).
        // Pattern:
        //   let deadline = std::time::Instant::now() + timeout;
        //   loop {
        //     if Instant::now() >= deadline {
        //       return Err(SidecarError::HealthTimeout { timeout_secs: timeout.as_secs(), port: self.port });
        //     }
        //     match blocking_http_get(&format!("http://127.0.0.1:{}/health", self.port)) {
        //       Ok(200) => return Ok(()),
        //       Ok(status) => return Err(SidecarError::HealthUnexpected { status }),
        //       Err(_) => {} // not yet up; sleep and retry
        //     }
        //     std::thread::sleep(Duration::from_millis(250));
        //   }
        //
        // NOTE: the /health endpoint JSON body contains `lifecycle_state`; Tauri does
        // not need to parse it for the probe — 200 OK is sufficient.
        // See IPC_PROTOCOL.md §1 for the response shape if state inspection is ever needed.
        let _ = timeout; // suppress unused warning until Forge implements
        todo!("Forge implements: HTTP GET http://127.0.0.1:{}/health with retry loop", self.port)
    }

    /// Kill the sidecar process.
    ///
    /// Sends SIGTERM (POSIX) / TerminateProcess (Windows) to the child.
    /// Sets `self.child` to `None` after a successful kill so that `Drop`
    /// does not attempt a second kill.
    ///
    /// # Errors
    /// Returns [`SidecarError::KillFailed`] if the OS kill call fails.
    /// Returns [`SidecarError::NotRunning`] if the child was already killed.
    pub fn kill(&mut self) -> Result<(), SidecarError> {
        // FORGE: implement this body.
        // Pattern:
        //   match self.child.take() {
        //     None => Err(SidecarError::NotRunning),
        //     Some(mut child) => {
        //       let pid = child.id();
        //       child.kill().map_err(|e| SidecarError::KillFailed { pid, source: e })?;
        //       child.wait().ok(); // reap the process to avoid zombie
        //       Ok(())
        //     }
        //   }
        todo!("Forge implements: kill child process and reap with .wait()")
    }

    /// Return the port this sidecar is bound to.
    ///
    /// Used by the `get_sidecar_port` Tauri command so that the WebView can
    /// confirm the port it should use for WebSocket connections. In v0.4.1 the
    /// port is always 8642 (from heretic.yaml default); this accessor is here
    /// so the Tauri command does not hardcode that value.
    pub fn port(&self) -> u16 {
        self.port
    }
}

/// Safety net: kill the sidecar if the struct is dropped without an explicit kill().
/// This covers panics and unclean exits where the RunEvent::ExitRequested handler
/// did not run.
impl Drop for PythonSidecar {
    fn drop(&mut self) {
        if self.child.is_some() {
            log::warn!(
                "PythonSidecar dropped without explicit kill; terminating sidecar on port {}",
                self.port
            );
            // Best-effort kill — ignore the result in Drop.
            if let Some(mut child) = self.child.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}
