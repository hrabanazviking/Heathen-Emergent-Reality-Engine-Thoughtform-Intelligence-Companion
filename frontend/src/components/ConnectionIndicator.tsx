/**
 * ConnectionIndicator — WebSocket transport health indicator (bottom bar).
 *
 * Shows the state of the WebSocket connection between the browser frontend
 * and the Python backend (NOT the Bifrost agent connection — that is in
 * LayerStatusPanel). This is the ws://localhost:8642/ws transport layer.
 *
 * States and colors:
 *   "connected":    Mal-green dot, "Connected" label
 *   "connecting":   Eld-amber pulsing dot, "Connecting..." label
 *   "disconnected": Hvila-grey dot, "Disconnected" label
 *   "error":        Varud dot, "Connection error" label
 *
 * Forge implements full behavior. This scaffold renders the status text.
 */

import React from "react";
import clsx from "clsx";
import { useCeremonyStore } from "../store/ceremony";

export function ConnectionIndicator(): React.ReactElement {
  const connectionStatus = useCeremonyStore((s) => s.connectionStatus);

  const dotClass = clsx("inline-block w-2 h-2 rounded-full mr-2", {
    "bg-mal-glow":      connectionStatus === "connected",
    "bg-eld animate-pulse": connectionStatus === "connecting",
    "bg-hvila":         connectionStatus === "disconnected",
    "bg-varud":         connectionStatus === "error",
  });

  const labels: Record<typeof connectionStatus, string> = {
    connected:    "Connected",
    connecting:   "Connecting...",
    disconnected: "Disconnected",
    error:        "Connection error",
  };

  return (
    <div
      className="flex items-center text-small text-text-secondary"
      aria-live="polite"
      aria-label={`Backend WebSocket: ${labels[connectionStatus]}`}
    >
      <span className={dotClass} aria-hidden="true" />
      <span>{labels[connectionStatus]}</span>
      {/* TODO Forge: add a retry button when status === "disconnected" or "error" */}
    </div>
  );
}
