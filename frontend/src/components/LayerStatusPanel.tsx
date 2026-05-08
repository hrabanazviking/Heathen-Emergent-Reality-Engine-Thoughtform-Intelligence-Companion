/**
 * LayerStatusPanel — left-panel layer health display.
 *
 * Shows the health status of each HERETIC layer:
 *   - L1 Bifrost (agent connection)
 *   - L2 Tunga (TTS / voice-out)
 *   - L2 Hlust (STT / voice-in)
 *   - L3 Sjon (screen capture vision — v0.5)
 *   - L5.5 Smidja (Brúarhönd hand — v0.6)
 *
 * Each layer entry is a LayerStatusItem component with a colored dot indicator.
 * Sjon uses the Sjon-glow blue accent (#4080b0 / #60a8e0 glow).
 * Smidja uses the Eld-amber accent (#c8860a / #e8a020 glow) for "fire/forge" semantics.
 * A pulsing animation fires when a tool call is active.
 * "failed" maps to Varud sienna (degraded). "idle" is dim (unavailable or at rest).
 *
 * Data sources: useCeremonyStore — bifrostStatus, tungaState, hlustState, sjonState,
 *   smidjaToolCallState, smidjaLastToolName.
 */

import React from "react";
import { LayerStatusItem } from "./LayerStatusItem";
import { useCeremonyStore } from "../store/ceremony";
import type { SjonState, SenseToolCallState } from "../types/ipc";

/** Map a Sjon pipeline state to a LayerStatusItem health value. */
function sjonStateToHealth(
  state: SjonState
): "healthy" | "active" | "degraded" | "unavailable" {
  switch (state) {
    case "capturing":
    case "encoding":
      // Actively processing a frame — show as active (pulsing).
      return "active";
    case "continuous_running":
    case "buffer_full":
      // Continuous mode active — the eye keeps watching.
      // buffer_full is informational: buffer is saturated but operational.
      // Use "active" so the Sjon-glow blue accent pulses continuously.
      return "active";
    case "idle":
    case "continuous_stopped":
      // Available and waiting, or continuous task cleanly stopped.
      return "healthy";
    case "failed":
      // Last capture or encode attempt failed.
      return "degraded";
    default:
      return "unavailable";
  }
}

/** Map a Smidja tool call state to a LayerStatusItem health value. */
function smidjaStateToHealth(
  state: SenseToolCallState | null
): "healthy" | "active" | "degraded" | "unavailable" {
  switch (state) {
    case "started":
      // Tool call in flight — pulse the Eld-amber indicator
      return "active";
    case "completed":
      // Last call succeeded — show healthy at rest
      return "healthy";
    case "failed":
      // Last call failed — show degraded until the next successful call
      return "degraded";
    case null:
    default:
      // No tool calls yet (or sense disabled) — dim unavailable
      return "unavailable";
  }
}

export function LayerStatusPanel(): React.ReactElement {
  const bifrostStatus = useCeremonyStore((s) => s.bifrostStatus);
  const tungaState = useCeremonyStore((s) => s.tungaState);
  const hlustState = useCeremonyStore((s) => s.hlustState);
  const sjonState = useCeremonyStore((s) => s.sjonState);
  const smidjaToolCallState = useCeremonyStore((s) => s.smidjaToolCallState);
  const smidjaLastToolName = useCeremonyStore((s) => s.smidjaLastToolName);

  // Derive a note for the Sjon row so operators see the current pipeline state.
  // v0.5.1: "continuous" badge when the background task is running.
  const sjonNote =
    sjonState === "continuous_running"
      ? "continuous"
      : sjonState === "buffer_full"
      ? "continuous"
      : sjonState === "capturing"
      ? "capturing"
      : sjonState === "encoding"
      ? "encoding"
      : sjonState === "failed"
      ? "failed"
      : undefined;

  // Derive a note for the Smidja row — show abbreviated tool name when active
  const smidjaNote =
    smidjaToolCallState === "started" && smidjaLastToolName
      ? smidjaLastToolName.replace("smidja.", "")
      : smidjaToolCallState === "failed"
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
      {/*
        Smidja row — L5.5 the agent's first hand (Brúarhönd).
        Uses Eld-amber accent per AESTHETIC.md (#c8860a / #e8a020 glow).
        "active" = tool call in flight (pulse); "completed" = healthy at rest;
        "failed" = last call failed; null/unavailable = sense not enabled.
      */}
      <LayerStatusItem
        label="Smidja"
        status={smidjaStateToHealth(smidjaToolCallState)}
        note={smidjaNote}
        accent="eld"
      />
    </section>
  );
}
