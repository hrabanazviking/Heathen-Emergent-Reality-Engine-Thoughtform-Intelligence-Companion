/**
 * HERETIC WebSocket client — L4 Vebond IPC transport
 *
 * WsClient manages the WebSocket connection to the Python backend server
 * (ws://localhost:8642/ws by default). It provides:
 *   - connect() / disconnect()
 *   - send(command) — serialize and send a ProtocolCommand
 *   - subscribe(eventType, handler) — register a typed event handler
 *   - onStatusChange(handler) — register a connection status handler
 *
 * Reconnection strategy: exponential backoff starting at 1s, max 16s.
 * The backoff resets when a connection succeeds.
 *
 * Connection state machine:
 *   disconnected -> connecting -> connected -> disconnected (on close/error)
 *                                           -> error (on onerror without prior open)
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

/** Backoff delays in milliseconds — 1s, 2s, 4s, 8s, 16s, then stays at 16s. */
const BACKOFF_DELAYS_MS = [1000, 2000, 4000, 8000, 16000];

/**
 * HERETIC L4 Vebond WebSocket client.
 *
 * One instance per ceremony — constructed in the Zustand store and shared
 * across all subscribers. Components do not interact with WebSocket directly.
 */
export class WsClient {
  private readonly _url: string;
  private _ws: WebSocket | null = null;
  private _status: WsConnectionStatus = "disconnected";
  /** Per-event-type handler lists. Key "*" is the catch-all. */
  private _handlers: Map<string, Array<EventHandler>> = new Map();
  private _statusHandlers: Array<ConnectionStatusHandler> = [];
  /** How many times we have tried to reconnect (for backoff index). */
  private _reconnectAttempts: number = 0;
  /** Whether disconnect() was called explicitly (stops reconnect). */
  private _explicitDisconnect: boolean = false;

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
   * Status transitions: disconnected -> connecting -> connected
   * On failure: -> "error", then reconnect with exponential backoff.
   *
   * @returns Promise that resolves when connected, or rejects on the first
   *   connection failure (before reconnect kicks in).
   */
  async connect(): Promise<void> {
    this._explicitDisconnect = false;
    return new Promise((resolve, reject) => {
      this._setStatus("connecting");
      let settled = false;

      try {
        const ws = new WebSocket(this._url);
        this._ws = ws;

        ws.onopen = () => {
          this._reconnectAttempts = 0;
          this._setStatus("connected");
          if (!settled) {
            settled = true;
            resolve();
          }
        };

        ws.onmessage = (event: MessageEvent) => {
          this._dispatch(event.data as string);
        };

        ws.onerror = () => {
          // onerror always fires before onclose; onclose handles reconnect
          this._setStatus("error");
          if (!settled) {
            settled = true;
            reject(new Error(`WebSocket connection to ${this._url} failed`));
          }
        };

        ws.onclose = () => {
          this._ws = null;
          const wasConnected = this._status === "connected";
          this._setStatus("disconnected");

          // Attempt reconnect unless disconnect() was called explicitly
          if (!this._explicitDisconnect) {
            const delay = BACKOFF_DELAYS_MS[
              Math.min(this._reconnectAttempts, BACKOFF_DELAYS_MS.length - 1)
            ];
            this._reconnectAttempts += 1;
            console.warn(
              `[HERETIC] WebSocket closed. Reconnecting in ${delay}ms ` +
              `(attempt ${this._reconnectAttempts})...`
            );
            setTimeout(() => {
              if (!this._explicitDisconnect) {
                this._reconnectNow();
              }
            }, delay);
          }

          // If promise not yet settled and we never connected, reject was already called
          if (!settled && !wasConnected) {
            settled = true;
          }
        };
      } catch (err) {
        this._setStatus("error");
        if (!settled) {
          settled = true;
          reject(err instanceof Error ? err : new Error(String(err)));
        }
      }
    });
  }

  /**
   * Internal: open a new WebSocket without returning a Promise.
   * Used for reconnect attempts after the initial connect() call.
   */
  private _reconnectNow(): void {
    if (this._explicitDisconnect) return;
    this._setStatus("connecting");

    try {
      const ws = new WebSocket(this._url);
      this._ws = ws;

      ws.onopen = () => {
        this._reconnectAttempts = 0;
        this._setStatus("connected");
      };

      ws.onmessage = (event: MessageEvent) => {
        this._dispatch(event.data as string);
      };

      ws.onerror = () => {
        this._setStatus("error");
      };

      ws.onclose = () => {
        this._ws = null;
        this._setStatus("disconnected");
        if (!this._explicitDisconnect) {
          const delay = BACKOFF_DELAYS_MS[
            Math.min(this._reconnectAttempts, BACKOFF_DELAYS_MS.length - 1)
          ];
          this._reconnectAttempts += 1;
          setTimeout(() => {
            if (!this._explicitDisconnect) {
              this._reconnectNow();
            }
          }, delay);
        }
      };
    } catch (err) {
      this._setStatus("error");
    }
  }

  /**
   * Close the WebSocket connection cleanly.
   * After disconnect(), no reconnect attempts will be made.
   */
  async disconnect(): Promise<void> {
    this._explicitDisconnect = true;
    if (this._ws) {
      this._ws.close(1000, "Client disconnect");
      this._ws = null;
    }
    this._setStatus("disconnected");
  }

  /**
   * Serialize and send a ProtocolCommand to the backend.
   *
   * @param command A ProtocolCommand instance.
   * @throws Error if the WebSocket is not in OPEN state.
   */
  send(command: ProtocolCommand): void {
    if (!this._ws || this._ws.readyState !== WebSocket.OPEN) {
      throw new Error(
        `Cannot send command '${command.type}': WebSocket is not connected ` +
        `(status: ${this._status})`
      );
    }
    this._ws.send(JSON.stringify(command));
  }

  /**
   * Register a handler for a specific event type.
   *
   * @param eventType The `type` discriminator from ProtocolEvent, or "*" for all.
   * @param handler   Called with the typed event when it arrives.
   * @returns An unsubscribe function. Call it to remove the handler (for useEffect cleanup).
   */
  subscribe<T extends ProtocolEvent>(
    eventType: T["type"] | "*",
    handler: EventHandler<T>,
  ): () => void {
    if (!this._handlers.has(eventType)) {
      this._handlers.set(eventType, []);
    }
    const handlers = this._handlers.get(eventType)!;
    handlers.push(handler as EventHandler);

    // Return unsubscribe function
    return () => {
      const idx = handlers.indexOf(handler as EventHandler);
      if (idx !== -1) {
        handlers.splice(idx, 1);
      }
    };
  }

  /**
   * Register a handler for WebSocket connection status changes.
   *
   * @param handler Called whenever connection status changes.
   * @returns An unsubscribe function.
   */
  onStatusChange(handler: ConnectionStatusHandler): () => void {
    this._statusHandlers.push(handler);
    return () => {
      const idx = this._statusHandlers.indexOf(handler);
      if (idx !== -1) {
        this._statusHandlers.splice(idx, 1);
      }
    };
  }

  // ------------------------------------------------------------------
  // Internal helpers
  // ------------------------------------------------------------------

  /**
   * Route a received raw message string to registered handlers.
   * Called from ws.onmessage. Parses the message and dispatches.
   */
  private _dispatch(raw: string): void {
    const event = parseProtocolEvent(raw);
    if (event === null) {
      console.warn("[HERETIC] WsClient: received unrecognized event:", raw.slice(0, 120));
      return;
    }

    // Dispatch to type-specific handlers
    const typeHandlers = this._handlers.get(event.type);
    if (typeHandlers) {
      for (const handler of typeHandlers) {
        try {
          handler(event);
        } catch (err) {
          console.error("[HERETIC] WsClient: event handler threw:", err);
        }
      }
    }

    // Dispatch to catch-all handlers
    const catchAllHandlers = this._handlers.get("*");
    if (catchAllHandlers) {
      for (const handler of catchAllHandlers) {
        try {
          handler(event);
        } catch (err) {
          console.error("[HERETIC] WsClient: catch-all handler threw:", err);
        }
      }
    }
  }

  /**
   * Update internal connection status and notify all status handlers.
   */
  private _setStatus(status: WsConnectionStatus): void {
    if (this._status === status) return; // No-op if same status
    this._status = status;
    for (const handler of this._statusHandlers) {
      try {
        handler(status);
      } catch (err) {
        console.error("[HERETIC] WsClient: status handler threw:", err);
      }
    }
  }
}

export { parseProtocolEvent };
