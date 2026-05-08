/**
 * Component tests — Vitest + React Testing Library
 *
 * Run with: npm test  (from the frontend/ directory)
 */

import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Minimal active test — confirms the testing setup works
// ---------------------------------------------------------------------------

describe("scaffold smoke test", () => {
  it("React renders a div", () => {
    const { container } = render(<div data-testid="smoke">HERETIC</div>);
    expect(container.querySelector("[data-testid='smoke']")).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// Store reset helper
// ---------------------------------------------------------------------------

async function resetStore() {
  const { useCeremonyStore } = await import("../src/store/ceremony");
  useCeremonyStore.setState({
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
  });
}

// ---------------------------------------------------------------------------
// ConnectionIndicator
// ---------------------------------------------------------------------------

describe("ConnectionIndicator", () => {
  beforeEach(() => resetStore());

  it("shows 'Disconnected' when connectionStatus is disconnected", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ConnectionIndicator } = await import("../src/components/ConnectionIndicator");
    useCeremonyStore.setState({ connectionStatus: "disconnected" });
    render(<ConnectionIndicator />);
    expect(screen.getByText("Disconnected")).toBeTruthy();
  });

  it("shows 'Connected' when connectionStatus is connected", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ConnectionIndicator } = await import("../src/components/ConnectionIndicator");
    useCeremonyStore.setState({ connectionStatus: "connected" });
    render(<ConnectionIndicator />);
    expect(screen.getByText("Connected")).toBeTruthy();
  });

  it("shows 'Connection error' when connectionStatus is error", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ConnectionIndicator } = await import("../src/components/ConnectionIndicator");
    useCeremonyStore.setState({ connectionStatus: "error" });
    render(<ConnectionIndicator />);
    expect(screen.getByText("Connection error")).toBeTruthy();
  });

  it("shows 'Connecting...' when connectionStatus is connecting", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ConnectionIndicator } = await import("../src/components/ConnectionIndicator");
    useCeremonyStore.setState({ connectionStatus: "connecting" });
    render(<ConnectionIndicator />);
    expect(screen.getByText("Connecting...")).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// LayerStatusItem
// ---------------------------------------------------------------------------

describe("LayerStatusItem", () => {
  it("renders the label", async () => {
    const { LayerStatusItem } = await import("../src/components/LayerStatusItem");
    render(<LayerStatusItem label="Bifrost" status="healthy" />);
    expect(screen.getByText("Bifrost")).toBeTruthy();
  });

  it("renders optional note when provided", async () => {
    const { LayerStatusItem } = await import("../src/components/LayerStatusItem");
    render(<LayerStatusItem label="Sjon" status="unavailable" note="v0.5" />);
    expect(screen.getByText("v0.5")).toBeTruthy();
  });

  it("renders healthy dot aria-label", async () => {
    const { LayerStatusItem } = await import("../src/components/LayerStatusItem");
    render(<LayerStatusItem label="Bifrost" status="healthy" />);
    expect(screen.getByLabelText("Bifrost: healthy")).toBeTruthy();
  });

  it("renders degraded dot aria-label", async () => {
    const { LayerStatusItem } = await import("../src/components/LayerStatusItem");
    render(<LayerStatusItem label="Bifrost" status="degraded" />);
    expect(screen.getByLabelText("Bifrost: degraded")).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// LightButton
// ---------------------------------------------------------------------------

describe("LightButton", () => {
  beforeEach(() => resetStore());

  it("is enabled when lifecycle is hvild", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { LightButton } = await import("../src/components/LightButton");
    useCeremonyStore.setState({ lifecycleState: "hvild" });
    render(<LightButton />);
    const btn = screen.getByRole("button", { name: /light the candle/i });
    expect((btn as HTMLButtonElement).disabled).toBe(false);
  });

  it("is disabled when lifecycle is samraedur", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { LightButton } = await import("../src/components/LightButton");
    useCeremonyStore.setState({ lifecycleState: "samraedur" });
    render(<LightButton />);
    const btn = screen.getByRole("button", { name: /light the candle/i });
    expect((btn as HTMLButtonElement).disabled).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// ExtinguishButton
// ---------------------------------------------------------------------------

describe("ExtinguishButton", () => {
  beforeEach(() => resetStore());

  it("is enabled when lifecycle is samraedur", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ExtinguishButton } = await import("../src/components/ExtinguishButton");
    useCeremonyStore.setState({ lifecycleState: "samraedur" });
    render(<ExtinguishButton />);
    const btn = screen.getByRole("button", { name: /extinguish/i });
    expect((btn as HTMLButtonElement).disabled).toBe(false);
  });

  it("is disabled when lifecycle is hvild", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ExtinguishButton } = await import("../src/components/ExtinguishButton");
    useCeremonyStore.setState({ lifecycleState: "hvild" });
    render(<ExtinguishButton />);
    const btn = screen.getByRole("button", { name: /extinguish/i });
    expect((btn as HTMLButtonElement).disabled).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// ChatHistory
// ---------------------------------------------------------------------------

describe("ChatHistory", () => {
  beforeEach(() => resetStore());

  it("shows placeholder when chatHistory is empty", async () => {
    const { ChatHistory } = await import("../src/components/ChatHistory");
    render(<ChatHistory />);
    // The placeholder text from our implementation
    expect(screen.getByText(/Light the candle to begin/i)).toBeTruthy();
  });

  it("renders user message", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ChatHistory } = await import("../src/components/ChatHistory");
    useCeremonyStore.setState({
      chatHistory: [{
        id: "user-1",
        role: "user",
        content: "Hello there",
        streaming: false,
        timestamp: new Date().toISOString(),
      }],
    });
    render(<ChatHistory />);
    expect(screen.getByText("Hello there")).toBeTruthy();
  });

  it("renders assistant message with streaming cursor when streaming=true", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ChatHistory } = await import("../src/components/ChatHistory");
    useCeremonyStore.setState({
      chatHistory: [{
        id: "assistant-turn-1",
        role: "assistant",
        content: "In progress...",
        streaming: true,
        timestamp: null,
      }],
    });
    const { container } = render(<ChatHistory />);
    expect(screen.getByText("In progress...")).toBeTruthy();
    // The streaming cursor span is aria-hidden, check it exists in the DOM
    const cursors = container.querySelectorAll("[aria-hidden='true']");
    expect(cursors.length).toBeGreaterThan(0);
  });
});

// ---------------------------------------------------------------------------
// ToastSystem
// ---------------------------------------------------------------------------

describe("ToastSystem", () => {
  beforeEach(() => resetStore());

  it("renders nothing when toasts is empty", async () => {
    const { ToastSystem } = await import("../src/components/ToastSystem");
    const { container } = render(<ToastSystem />);
    // Empty fragment renders nothing visible
    expect(container.firstChild).toBeFalsy();
  });

  it("renders a warn toast", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ToastSystem } = await import("../src/components/ToastSystem");
    useCeremonyStore.getState().addToast("warn", "bifrost", "Reconnecting...");
    render(<ToastSystem />);
    expect(screen.getByText("Reconnecting...")).toBeTruthy();
    expect(screen.getByText("bifrost")).toBeTruthy();
  });

  it("dismisses toast on button click", async () => {
    const { useCeremonyStore } = await import("../src/store/ceremony");
    const { ToastSystem } = await import("../src/components/ToastSystem");
    useCeremonyStore.getState().addToast("error", "lifecycle", "Config invalid");
    render(<ToastSystem />);
    expect(screen.getByText("Config invalid")).toBeTruthy();

    const dismissBtn = screen.getByRole("button", { name: /dismiss/i });
    fireEvent.click(dismissBtn);
    expect(useCeremonyStore.getState().toasts).toHaveLength(0);
  });
});
