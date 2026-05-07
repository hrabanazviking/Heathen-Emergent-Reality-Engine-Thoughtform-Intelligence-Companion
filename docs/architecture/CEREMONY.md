# HERETIC — Ceremony (Lifecycle State Machine)

**Last updated:** 2026-05-07
**Scope:** The five ceremonial phases mapped to True Names; runtime states; instantiation/teardown sequences; error/abort paths; full state diagram; recovery behaviors; timeouts; persistent vs ephemeral state; Holdvörðr responsibilities.
**Authority:** Derives from `docs/BODY_MANIFESTO.md` and `ARCHITECTURE.md`.
**Owner:** Architect (Rúnhild Svartdóttir)
**Legend:** True Names from `docs/NAMING.md` are used throughout. Code constants appear in parentheses.

---

## 1. The Five Phases — Canonical Mapping

The manifesto names five phases of ceremony:

> "1. Light the Candle — Launch the app on your laptop
> 2. Open Bifröst — Tailscale tunnel activates, connecting to the agent runtime
> 3. The Spirit Enters — The agent inhabits H.E.R.E.T.I.C., gains access to all senses and tools
> 4. Communion — Voice, vision, creative tools — deep immersive interaction
> 5. Extinguish — Close the app. The body rests. No RAM eaten. No background drain."

These map onto the True Names and runtime states as follows:

| Manifesto Phase | True Name | Code Constant | What it means |
|---|---|---|---|
| Before launch | Hvíld (hvild) | `STATE_HVILD` | Rest, repose; the fire is banked. All processes stopped; RAM free. |
| Light the Candle (boot + init) | Kynding (kynding) | `STATE_KYNDING` | Kindling; the first flame has caught. Config loads, senses spawn. |
| Open Bifröst (connection bound) | Tengsl (tengsl) | `STATE_TENGSL` | Bonds; the spirit and body are in covenant. Bifröst is open. |
| Communion (active session) | Samræður (samraedur) | `STATE_SAMRAEDUR` | Mutual speech; the ceremony is alive. |
| Extinguish (clean shutdown) | Slokna (slokna) | `STATE_SLOKNA` | The flame goes out. Ceremony well-ended. |

The Holdvörðr (holdvordur) — the runtime process itself — is the warden of this arc. It holds the body open while Tengsl and Samræður persist; it oversees the return to Hvíld.

---

## 2. Full State Diagram

```
                        ┌───────────────────┐
                        │   Hvíld           │ ◄──────────────────────────────┐
                        │   (STATE_HVILD)   │                                │
                        │   Not running     │                                │
                        └─────────┬─────────┘                                │
                                  │ user launches HERETIC                    │
                                  ▼                                          │
                        ┌───────────────────┐                                │
                        │   Kynding         │ ← Phase 1 begins               │
                        │ (STATE_KYNDING)   │                                │
                        │ L0 Grunnr loads   │                                │
                        │ L5 Skilningr      │                                │
                        │ spawns senses     │                                │
                        └─────────┬─────────┘                                │
                config error ◄────┤                                          │
                (CONFIG_ERROR     │ all layers initialized                   │
                 terminal state)  │ (or timeout → senses DEGRADED)           │
                                  ▼                                          │
                        ┌───────────────────┐                                │
                        │   READY           │ ← Phase 1 complete             │
                        │ Summoning Circle  │ (Eldahús lit; fire banked)     │
                        │ visible; Bifröst  │ ◄────────────────┐            │
                        │ not yet open      │                  │ reconnect   │
                        └─────────┬─────────┘  failed         │ failed      │
                                  │ user clicks                │            │
                                  │ "Light the Candle"        │            │
                                  ▼                           │            │
                        ┌───────────────────┐                 │            │
                        │   OPENING         │ ← Phase 2 begins│            │
                        │ L1 Bifröst        │                 │            │
                        │ resolves endpoint │                 │            │
                        │ capability probe  │                 │            │
                        └─────────┬─────────┘                 │            │
              probe failed ◄──────┤                           │            │
              (stays READY)       │ probe succeeded            │            │
                                  ▼                           │            │
                        ┌───────────────────┐                 │            │
                        │   Tengsl          │ ← Phase 3       │            │
                        │ (STATE_TENGSL)    │                 │            │
                        │ Spirit present    │                 │            │
                        │ Bifröst bound     │                 │            │
                        └──┬────────────────┘                 │            │
                           │ first input or turn starts       │            │
                           ▼                                  │            │
                        ┌───────────────────┐                 │            │
                        │   Samræður        │ ← Phase 4       │            │
                        │(STATE_SAMRAEDUR)  │                 │            │
                        │ Active Communion  │                 │            │
                        └──┬────────┬───────┘                 │            │
                           │        │ connection drops         │            │
                           │        ▼                          │            │
                           │  ┌───────────────┐               │            │
                           │  │  RECOVERING   │               │            │
                           │  │ reconnect in  │ ──────────────┘            │
                           │  │ progress      │                             │
                           │  └───────────────┘                             │
                           │                                                 │
                           │ user clicks "Extinguish"                       │
                           ▼                                                 │
                  ┌─────────────────────┐                                   │
                  │   Slokna            │ ← Phase 5 begins                  │
                  │  (STATE_SLOKNA)     │                                   │
                  │  drain tool calls   │                                   │
                  │  close Bifröst      │                                   │
                  │  stop senses        │                                   │
                  └──────────┬──────────┘                                   │
                             │ all clean                                     │
                             ▼                                               │
                  ┌─────────────────────┐                                   │
                  │   EXTINGUISHED      │                                   │
                  │   Session state     │                                   │
                  │   zeroed            │                                   │
                  └──────────┬──────────┘                                   │
                             │ app close OR new ceremony                    │
                             ▼                                               │
                     app window closed ──────────────────────────────────── ┘
                     new ceremony → Kynding (senses already running → skip to READY)
```

---

## 3. Phase Detail

### Phase 1 — Kynding (Light the Candle)

**User experience:** App launches. Norse dark-mode UI (Eldahús) appears. The Summoning Circle renders. Sense status indicators populate as each sense subprocess comes online.

**Runtime states during this phase:** Hvíld → Kynding → READY

**What Holdvörðr instantiates:**
- L0 Grunnr: config loaded, logging started, subprocess supervisor active
- L5 Skilningr: sense subprocesses spawned for all `enabled: true` senses; each performs a self-health check via `tools/list`
- L4 Vébond: React component tree rendered; Summoning Circle shows per-sense healthy/degraded/unavailable

**What is NOT yet instantiated:**
- L1 Bifröst connection (not yet open)
- L2 Rödd STT (Hlust) capture loop (starts when Bifröst opens)
- L3 Sjón capture schedule (starts when Bifröst opens)

**Kynding timeout:** If sense subprocess startup exceeds `foundation.startup_timeout_seconds` (default 30 s), Holdvörðr logs a warning per slow sense but transitions to READY anyway. Senses that miss their startup window are marked DEGRADED in the UI — they may recover when they respond to their health check.

**Config errors:** If `heretic.yaml` is missing or malformed, Holdvörðr transitions to `CONFIG_ERROR` (terminal state for this launch). User sees a clear error message with the config path and validation failure detail. Ceremony does not reach READY.

**Abort path:** User closes app window during Kynding → graceful Hvíld; subprocesses killed cleanly via supervisor.

**Holdvörðr responsibility at this transition:** Load config, spawn sense tree, verify L0 and L4 are live, mark each sense healthy or degraded, expose READY state to L4 Vébond.

---

### Phase 2 — Opening Bifröst (toward Tengsl)

**User experience:** User clicks the "Light the Candle" button in the Summoning Circle. A connecting indicator appears (Eldahús fire beginning to rise). The button becomes a cancel option.

**Runtime states during this phase:** READY → OPENING → (Tengsl or READY on failure)

**What Holdvörðr does in OPENING:**
1. L1 Bifröst resolves agent endpoint via Tailscale or direct routing
2. L1 sends capability probe (see `AGENT_AGNOSTIC_PROTOCOL.md` §5.1)
3. L1 records capability flags
4. If probe succeeds: transition to Tengsl; sense tool schemas injected into future turns
5. If probe fails: transition back to READY; L4 Vébond shows error notification with retry button

**OPENING timeout:** `bifrost.connect_timeout_seconds` (default 15 s). If probe does not complete within this window, Bifröst aborts and transitions back to READY.

**Error states:**
- `BIFROST_UNREACHABLE` — Tailscale not active or endpoint not responding; user sees "Cannot reach agent — is Tailscale running?" notification.
- `BIFROST_AUTH_FAILED` — HTTP 401/403 from probe; user sees "Authentication failed — check your API key" notification. No auto-retry.
- `BIFROST_PROBE_TIMEOUT` — probe timed out; user sees "Agent not responding" notification with a retry button.

**Abort path:** User clicks cancel during OPENING → graceful transition back to READY; no partial state left.

**Holdvörðr responsibility:** Initiate Bifröst connection, execute probe, record capabilities, invoke Tengsl on success.

---

### Phase 3 — Tengsl (The Spirit Enters)

**User experience:** The "connected" indicator glows steadily (Eldahús: fire burning clean). Sense toggles become active. Voice indicator activates if voice is enabled.

**Runtime states:** Transition from OPENING into Tengsl (and immediately into Samræður on first input).

**What Holdvörðr instantiates on entering Tengsl:**
- L2 Rödd STT (Hlust): capture loop starts; VAD listening begins
- L3 Sjón: screen capture schedule starts; first frame captured
- L1 Bifröst: message queue cleared and ready
- L4 Vébond: transitions to INHABITED appearance (glowing accents active, Samræður pulse)

**What is injected into the first agent turn:**
- System prompt (if configured)
- Tool schemas for all enabled senses
- Optional HERETIC context message if `bifrost.inject_context_on_connect: true`:
  ```json
  {"role": "system", "content": "You are now inhabiting H.E.R.E.T.I.C. Your available senses: [list]. Ceremony has begun."}
  ```

**Holdvörðr responsibility:** Verify all enabled senses are healthy; activate Rödd and Sjón; deliver first tool schema list to L1.

---

### Phase 4 — Samræður (Communion)

**User experience:** Deep immersive interaction. The agent hears speech (Hlust), sees the screen (Sjón), calls tools through Skilningr. This is the full operational state.

**Runtime state:** Samræður (sustained)

**What is running:**
- L1 Bifröst: agent turns dispatched on each voice transcript (from Rödd/Hlust) or user text input
- L2 Rödd Hlust: continuous capture + VAD; transcripts queued to L1
- L2 Rödd Tunga: agent text chunks played as they arrive via streaming
- L3 Sjón: frames captured on schedule; injected into turns per `?vision_in` capability flag
- L5 Skilningr: tool calls dispatched and results returned as they arrive
- L4 Vébond: status panel updating in real time (voice waveform, turn indicator, tool call badges)

**Concurrent turn handling:** Holdvörðr processes one agent turn at a time. If a new user transcript arrives while a turn is in progress, it is queued. Queue depth: `bifrost.input_queue_depth` (default 10). If queue overflows, the oldest queued input is discarded — not the current in-flight turn.

**Holdvörðr responsibility:** Sustain the Samræður loop; route tool calls; monitor sense health; surface degradation to L4 Vébond without interrupting turns.

---

### Phase 5 — Slokna (Extinguish)

**User experience:** User clicks "Extinguish". A brief drain indicator shows (Eldahús fire dying down). App returns to READY state (body dormant, senses still loaded) OR the app closes entirely depending on whether the user clicked the button or closed the window.

**Runtime states:** Samræður → Slokna → EXTINGUISHED → READY (or Hvíld if app closes)

**Drain window:** `bifrost.drain_timeout_seconds` (default 10 s). In-flight tool calls are allowed to complete within this window. In-flight agent turns are allowed to complete one final round. After the window, any remaining calls are abandoned cleanly.

**Holdvörðr teardown sequence:**
1. L1 Bifröst stops accepting new user inputs from L2 Rödd
2. L1 waits for in-flight turn / tool calls (drain window)
3. L1 sends optional graceful close to agent (final `HERETIC_CEREMONY_END` system message)
4. L1 closes HTTP connection
5. L2 Rödd: STT (Hlust) capture stops; TTS (Tunga) queue flushed (plays any queued speech before stopping)
6. L3 Sjón: capture schedule stops; frame buffer cleared
7. L5 Skilningr: all senses receive shutdown signal; subprocesses terminate cleanly (or are killed after `shutdown_grace_seconds`)
8. Session state zeroed in memory (message array, frame buffer, tool routing table, capability flags)
9. L4 Vébond: returns to READY appearance (Eldahús: fire banked — Hvíld approached)

**If app window is closed (not just Extinguish button):** Same teardown, then L5 Skilningr subprocess tree is also killed, reaching Hvíld.

**Holdvörðr responsibility:** Execute teardown in order; guarantee no dangling subprocesses; zero session state; confirm EXTINGUISHED.

---

## 4. Recovery Behaviors

### 4.1 Agent disconnects mid-Samræður

```
Samræður → RECOVERING → (Samræður restored or READY)
```

1. L1 Bifröst detects disconnect (missed heartbeat or HTTP error during turn)
2. Bifröst transitions to RECOVERING; L4 Vébond shows "Reconnecting..." indicator (fire flickering)
3. Bifröst attempts reconnect with exponential backoff (`bifrost.max_retries` and `backoff_seconds`)
4. During recovery: Rödd (Hlust) continues capturing voice (queued, not dispatched); Sjón continues capturing (buffered)
5. On successful reconnect: capability re-probe; recovery message injected; transitions to Samræður restored
6. On exhausted retries: transitions to READY; L4 shows "Connection lost — click to retry"; queued voice inputs discarded

### 4.2 Tailscale drops mid-Samræður

Same as agent disconnect above. If `tailscale.fallback_to_direct: true`, Bifröst also attempts the endpoint URL directly before declaring connection failed.

### 4.3 Sense subprocess crashes

```
(Samræður, sense running) → (Samræður, sense degraded)
```

1. L5 Skilningr detects subprocess exit (non-zero exit code or supervisor notification)
2. Skilningr removes the dead sense's tools from the active tool registry
3. Skilningr emits `sense_hub::sense_degraded(sense_id)` → L4 Vébond shows degraded indicator
4. Skilningr injects tool schemas update to L1: next agent turn will not include that sense's tools
5. Skilningr optionally injects system message to agent: `"The <sense_name> sense is temporarily unavailable."`
6. Skilningr attempts subprocess restart per `restart_policy`
7. On successful restart: sense re-added to registry; tool schemas updated; L4 shows healthy indicator
8. On max restart failures: sense marked UNAVAILABLE for this ceremony; user notified; other senses unaffected

### 4.4 Mic/speaker device disappears

1. L2 Rödd detects OS audio error
2. Rödd emits `voice::error(DEVICE_UNAVAILABLE)`
3. Affected half (Hlust / STT or Tunga / TTS) is suspended; other half continues
4. L4 Vébond shows degraded voice indicator
5. Rödd polls for device return every 5 seconds; re-enables on device restore
6. No ceremony abort — voice is degraded, not fatal

### 4.5 Screen capture permission revoked mid-ceremony

1. L3 Sjón detects OS permission denial on next capture attempt
2. Sjón emits `vision::error(PERMISSION_DENIED)`
3. Sjón suspends capture schedule
4. L4 Vébond shows vision unavailable indicator
5. L1 Bifröst stops injecting frames (capability flag `?vision_screen` becomes false for remainder of ceremony)
6. Ceremony continues without vision

---

## 5. Timeouts and Retries Reference

| Timeout | Config key | Default | Behavior on expiry |
|---|---|---|---|
| Startup timeout (Kynding) | `foundation.startup_timeout_seconds` | 30 s | Slow senses marked DEGRADED; proceed to READY |
| Connect timeout (probe, OPENING) | `bifrost.connect_timeout_seconds` | 15 s | Transition back to READY; show error |
| Agent response timeout | `bifrost.timeout_seconds` | 30 s | Emit `BIFROST_TIMEOUT`; retry per policy |
| Stream completion timeout | `bifrost.stream_timeout_seconds` | 120 s | Kill stream; treat as timeout |
| Drain window (Slokna) | `bifrost.drain_timeout_seconds` | 10 s | Abandon remaining calls cleanly |
| Heartbeat interval | `bifrost.heartbeat_interval_seconds` | 30 s | Send keepalive probe |
| Heartbeat miss threshold | `bifrost.heartbeat_miss_threshold` | 3 | Transition to RECOVERING after N misses |
| Sense subprocess grace period (Slokna) | `senses.<id>.shutdown_grace_seconds` | 5 s | Kill subprocess after grace |
| Tool call timeout (per-sense) | per-sense config in `SENSE_CONTRACTS.md` | 30 s | Return `SENSE_TIMEOUT` to agent |
| Health check interval (per-sense) | `senses.<id>.health_interval_seconds` | 15 s | Consecutive failures → DEGRADED → restart |

**Retry policy for Bifröst (Tengsl recovery):**
```yaml
bifrost:
  max_retries: 3
  backoff_seconds: [2, 5, 15]    # wait before retry 1, 2, 3
```

---

## 6. Persistent vs Ephemeral State

### Persistent (survives across ceremonies and app restarts)

| State | Location | Owner | Notes |
|---|---|---|---|
| `heretic.yaml` configuration | OS config dir (never hardcoded path) | L0 Grunnr | Config survives; is never auto-written by HERETIC |
| Mímisbrunnr library indices | `~/.heretic/library/` (configurable) | L5.9 Mímisbrunnr | Persist between ceremonies; rebuilt only on explicit re-index |
| Downloaded library corpora | `~/.heretic/library/mimisbrunnr/` | L5.9 Mímisbrunnr | Explicit user download only |
| Plunder / vendor code | `vendor/` in repo | Build | Static; version-controlled |

### Session-only (exists for one ceremony; zeroed on EXTINGUISHED / Slokna complete)

| State | Location | Owner |
|---|---|---|
| Agent message array | L1 Bifröst in-memory | L1 Bifröst |
| Voice transcript queue | L2 Rödd in-memory | L2 Rödd |
| Vision frame ring buffer | L3 Sjón in-memory | L3 Sjón |
| Active tool call map | L5 Skilningr in-memory | L5 Skilningr |
| Capability flags for current agent | L1 Bifröst in-memory | L1 Bifröst |
| UI ceremony state | L4 Vébond React state | L4 Vébond |
| Tailscale connection state | L1 Bifröst in-memory | L1 Bifröst |

### Explicitly never stored by HERETIC

- Agent conversation history (the spirit brings its mind; it keeps its own history)
- User audio recordings (Rödd's capture buffer is a ring; not persisted)
- Screen capture images (Sjón's ring buffer; not persisted unless user explicitly enables `vision.save_frames: true`)

**Open question:** Should HERETIC offer an optional `session.save_transcript: true` config that appends STT transcripts to a local log file? This would aid post-ceremony review without constituting agent memory. Deferred to v1.x design review — requires explicit user opt-in; the manifesto does not address it.

---

## 7. State Machine — Formal Summary

| State | Entry condition | Active components | Exit transitions |
|---|---|---|---|
| `Hvíld` | App not running | None | Launch app → Kynding |
| `Kynding` | App launched | L0 Grunnr starting, L5 Skilningr spawning | All layers init → READY; config error → CONFIG_ERROR |
| `READY` | All layers initialized | L0 Grunnr, L4 Vébond, L5 Skilningr (senses idle) | Click "Light the Candle" → OPENING; close app → Hvíld |
| `OPENING` | User clicked connect | L0, L4, L5, L1 Bifröst probing | Probe succeeds → Tengsl; probe fails → READY; cancel → READY |
| `Tengsl` | Probe succeeded | All layers active | First input/turn → Samræður; connection drop → RECOVERING |
| `Samræður` | Spirit active, turns flowing | All layers at full operation | Click Extinguish → Slokna; connection drop → RECOVERING |
| `RECOVERING` | Connection dropped during Samræður | L0, L4, L5 (active), L1 (reconnecting), L2/L3 (buffering) | Reconnect succeeds → Samræður; retries exhausted → READY |
| `Slokna` | Extinguish triggered | L0, L4, L1 (draining), L5 (shutting down) | Drain complete → EXTINGUISHED |
| `EXTINGUISHED` | Drain complete, session zeroed | L0, L4 (returning to READY UI) | New ceremony → Kynding; close app → Hvíld |
| `CONFIG_ERROR` | Config parse failed at Kynding | None | User fixes config; re-launch → Kynding |
