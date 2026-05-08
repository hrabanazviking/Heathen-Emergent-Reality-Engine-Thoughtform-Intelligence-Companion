# Grunnr Module Interface

**Last updated:** 2026-05-07
**Scope:** L0 Grunnr — the Foundation layer Python module (`src/heretic/grunnr/`)
**Owner:** Architect (Rúnhild Svartdóttir)
**Derives from:** `docs/architecture/LAYER_INTERFACES.md §L0 Grunnr`
**Legend:** Owns = authoritative data owner; Never-controls = hard boundary.

---

## What Grunnr Owns

- `heretic.yaml` loading and typed `HereticConfig` struct
- Logging initialisation and the `get_logger(name)` factory
- The `LifecycleState` enum and `Lifecycle` state machine
- Portable path resolution (`paths.py`) — all OS-appropriate data/config/log dirs
- `ConfigLoadError` error type

## What Grunnr Exposes (Public API)

| Export | Module | Purpose |
|---|---|---|
| `HereticConfig` | `grunnr.config` | Typed root config struct. All layers read from this. |
| `load_config(path?)` | `grunnr.config` | Load, parse, validate heretic.yaml → HereticConfig. |
| `ConfigLoadError` | `grunnr.config` | Raised on unreadable or malformed config. |
| `get_logger(name)` | `grunnr.logger` | Return a `logging.Logger` namespaced under `heretic.*`. |
| `configure_logging(level, log_file?)` | `grunnr.logger` | One-time logging setup at Kynding. |
| `LifecycleState` | `grunnr.lifecycle` | Enum of all ceremony states (public + sub-states). |
| `Lifecycle` | `grunnr.lifecycle` | State machine; `transition()`, `on_state_change()`. |
| `LifecycleError` | `grunnr.lifecycle` | Raised on invalid state transitions. |
| `heretic_config_dir()` | `grunnr.paths` | OS config directory for heretic.yaml. |
| `heretic_data_dir()` | `grunnr.paths` | OS data directory for models, indices. |
| `heretic_log_dir()` | `grunnr.paths` | OS log directory. |
| `resolve_relative_path(raw, base?)` | `grunnr.paths` | Resolve config path string safely. |
| `resolve_env_var(value)` | `grunnr.paths` | Expand `${ENV_VAR}` references. |
| `package_root()` | `grunnr.paths` | Path to installed heretic package root. |

## What Grunnr Must Never Control

- Agent conversation, message content, or conversation history
- Sense data (voice audio, screen frames, MCP tool calls)
- Network routing (Tailscale logic lives in L1 Bifröst)
- Layer-level business logic beyond initialisation

## Inputs

| Input | Source | Notes |
|---|---|---|
| `heretic.yaml` | Filesystem (OS config search path) | Path resolved via `_resolve_config_path()` |
| OS signals (SIGTERM, Ctrl+C) | Operating system | Holdvörðr handles these and calls `lifecycle.transition(SLOKNA)` |
| `$HERETIC_CONFIG` env var | Shell environment | Override config path |

## Outputs (events emitted on the lifecycle event bus)

| Event | When |
|---|---|
| `heretic::lifecycle::starting` | Kynding begins |
| `heretic::lifecycle::layer_ready(layer_id)` | A layer completes initialisation |
| `heretic::lifecycle::layer_error(layer_id, error)` | A layer fails to initialise |
| `heretic::lifecycle::config_error(detail)` | heretic.yaml is missing or malformed |
| `heretic::lifecycle::shutdown` | Slokna sequence begins |

## Error Model

| Error | Condition | Behaviour |
|---|---|---|
| `ConfigLoadError` | heretic.yaml missing, unreadable, or malformed YAML | Lifecycle transitions to `CONFIG_ERROR` terminal state |
| `LifecycleError` | Invalid state transition attempted | Raised immediately; state unchanged |
| `EnvironmentError` | `${ENV_VAR}` reference in config not set in environment | Raised by `resolve_env_var()` |

## Capability Flags

None — Grunnr is infrastructure, not a capability surface. It does not appear in
the capability handshake reported to the agent.

## Invariants

1. No layer reads `heretic.yaml` directly after `load_config()` returns. All config
   flows through the `HereticConfig` struct.
2. All paths returned by `grunnr.paths` are derived from OS conventions, never
   hardcoded absolute strings.
3. `get_logger(name)` is the only way any layer creates a logger. No `print()` calls.
4. The `Lifecycle` instance is the single source of truth for ceremony state.
   Only Holdvörðr (the runtime process) calls `lifecycle.transition()`. Observers
   may not.

## What Callers Must Not Assume

- That `configure_logging()` has been called before `get_logger()`. Callers that
  need logging must call `configure_logging()` at their own initialisation, or rely
  on Holdvörðr to call it before their layer initialises.
- That `load_config()` is idempotent across calls with different paths — call it
  once per process startup and pass the result everywhere.
- That `LifecycleState` values map to any particular integer — compare by identity
  (`state == LifecycleState.HVILD`), not by value.
