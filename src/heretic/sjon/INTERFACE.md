# Sjón Module Interface

**Last updated:** 2026-05-08 (v0.5.2 pre-stage — Rúnhild Svartdóttir: added §Webcam capture, extended §Public API, §Config Keys, §Optional Dependencies, §Error Model, §Privacy Invariant for webcam) | 2026-05-08 (v0.5.1 pre-stage — Rúnhild Svartdóttir: added §Continuous mode, extended Config Keys with new fields, extended Public API table) | 2026-05-08 (v0.5 scaffold — Rúnhild Svartdóttir)
**Scope:** L3 Sjón — the vision layer Python module (`src/heretic/sjon/`)
**Owner:** Architect (Rúnhild Svartdóttir)
**Derives from:** `docs/architecture/LAYER_INTERFACES.md §L3 Sjón`
**Legend:** Owns = authoritative data owner; Never-controls = hard boundary.
**SLO tier:** Cold — frames captured on demand per turn; < 30 s p95. Frame injection is not latency-critical.

---

## What Sjón Owns

- `SjonConfig`, `SjonScreenConfig`, `SjonWebcamConfig` — the canonical typed config structs.
  These are the authoritative definitions; `heretic.grunnr.config.HereticConfig.sjon` imports
  from here (Approach B — mirror of the rodd.config_model and vebond.config_model pattern).
- `ScreenCaptureBackend` ABC and all concrete backends: `MssBackend`, `NullBackend`.
- `FrameEncoder` — BGRA to resize to PNG to base64 data URL pipeline.
- `Sjón` orchestrator — throttle guard, on-demand snapshot delivery, async lifecycle.
- The Sjón error hierarchy: `SjonError` and all subclasses.
- The `best_available()` factory function for backend selection.
- Privacy invariant enforcement: `save_frames` defaults to False; a warning is emitted
  at config construction time when operators explicitly set it True.

Webcam support is scaffolded in v0.5.2:
- `SjonWebcamConfig` fields are fully activated (was a stub in v0.5).
- `WebcamCaptureBackend` ABC, `OpenCvBackend` skeleton, `WebcamNullBackend`, and
  `best_available()` webcam factory live in `webcam.py`.
- `Sjón.snapshot_webcam()` stub declared; raises NotImplementedError until Forge Wave 2.
- Full implementation (cv2.VideoCapture, JPEG/PNG encode, data URL return) is Forge Wave 2.

---

## What Sjón Exposes (Public API)

All of the following are re-exported from `heretic.sjon` directly.

| Export | Module | Purpose |
|---|---|---|
| `SjonConfig` | `sjon.config_model` | Root config: screen + webcam sub-configs. |
| `SjonScreenConfig` | `sjon.config_model` | Screen capture settings. Canonical definition. |
| `SjonWebcamConfig` | `sjon.config_model` | Webcam settings. Fields activated in v0.5.2 (was stub in v0.5). |
| `ScreenCaptureBackend` | `sjon.capture` | ABC for all screen capture backends. |
| `MssBackend` | `sjon.capture` | mss-based cross-platform backend (mss in [vision] extra). |
| `NullBackend` | `sjon.capture` | Always-unavailable silent stub. Final fallback in screen factory. |
| `best_available` | `sjon.capture` | Module-level factory: selects the best screen backend for the current machine. |
| `WebcamCaptureBackend` | `sjon.webcam` | ABC for all webcam capture backends (v0.5.2). |
| `OpenCvBackend` | `sjon.webcam` | cv2.VideoCapture-based backend skeleton (v0.5.2; Forge Wave 2 implements). |
| `WebcamNullBackend` | `sjon.webcam` | Always-unavailable webcam stub. Final fallback in webcam factory. |
| `best_available` (webcam) | `sjon.webcam` | Module-level factory: selects the best webcam backend. |
| `Sjón.snapshot_webcam` | `sjon.sjon` | Async on-demand webcam capture stub (v0.5.2; NotImplementedError until Forge Wave 2). |
| `FrameEncoder` | `sjon.encoder` | Encodes raw BGRA bytes to inline base64 PNG data URL. |
| `Sjón` | `sjon.sjon` | Async orchestrator: snapshot(), throttle, lifecycle. True Name spelling. |
| `Sjon` | `sjon.__init__` | ASCII alias for `Sjón` (identical class). |
| `Sjón.start_continuous_capture` | `sjon.sjon` | Start the background periodic capture task (v0.5.1; NotImplementedError until Forge Wave 2). |
| `Sjón.stop_continuous_capture` | `sjon.sjon` | Stop the background task cleanly and emit CONTINUOUS_STOPPED (v0.5.1; NotImplementedError until Forge Wave 2). |
| `Sjón.recent_frames` | `sjon.sjon` | Return last N data URLs from ring buffer; n=None = all (v0.5.1; NotImplementedError until Forge Wave 2). |
| `MssBackend.list_monitors` | `sjon.capture` | Return mss monitor list; index 0 = composite, 1+ = individual (v0.5.1; NotImplementedError until Forge Wave 2). |
| `SjonError` | `sjon.errors` | Root error; catch this to handle any Sjón failure. |
| `ScreenCaptureError` | `sjon.errors` | Capture operation failure (backend available, capture failed). |
| `PermissionDeniedError` | `sjon.errors` | OS denied screen capture permission. |
| `BackendUnavailableError` | `sjon.errors` | No screen capture backend available on this machine. |
| `FrameEncodingError` | `sjon.errors` | Pillow encoding failure (import, resize, PNG, base64). |
| `ThrottleRejectedError` | `sjon.errors` | Snapshot rejected within min_interval_ms window. |
| `WebcamCaptureError` | `sjon.errors` | Webcam capture operation failure (v0.5.2). |
| `WebcamBackendUnavailableError` | `sjon.errors` | No webcam backend / cv2 absent / device missing (v0.5.2). |

---

## What Sjón Must Never Control

- Frame interpretation — what the agent does with images is L1 Bifröst's decision.
- Conversation content, system prompts, or message history — L1 Bifröst's domain.
- When frames are injected into agent messages — the turn loop (CLI / Bifröst client) decides.
  Sjón only captures and encodes; it does not push frames into the message array.
- MCP tool calls or tool routing — L5 Skilningr.
- UI rendering or status event display — L4 Vébond. Sjón emits `SjonActivity` events
  via EventBus; Vébond consumes them. Sjón does not write to the WebSocket directly.
- Config file loading — Sjón receives a typed `SjonConfig`; it never reads heretic.yaml directly.
- Persistent frame storage — `save_frames: false` is the immutable default.
  **NEVER write frames to permanent disk locations. Opt-in ephemeral writes only.**

---

## Inputs

| Input | Source | Notes |
|---|---|---|
| `SjonConfig` | L0 Grunnr `load_config()` | Resolved and typed at Kynding; passed to `Sjón.__init__()`. |
| `snapshot()` call | L1 Bifröst / CLI turn loop | Called before user message is sent, when `?vision_screen` AND `?vision_in` are both True. |

---

## Outputs

| Output | Consumer | Condition |
|---|---|---|
| `list[str]` (data URL list) from `snapshot()` | L1 Bifröst / CLI turn loop | One data URL per captured frame. Empty list on throttle, unavailability, or error. |
| `SjonActivity` events (via EventBus) | L4 Vébond — `sjon.activity` wire event | Emitted at capturing / encoding / idle / failed milestones. |

---

## Capability Flags

Two distinct namespaces; see `docs/architecture/LAYER_INTERFACES.md §L3 Capability flags` for the full resolution.

| Flag | Set by | Meaning |
|---|---|---|
| `?vision_screen` | HERETIC body state (L3 Sjón) | `sjon.screen.enabled AND MssBackend.available()`. Answers: "Can the body see?" Delivered to agent in senses-manifest at Tengsl. |
| `?vision_in` | Agent-protocol capability probe | Agent accepts `image_url` content blocks. Answers: "Does the spirit accept images?" Governed by `AGENT_AGNOSTIC_PROTOCOL.md §5`. |

Frames are injected into agent turns ONLY when BOTH flags are True.

---

## Error Model

All errors are subclasses of `SjonError`. The turn loop must catch `SjonError` and
degrade gracefully — ceremony must continue without a frame rather than crashing.

| Error | Condition | Recovery |
|---|---|---|
| `PermissionDeniedError` | OS denied screen capture | Disable Sjón; set `?vision_screen = False`; continue without frames; do not retry until ceremony restarts. |
| `ScreenCaptureError` | Capture failed (backend live, capture failed) | Log warning; skip frame for this turn; retry on next snapshot() call. |
| `BackendUnavailableError` | No backend available | Log warning; return []; set `?vision_screen = False`. |
| `FrameEncodingError` | Pillow encoding failed | Log warning; discard raw bytes; skip frame for this turn. |
| `ThrottleRejectedError` | Within min_interval_ms window | Expected; not logged as warning; return [] silently. |
| `WebcamCaptureError` | Webcam capture failed (v0.5.2) | Log warning; skip webcam frame for this turn; retry on next snapshot_webcam() call. Ceremony continues with screen-only frames. |
| `WebcamBackendUnavailableError` | cv2 absent or device missing (v0.5.2) | Log warning; return []; webcam capture disabled for ceremony. Install cv2 and/or connect device and restart. |

`Sjón.snapshot()` NEVER raises — all errors are caught internally and [] is returned.
`Sjón.snapshot_webcam()` will follow the same contract once Forge Wave 2 implements it.

---

## Config Keys

Canonical reference: `docs/architecture/LAYER_INTERFACES.md §L3 Sjón config keys`.

```yaml
sjon:
  screen:
    enabled: true             # bool; True = screen capture active
    interval_ms: 5000         # int >= 0; ms between periodic captures (activates in v0.5.1)
    max_width: 1280           # int >= 1; max output width in pixels
    max_height: 720           # int >= 1; max output height in pixels
    crop: null                # null | {x, y, w, h}; sub-region capture
    buffer_depth: 5           # int >= 1; ring buffer depth (activates in v0.5.1)
    save_frames: false        # bool; NEVER True by default; warning logged when True
    monitor_index: 0          # int >= 0; 0 mapping depends on continuous mode (see §Continuous mode)
    min_interval_ms: 1000     # int >= 0; throttle: minimum ms between captures
    continuous: false         # bool; v0.5.1+; opt-in periodic background capture
    attach_policy: latest     # str; v0.5.1+; "latest" | "all_buffered" | "none"
  # v0.5.2 — all webcam fields activated (was stub in v0.5)
  webcam:
    enabled: false            # bool; false = inactive (default); explicit opt-in required
    device_index: 0           # int >= 0; 0 = first camera; increase for additional devices
    max_width: 1280           # int >= 1; max output width (proportional scale-down)
    max_height: 720           # int >= 1; max output height (proportional scale-down)
    format: jpeg              # "jpeg" | "png"; jpeg = smaller payload; png = lossless
    jpeg_quality: 85          # int 1-100; JPEG quality; ignored when format: png
    attach_policy: screen_only  # "screen_only" | "webcam_only" | "alongside" | "alternate"
```

---

## Privacy Invariant

**Sealed by audit `docs/audit/AUDIT_v0.0_INITIAL_DOC_SET.md` C-Q-C3 (RESOLVED).**

**Screen capture (v0.5):**

1. Captured frames are NEVER auto-saved to permanent disk locations.
2. `save_frames` defaults to False and a WARNING is logged at config construction time
   when it is explicitly set True.
3. Even when `save_frames` is True, frames are written ONLY to an ephemeral
   session-scoped temp directory — never to the project workspace or user home.
4. Frames are transmitted inline as base64 PNG `image_url` content in the agent
   message. They are not stored server-side, cached between turns, or written to
   the Bifröst connection log.
5. This invariant is non-negotiable. Any Forge implementation that violates it
   must be corrected by the Auditor before v0.5 ships.

**Webcam capture (v0.5.2 — stronger gate):**

6. `sjon.webcam.enabled` defaults to False. Webcam captures the user's physical presence.
   Operators must explicitly opt in. A WARNING is logged at config construction time
   when `enabled` is True (matching the `save_frames` pattern).
7. Webcam frames are NEVER written to disk in v0.5.2. No ring buffer, no continuous mode.
   On-demand only: one frame per `snapshot_webcam()` call, held in memory, transmitted
   inline as a base64 data URL, then released.
8. The Auditor must verify this invariant during the v0.5.2 audit: check that
   `snapshot_webcam()` contains no file-write calls and that `enabled: false` is the
   tested default.

---

## Frame Format

**Sealed by audit C-Q-C3.** All frames are delivered as inline base64 PNG:

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/png;base64,<encoded_png>"
  }
}
```

Injected into the `content` array of a `user`-role message. This is standard
OpenAI vision format. Inline base64 avoids any file-server dependency and keeps
frames within the Tailscale trust boundary. Maximum frame size at 1280x720 PNG:
approximately 1.2 MB — within the `max_tokens: 127000` budget as image content.

PNG compression level: 6 (good compression ratio, fast encode — Forge sets this
in `FrameEncoder.encode()` via `img.save(..., compress_level=6)`).

---

## Optional Dependencies

| Package | Extra | Version | Purpose |
|---|---|---|---|
| `mss` | `[vision]` | `>=9` | Cross-platform screen capture (Windows GDI / macOS Quartz / Linux X11) |
| `Pillow` | `[vision]` | `>=10` | Image manipulation: BGRA→RGB conversion, proportional resize, PNG encoding |
| `opencv-python` | `[vision]` | `>=4.8` | Webcam capture via cv2.VideoCapture (v0.5.2). Apache 2.0. ~70 MB wheel. |

`pip install heretic` (no extras) works on headless machines without either dep.
`pip install heretic[vision]` activates all three. The `[vision]` extra is deliberately
separate from `[voice]` — operators may need TTS on a display-less server (voice
without vision) or screen+webcam capture without audio (vision without voice).
opencv-python is the heaviest dep in the vision extra; operators without a webcam
still get MssBackend and FrameEncoder without cost, but the wheel is present in the env.

---

---

## Continuous Mode (v0.5.1)

Continuous mode activates when `sjon.screen.continuous: true` in `heretic.yaml`.
It is opt-in; the default (`false`) preserves the v0.5 on-demand behaviour exactly.

### Continuous task lifecycle

At TENGSL, the CLI wires `Sjón.start_continuous_capture()`, which launches a
background `asyncio.Task`. That task loops indefinitely at `interval_ms`-millisecond
intervals, calling `snapshot()` internally and appending returned data URLs to the
ring buffer. At SLOKNA, the CLI calls `Sjón.stop_continuous_capture()`, which
cancels the task, awaits its completion, and then `close()` clears the buffer.

State transitions emitted on the `sjon.activity` IPC wire event:

| Transition | State emitted |
|---|---|
| Task launches successfully | `continuous_running` |
| Task stops cleanly | `continuous_stopped` |
| Buffer reaches `buffer_depth` capacity | `buffer_full` (at most once per fill cycle) |
| Capture or encode failure within loop | `failed` (loop continues; next tick retries) |

### Ring buffer semantics

`self._buffer` is a `collections.deque(maxlen=buffer_depth)`. Appends are O(1).
When the buffer is full, the oldest entry is evicted automatically. The buffer lives
entirely in memory — frames are never written to disk (privacy invariant). On
`Sjón.close()`, `self._buffer.clear()` is called unconditionally, even if continuous
mode was never active.

`Sjón.recent_frames(n)` returns the last N data URL strings, oldest-to-newest.
`n=None` returns all buffered frames. Returns `[]` if the buffer is empty.

### Attach policy

When a user message is sent and `continuous=True`, the turn loop reads the buffer
via `recent_frames()` and applies `attach_policy`:

| Policy | Frames attached |
|---|---|
| `"latest"` (default) | The single most-recently captured frame. Mirrors v0.5 behaviour. |
| `"all_buffered"` | All frames in the buffer at send time (up to `buffer_depth`). Higher token cost. |
| `"none"` | No frames attached; continuous capture runs but nothing is injected. |

### Multi-monitor index mapping asymmetry

`monitor_index` selects which screen to capture, but the mss index mapping differs
between modes:

| Mode | `monitor_index = 0` | `monitor_index >= 1` |
|---|---|---|
| On-demand (`continuous=False`) | Maps to mss index 1 — the primary single monitor | Direct mapping (config N → mss N) |
| Continuous (`continuous=True`) | Maps to mss index 0 — the virtual all-monitors composite | Direct mapping (config N → mss N) |

This asymmetry exists because continuous background capture is the natural place to
watch the full desktop composite (the agent sees everything), while on-demand per-turn
capture defaults to the focused primary screen. Forge enforces the correct mapping
inside `MssBackend.capture()` by reading `config.continuous`.

`MssBackend.list_monitors()` (v0.5.1) returns the raw `mss.monitors` list (index 0 =
composite, 1+ = physical screens) so operators and future config tools can inspect
available monitor geometry before committing to a `monitor_index`.

---

---

## Webcam Capture (v0.5.2)

Webcam support activates when `sjon.webcam.enabled: true` in `heretic.yaml`.
The default is `false` — this is a stronger consent gate than screen capture, because
webcam frames contain the user's physical presence (face, body, environment).

### Privacy stance

This is the strongest privacy boundary in L3 Sjón:

1. `enabled: false` by default. Operators must explicitly opt in. A WARNING is logged at
   startup when `enabled: true` to ensure the choice is visible in the log stream.
2. No disk writes in v0.5.2 (on-demand only; no ring buffer, no continuous mode).
3. Physical-presence frames are transmitted inline as base64 data URLs in agent messages
   and are never stored server-side, cached between turns, or written to any file.
4. v0.5.2 is on-demand only — `snapshot_webcam()` mirrors `snapshot()`: one frame per call,
   no background task, no periodic capture. Continuous webcam is v0.5.x backlog.

### Backend chain

```
cv2 importable AND device available? → OpenCvBackend
otherwise                            → WebcamNullBackend (graceful degradation)
```

`WebcamNullBackend.available()` always returns False; `WebcamNullBackend.capture()` raises
`WebcamBackendUnavailableError`. Code must check `available()` before calling `capture()`.

### attach_policy paths

| Policy | Screen frame | Webcam frame | Use case |
|---|---|---|---|
| `screen_only` (default) | Attached if screen enabled | Never attached | Backward compat with v0.5 |
| `webcam_only` | Suppressed | Attached | Identity / presence focus |
| `alongside` | Attached | Attached | Maximum agent context; higher token cost |
| `alternate` | Odd turns | Even turns | Temporal variety; moderate token cost |

The turn loop (CLI / Bifröst client) applies the attach_policy by calling both
`snapshot()` (screen) and `snapshot_webcam()` (webcam) and combining the lists.
Neither method is aware of the other — combination is the caller's responsibility.

### Data URL format

When `format: jpeg`:
```
"data:image/jpeg;base64,<encoded_jpeg>"
```

When `format: png`:
```
"data:image/png;base64,<encoded_png>"
```

Both are injected into the `content` array of a `user`-role message as `image_url`
content blocks, identical in structure to screen frames. The agent cannot distinguish
screen frames from webcam frames by URL format alone — context comes from the turn
prompt, not the frame metadata.

### OpenCvBackend lifecycle

```
backend = OpenCvBackend(config, logger)
if not backend.available():
    # degrade gracefully
    ...
backend.open()                           # cv2.VideoCapture(device_index)
raw_bgr, w, h = backend.capture(idx)    # cap.read() -> (retval, frame)
backend.close()                          # cap.release()
```

`open()` and `capture()` are synchronous. `snapshot_webcam()` runs them in a thread
pool executor to avoid blocking the asyncio event loop (matching the `snapshot()` pattern).

### v0.5.2 scope

**In scope (v0.5.2 scaffold — this file):**
- `SjonWebcamConfig` fields fully activated.
- `WebcamCaptureBackend` ABC.
- `OpenCvBackend` skeleton (NotImplementedError stubs; Forge Wave 2 implements).
- `WebcamNullBackend` (fully functional fallback).
- `best_available()` webcam factory (falls through to NullBackend until Wave 2).
- `Sjón.snapshot_webcam()` stub.
- `WebcamCaptureError`, `WebcamBackendUnavailableError` error types.

**Deferred (Forge Wave 2):**
- `OpenCvBackend.available()`, `.open()`, `.capture()`, `.close()` implementation.
- `Sjón.snapshot_webcam()` full implementation (cv2 capture + JPEG/PNG encode + data URL).
- CLI attach_policy dispatch combining screen + webcam lists.
- Frontend Sjón row webcam active badge.
- Full test coverage (20+ new tests targeting 711+ Python total).

---

## v0.5 Scope Boundaries

**In scope (v0.5):**
- On-demand snapshot: one frame per user-message-send turn
- `MssBackend` full implementation
- `FrameEncoder` full implementation (BGRA resize PNG base64)
- `Sjón` orchestrator with throttle and graceful degradation
- `SjonActivity` events emitted at capture milestones

**Deferred (v0.5.2 Forge Wave 2):**
- `OpenCvBackend` full implementation (available, open, capture, close).
- `Sjón.snapshot_webcam()` full implementation.
- CLI attach_policy dispatch (combine screen + webcam per policy).
- Frontend Sjón row webcam active badge.

**Deferred (v0.5.x backlog):**
- Periodic interval capture (interval_ms activates)
- Ring buffer recall (buffer_depth activates)
- Multi-monitor enumeration beyond monitor_index selection
- Continuous webcam capture + ring buffer (mirrors v0.5.1 for screen)
- Multi-camera support (device_index > 0 combinations)
- Privacy modes (blur/mask configurable regions before send — v0.5.3)

**Deferred (v0.7+):**
- `auga.snapshot` MCP tool (L5 Skilningr — agent-on-demand capture)
