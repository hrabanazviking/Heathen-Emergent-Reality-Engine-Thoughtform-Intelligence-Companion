/**
 * LifecyclePulse — the animated ring overlay for the Summoning Circle.
 *
 * Drives the slow 4s sinusoidal breathing animation (animate-ring-breathe from
 * tailwind.config.js) when the ceremony is active. Transitions color between
 * Hvila-grey (dormant) and Eld-amber (active) based on lifecycle state.
 *
 * Per AESTHETIC.md: "approximately 4 seconds for a full breath cycle.
 * Easing: sinusoidal (ease-in-out). Amplitude: 4-8% luminance change and
 * 1-2px scale change."
 *
 * Forge implements all animation logic. This scaffold returns a placeholder.
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";

export function LifecyclePulse(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);

  const isActive =
    lifecycleState === "tengsl" ||
    lifecycleState === "samraedur" ||
    lifecycleState === "recovering";

  return (
    <div
      className={[
        "absolute inset-0 rounded-full",
        isActive ? "animate-ring-breathe" : "",
        /* TODO Forge: apply glow-eld when active, border-hvila when dormant */
      ].join(" ")}
      aria-hidden="true"
    >
      {/* TODO Forge: implement breathing animation, glow effects, color transitions */}
    </div>
  );
}
