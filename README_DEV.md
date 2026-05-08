# HERETIC — Developer Setup Guide

**Last updated:** 2026-05-07
**Scope:** How to install and run the Python package in development mode.
**For:** Forge Worker and contributors working on L0 Grunnr and L1 Bifröst.

---

## Prerequisites

- Python 3.11 or later
- pip (or uv/pipx — any PEP 517-compatible installer)
- Git on the `development` branch
- (Optional) Tailscale installed and authenticated if you want live Bifröst connection tests
- **v0.4.1+: Rust toolchain** — required to compile and run the Tauri shell (see §Tauri Shell below)
- **v0.4.1+: Node.js 18+** — required to build the React frontend and run `npm` scripts

---

## Installation

```bash
# From the repo root (C:/Users/volma/runa/HERETIC)
pip install -e ".[dev]"
```

The `-e` flag installs in editable mode — changes to `src/heretic/` take effect
immediately without reinstalling.

This installs:
- `heretic` Python package (from `src/heretic/`)
- `heretic` CLI entry point (`heretic light`, `heretic extinguish`, etc.)
- Dev dependencies: pytest, pytest-asyncio, pytest-mock

---

## Running the CLI

```bash
# After pip install -e .
heretic --help
heretic version

# Or run as a module (equivalent):
python -m heretic --help
python -m heretic version
```

In the v0.1 skeleton, `light` and `extinguish` raise `NotImplementedError` with
a clear Forge-facing message. `version` works immediately.

---

## Running Tests

```bash
# From the repo root
pytest

# Run only specific test files
pytest tests/test_grunnr_config.py
pytest tests/test_grunnr_lifecycle.py
pytest tests/test_bifrost_client.py

# Verbose output
pytest -v

# Show why skipped tests were skipped
pytest -v --tb=short
```

Expected output during skeleton phase: a mix of PASSED (structural tests) and
SKIPPED (Forge placeholder tests). Zero failures is the target.

---

## Import Verification

```bash
python -c "import sys; sys.path.insert(0, 'src'); import heretic; print(heretic.__version__)"
```

Expected output: `0.1.0.dev0`

---

## Package Structure

```
src/heretic/
  __init__.py         — package version, exported API
  __main__.py         — python -m heretic entrypoint
  cli.py              — argparse skeleton (light, extinguish, status, version)
  grunnr/             — L0 Foundation
    __init__.py
    INTERFACE.md      — what Grunnr exposes to other layers
    config.py         — HereticConfig dataclass + load_config() signature
    logger.py         — get_logger(name) + configure_logging()
    lifecycle.py      — LifecycleState enum + Lifecycle state machine
    paths.py          — portable path resolution helpers
  bifrost/            — L1 Agent Connection
    __init__.py
    INTERFACE.md      — what Bifröst exposes (open, send, close)
    client.py         — BifrostClient ABC + OpenAICompatClient skeleton
    config_model.py   — BifrostConfig dataclass
    tailscale.py      — TailscaleAwareness class skeleton
    errors.py         — BifrostError hierarchy
tests/
  __init__.py
  conftest.py         — pytest fixtures
  test_grunnr_config.py
  test_grunnr_lifecycle.py
  test_bifrost_client.py
```

---

## Configuration

Copy `heretic.example.yaml` to `~/heretic.yaml` (or the OS config dir) and edit:

```bash
# Windows
cp heretic.example.yaml "$env:APPDATA/heretic/heretic.yaml"

# Linux/macOS
cp heretic.example.yaml ~/.config/heretic/heretic.yaml
```

Set the required environment variable for the agent API key:

```bash
# Windows PowerShell
$env:HERETIC_AGENT_KEY = "your-api-key-here"

# Linux/macOS
export HERETIC_AGENT_KEY="your-api-key-here"
```

---

## Forge Notes

Every `NotImplementedError` in the skeleton carries a descriptive message explaining
exactly what needs to be built. Search for `raise NotImplementedError` to find all
implementation targets:

```bash
grep -rn "NotImplementedError" src/heretic/
```

Implementation priority order for v0.1 First Communion:
1. `grunnr/config.py` — `_hydrate_config()` and `load_config()`
2. `grunnr/logger.py` — `configure_logging()`
3. `grunnr/lifecycle.py` — `_validate_transition()` and `Lifecycle.transition()`
4. `bifrost/tailscale.py` — `_detect_tailscale()` and `TailscaleAwareness.resolve_endpoint()`
5. `bifrost/client.py` — `OpenAICompatClient.open()`, `send_message()`, `close()`
6. `cli.py` — `_cmd_light()` (the turn loop)

Cover each with real tests as you go. Target ≥ 80% coverage per the v0.1 exit criteria.

---

## Tauri Shell (v0.4.1+)

The native desktop shell wraps the React frontend in a WebView2 (Windows) /
WebKit (macOS) / WebKitGTK (Linux) window and manages the Python sidecar lifecycle.

### Install Rust

**Windows (recommended via winget):**
```powershell
winget install Rustlang.Rust.MSVC
# Restart your terminal after install to pick up PATH changes.
rustc --version   # verify: rustc 1.77+
```

**Windows (alternative via rustup-init):**
```powershell
# Download and run https://win.rustup.rs/x86_64 (rustup-init.exe)
# Then: rustup default stable
```

**Linux / macOS:**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup default stable
```

**Required target for Windows MSI builds:**
```bash
rustup target add x86_64-pc-windows-msvc
```

### Install Tauri CLI

```bash
cargo install tauri-cli --version "^2" --locked
# Verify:
cargo tauri --version
```

### Install Node dependencies

```bash
# From the repo root (installs workspace devDeps including @tauri-apps/cli)
npm install
# From the frontend directory (installs @tauri-apps/api and React deps)
cd frontend && npm install
```

### Run in development mode (Tauri + React + Python)

```bash
# 1. Ensure the heretic Python package is installed in editable mode:
pip install -e ".[dev,serve]"

# 2. From the repo root, run Tauri dev mode.
#    This starts Vite on port 1420 AND the Rust shell simultaneously.
#    The Rust shell spawns `python -m heretic serve` as a sidecar.
cargo tauri dev
```

The window opens when: Vite is serving on 1420, the Rust shell compiled,
and the Python sidecar passed its /health probe.

### Build for release (platform installer)

```bash
# Builds: frontend (npm run build) -> Rust release binary -> platform installer
cargo tauri build
# Output (Windows): src-tauri/target/release/bundle/msi/heretic_0.4.1_x64_en-US.msi
# Output (Linux):   src-tauri/target/release/bundle/deb/ and appimage/
# Output (macOS):   src-tauri/target/release/bundle/dmg/
```

**v0.4.1 prerequisite note:** The .msi installer does NOT bundle Python. The
end user must have Python 3.10+ on PATH with `pip install heretic[serve]` completed.
Full self-contained bundling (PyInstaller) is v0.4.1.x work.

### Troubleshoot: Rust not found after install

```powershell
# Windows: ensure Cargo bin directory is on PATH
$env:PATH += ";$env:USERPROFILE\.cargo\bin"
# Add that line to your PowerShell profile ($PROFILE) to persist it.
```

### Architecture reference

See `docs/architecture/TAURI_SHELL.md` for the full window lifecycle diagram,
sidecar approach rationale, IPC delineation, and Tauri 2 vs 1 differences.
