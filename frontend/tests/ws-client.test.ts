/**
 * WsClient tests — Vitest
 *
 * Uses a hand-rolled MockWebSocket stub that lets tests control open/close/error/message
 * without hitting a real server. The stub is installed on globalThis before each test.
 *
 * Run with: npm test  (from the frontend/ directory)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { parseProtocolEvent } from "../src/types/ipc";

// ---------------------------------------------------------------------------
// MockWebSocket — hand-rolled stub
// ---------------------------------------------------------------------------

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readonly url: string;
  readyState: number = MockWebSocket.CONNECTING;

  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  readonly sentMessages: string[] = [];

  // Registry for tests to grab the latest instance
  static lastInstance: MockWebSocket | null = null;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.lastInstance = this;
  }

  send(data: string): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error("MockWebSocket: send called when not OPEN");
    }
    this.sentMessages.push(data);
  }

  close(code?: number, reason?: string): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent("close", { code: code ?? 1000, reason: reason ?? "" }));
    }
  }

  /** Test helper: simulate a successful connection open. */
  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) this.onopen(new Event("open"));
  }

  /** Test helper: simulate a connection error. */
  simulateError(): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onerror) this.onerror(new Event("error"));
    if (this.onclose) this.onclose(new CloseEvent("close", { code: 1006 }));
  }

  /** Test helper: simulate receiving a server message. */
  simulateMessage(data: string): void {
    if (this.onmessage) {
      this.onmessage(new MessageEvent("message", { data }));
    }
  }
}

// ---------------------------------------------------------------------------
// Active utility tests — parseProtocolEvent is pure, needs no mock
// ---------------------------------------------------------------------------

describe("parseProtocolEvent", () => {
  it("returns null for invalid JSON", () => {
    expect(parseProtocolEvent("not json")).toBeNull();
  });

  it("returns null for JSON without a type field", () => {
    expect(parseProtocolEvent(JSON.stringify({ foo: "bar" }))).toBeNull();
  });

  it("returns null for unknown type field", () => {
    expect(parseProtocolEvent(JSON.stringify({ type: "totally.unknown" }))).toBeNull();
  });

  it("parses a valid ceremony.state_changed event", () => {
    const raw = JSON.stringify({
      type: "ceremony.state_changed",
      from_state: "kynding",
      to_state: "tengsl",
      timestamp: "2026-05-07T00:00:00.000Z",
    });
    const event = parseProtocolEvent(raw);
    expect(event).not.toBeNull();
    expect(event?.type).toBe("ceremony.state_changed");
  });

  it("parses a valid error event", () => {
    const raw = JSON.stringify({
      type: "error",
      level: "warn",
      source: "bifrost",
      message: "Reconnecting...",
    });
    const event = parseProtocolEvent(raw);
    expect(event).not.toBeNull();
    expect(event?.type).toBe("error");
  });

  it("parses a valid agent.token event", () => {
    const raw = JSON.stringify({
      type: "agent.token",
      role: "assistant",
      text_delta: "Hello",
      sequence_id: 0,
    });
    const event = parseProtocolEvent(raw);
    expect(event).not.toBeNull();
    expect(event?.type).toBe("agent.token");
  });
});

// ---------------------------------------------------------------------------
// WsClient tests — using MockWebSocket
// ---------------------------------------------------------------------------

let originalWebSocket: typeof globalThis.WebSocket;

beforeEach(() => {
  originalWebSocket = globalThis.WebSocket;
  // @ts-expect-error — replacing with mock for test isolation
  globalThis.WebSocket = MockWebSocket;
  MockWebSocket.lastInstance = null;
});

afterEach(() => {
  globalThis.WebSocket = originalWebSocket;
  vi.restoreAllMocks();
});

describe("WsClient.connect", () => {
  it("transitions status to 'connected' on successful open", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");

    const connectPromise = client.connect();
    // Simulate open from the mock
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;

    expect(client.connectionStatus).toBe("connected");
  });

  it("transitions status to 'error' then rejects on failed connection", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateError();

    await expect(connectPromise).rejects.toThrow();
  });

  it("calls status handlers when status changes", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");
    const statuses: string[] = [];
    client.onStatusChange((s) => statuses.push(s));

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;

    expect(statuses).toContain("connecting");
    expect(statuses).toContain("connected");
  });
});

describe("WsClient.send", () => {
  it("serializes LightCommand to JSON and sends", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;

    client.send({ type: "light" });
    expect(MockWebSocket.lastInstance?.sentMessages).toHaveLength(1);
    expect(JSON.parse(MockWebSocket.lastInstance!.sentMessages[0])).toEqual({ type: "light" });
  });

  it("throws when not connected", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");
    // Do not connect
    expect(() => client.send({ type: "light" })).toThrow();
  });
});

describe("WsClient.subscribe", () => {
  it("calls handler when matching event arrives", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;

    const received: unknown[] = [];
    client.subscribe("bifrost.health", (e) => received.push(e));

    const raw = JSON.stringify({
      type: "bifrost.health",
      status: "open",
      endpoint: "http://example.com/v1",
      latency_ms: 10,
    });
    MockWebSocket.lastInstance?.simulateMessage(raw);
    expect(received).toHaveLength(1);
  });

  it("calls catchall '*' handler for all event types", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;

    const received: unknown[] = [];
    client.subscribe("*", (e) => received.push(e));

    const events = [
      { type: "bifrost.health", status: "open", endpoint: "", latency_ms: null },
      { type: "tunga.activity", state: "idle" },
      { type: "hlust.activity", state: "idle", level_db: null },
    ];
    for (const ev of events) {
      MockWebSocket.lastInstance?.simulateMessage(JSON.stringify(ev));
    }
    expect(received).toHaveLength(3);
  });

  it("unsubscribe function removes the handler", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;

    const received: unknown[] = [];
    const unsub = client.subscribe("tunga.activity", (e) => received.push(e));

    // Fire event — handler should fire
    MockWebSocket.lastInstance?.simulateMessage(JSON.stringify({ type: "tunga.activity", state: "idle" }));
    expect(received).toHaveLength(1);

    // Unsubscribe then fire again — handler should NOT fire
    unsub();
    MockWebSocket.lastInstance?.simulateMessage(JSON.stringify({ type: "tunga.activity", state: "speaking" }));
    expect(received).toHaveLength(1);
  });

  it("discards unknown event types without throwing", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;

    // Should not throw
    expect(() => {
      MockWebSocket.lastInstance?.simulateMessage(JSON.stringify({ type: "totally.unknown" }));
    }).not.toThrow();
  });
});

describe("WsClient.disconnect", () => {
  it("transitions status to 'disconnected'", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;
    expect(client.connectionStatus).toBe("connected");

    await client.disconnect();
    expect(client.connectionStatus).toBe("disconnected");
  });

  it("does not attempt reconnect after explicit disconnect", async () => {
    const { WsClient } = await import("../src/api/ws-client");
    const client = new WsClient("ws://localhost:8642/ws");
    const setTimeoutSpy = vi.spyOn(globalThis, "setTimeout");

    const connectPromise = client.connect();
    MockWebSocket.lastInstance?.simulateOpen();
    await connectPromise;
    await client.disconnect();

    // After explicit disconnect, setTimeout for reconnect should NOT have been called
    // (it may be called for other things but our close should not trigger reconnect)
    const reconnectCalls = setTimeoutSpy.mock.calls.filter(
      (args) => typeof args[1] === "number" && (args[1] as number) >= 1000
    );
    expect(reconnectCalls).toHaveLength(0);
  });
});
