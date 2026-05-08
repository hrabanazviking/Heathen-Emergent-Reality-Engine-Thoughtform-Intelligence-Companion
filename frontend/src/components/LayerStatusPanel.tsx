/**
 * LayerStatusPanel — left-panel layer health display.
 *
 * Shows the health status of each HERETIC layer:
 *   - L1 Bifrost (agent connection)
 *   - L2 Tunga (TTS / voice-out)
 *   - L2 Hlust (STT / voice-in)
 *   - L3 Sjon (vision — deferred to v0.5)
 *
 * Each layer entry is a LayerStatusItem component with a colored dot indicator
 * (Eld = healthy, Varud = degraded, Hvila = idle/unavailable) and a label.
 *
 * Data sources: useCeremonyStore — bifrostStatus, tungaState, hlustState.
 *
 * Forge implements the full panel. This scaffold renders a labeled placeholder.
 */

import React from "react";
import { LayerStatusItem } from "./LayerStatusItem";
import { useCeremonyStore } from "../store/ceremony";

export function LayerStatusPanel(): React.ReactElement {
  const bifrostStatus = useCeremonyStore((s) => s.bifrostStatus);
  const tungaState = useCeremonyStore((s) => s.tungaState);
  const hlustState = useCeremonyStore((s) => s.hlustState);

  return (
    <section className="flex flex-col gap-2 p-4">
      <h2 className="text-small font-cinzel text-text-secondary uppercase tracking-wider">
        Layers
      </h2>

      {/* TODO Forge: map bifrostStatus / tungaState / hlustState to health indicators */}
      <LayerStatusItem label="Bifrost" status={bifrostStatus === "open" ? "healthy" : "degraded"} />
      <LayerStatusItem label="Tunga" status={tungaState === "idle" || tungaState === "speaking" ? "healthy" : "degraded"} />
      <LayerStatusItem label="Hlust" status={hlustState === "idle" || hlustState === "listening" ? "healthy" : "degraded"} />
      <LayerStatusItem label="Sjon" status="unavailable" note="v0.5" />
    </section>
  );
}
