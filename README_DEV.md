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
