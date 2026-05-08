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
 * Forge implementation guide:
 *   1. Wire WsClient.subscribe() calls inside the `connectWs` action.
 *   2. Each subscribe call maps one ProtocolEvent type to the corresponding action.
 *   3. Actions must be pure state transitions — no side effects in actions.
 *   4. The WsClient instance is held outside Zustand state (it is a class, not
 *      serializable data) — import it or accept it as a parameter to connectWs.
 */

import { create } from "zustand";
import type {
  LifecycleState,
  BifrostStatus,
  TungaState,
  HlustState,
  WsConnectionStatus,
} from "../types/ipc";

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
   * Forge implements this action — it imports or receives WsClient and
   * subscribes to each ProtocolEvent type, mapping each to the relevant action.
   */
  connectWs: (wsUrl?: string) => Promise<void>;

  /**
   * Disconnect the WebSocket client cleanly.
   * Called on app unmount or Slokna completion.
   */
  disconnectWs: () => Promise<void>;
}

// ==============================================================================
// Store implementation — Forge fills in all action bodies
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
    // Forge: set({ lifecycleState: state })
    set({ lifecycleState: state }),

  setBifrostHealth: (status, endpoint, latencyMs) =>
    // Forge: set({ bifrostStatus: status, bifrostEndpoint: endpoint, bifrostLatencyMs: latencyMs })
    set({ bifrostStatus: status, bifrostEndpoint: endpoint, bifrostLatencyMs: latencyMs }),

  setTungaState: (state) =>
    // Forge: set({ tungaState: state })
    set({ tungaState: state }),

  setHlustActivity: (state, levelDb) =>
    // Forge: set({ hlustState: state, hlustLevelDb: levelDb })
    set({ hlustState: state, hlustLevelDb: levelDb }),

  appendAgentToken: (_textDelta, _sequenceId, _turnId) => {
    throw new Error(
      "Forge will implement: find or create the active streaming ChatMessage, " +
      "append textDelta to its content, update activeTurnId and activeTokenSequence. " +
      "If turnId is new (first token of a new turn), push a new streaming message."
    );
  },

  finalizeAgentTurn: (_turnId, _finishReason) => {
    throw new Error(
      "Forge will implement: set streaming=false on the ChatMessage with matching " +
      "activeTurnId, set timestamp to now, clear activeTurnId."
    );
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

  connectWs: async (_wsUrl?: string) => {
    throw new Error(
      "Forge will implement: construct WsClient(wsUrl ?? default), call connect(), " +
      "subscribe to each ProtocolEvent type and route to corresponding store actions: " +
      "  ceremony.state_changed -> setLifecycleState(event.to_state) " +
      "  bifrost.health -> setBifrostHealth(...) " +
      "  tunga.activity -> setTungaState(event.state) " +
      "  hlust.activity -> setHlustActivity(event.state, event.level_db) " +
      "  agent.token -> appendAgentToken(event.text_delta, event.sequence_id, event.turn_id?) " +
      "  agent.turn_complete -> finalizeAgentTurn(event.turn_id, event.finish_reason) " +
      "  error -> addToast(event.level, event.source, event.message) " +
      "  WsClient.onStatusChange -> setConnectionStatus(status)"
    );
  },

  disconnectWs: async () => {
    throw new Error(
      "Forge will implement: call wsClient.disconnect(), set connectionStatus 'disconnected'."
    );
  },
}));
