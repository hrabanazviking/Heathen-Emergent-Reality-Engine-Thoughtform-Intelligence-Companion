/**
 * LayerStatusPanel — left-panel layer health display.
 *
 * Shows the health status of each HERETIC layer:
 *   - L1 Bifrost (agent connection)
 *   - L2 Tunga (TTS / voice-out)
 *   - L2 Hlust (STT / voice-in)
 *   - L3 Sjon (screen capture vision — v0.5)
 *
 * Each layer entry is a LayerStatusItem component with a colored dot indicator.
 * Sjon uses the Sjon-glow blue accent (#4080b0 / #60a8e0 glow) to distinguish
 * it from the Mal-green voice layers and the Eld-amber connection indicator.
 * A pulsing animation fires when state is "capturing" or "encoding".
 * "failed" maps to Varud sienna (degraded). "idle" is dim (unavailable or at rest).
 *
 * Data sources: useCeremonyStore — bifrostStatus, tungaState, hlustState, sjonState.
 */

import React from "react";
import { LayerStatusItem } from "./LayerStatusItem";
import { useCeremonyStore } from "../store/ceremony";
import type { SjonState } from "../types/ipc";

/** Map a Sjon pipeline state to a LayerStatusItem health value. */
function sjonStateToHealth(
  state: SjonState
): "healthy" | "active" | "degraded" | "unavailable" {
  switch (state) {
    case "capturing":
    case "encoding":
      // Actively processing a frame — show as active (pulsing).
      return "active";
    case "idle":
      // Available and waiting for the next snapshot() call.
      return "healthy";
    case "failed":
      // Last capture or encode attempt failed.
      return "degraded";
    default:
      return "unavailable";
  }
}

export function LayerStatusPanel(): React.ReactElement {
  const bifrostStatus = useCeremonyStore((s) => s.bifrostStatus);
  const tungaState = useCeremonyStore((s) => s.tungaState);
  const hlustState = useCeremonyStore((s) => s.hlustState);
  const sjonState = useCeremonyStore((s) => s.sjonState);

  // Derive a note for the Sjon row so operators see the current pipeline state.
  const sjonNote =
    sjonState === "capturing"
      ? "capturing"
      : sjonState === "encoding"
      ? "encoding"
      : sjonState === "failed"
      ? "failed"
      : undefined;

  return (
    <section className="flex flex-col gap-2 p-4">
      <h2 className="text-small font-cinzel text-text-secondary uppercase tracking-wider">
        Layers
      </h2>

      <LayerStatusItem
        label="Bifrost"
        status={bifrostStatus === "open" ? "healthy" : "degraded"}
      />
      <LayerStatusItem
        label="Tunga"
        status={
          tungaState === "idle" || tungaState === "speaking" ? "healthy" : "degraded"
        }
      />
      <LayerStatusItem
        label="Hlust"
        status={
          hlustState === "idle" || hlustState === "listening" ? "healthy" : "degraded"
        }
      />
      {/*
        Sjon row — L3 Vision.
        Uses the sjonStateToHealth mapper so the indicator responds to capture
        lifecycle events pushed by the server via sjon.activity WebSocket events.
        Color accent is Sjon-glow blue per AESTHETIC.md L3 token (#4080b0).
        The "active" health value drives a blue-tinted pulse animation.
      */}
      <LayerStatusItem
        label="Sjon"
        status={sjonStateToHealth(sjonState)}
        note={sjonNote}
        accent="sjon"
      />
    </section>
  );
}
