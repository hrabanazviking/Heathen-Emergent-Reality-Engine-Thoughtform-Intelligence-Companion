/**
 * HERETIC Ceremony Store — Zustand state for the L4 Vebond UI
 *
 * This store is the single source of truth for the ceremony's observable state
 * in the React frontend. Components read from it; WsClient events write to it.
 *
 * Shape mirrors the server-side ceremony state as documented in:
 *   docs/architecture/CEREMONY.md
 *   docs/architecture/IPC_PROTOCOL.md
 *
 * WsClient singleton pattern:
 *   The WsClient instance lives outside Zustand state (it is a class instance,
 *   not serializable data). It is held in a module-level variable `_wsClient`
 *   and created inside `connectWs`. This is intentional — see connectWs docstring.
 */

import { create } from "zustand";
import type {
  LifecycleState,
  BifrostStatus,
  TungaState,
  HlustState,
  WsConnectionStatus,
  CeremonyStateChanged,
  BifrostHealth,
  TungaActivity,
  HlustActivity,
  AgentToken,
  AgentTurnComplete,
  ErrorEvent,
} from "../types/ipc";
import { WsClient } from "../api/ws-client";

// ==============================================================================
// Chat history entry types
// ==============================================================================

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  /** Complete message content (assembled from AgentToken deltas). */
  content: string;
  /** True while the assistant message is still receiving tokens. */
  streaming: boolean;
  /** ISO timestamp when this message was finalized. */
  timestamp: string | null;
}

export interface Toast {
  id: string;
  level: "warn" | "error";
  source: string;
  message: string;
  /** ISO timestamp when the toast was created. */
  createdAt: string;
}

// ==============================================================================
// Store state shape
// ==============================================================================

export interface CeremonyState {
  // ---- Lifecycle ---
  lifecycleState: LifecycleState;

  // ---- Bifrost ---
  bifrostStatus: BifrostStatus;
  bifrostEndpoint: string;
  bifrostLatencyMs: number | null;

  // ---- Voice layers ---
  tungaState: TungaState;
  hlustState: HlustState;
  hlustLevelDb: number | null;

  // ---- Chat ---
  chatHistory: ChatMessage[];
  /** The turn_id of the currently in-flight agent turn, or null. */
  activeTurnId: string | null;
  /** Monotonically increasing sequence counter for the active turn's tokens. */
  activeTokenSequence: number;

  // ---- WebSocket transport ---
  connectionStatus: WsConnectionStatus;

  // ---- Error toasts ---
  toasts: Toast[];

  // ---- Actions ---
  /** Called by WsClient when a CeremonyStateChanged event arrives. */
  setLifecycleState: (state: LifecycleState) => void;

  /** Called by WsClient when a BifrostHealth event arrives. */
  setBifrostHealth: (status: BifrostStatus, endpoint: string, latencyMs: number | null) => void;

  /** Called by WsClient when a TungaActivity event arrives. */
  setTungaState: (state: TungaState) => void;

  /** Called by WsClient when a HlustActivity event arrives. */
  setHlustActivity: (state: HlustState, levelDb: number | null) => void;

  /** Called by WsClient when an AgentToken event arrives. Appends to active message. */
  appendAgentToken: (textDelta: string, sequenceId: number, turnId?: string) => void;

  /** Called by WsClient when an AgentTurnComplete event arrives. */
  finalizeAgentTurn: (turnId: string, finishReason: string) => void;

  /** Called by WsClient when an ErrorEvent arrives. */
  addToast: (level: "warn" | "error", source: string, message: string) => void;

  /** Called by the ToastSystem component to dismiss a toast. */
  dismissToast: (id: string) => void;

  /** Called by WsClient on connection status changes. */
  setConnectionStatus: (status: WsConnectionStatus) => void;

  /** Add a user message to chat history (before sending to backend). */
  addUserMessage: (text: string) => void;

  /** Clear all chat history (called on new ceremony or EXTINGUISHED). */
  clearChatHistory: () => void;

  /**
   * Connect the WebSocket client and wire all event subscriptions.
   *
   * Creates a WsClient singleton (or reuses it if already connected), calls
   * connect(), then subscribes each ProtocolEvent type to its corresponding
   * store action. Also wires onStatusChange to setConnectionStatus.
   *
   * @param wsUrl Optional override for the WebSocket URL. Defaults to
   *   the WsClient default (ws://localhost:8642/ws).
   */
  connectWs: (wsUrl?: string) => Promise<void>;

  /**
   * Disconnect the WebSocket client cleanly.
   * Called on app unmount or Slokna completion.
   */
  disconnectWs: () => Promise<void>;

  /**
   * Send a command via the active WsClient.
   * Returns false if no client is connected.
   */
  sendCommand: (command: Record<string, unknown>) => boolean;
}

// ==============================================================================
// Module-level WsClient singleton — lives outside Zustand state
// ==============================================================================

/**
 * The single WsClient for this browser session.
 * Held here so it can be shared across connectWs / disconnectWs / sendCommand
 * without polluting Zustand's serializable state.
 */
let _wsClient: WsClient | null = null;

/**
 * Monotonic counter for local turn ID generation.
 *
 * Appended to Date.now() so that two turns starting within the same millisecond
 * (common in synchronous test code) still receive distinct IDs. Resets only on
 * module reload (page refresh / HMR), which is fine — the counter just needs to
 * be unique within a single browser session.
 */
let _localTurnCounter = 0;

// ==============================================================================
// Store implementation
// ==============================================================================

/**
 * Zustand store for the HERETIC ceremony UI state.
 *
 * Import and use in components:
 *   import { useCeremonyStore } from "../store/ceremony";
 *   const lifecycleState = useCeremonyStore(s => s.lifecycleState);
 */
export const useCeremonyStore = create<CeremonyState>((set, get) => ({
  // ---- Initial state ----
  lifecycleState: "hvild",
  bifrostStatus: "closed",
  bifrostEndpoint: "",
  bifrostLatencyMs: null,
  tungaState: "idle",
  hlustState: "idle",
  hlustLevelDb: null,
  chatHistory: [],
  activeTurnId: null,
  activeTokenSequence: -1,
  connectionStatus: "disconnected",
  toasts: [],

  // ---- Actions ----

  setLifecycleState: (state) =>
    set({ lifecycleState: state }),

  setBifrostHealth: (status, endpoint, latencyMs) =>
    set({ bifrostStatus: status, bifrostEndpoint: endpoint, bifrostLatencyMs: latencyMs }),

  setTungaState: (state) =>
    set({ tungaState: state }),

  setHlustActivity: (state, levelDb) =>
    set({ hlustState: state, hlustLevelDb: levelDb }),

  appendAgentToken: (textDelta, sequenceId, turnId) => {
    set((s) => {
      const chatHistory = s.chatHistory;

      // Determine the effective turn ID.
      //
      // Priority: explicit turnId arg (tests or future protocol) > existing
      // activeTurnId (continuing a turn) > generate a stable local ID.
      //
      // The local ID uses "local-" prefix so it is distinct from backend UUIDs.
      // It is generated ONCE on the first token and held in activeTurnId for
      // all subsequent tokens of this turn. finalizeAgentTurn() resolves the
      // message by activeTurnId, not by the backend turn_id from AgentTurnComplete,
      // so there is never a mismatch between the local ID and the backend UUID.
      const effectiveTurnId = turnId ?? s.activeTurnId ?? `local-${Date.now()}-${++_localTurnCounter}`;

      // If this is a new turn (activeTurnId changed or first token), append a new message
      if (s.activeTurnId !== effectiveTurnId) {
        const newMsg: ChatMessage = {
          id: `assistant-${effectiveTurnId}`,
          role: "assistant",
          content: textDelta,
          streaming: true,
          timestamp: null,
        };
        return {
          chatHistory: [...chatHistory, newMsg],
          activeTurnId: effectiveTurnId,
          activeTokenSequence: sequenceId,
        };
      }

      // Continuing an in-flight turn — find the streaming message and append
      const updatedHistory = chatHistory.map((msg) => {
        if (msg.id === `assistant-${effectiveTurnId}` && msg.streaming) {
          return { ...msg, content: msg.content + textDelta };
        }
        return msg;
      });

      return {
        chatHistory: updatedHistory,
        activeTokenSequence: sequenceId,
      };
    });
  },

  finalizeAgentTurn: (_turnId, _finishReason) => {
    // IMPORTANT: we finalize by activeTurnId (the store's local ID), NOT by the
    // backend _turnId from AgentTurnComplete. The backend UUID never travels on
    // AgentToken events, so the streaming message was keyed by a local ID.
    // Attempting to find msg.id === `assistant-${backendUuid}` would always miss.
    // The backend _turnId is accepted for future use (logging, protocol v0.4.x).
    set((s) => {
      const localTurnId = s.activeTurnId;
      if (localTurnId === null) {
        // No active turn to finalize — guard against spurious complete events
        return { activeTurnId: null, activeTokenSequence: -1 };
      }
      const now = new Date().toISOString();
      const updatedHistory = s.chatHistory.map((msg) => {
        if (msg.id === `assistant-${localTurnId}` && msg.streaming) {
          return { ...msg, streaming: false, timestamp: now };
        }
        return msg;
      });
      return {
        chatHistory: updatedHistory,
        activeTurnId: null,
        activeTokenSequence: -1,
      };
    });
  },

  addToast: (level, source, message) => {
    const toast: Toast = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      level,
      source,
      message,
      createdAt: new Date().toISOString(),
    };
    set((s) => ({ toasts: [...s.toasts, toast] }));
  },

  dismissToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),

  setConnectionStatus: (status) =>
    set({ connectionStatus: status }),

  addUserMessage: (text) => {
    const msg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      streaming: false,
      timestamp: new Date().toISOString(),
    };
    set((s) => ({ chatHistory: [...s.chatHistory, msg] }));
  },

  clearChatHistory: () =>
    set({ chatHistory: [], activeTurnId: null, activeTokenSequence: -1 }),

  connectWs: async (wsUrl?: string) => {
    // Reuse existing connected client if already live
    if (_wsClient !== null) {
      const status = _wsClient.connectionStatus;
      if (status === "connected" || status === "connecting") {
        return;
      }
    }

    _wsClient = new WsClient(wsUrl);

    // Wire connection status changes
    _wsClient.onStatusChange((status) => {
      get().setConnectionStatus(status);
    });

    // Wire all server->client event types to corresponding store actions
    _wsClient.subscribe<CeremonyStateChanged>("ceremony.state_changed", (event) => {
      get().setLifecycleState(event.to_state);
    });

    _wsClient.subscribe<BifrostHealth>("bifrost.health", (event) => {
      get().setBifrostHealth(event.status, event.endpoint, event.latency_ms);
    });

    _wsClient.subscribe<TungaActivity>("tunga.activity", (event) => {
      get().setTungaState(event.state);
    });

    _wsClient.subscribe<HlustActivity>("hlust.activity", (event) => {
      get().setHlustActivity(event.state, event.level_db);
    });

    _wsClient.subscribe<AgentToken>("agent.token", (event) => {
      // AgentToken has no turn_id field in the protocol — sequence_id tracks ordering
      get().appendAgentToken(event.text_delta, event.sequence_id);
    });

    _wsClient.subscribe<AgentTurnComplete>("agent.turn_complete", (event) => {
      get().finalizeAgentTurn(event.turn_id, event.finish_reason);
    });

    _wsClient.subscribe<ErrorEvent>("error", (event) => {
      get().addToast(event.level, event.source, event.message);
    });

    // Attempt connection — throws if backend is unreachable
    try {
      await _wsClient.connect();
    } catch (err) {
      // Status already set to "error" by WsClient. Backoff reconnect is running.
      console.warn("[HERETIC] Initial WS connect failed:", err);
    }
  },

  disconnectWs: async () => {
    if (_wsClient !== null) {
      await _wsClient.disconnect();
      _wsClient = null;
    }
    set({ connectionStatus: "disconnected" });
  },

  sendCommand: (command) => {
    if (_wsClient === null || _wsClient.connectionStatus !== "connected") {
      return false;
    }
    try {
      _wsClient.send(command as unknown as Parameters<WsClient["send"]>[0]);
      return true;
    } catch {
      return false;
    }
  },
}));

/**
 * Expose the raw WsClient instance for components that need to call send() directly.
 * Returns null if not connected.
 */
export function getWsClient(): WsClient | null {
  return _wsClient;
}
