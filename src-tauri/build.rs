// build.rs — Tauri 2.x build script.
//
// This must remain at the crate root (src-tauri/build.rs).
// It calls tauri_build::build() which generates the necessary code and
// validates the tauri.conf.json at compile time.
//
// FORGE: if you add Tauri allowlists or capabilities that require additional
// build-time features, pass a BuildAttributes struct to build_from_config()
// instead of the bare build() call.
fn main() {
    tauri_build::build()
}
