/**
 * HERETIC WebSocket client — L4 Vebond IPC transport
 *
 * WsClient manages the WebSocket connection to the Python backend server
 * (ws://localhost:8642/ws by default). It provides:
 *   - connect() / disconnect()
 *   - send(command) — serialize and send a ProtocolCommand
 *   - subscribe(eventType, handler) — register a typed event handler
 *
 * All method bodies in this skeleton throw an error with a clear message
 * describing what Forge must implement.
 *
 * Design constraints:
 *   - Single WebSocket connection per WsClient instance
 *   - Reconnection strategy: Forge implements exponential backoff (v0.4.x)
 *   - No auth in v0.4.0 (localhost only); token auth deferred to v0.4.x
 *   - Callers never interact with the native WebSocket directly — all
 *     communication flows through this class
 *
 * Forge implementation note:
 *   The Zustand ceremony store (store/ceremony.ts) calls connect() on mount
 *   and subscribe() to route events into store actions. WsClient does not
 *   import the store directly — the store imports WsClient.
 */

import type {
  ProtocolCommand,
  ProtocolEvent,
  WsConnectionStatus,
} from "../types/ipc";
import { parseProtocolEvent } from "../types/ipc";

/** Handler for a specific ProtocolEvent type. */
export type EventHandler<T extends ProtocolEvent = ProtocolEvent> = (event: T) => void;

/** Handler for WebSocket connection status changes. */
export type ConnectionStatusHandler = (status: WsConnectionStatus) => void;

/**
 * HERETIC L4 Vebond WebSocket client.
 *
 * One instance is created at app startup and shared across the component tree
 * via the ceremony Zustand store or React context (Forge decides the wiring).
 *
 * Lifecycle:
 *   1. Forge Worker constructs WsClient(wsUrl)
 *   2. Forge Worker calls client.connect() on app mount
 *   3. Components subscribe via client.subscribe() to receive typed events
 *   4. Components call client.send() to issue ProtocolCommand messages
 *   5. Forge Worker calls client.disconnect() on app unmount or Slokna
 */
export class WsClient {
  private readonly _url: string;
  private _ws: WebSocket | null = null;
  private _status: WsConnectionStatus = "disconnected";
  private _handlers: Map<string, Array<EventHandler>> = new Map();
  private _statusHandlers: Array<ConnectionStatusHandler> = [];

  constructor(url: string = "ws://localhost:8642/ws") {
    this._url = url;
  }

  /** Current WebSocket connection status. */
  get connectionStatus(): WsConnectionStatus {
    return this._status;
  }

  /**
   * Open the WebSocket connection to the backend.
   *
   * On success: status transitions disconnected -> connecting -> connected.
   * On failure: status transitions to "error"; the caller sees the rejection.
   *
   * Forge implementation note:
   *   1. Construct a native WebSocket(this._url)
   *   2. Wire ws.onopen -> set status "connected", notify status handlers
   *   3. Wire ws.onmessage -> parseProtocolEvent(event.data), route to handlers
   *   4. Wire ws.onerror -> set status "error", notify status handlers
   *   5. Wire ws.onclose -> set status "disconnected", notify status handlers
   *   6. Store ws in this._ws
   *   7. Return a Promise that resolves on ws.onopen or rejects on ws.onerror
   *
   * @returns Promise that resolves when the connection is established.
   * @throws Error if connection fails.
   */
  async connect(): Promise<void> {
    throw new Error(
      "Forge will implement: construct WebSocket(this._url), wire onopen/onmessage/" +
      "onerror/onclose, update this._status, notify status handlers, route parsed " +
      "ProtocolEvent instances to registered handlers. Return promise resolving on open."
    );
  }

  /**
   * Close the WebSocket connection cleanly.
   *
   * Forge implementation note:
   *   Call this._ws?.close(1000, "Client disconnect") and set status "disconnected".
   *   Clear this._ws. Notify status handlers.
   */
  async disconnect(): Promise<void> {
    throw new Error(
      "Forge will implement: call ws.close(1000), set status 'disconnected', " +
      "clear this._ws, notify all status handlers."
    );
  }

  /**
   * Serialize and send a ProtocolCommand to the backend.
   *
   * Forge implementation note:
   *   1. Assert this._ws is not null and readyState === WebSocket.OPEN
   *   2. JSON.stringify(command) and call this._ws.send(json)
   *   3. If not connected: throw an Error ("Cannot send: WebSocket not connected")
   *
   * @param command A ProtocolCommand instance (LightCommand, ExtinguishCommand, etc.)
   * @throws Error if the WebSocket is not connected.
   */
  send(command: ProtocolCommand): void {
    throw new Error(
      "Forge will implement: assert connected, JSON.stringify(command), " +
      "call this._ws.send(json). Throw if not connected."
    );
  }

  /**
   * Register a handler for a specific event type.
   *
   * @param eventType The `type` discriminator value from ProtocolEvent.
   *   Pass "*" to receive all events regardless of type.
   * @param handler   Called with the typed event when it arrives.
   * @returns An unsubscribe function. Call it to remove the handler.
   *
   * Forge implementation note:
   *   Store handlers in this._handlers (Map<string, EventHandler[]>).
   *   Support "*" as a catch-all. The unsubscribe function removes the handler
   *   from the array for the given event type.
   */
  subscribe<T extends ProtocolEvent>(
    eventType: T["type"] | "*",
    handler: EventHandler<T>,
  ): () => void {
    throw new Error(
      "Forge will implement: push handler into this._handlers map keyed by eventType. " +
      "Return () => void that removes the handler (for React cleanup in useEffect)."
    );
  }

  /**
   * Register a handler for WebSocket connection status changes.
   *
   * @param handler Called whenever connection status changes.
   * @returns An unsubscribe function.
   */
  onStatusChange(handler: ConnectionStatusHandler): () => void {
    throw new Error(
      "Forge will implement: push handler into this._statusHandlers. " +
      "Return () => void unsubscribe function."
    );
  }

  // ------------------------------------------------------------------
  // Internal helpers — Forge implements these in the same session
  // ------------------------------------------------------------------

  /**
   * Route a received raw message string to registered handlers.
   * Called from ws.onmessage. Parses the message and dispatches to handlers.
   *
   * Forge implementation note:
   *   1. Call parseProtocolEvent(raw) from types/ipc.ts
   *   2. If null: log a warning and return (do not crash)
   *   3. Route to handlers for event.type AND to all "*" handlers
   */
  private _dispatch(raw: string): void {
    throw new Error(
      "Forge will implement: parseProtocolEvent(raw), route to type-specific handlers " +
      "and '*' catch-all handlers. Log a warning on parse failure."
    );
  }

  /**
   * Update internal connection status and notify all status handlers.
   *
   * Forge implementation note: set this._status = status, call each handler.
   */
  private _setStatus(status: WsConnectionStatus): void {
    throw new Error(
      "Forge will implement: set this._status = status, invoke each handler in " +
      "this._statusHandlers with the new status."
    );
  }
}

// Default export — a singleton is typically appropriate for one ceremony.
// Forge decides whether to export a singleton or let the store construct an instance.
export { parseProtocolEvent };
