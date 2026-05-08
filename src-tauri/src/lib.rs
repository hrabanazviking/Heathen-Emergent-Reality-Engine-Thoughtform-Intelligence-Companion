// lib.rs — HERETIC Tauri shell library crate root.
//
// This crate is compiled as both a bin (main.rs) and a lib (lib.rs) so that
// future mobile targets (iOS, Android) can link against the library without
// recompiling the full binary. The lib surface is intentionally minimal for v0.4.1.
//
// FORGE: as you implement Tauri commands in main.rs, consider moving them here
// and re-exporting from main.rs via `pub use heretic_lib::*;` so they are
// accessible from mobile harnesses. For v0.4.1 this is optional scaffolding.

pub mod error;
pub mod sidecar;

/// HERETIC shell version — mirrors Cargo.toml version.
/// FORGE: consider driving this from `env!("CARGO_PKG_VERSION")` in the
/// `get_sidecar_port` command response so it never drifts.
pub const SHELL_VERSION: &str = env!("CARGO_PKG_VERSION");
