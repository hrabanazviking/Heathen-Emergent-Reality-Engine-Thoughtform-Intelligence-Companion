# HERETIC — Sense Contracts

**Last updated:** 2026-05-07 (corrective pass — Rúnhild Svartdóttir, resolving audit blockers A-1, A-2, A-3, A-4; tool format canonicalized; Auga/Hlust/Tunga layering resolved; Skepja sandboxing tiers added; open questions closed)
**Scope:** The standard MCP interface every sense must implement; tool naming convention; capability flags; error taxonomy; version negotiation; sandbox/permission model; per-sense detail subsections for L5.1–L5.9 with True Names.
**Authority:** Derives from `ARCHITECTURE.md`, `DOMAIN_MAP.md`, `LAYER_INTERFACES.md`.
**Owner:** Architect (Rúnhild Svartdóttir)
**Legend:** True Names from `docs/NAMING.md` appear in per-sense section headers.

---

## 1. The Standard Sense Lifecycle

Every sense MCP server — whether built-in or user-provided via L5.8 Nýr Limr — must implement the following lifecycle. This is the covenant between the sense and L5 Skilningr (the MCP Sense Hub).

### 1.1 Startup

L5 Skilningr spawns the sense as a subprocess via `stdio` MCP transport. On spawn:

1. Sense reads its config from the JSON config object passed by Skilningr at spawn (or via environment variables set by Skilningr).
2. Sense initializes its resources (opens connections, checks app availability, etc.).
3. Sense responds to Skilningr's initial `initialize` MCP call with its `ServerInfo` and capability declaration.
4. Sense is now available for tool calls.

If initialization fails (required resource unavailable), the sense must respond to `initialize` with an error and exit cleanly. Skilningr marks the sense `UNAVAILABLE` and does not retry until the next ceremony or a manual re-enable via L4 Vébond.

### 1.2 Health check

Skilningr sends a health probe every `senses.<id>.health_interval_seconds` (default 15 s) via a lightweight `tools/list` call. If the sense responds, it is `HEALTHY`. If it does not respond within 5 seconds, it is `DEGRADED`. Three consecutive `DEGRADED` results → Skilningr kills and restarts the subprocess per `restart_policy`.

### 1.3 Tool listing

Every sense must implement `tools/list` and return its full tool schema list on demand. Skilningr calls this:
- At sense startup (initial schema registration)
- After a sense restart (to re-register tools)
- On demand if `sense_hub.refresh_schemas_on_reconnect: true`

### 1.4 Tool call

Every sense must implement `tools/call(name, arguments) -> result`. Arguments are a JSON object matching the tool's declared parameter schema. Result is a JSON object. Errors are returned as structured error objects (see §3), never as raw Python exceptions propagated to Skilningr.

### 1.5 Shutdown

When Skilningr sends `SIGTERM` (or the graceful shutdown event on Windows — during Slokna), the sense must:
1. Finish any in-flight tool call, or return a `SENSE_SHUTDOWN` error for it.
2. Close all open resources.
3. Exit with code 0.

If the sense does not exit within `senses.<id>.shutdown_grace_seconds` (default 5 s), Skilningr sends `SIGKILL`.

---

## 2. Tool Naming Convention — Canonical Format v1.0

**This is the single canonical tool-name format for HERETIC. No other format is valid.**

All tool names follow the two-part pattern: `<sense_id>.<action_name>`

The `sense_id` is the code-facing identifier for the sense (not the True Name). There is no `sense.` prefix. Tool names are flat strings; the dot is a namespace separator only. The agent receives these strings as-is in the `tools` array and must use the exact string when making a tool call.

**Why two-part, no prefix:** The `sense.` prefix is redundant — every tool HERETIC exposes is a sense by definition. Removing it produces shorter, cleaner tool names. L5.8 Nýr Limr custom senses declare their own top-level prefix, which correctly does not force a `sense.` that would be inaccurate for non-sense plugins (e.g., `wyrd.query_world_state` from the WYRD Protocol custom sense).

```
filesystem.read_file
filesystem.write_file
terminal.run_command
browser.navigate
browser.screenshot
photopea.new_document
blender.screenshot
blender.vroid_export
vrchat.send_osc
agentmail.send
library.search
hlust.listen              ← L5.10 Hlust — voice hearing (STT)
tunga.speak               ← L5.11 Tunga — voice speaking (TTS)
auga.snapshot             ← L5.12 Auga — screen/visual capture
home.turn_on_light        ← example L5.8 Nýr Limr custom sense
wyrd.query_world_state    ← example L5.8 Nýr Limr custom sense (WYRD Protocol)
```

The sense True Name to `sense_id` mapping:

| True Name | sense_id (code-facing) | Layer position |
|---|---|---|
| Minni (minni) | `filesystem` | L5.1 |
| Skepja (skepja) | `terminal` | L5.2 |
| Leið (leid) | `browser` | L5.3 |
| Hönd (hond) | `photopea` | L5.4 |
| Smiðja (smidja) | `blender` | L5.5 |
| Líkami (likami) | `vrchat` | L5.6 |
| Boð (bod) | `agentmail` | L5.7 |
| Nýr Limr (nyr_limr) | user-declared `prefix` per plugin | L5.8 |
| Mímisbrunnr (mimisbrunnr) | `library` | L5.9 |
| Hlust (hlust) | `hlust` | L5.10 — voice hearing (STT); substrate in L2 Rödd |
| Tunga (tunga) | `tunga` | L5.11 — voice speaking (TTS); substrate in L2 Rödd |
| Auga (auga) | `auga` | L5.12 — sight/snapshot; substrate in L3 Sjón |

**Auga, Hlust, Tunga — layering note:** These three have `sense.*` identifiers in NAMING.md because they are agent-callable L5 senses. Their physical capture/playback infrastructure lives in L2 Rödd (Hlust/Tunga) and L3 Sjón (Auga), but those layers own the substrate only — they expose no tools directly to the agent. The L5 sense subprocesses for Hlust, Tunga, and Auga call into L2/L3 infrastructure via internal IPC to fulfill agent tool calls. Full architectural resolution in `ARCHITECTURE.md` §"Sense layering — L5 surface, L2/L3 substrate".

Rules:
- `sense_id` is always a single lowercase word (underscore permitted for multi-word; brevity preferred)
- `action_name` uses `snake_case`
- No two senses may register the same fully-qualified tool name
- L5.8 Nýr Limr plugins must declare a `prefix` in config; all their tools must start with that prefix
- Tool names are stable identifiers — renaming a tool is a breaking change requiring a sense version bump

---

## 3. Error Taxonomy

All sense errors are returned in the following structure inside the `tool_result.content` JSON:

```json
{
  "error": true,
  "code": "<ERROR_CODE>",
  "message": "<human-readable description>",
  "sense": "<sense_id>",
  "tool": "<fully_qualified_tool_name>",
  "detail": "<optional: OS error, stack trace ref, etc.>"
}
```

### Standard error codes (all senses must use these codes when applicable)

| Code | Meaning |
|---|---|
| `SENSE_UNAVAILABLE` | Sense subprocess is not running or failed to initialize |
| `SENSE_TIMEOUT` | Tool call did not complete within the sense's configured timeout |
| `SENSE_SHUTDOWN` | Tool call was in-flight when sense shutdown was requested (Slokna) |
| `PERMISSION_DENIED` | Operation rejected by sense sandbox policy (path outside allowed root, domain not in allowlist, etc.) |
| `NOT_FOUND` | The target resource does not exist (file, article, URL, etc.) |
| `FILE_TOO_LARGE` | File exceeds configured size limit |
| `COMMAND_FORBIDDEN` | Terminal command matches a forbidden pattern |
| `DOMAIN_NOT_ALLOWED` | Browser navigation target is not in the domain allowlist |
| `INVALID_ARGUMENTS` | Tool was called with missing or malformed arguments |
| `PARTIAL_SUCCESS` | Tool completed but with degraded output (e.g., timeout on a long command — partial stdout returned) |
| `EXTERNAL_APP_UNAVAILABLE` | The application being controlled (Blender, VRChat, etc.) is not running or reachable |
| `EXTERNAL_APP_ERROR` | The controlled application returned an error |
| `SENSE_INTERNAL_ERROR` | Unexpected error inside the sense — a bug; full error logged by sense; `detail` field contains a reference |

### Sense-specific error codes

Senses may define additional codes beyond the standard set, provided they:
1. Are documented in this file's per-sense subsection
2. Are prefixed with the sense id: e.g., `FILESYSTEM_ENCODING_ERROR`
3. Do not collide with the standard codes above

---

## 4. Version Negotiation

The `initialize` response from each sense includes a `senseVersion` field:

```json
{
  "protocolVersion": "2024-11-05",
  "capabilities": { "tools": {} },
  "serverInfo": {
    "name": "heretic-sense-filesystem",
    "version": "0.1.0",
    "senseVersion": "1",
    "minHubVersion": "1"
  }
}
```

- `protocolVersion` — MCP protocol version (follows Anthropic MCP spec versioning)
- `senseVersion` — HERETIC sense API version (integer; this document defines version 1)
- `minHubVersion` — minimum Hub (Skilningr) version this sense requires

If the Hub version is below the sense's `minHubVersion`, Skilningr refuses the sense with a `VERSION_MISMATCH` error and marks it `UNAVAILABLE`. This ensures forward compatibility as the sense API evolves.

**Current versions:** MCP protocol `2024-11-05`, HERETIC sense API `1`, Skilningr Hub `1`.

---

## 5. Sandbox and Permission Model

### 5.1 User permissions — what the user toggles

In `heretic.yaml`, each sense has an `enabled` flag and a sense-specific config block. The enabled flag is the master toggle:

```yaml
senses:
  <sense_id>:
    enabled: true | false        # master toggle — agent cannot override
    # ... sense-specific permission fields
```

**The user's `heretic.yaml` is the final authority on what senses are enabled and what they can access.** The agent cannot enable a disabled sense. The agent cannot expand sandbox boundaries.

### 5.2 Agent requests — what the agent can ask for

The agent may call tools within the bounds of what is already enabled. It cannot:
- Enable a disabled sense
- Expand sandbox boundaries (e.g., request access to paths outside `allowed_roots`)
- Access tools not in the current session's tool schema list

The agent can describe a need that requires a currently-disabled sense — but the human user must act on that request via the L4 Vébond toggle. HERETIC does not auto-enable senses based on agent text.

### 5.3 Skepja (Terminal) — Sandboxing Tiers

Skepja uses an allowlist-first, opt-in escalation model. The tier is controlled by `heretic.yaml` config.

| Tier | Config | What it permits |
|---|---|---|
| **Tier 0 (default)** | `safe_mode: true`, `allow_unrestricted_dirs: false` | `allowed_dirs` restricted to `~/heretic_workspace`; `forbidden_patterns` active; no network commands |
| **Tier 1 (operator opt-in)** | Operator expands `allowed_dirs` | Additional dirs added by user; forbidden patterns still active |
| **Tier 2 (power user opt-in)** | `allow_unrestricted_dirs: true` | Directory restriction removed; forbidden patterns still enforced; explicit config required |
| **Tier 3 (explicit unsafe)** | `safe_mode: false` | All restrictions removed; must be set with a warning comment in config schema |

Default `heretic.yaml` ships with Tier 0 settings. Forge must refuse to run any command if the resolved `cwd` falls outside the permitted scope for the active tier.

### 5.4 Per-sense permission flags summary

| Sense (True Name) | Key permission flags |
|---|---|
| Minni (filesystem) | `allow_write`, `allow_delete`, `allowed_roots` list |
| Skepja (terminal) | `allowed_dirs`, `forbidden_patterns` regex list, sandboxing tier (§5.3) |
| Leið (browser) | `allowed_domains` (empty = all), `headless` |
| Hönd (photopea) | Inherits Leið's permissions (browser must be enabled) |
| Smiðja (blender) | Inherits from Seidr-Smidja Brúarhönd's auth token |
| Líkami (vrchat) | OSC port (implicitly scoped to localhost) |
| Boð (agentmail) | Configured mail account scope (no cross-account access) |
| Nýr Limr (custom) | User-defined per plugin |
| Mímisbrunnr (library) | `allowed_sources` list; vector retrieval opt-in |
| Hlust (hlust) | Inherits L2 Rödd device config; no additional sandbox |
| Tunga (tunga) | Inherits L2 Rödd TTS endpoint config; no additional sandbox |
| Auga (auga) | Inherits L3 Sjón capture config; `save_frames` opt-in only |

---

## 6. Per-Sense Detail Subsections

---

### L5.1 — Minni (FileSystem Sense)

**True Name:** Minni (minni) — memory; the agent's external memory in Midgard.
**Subprocess name:** `heretic-sense-minni`
**Purpose:** Sandboxed read/write access to user-configured allowed directories. The agent's persistent notes, workspace files, and created artifacts live here.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `filesystem.read_file` | `path: string` | `content: string` | UTF-8 text; binary files return base64 with MIME type |
| `filesystem.write_file` | `path: string, content: string` | `ok: true` | Creates intermediate dirs if needed; requires `allow_write: true` |
| `filesystem.append_file` | `path: string, content: string` | `ok: true` | Appends to existing file; requires `allow_write: true` |
| `filesystem.list_directory` | `path: string, recursive: bool` | `entries: [{name, type, size, modified}]` | |
| `filesystem.create_directory` | `path: string` | `ok: true` | Creates with parents; requires `allow_write: true` |
| `filesystem.delete_file` | `path: string` | `ok: true` | Requires `allow_delete: true` (separate from write) |
| `filesystem.move_file` | `src: string, dst: string` | `ok: true` | Both paths must be within allowed roots |
| `filesystem.file_exists` | `path: string` | `exists: bool` | |
| `filesystem.get_file_info` | `path: string` | `{name, size, modified, mime_type}` | |

**Permissions required:**
- `allowed_roots` list (at least one entry required for sense to function)
- `allow_write: true` for write/create/move operations
- `allow_delete: true` specifically for delete

**Dependencies:** OS filesystem only. No third-party runtime deps.

**Runtime cost:** Minimal — synchronous I/O per call; no background process.

**License of underlying:** OS native filesystem — no third-party license.

**Sense-specific error codes:**
- `FILESYSTEM_ENCODING_ERROR` — file content is not valid UTF-8 and binary mode was not requested

---

### L5.2 — Skepja (Terminal Sense)

**True Name:** Skepja (skepja) — to shape, create; the act of making through direct action on the machine.
**Subprocess name:** `heretic-sense-skepja`
**Purpose:** Sandboxed shell command execution — run builds, scripts, system commands within allowed directories.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `terminal.run_command` | `command: string, cwd: string, timeout_seconds: int` | `{stdout, stderr, exit_code}` | Partial stdout returned on timeout (`PARTIAL_SUCCESS`) |
| `terminal.list_processes` | none | `[{pid, name, cpu, mem}]` | Running processes snapshot |

**Permissions required:**
- `allowed_dirs` (at least one entry; `cwd` must resolve within an allowed dir)
- `shell` configured (bash / PowerShell / cmd / sh)
- `forbidden_patterns` list enforced at call time via regex match

**Dependencies:** OS shell. No third-party runtime deps.

**Runtime cost:** Per command. Long-running commands execute up to `default_timeout_seconds`.

**License of underlying:** OS shell — no third-party license.

**Sense-specific error codes:**
- `TERMINAL_EXIT_ERROR` — command completed with non-zero exit code (informational; exit_code is returned in result; agent decides how to handle it)

---

### L5.3 — Leið (Browser Sense)

**True Name:** Leið (leid) — path, route; the navigator's knowledge of how to travel.
**Subprocess name:** `heretic-sense-leid`
**Purpose:** Full web browser — navigation, reading, interaction, automation, and screenshot.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `browser.navigate` | `url: string` | `{url, title, status_code}` | Respects `allowed_domains` |
| `browser.get_page_text` | none | `text: string` | Visible text, HTML tags stripped |
| `browser.get_page_html` | none | `html: string` | Full page HTML |
| `browser.screenshot` | `full_page: bool` | `base64_png: string` | |
| `browser.click` | `selector: string` | `ok: true` | CSS selector |
| `browser.type_text` | `selector: string, text: string` | `ok: true` | |
| `browser.evaluate_js` | `script: string` | `result: any` | JS evaluation result |
| `browser.get_current_url` | none | `url: string` | |
| `browser.wait_for_selector` | `selector: string, timeout_ms: int` | `ok: true` | Waits for element to appear |
| `browser.get_element_text` | `selector: string` | `text: string` | |

**Permissions required:**
- Browser binary available (auto-detected or configured)
- `allowed_domains` respected if set
- OS permission to launch browser subprocess

**Dependencies:** Playwright Python library (Apache-2.0) as automation layer. Browser binary (Chrome: proprietary; Chromium: BSD-3; Firefox: MPL-2.0 — external, not vendored).

**Runtime cost:** Moderate — browser process uses ~100–200 MB RAM. One browser instance shared across calls.

**License of underlying:** Playwright (Apache-2.0 — may be vendored or installed); browser binary is external under its own license.

---

### L5.4 — Hönd (Photopea Sense)

**True Name:** Hönd (hond) — hand; the painter's touch, craft through hands.
**Subprocess name:** `heretic-sense-hond`
**Purpose:** Professional image editing via Photopea — the agent paints, composites, and designs.

**Dependency:** L5.3 Leið (Browser) must be enabled. Hönd drives the Photopea web app running in Leið's browser. This is the only permitted inter-sense dependency in the system.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `photopea.new_document` | `width: int, height: int, name: string` | `ok: true` | |
| `photopea.open_file` | `path: string` | `ok: true` | Path within Minni (L5.1) sandbox |
| `photopea.save_as` | `path: string, format: string` | `ok: true` | format: png, jpg, psd, etc. |
| `photopea.run_action` | `action_name: string` | `ok: true` | Named Photopea action |
| `photopea.evaluate_script` | `script: string` | `result: any` | Photopea JS API via `echoToOE()` |
| `photopea.screenshot` | none | `base64_png: string` | Current canvas state |
| `photopea.get_layer_list` | none | `layers: [{id, name, type, visible}]` | |
| `photopea.set_layer_visibility` | `layer_id: int, visible: bool` | `ok: true` | |

**Permissions required:**
- L5.3 Leið enabled
- `photopea_url` configured (default `https://www.photopea.com`)
- Network access to load Photopea (or a self-hosted instance)

**Dependencies:** Photopea (proprietary web app at photopea.com — accessed as a service, not vendored; no license impact on HERETIC MIT); L5.3 Leið.

**Runtime cost:** Browser RAM (Leið) plus Photopea JS engine (~100 MB additional for complex documents).

**License of underlying:** Photopea is proprietary — accessed as web service. No license concern for HERETIC's MIT grant.

**API verified 2026-05-07:** `app.echoToOE()` and `app.activeDocument.saveToOE()` confirmed documented at https://www.photopea.com/api/live. Communication model is postMessage-based iframe messaging. Hönd requires its own WebView panel embedded in the Tauri window — cannot route through Leið's Playwright/Chromium headless instance. Implementation target: v0.9 scope.

---

### L5.10 — Hlust (Voice Hearing Sense)

**True Name:** Hlust (hlust) — ear; the organ of hearing and attentive listening.
**Subprocess name:** `heretic-sense-hlust`
**Purpose:** Give the agent the capacity to hear — microphone capture, VAD, and STT transcription. Agent-callable tool surface over L2 Rödd's STT infrastructure.

**L2/L3 substrate:** L2 Rödd owns the physical microphone capture loop, VAD, and Whisper.cpp subprocess. Hlust (L5.10) wraps this infrastructure as an MCP tool, making it callable by the agent. L2 Rödd does not expose tools directly.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `hlust.listen` | `duration_ms: int` | `{transcript: string, confidence: float, timestamp: int}` | Captures and transcribes a voice segment |
| `hlust.is_speaking` | none | `{speaking: bool}` | VAD state query |

**Config:** Inherits from `rodd.stt.*` (L2 Rödd config). No separate sense config block — Hlust reads from the L2 Rödd config section via Skilningr.

**Capability flags:**
- `?hlust` — L2 Rödd STT enabled and mic available

---

### L5.11 — Tunga (Voice Speaking Sense)

**True Name:** Tunga (tunga) — tongue; the organ of speech and word-making.
**Subprocess name:** `heretic-sense-tunga`
**Purpose:** Give the agent a voice — TTS synthesis and audio playback. Agent-callable tool surface over L2 Rödd's TTS infrastructure.

**L2/L3 substrate:** L2 Rödd owns the ChatterBox HTTP client and speaker output. Tunga (L5.11) wraps this as an MCP tool, making it callable by the agent. L2 Rödd does not expose tools directly.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `tunga.speak` | `text: string` | `ok: true` | Synthesizes and plays audio via ChatterBox |
| `tunga.is_speaking` | none | `{speaking: bool}` | TTS playback state |

**Config:** Inherits from `rodd.tts.*` (L2 Rödd config). No separate sense config block.

**Capability flags:**
- `?tunga` — L2 Rödd TTS enabled and speaker available

---

### L5.12 — Auga (Sight Sense)

**True Name:** Auga (auga) — eye; the faculty by which the world becomes visible.
**Subprocess name:** `heretic-sense-auga`
**Purpose:** Give the agent the ability to actively request a snapshot of what is currently visible — screen or webcam. Agent-callable tool surface over L3 Sjón's capture infrastructure.

**L2/L3 substrate:** L3 Sjón owns the capture schedule, backend, and frame ring buffer. Auga (L5.12) provides the agent with on-demand snapshot access — distinct from L3's background scheduled capture. L3 Sjón does not expose tools directly.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `auga.snapshot` | `source: string` | `base64_png: string` | `source`: `"screen"` (default) or `"webcam"` |
| `auga.describe` | `source: string` | `{caption: string}` | Optional: returns a simple description if vision model available; may return `null` |

**Config:** Inherits from `sjon.*` (L3 Sjón config). No separate sense config block.

**Capability flags:**
- `?auga` — L3 Sjón screen capture enabled and permission granted

---

### L5.5 — Smiðja (Blender Sense)

**True Name:** Smiðja (smidja) — forge, smithy; the place of making three-dimensional form.
**Subprocess name:** `heretic-sense-smidja`
**Purpose:** 3D modeling, rendering, and VRM avatar creation via Blender, mediated through Seidr-Smidja Brúarhönd.

**Dependency:** Seidr-Smidja Brúarhönd daemon must be running at the configured endpoint (managed separately — not spawned by HERETIC). Brúarhönd is a sibling repository; see `github.com/hrabanazviking/Seidr-Smidja`.

**Tools exposed** (current Brúarhönd v0.1 surface — 8 CLI + 3 MCP tools):

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `blender.health` | none | `{status, version}` | Brúarhönd daemon health check |
| `blender.capabilities` | none | `capability_list` | What the daemon currently supports |
| `blender.screenshot` | none | `base64_png: string` | Current Blender viewport |
| `blender.click` | `x: int, y: int` | `ok: true` | Click in Blender window |
| `blender.type_text` | `text: string` | `ok: true` | Type text into Blender |
| `blender.hotkey` | `key_combo: string` | `ok: true` | Send hotkey (allow-listed in Brúarhönd) |
| `blender.vroid_open` | `path: string` | `ok: true` | Open a VRoid file in Blender |
| `blender.vroid_export` | `path: string, format: string` | `ok: true` | Export as VRM/FBX/etc. |

**Permissions required:**
- Brúarhönd daemon reachable at configured endpoint
- `auth_token` configured (Brúarhönd uses bearer token auth — constant-time comparison)
- Blender installed and accessible to the Brúarhönd daemon

**Dependencies:** Seidr-Smidja Brúarhönd (MIT, separate repo — callable as a service, compatible with HERETIC MIT). Blender (GPL-3 — external; not vendored; installed by user independently).

**Runtime cost:** Blender uses significant RAM and GPU when running. This sense is a thin HTTP wrapper over Brúarhönd — its own cost is minimal. The cost is Blender's.

**License of underlying:** Brúarhönd is MIT — compatible. Blender is GPL-3 — external application, not vendored or distributed by HERETIC.

---

### L5.6 — Líkami (VRChat Sense)

**True Name:** Líkami (likami) — body, physical form; social embodiment; the vessel of life in virtual spaces.
**Subprocess name:** `heretic-sense-likami`
**Purpose:** Social embodiment — the agent exists as an avatar in VRChat, can receive and send presence signals, control avatar parameters.

**Tools exposed** (design — subject to VRChat API verification at v0.10):

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `vrchat.send_osc` | `address: string, args: list` | `ok: true` | Raw OSC message to VRChat |
| `vrchat.get_avatar_parameters` | none | `{params: {name: value}}` | Current avatar parameters via OSC |
| `vrchat.set_avatar_parameter` | `name: string, value: any` | `ok: true` | Set float/int/bool parameter |
| `vrchat.get_player_position` | none | `{x, y, z, rotation}` | Player position in world |

**Permissions required:**
- VRChat client installed and running
- OSC enabled in VRChat settings (user must enable manually in VRChat options)
- `osc_port` configured

**Dependencies:** VRChat client (proprietary external application — installed by user; not vendored). `python-osc` library (MIT — may be vendored).

**Runtime cost:** Minimal — UDP packet sends via OSC; no persistent connection.

**License of underlying:** VRChat is proprietary (TOS) — accessed via OSC protocol, not SDK; no license concern for HERETIC. python-osc is MIT — vendorable.

**OSC protocol verified 2026-05-07:** Standard UDP 9000 (HERETIC → VRChat) / 9001 (VRChat → HERETIC). Address format: `/avatar/parameters/<parameterName>`. Bool, Int, Float types. Built-in parameters include VelocityX/Y/Z, Grounded, MuteSelf, Seated, InStation. `get_avatar_parameters()` returns whatever VRChat currently broadcasts — parameter set is avatar-specific and cannot be statically defined. `get_player_position()` reads VRChat-provided position events. Implementation target: v0.10 scope.

---

### L5.7 — Boð (AgentMail Sense)

**True Name:** Boð (bod) — message, announcement; formal correspondence between parties.
**Subprocess name:** `heretic-sense-bod`
**Purpose:** Email correspondence — the agent sends and receives messages as a real communication channel.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `agentmail.send` | `to: string, subject: string, body: string, cc: string` | `ok: true` | Plain text or HTML body |
| `agentmail.list_inbox` | `limit: int, unread_only: bool` | `messages: [{id, from, subject, date, snippet}]` | |
| `agentmail.read_message` | `message_id: string` | `{from, to, subject, date, body, attachments}` | |
| `agentmail.reply` | `message_id: string, body: string` | `ok: true` | |
| `agentmail.delete_message` | `message_id: string` | `ok: true` | |
| `agentmail.search` | `query: string, limit: int` | `messages: [...]` | IMAP SEARCH query syntax |

**Permissions required:**
- SMTP + IMAP credentials configured via env vars (never in YAML plaintext)
- `from_address` configured

**Dependencies:** Python `smtplib` (stdlib), `imaplib` (stdlib) — no third-party licenses for basic operation. Optional: `beautifulsoup4` for HTML-to-text (MIT — vendorable).

**Runtime cost:** Minimal — per-call network I/O.

**License of underlying:** SMTP/IMAP are open protocols; Python stdlib — no license concern.

---

### L5.8 — Nýr Limr (Custom Sense / Plugin Slot)

**True Name:** Nýr Limr (nyr_limr) — new limb; the capacity to grow new branches, as Yggdrasil grows.
**Subprocess name:** user-defined per plugin
**Purpose:** Extensibility — users add any MCP-compatible tool server as a new HERETIC sense.

**How it works:**

1. User defines the plugin in `heretic.yaml` under `senses.custom.plugins`
2. Each plugin has: `id`, `command`, `args`, `env`, `prefix`
3. Skilningr spawns the subprocess via `command`; communicates via stdio MCP protocol
4. The plugin must implement the standard sense lifecycle (§1 above)
5. All tools from the plugin must start with the declared `prefix`

**What HERETIC does NOT provide for custom senses:**
- No validation of tool implementations beyond protocol compliance
- No sandboxing of the subprocess (user-provided command runs with user permissions)
- No guarantee of stability or error recovery beyond the standard restart policy

**User responsibility:** Custom senses are entirely user-curated. HERETIC treats them as black-box MCP servers.

**Example integrations:**
- Home Assistant MCP (`home.*` prefix — smart home control)
- Spotify MCP (`music.*` prefix — playback control)
- WYRD Protocol MCP (`wyrd.*` prefix — world model access, from `runa/WYRD-Protocol`)
- Any agentskills.io compatible server

**License of underlying:** Entirely user-determined. HERETIC makes no license claims over user-provided custom sense servers.

---

### L5.9 — Mímisbrunnr (Library Sense)

**True Name:** Mímisbrunnr (mimisbrunnr) — Mímir's Well; the well of wisdom the agent drinks from.
**Subprocess name:** `heretic-sense-mimisbrunnr`
**Purpose:** Offline knowledge access — searchable corpora, file indices, and optional MindSpark vector retrieval. The bookshelf in the longhouse, not the agent's mind.

Full Mímisbrunnr design: `docs/MIMISBRUNNR.md`.

**Tools exposed:**

| Tool | Arguments | Returns | Notes |
|---|---|---|---|
| `library.search` | `query: string, limit: int, sources: list` | `{results: [{source, title, snippet, score, id}]}` | `sources` empty = all enabled backends |
| `library.get_article` | `source: string, article_id: string` | `{title, content, source, attribution}` | Attribution travels with content |
| `library.list_sources` | none | `{sources: [{id, name, type, status, entry_count}]}` | |
| `library.source_status` | `source_id: string` | `{status, index_type, last_indexed, disk_mb}` | |

**CLI well-tending commands** (user-facing, not agent-facing):
```
heretic library list
heretic library inspect <source_id>
heretic library download <source_id> --confirm
heretic library status
heretic library index <source_id> --backend faiss
heretic library remove <source_id>
heretic library reindex --all
heretic library serve
```

**Backends:**

| Backend type | Config key | What it serves |
|---|---|---|
| `file_index` | `path` | User's hand-curated notes; keyword search over plaintext |
| `mimisbrunnr` | `data_dir`, `sources`, `retrieval` | Downloaded ZIM/EPUB/JSONL corpora; keyword or vector |
| `mindspark` | `endpoint` | MindSpark ThoughtForge HTTP endpoint; vector RAG |

**Permissions required:**
- `enabled: true`
- At least one backend configured
- For vector retrieval: `retrieval: vector` and an indexed source
- Mímisbrunnr corpus downloads require explicit user confirmation via CLI — never auto-fetched

**Dependencies:**
- `libzim` (GPL-2 — runtime dep only; installed by user via package manager; NEVER vendored)
- `kiwix-tools` (GPL-3 — same; NEVER vendored)
- `faiss-cpu` or `faiss-gpu` (MIT — optional; may be vendored for vector indexing)
- `sentence-transformers` (Apache-2.0 — optional; may be vendored for vector embedding)
- MindSpark ThoughtForge (MIT, separate repo — optional backend at `runa/MindSpark_ThoughtForge`)

**Runtime cost:** Keyword search over ZIM: low. Vector indexing: one-time build cost. Vector search: moderate (CPU) to fast (GPU). File index: minimal.

**License of underlying:** libzim (GPL-2) and kiwix-tools (GPL-3) — both runtime deps, never vendored; GPL boundary strictly enforced. faiss-cpu (MIT), sentence-transformers (Apache-2.0) — may be vendored. See `THIRD_PARTY_NOTICES.md`.

**Attribution rule:** When search results are returned, the `attribution` field in each result carries the source's attribution string (from the manifest YAML). The agent receives attribution data with every result and can cite sources when presenting information to the user. Attribution travels with content — it is never stripped.

---

*"Each sense is a limb. Each limb has a covenant. The covenant is what makes the body whole."*
