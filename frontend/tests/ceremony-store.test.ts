/**
 * Ceremony store tests — Vitest
 *
 * Tests for the Zustand ceremony store actions and initial state.
 * Uses useCeremonyStore.getState() directly (no React hooks needed for pure state tests).
 *
 * Run with: npm test  (from the frontend/ directory)
 */

import { describe, it, expect, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Minimal active test — confirms Zustand store imports without crashing
// ---------------------------------------------------------------------------

describe("ceremony store — import smoke test", () => {
  it("useCeremonyStore is importable", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    expect(typeof useCeremonyStore).toBe("function");
  });
});

// ---------------------------------------------------------------------------
// Store action tests
// ---------------------------------------------------------------------------

describe("ceremony store — initial state", () => {
  it("starts with lifecycleState 'hvild'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const store = useCeremonyStore.getState();
    expect(store.lifecycleState).toBe("hvild");
  });

  it("starts with connectionStatus 'disconnected'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const store = useCeremonyStore.getState();
    expect(store.connectionStatus).toBe("disconnected");
  });

  it("starts with empty chatHistory", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const store = useCeremonyStore.getState();
    expect(store.chatHistory).toHaveLength(0);
  });

  it("starts with empty toasts", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const store = useCeremonyStore.getState();
    expect(store.toasts).toHaveLength(0);
  });

  it("starts with bifrostStatus 'closed'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const store = useCeremonyStore.getState();
    expect(store.bifrostStatus).toBe("closed");
  });

  it("starts with activeTurnId null", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const store = useCeremonyStore.getState();
    expect(store.activeTurnId).toBeNull();
  });
});

describe("ceremony store — setLifecycleState", () => {
  beforeEach(async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setLifecycleState("hvild");
  });

  it("transitions from hvild to kynding", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setLifecycleState("kynding");
    expect(useCeremonyStore.getState().lifecycleState).toBe("kynding");
  });

  it("can transition through all valid states", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const states = ["hvild", "kynding", "tengsl", "samraedur", "recovering", "slokna", "config_error"] as const;
    for (const s of states) {
      useCeremonyStore.getState().setLifecycleState(s);
      expect(useCeremonyStore.getState().lifecycleState).toBe(s);
    }
  });
});

describe("ceremony store — addToast / dismissToast", () => {
  beforeEach(async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    // Clear toasts
    useCeremonyStore.setState({ toasts: [] });
  });

  it("addToast pushes a toast with correct fields", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().addToast("warn", "bifrost", "Reconnecting...");
    const toasts = useCeremonyStore.getState().toasts;
    expect(toasts).toHaveLength(1);
    expect(toasts[0].level).toBe("warn");
    expect(toasts[0].source).toBe("bifrost");
    expect(toasts[0].message).toBe("Reconnecting...");
    expect(typeof toasts[0].id).toBe("string");
    expect(toasts[0].id.length).toBeGreaterThan(0);
  });

  it("dismissToast removes by id", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().addToast("error", "lifecycle", "Config invalid");
    const id = useCeremonyStore.getState().toasts[0].id;
    useCeremonyStore.getState().dismissToast(id);
    expect(useCeremonyStore.getState().toasts).toHaveLength(0);
  });

  it("dismissToast with unknown id is a no-op", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().addToast("warn", "vebond", "test");
    useCeremonyStore.getState().dismissToast("nonexistent-id");
    expect(useCeremonyStore.getState().toasts).toHaveLength(1);
  });
});

describe("ceremony store — addUserMessage", () => {
  beforeEach(async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({ chatHistory: [] });
  });

  it("pushes a user ChatMessage to chatHistory", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().addUserMessage("hello");
    const history = useCeremonyStore.getState().chatHistory;
    expect(history).toHaveLength(1);
    expect(history[0].role).toBe("user");
    expect(history[0].content).toBe("hello");
    expect(history[0].streaming).toBe(false);
    expect(history[0].timestamp).not.toBeNull();
  });

  it("appends multiple messages in order", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().addUserMessage("first");
    useCeremonyStore.getState().addUserMessage("second");
    const history = useCeremonyStore.getState().chatHistory;
    expect(history).toHaveLength(2);
    expect(history[0].content).toBe("first");
    expect(history[1].content).toBe("second");
  });
});

describe("ceremony store — setBifrostHealth", () => {
  it("updates bifrostStatus, endpoint, and latency", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setBifrostHealth("open", "http://example.com/v1", 120);
    const state = useCeremonyStore.getState();
    expect(state.bifrostStatus).toBe("open");
    expect(state.bifrostEndpoint).toBe("http://example.com/v1");
    expect(state.bifrostLatencyMs).toBe(120);
  });

  it("accepts null latency", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setBifrostHealth("closed", "", null);
    expect(useCeremonyStore.getState().bifrostLatencyMs).toBeNull();
  });
});

describe("ceremony store — appendAgentToken / finalizeAgentTurn", () => {
  beforeEach(async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({
      chatHistory: [],
      activeTurnId: null,
      activeTokenSequence: -1,
    });
  });

  it("appendAgentToken creates a new streaming message for a new turn", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({ activeTurnId: null });
    useCeremonyStore.getState().appendAgentToken("Hello", 0, "turn-001");
    const history = useCeremonyStore.getState().chatHistory;
    expect(history).toHaveLength(1);
    expect(history[0].role).toBe("assistant");
    expect(history[0].content).toBe("Hello");
    expect(history[0].streaming).toBe(true);
    expect(useCeremonyStore.getState().activeTurnId).toBe("turn-001");
  });

  it("appendAgentToken appends to existing streaming message", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({ activeTurnId: null });
    useCeremonyStore.getState().appendAgentToken("Hello", 0, "turn-002");
    useCeremonyStore.getState().appendAgentToken(" world", 1, "turn-002");
    const history = useCeremonyStore.getState().chatHistory;
    expect(history).toHaveLength(1);
    expect(history[0].content).toBe("Hello world");
  });

  it("finalizeAgentTurn marks streaming message as complete", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({ activeTurnId: null });
    useCeremonyStore.getState().appendAgentToken("Response", 0, "turn-003");
    useCeremonyStore.getState().finalizeAgentTurn("turn-003", "stop");
    const history = useCeremonyStore.getState().chatHistory;
    expect(history[0].streaming).toBe(false);
    expect(history[0].timestamp).not.toBeNull();
    expect(useCeremonyStore.getState().activeTurnId).toBeNull();
  });
});

describe("ceremony store — appendAgentToken / finalizeAgentTurn — real WS path (no explicit turnId)", () => {
  // These tests simulate the actual WS subscription wiring in connectWs:
  //   _wsClient.subscribe<AgentToken>("agent.token", (event) => {
  //       get().appendAgentToken(event.text_delta, event.sequence_id); // NO turnId
  //   });
  //   _wsClient.subscribe<AgentTurnComplete>("agent.turn_complete", (event) => {
  //       get().finalizeAgentTurn(event.turn_id, event.finish_reason); // backend UUID
  //   });
  // S-1 regression: finalizeAgentTurn must locate the message via activeTurnId,
  // not via the backend uuid, because AgentToken carries no turn_id field.

  beforeEach(async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({
      chatHistory: [],
      activeTurnId: null,
      activeTokenSequence: -1,
    });
  });

  it("appendAgentToken without explicit turnId creates a streaming message", async () => {
    // Reproduces the real WS subscription: no turnId argument passed
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().appendAgentToken("Hail", 0);
    const history = useCeremonyStore.getState().chatHistory;
    expect(history).toHaveLength(1);
    expect(history[0].role).toBe("assistant");
    expect(history[0].content).toBe("Hail");
    expect(history[0].streaming).toBe(true);
    // activeTurnId must be set to a non-null stable local ID
    expect(useCeremonyStore.getState().activeTurnId).not.toBeNull();
    expect(useCeremonyStore.getState().activeTurnId).toMatch(/^local-\d+-\d+$/);
  });

  it("finalizeAgentTurn with backend UUID finalizes the streaming message via activeTurnId", async () => {
    // S-1 regression: backend UUID on AgentTurnComplete !== local ID on the message.
    // finalizeAgentTurn must use activeTurnId (local) not the argument (backend UUID).
    const { useCeremonyStore } = await import("../src/store/ceremony");
    // Simulate WS token stream — no turnId arg
    useCeremonyStore.getState().appendAgentToken("The ", 0);
    useCeremonyStore.getState().appendAgentToken("raven ", 1);
    useCeremonyStore.getState().appendAgentToken("speaks.", 2);

    const beforeHistory = useCeremonyStore.getState().chatHistory;
    expect(beforeHistory).toHaveLength(1);
    expect(beforeHistory[0].content).toBe("The raven speaks.");
    expect(beforeHistory[0].streaming).toBe(true);

    // Simulate AgentTurnComplete with a backend UUID that does NOT match the local ID
    const backendUuid = "a3c72f1b-0000-4b2e-9f1e-deadbeef0001";
    useCeremonyStore.getState().finalizeAgentTurn(backendUuid, "stop");

    const afterHistory = useCeremonyStore.getState().chatHistory;
    // Message must now be finalized — streaming flag cleared, timestamp set
    expect(afterHistory[0].streaming).toBe(false);
    expect(afterHistory[0].timestamp).not.toBeNull();
    expect(useCeremonyStore.getState().activeTurnId).toBeNull();
    expect(useCeremonyStore.getState().activeTokenSequence).toBe(-1);
  });

  it("two consecutive turns assemble separate messages", async () => {
    // Verifies that activeTurnId is reset after finalize so a second turn starts fresh
    const { useCeremonyStore } = await import("../src/store/ceremony");

    // Turn 1
    useCeremonyStore.getState().appendAgentToken("First.", 0);
    const firstLocalId = useCeremonyStore.getState().activeTurnId;
    useCeremonyStore.getState().finalizeAgentTurn("backend-uuid-turn-1", "stop");

    // After finalize: activeTurnId must be null
    expect(useCeremonyStore.getState().activeTurnId).toBeNull();

    // Turn 2
    useCeremonyStore.getState().appendAgentToken("Second.", 0);
    const secondLocalId = useCeremonyStore.getState().activeTurnId;

    // Both turns have distinct local IDs
    expect(firstLocalId).not.toBeNull();
    expect(secondLocalId).not.toBeNull();
    expect(firstLocalId).not.toBe(secondLocalId);

    useCeremonyStore.getState().finalizeAgentTurn("backend-uuid-turn-2", "stop");

    const history = useCeremonyStore.getState().chatHistory;
    expect(history).toHaveLength(2);
    expect(history[0].content).toBe("First.");
    expect(history[0].streaming).toBe(false);
    expect(history[1].content).toBe("Second.");
    expect(history[1].streaming).toBe(false);
    expect(useCeremonyStore.getState().activeTurnId).toBeNull();
  });
});

describe("ceremony store — clearChatHistory", () => {
  it("clears history and resets turn state", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().addUserMessage("hi");
    useCeremonyStore.setState({ activeTurnId: "turn-x", activeTokenSequence: 5 });
    useCeremonyStore.getState().clearChatHistory();
    const state = useCeremonyStore.getState();
    expect(state.chatHistory).toHaveLength(0);
    expect(state.activeTurnId).toBeNull();
    expect(state.activeTokenSequence).toBe(-1);
  });
});

// ---------------------------------------------------------------------------
// Sjon state (v0.5)
// ---------------------------------------------------------------------------

describe("ceremony store — Sjon state (v0.5)", () => {
  beforeEach(async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({ sjonState: "idle" });
  });

  it("starts with sjonState 'idle'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    expect(useCeremonyStore.getState().sjonState).toBe("idle");
  });

  it("setSjonState transitions to 'capturing'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSjonState("capturing");
    expect(useCeremonyStore.getState().sjonState).toBe("capturing");
  });

  it("setSjonState transitions to 'encoding'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSjonState("encoding");
    expect(useCeremonyStore.getState().sjonState).toBe("encoding");
  });

  it("setSjonState transitions to 'failed'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSjonState("failed");
    expect(useCeremonyStore.getState().sjonState).toBe("failed");
  });

  it("setSjonState can transition back to 'idle' after 'encoding'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSjonState("encoding");
    useCeremonyStore.getState().setSjonState("idle");
    expect(useCeremonyStore.getState().sjonState).toBe("idle");
  });
});

// ---------------------------------------------------------------------------
// Sjon state — v0.5.1 continuous mode states
// ---------------------------------------------------------------------------

describe("ceremony store — Sjon state v0.5.1 continuous mode", () => {
  beforeEach(async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({ sjonState: "idle" });
  });

  it("setSjonState transitions to 'continuous_running'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSjonState("continuous_running");
    expect(useCeremonyStore.getState().sjonState).toBe("continuous_running");
  });

  it("setSjonState transitions to 'continuous_stopped'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSjonState("continuous_stopped");
    expect(useCeremonyStore.getState().sjonState).toBe("continuous_stopped");
  });

  it("setSjonState transitions to 'buffer_full'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSjonState("buffer_full");
    expect(useCeremonyStore.getState().sjonState).toBe("buffer_full");
  });

  it("full continuous lifecycle: idle -> continuous_running -> buffer_full -> continuous_stopped -> idle", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const transitions = [
      "idle",
      "continuous_running",
      "buffer_full",
      "continuous_running",
      "continuous_stopped",
      "idle",
    ] as const;
    for (const state of transitions) {
      useCeremonyStore.getState().setSjonState(state);
      expect(useCeremonyStore.getState().sjonState).toBe(state);
    }
  });
});

// ---------------------------------------------------------------------------
// Smidja tool call state — v0.6
// ---------------------------------------------------------------------------

describe("ceremony store — Smidja tool call state", () => {
  beforeEach(async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.setState({
      smidjaToolCallState: null,
      smidjaLastToolName: null,
      smidjaToolCallCount: 0,
    });
  });

  it("smidjaToolCallState starts as null", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    expect(useCeremonyStore.getState().smidjaToolCallState).toBeNull();
  });

  it("smidjaLastToolName starts as null", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    expect(useCeremonyStore.getState().smidjaLastToolName).toBeNull();
  });

  it("setSmidjaToolCallActivity sets state and tool name", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSmidjaToolCallActivity("started", "smidja.screenshot");
    const s = useCeremonyStore.getState();
    expect(s.smidjaToolCallState).toBe("started");
    expect(s.smidjaLastToolName).toBe("smidja.screenshot");
  });

  it("setSmidjaToolCallActivity increments count on 'started'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSmidjaToolCallActivity("started", "smidja.click");
    expect(useCeremonyStore.getState().smidjaToolCallCount).toBe(1);
    useCeremonyStore.getState().setSmidjaToolCallActivity("started", "smidja.hotkey");
    expect(useCeremonyStore.getState().smidjaToolCallCount).toBe(2);
  });

  it("setSmidjaToolCallActivity does not increment count on 'completed'", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSmidjaToolCallActivity("started", "smidja.click");
    useCeremonyStore.getState().setSmidjaToolCallActivity("completed", "smidja.click");
    expect(useCeremonyStore.getState().smidjaToolCallCount).toBe(1);
  });

  it("setSmidjaToolCallActivity transitions: started -> completed", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSmidjaToolCallActivity("started", "smidja.screenshot");
    useCeremonyStore.getState().setSmidjaToolCallActivity("completed", "smidja.screenshot");
    expect(useCeremonyStore.getState().smidjaToolCallState).toBe("completed");
  });

  it("setSmidjaToolCallActivity transitions: started -> failed", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    useCeremonyStore.getState().setSmidjaToolCallActivity("started", "smidja.vroid_open");
    useCeremonyStore.getState().setSmidjaToolCallActivity("failed", "smidja.vroid_open");
    expect(useCeremonyStore.getState().smidjaToolCallState).toBe("failed");
    expect(useCeremonyStore.getState().smidjaLastToolName).toBe("smidja.vroid_open");
  });
});
