/**
 * Placeholder WsClient tests — Vitest
 *
 * These tests are skip-marked during the scaffold phase. Forge activates them
 * when WsClient method bodies are implemented.
 *
 * Forge will likely use vi.mock("../src/api/ws-client") or a mock WebSocket
 * implementation (e.g. jest-websocket-mock or a hand-rolled stub) for unit tests.
 *
 * Run with: npm test  (from the frontend/ directory)
 */

import { describe, it, expect, vi } from "vitest";
import { parseProtocolEvent } from "../src/types/ipc";

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
// Placeholder WsClient tests — Forge activates
// ---------------------------------------------------------------------------

describe.skip("WsClient.connect", () => {
  it("transitions status to 'connected' on successful open", async () => {
    // Forge: mock WebSocket, call client.connect(), assert connectionStatus === 'connected'
  });

  it("transitions status to 'error' on failed open", async () => {
    // Forge: mock WebSocket that fires onerror, assert status === 'error'
  });
});

describe.skip("WsClient.send", () => {
  it("serializes LightCommand to JSON and sends", () => {
    // Forge: connect, call client.send({ type: 'light' }), assert ws.send called with correct JSON
  });

  it("throws when not connected", () => {
    // Forge: call client.send() without connect(), assert Error thrown
  });
});

describe.skip("WsClient.subscribe", () => {
  it("calls handler when matching event arrives", () => {
    // Forge: subscribe to 'bifrost.health', inject ws.onmessage event, assert handler called
  });

  it("calls catchall '*' handler for all event types", () => {
    // Forge: subscribe '*', inject multiple event types, assert all invoke handler
  });

  it("unsubscribe function removes the handler", () => {
    // Forge: subscribe, call unsubscribe(), inject event, assert handler NOT called
  });
});

describe.skip("WsClient.disconnect", () => {
  it("transitions status to 'disconnected'", async () => {
    // Forge: connect, disconnect, assert connectionStatus === 'disconnected'
  });
});
