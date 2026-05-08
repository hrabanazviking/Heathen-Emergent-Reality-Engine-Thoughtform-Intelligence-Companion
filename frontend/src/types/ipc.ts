/**
 * HERETIC IPC Protocol — TypeScript type definitions
 *
 * This file is the TypeScript mirror of src/heretic/vebond/protocol.py (Python).
 * Both sides use discriminated unions on a `type` string literal field.
 * The `type` field values are identical between Python and TypeScript.
 *
 * Canonical schema authority: docs/architecture/IPC_PROTOCOL.md
 * Any change to the protocol MUST be reflected in all three:
 *   1. docs/architecture/IPC_PROTOCOL.md  (schema reference)
 *   2. src/heretic/vebond/protocol.py     (Python / pydantic)
 *   3. frontend/src/types/ipc.ts          (TypeScript — this file)
 *
 * Direction conventions:
 *   ProtocolEvent   — server -> client (backend pushes state)
 *   ProtocolCommand — client -> server (frontend sends user actions)
 */

// ==============================================================================
// Shared value types
// ==============================================================================

/** All ceremony lifecycle states the UI must be able to display. */
export type LifecycleState =
  | "hvild"        // Hvild — rest; process not running or in rest
  | "kynding"      // Kynding — kindling; startup and READY/OPENING sub-states
  | "tengsl"       // Tengsl — bonds; Bifrost open, spirit present
  | "samraedur"    // Samraedur — communion; active turns
  | "slokna"       // Slokna — extinguish; drain and shutdown
  | "recovering"   // RECOVERING — reconnecting mid-Samraedur
  | "config_error"; // CONFIG_ERROR — heretic.yaml invalid; terminal state

export type BifrostStatus = "open" | "closed" | "opening" | "failed";
export type TungaState = "idle" | "synthesizing" | "speaking" | "failed";
export type HlustState = "idle" | "loading" | "listening" | "transcribing" | "failed";
export type SjonState = "idle" | "capturing" | "encoding" | "failed";
export type ErrorLevel = "warn" | "error";

/** WebSocket connection state (client-managed; not a server-pushed event type). */
export type WsConnectionStatus = "disconnected" | "connecting" | "connected" | "error";

// ==============================================================================
// Server -> Client Events
// ==============================================================================

/**
 * Emitted when the ceremony lifecycle state transitions.
 * Frontend: update Summoning Circle visual, enable/disable controls.
 */
export interface CeremonyStateChanged {
  type: "ceremony.state_changed";
  from_state: LifecycleState;
  to_state: LifecycleState;
  /** ISO 8601 UTC timestamp: e.g. "2026-05-07T14:32:00.000Z" */
  timestamp: string;
}

/**
 * Emitted when L1 Bifrost connection state changes.
 * Frontend: update connection indicator and layer-status panel entry.
 */
export interface BifrostHealth {
  type: "bifrost.health";
  status: BifrostStatus;
  /** Agent endpoint URL — never includes auth tokens. */
  endpoint: string;
  /** Round-trip latency of last capability probe in milliseconds. null if unavailable. */
  latency_ms: number | null;
}

/**
 * Emitted when Tunga (TTS / voice-out) state changes.
 * Frontend: animate the Mal-green voice-out indicator.
 */
export interface TungaActivity {
  type: "tunga.activity";
  state: TungaState;
}

/**
 * Emitted when Hlust (STT / voice-in) state changes.
 * Frontend: animate the Mal-green voice-in indicator; drive waveform visualisation.
 */
export interface HlustActivity {
  type: "hlust.activity";
  state: HlustState;
  /**
   * Current microphone input level in dBFS. null when not capturing.
   * Range: -infinity to 0.0 dBFS (0.0 = max signal).
   */
  level_db: number | null;
}

/**
 * Emitted for each streaming text token received from the agent.
 * Frontend: append text_delta to the current assistant message.
 */
export interface AgentToken {
  type: "agent.token";
  role: "assistant";
  /** Text fragment for this streaming chunk. May be a single character or multiple words. */
  text_delta: string;
  /**
   * Monotonically increasing integer per turn (starts at 0).
   * Allows the frontend to detect out-of-order or dropped token events.
   */
  sequence_id: number;
}

/**
 * Emitted when the agent finishes generating a response for one turn.
 * Frontend: finalize the current message, enable ChatInput, stop streaming cursor.
 */
export interface AgentTurnComplete {
  type: "agent.turn_complete";
  /** Unique turn identifier. Same value used in AgentToken events for this turn. */
  turn_id: string;
  /**
   * Why the turn ended:
   *   "stop"       — natural end of generation
   *   "length"     — max_tokens reached
   *   "tool_calls" — agent issued tool calls (handled internally)
   *   "cancelled"  — turn cancelled by CancelTurnCommand
   *   "error"      — Bifrost error terminated the turn
   */
  finish_reason: string;
}

/**
 * Emitted when the Sjon (Vision / screen capture) state changes.
 * Frontend: animate the Sjon-glow blue accent in LayerStatusPanel.
 * Direction: server -> client
 * Emitted by: L3 Sjon orchestrator via EventBus
 */
export interface SjonActivity {
  type: "sjon.activity";
  /** Current state of the Sjon capture pipeline. */
  state: SjonState;
  /** ISO 8601 UTC timestamp of the state transition. */
  timestamp: string;
}

/**
 * Emitted when any layer encounters an error worth surfacing to the user.
 * Frontend: display as a toast notification (AESTHETIC.md error-tone motion).
 */
export interface ErrorEvent {
  type: "error";
  level: ErrorLevel;
  /**
   * Layer or module that emitted the error.
   * Examples: "bifrost", "tunga", "hlust", "vebond", "lifecycle"
   */
  source: string;
  /** Human-readable description — user-intelligible, not a Python traceback. */
  message: string;
}

/** Discriminated union of all events the server may push to the client. */
export type ProtocolEvent =
  | CeremonyStateChanged
  | BifrostHealth
  | TungaActivity
  | HlustActivity
  | SjonActivity
  | AgentToken
  | AgentTurnComplete
  | ErrorEvent;

// ==============================================================================
// Client -> Server Commands
// ==============================================================================

/**
 * Initiate the Kynding -> Tengsl ceremony sequence (Light the Candle).
 * Server responds with CeremonyStateChanged events and BifrostHealth updates.
 */
export interface LightCommand {
  type: "light";
}

/**
 * Initiate the Slokna shutdown sequence (Extinguish the Candle).
 * If VebondConfig.ceremony_button_confirm is true, the frontend must confirm
 * before sending this command — the backend does not re-confirm.
 */
export interface ExtinguishCommand {
  type: "extinguish";
}

/**
 * Send a user text message into the active turn loop.
 * Only valid while lifecycle is "samraedur" or "tengsl".
 * Server responds with AgentToken events followed by AgentTurnComplete.
 */
export interface SendMessageCommand {
  type: "send_message";
  /** Non-empty text after stripping whitespace. */
  text: string;
}

/**
 * Abort an in-flight agent turn.
 * Server emits AgentTurnComplete with finish_reason="cancelled" if successful.
 */
export interface CancelTurnCommand {
  type: "cancel_turn";
  /** The turn_id from the AgentToken events for the turn to abort. */
  turn_id: string;
}

/**
 * Toggle a sense on or off.
 * In v0.4.0: received but not acted upon (read-only; see IPC_PROTOCOL.md §Commands).
 * In v0.4.x: will hot-reload the sense subprocess.
 */
export interface ToggleSenseCommand {
  type: "toggle_sense";
  /**
   * Sense identifier. Valid values:
   *   "hlust", "tunga", "sjon_screen", "sjon_webcam",
   *   "filesystem", "terminal", "browser", "photopea",
   *   "blender", "vrchat", "agentmail", "library"
   */
  sense_id: string;
  enabled: boolean;
}

/** Discriminated union of all commands the client may send to the server. */
export type ProtocolCommand =
  | LightCommand
  | ExtinguishCommand
  | SendMessageCommand
  | CancelTurnCommand
  | ToggleSenseCommand;

// ==============================================================================
// Utility type guards — use in WsClient and store code
// ==============================================================================

/**
 * Narrow a parsed ProtocolEvent to a specific event type.
 * Usage: if (isCeremonyStateChanged(event)) { event.to_state ... }
 */
export function isCeremonyStateChanged(e: ProtocolEvent): e is CeremonyStateChanged {
  return e.type === "ceremony.state_changed";
}

export function isBifrostHealth(e: ProtocolEvent): e is BifrostHealth {
  return e.type === "bifrost.health";
}

export function isTungaActivity(e: ProtocolEvent): e is TungaActivity {
  return e.type === "tunga.activity";
}

export function isHlustActivity(e: ProtocolEvent): e is HlustActivity {
  return e.type === "hlust.activity";
}

export function isSjonActivity(e: ProtocolEvent): e is SjonActivity {
  return e.type === "sjon.activity";
}

export function isAgentToken(e: ProtocolEvent): e is AgentToken {
  return e.type === "agent.token";
}

export function isAgentTurnComplete(e: ProtocolEvent): e is AgentTurnComplete {
  return e.type === "agent.turn_complete";
}

export function isErrorEvent(e: ProtocolEvent): e is ErrorEvent {
  return e.type === "error";
}

/**
 * Parse a raw WebSocket message string into a ProtocolEvent.
 * Returns null if the message is not valid JSON or lacks a recognized type field.
 * The caller decides what to do with null (log a warning and discard).
 */
export function parseProtocolEvent(raw: string): ProtocolEvent | null {
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    if (typeof parsed.type !== "string") return null;

    const knownEventTypes = new Set([
      "ceremony.state_changed",
      "bifrost.health",
      "tunga.activity",
      "hlust.activity",
      "sjon.activity",
      "agent.token",
      "agent.turn_complete",
      "error",
    ]);

    if (!knownEventTypes.has(parsed.type)) return null;

    // Type assertion: we trust the server to send valid data for known types.
    // Forge may add runtime validation here if needed.
    return parsed as unknown as ProtocolEvent;
  } catch {
    return null;
  }
}
