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
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";

export function LifecyclePulse(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);

  const isActive =
    lifecycleState === "tengsl" ||
    lifecycleState === "samraedur" ||
    lifecycleState === "recovering";

  const isDormant = lifecycleState === "hvild" || lifecycleState === "slokna";

  // Ring border color: Eld-amber when active, Hvila-grey when dormant/resting
  const ringBorderClass = isActive
    ? "border-eld"
    : isDormant
      ? "border-hvila"
      : "border-hvila"; // kynding, config_error — still Hvila

  // Breathing animation only when actively connected
  const animationClass = isActive ? "animate-ring-breathe" : "";

  // Outer glow shadow — only when active
  const glowStyle: React.CSSProperties = isActive
    ? { boxShadow: "0 0 32px 4px rgba(200, 134, 10, 0.35), 0 0 8px 1px rgba(200, 134, 10, 0.2)" }
    : { boxShadow: "none" };

  return (
    <div
      className={[
        "absolute inset-0 rounded-full border-2",
        "transition-colors duration-700",
        ringBorderClass,
        animationClass,
      ].join(" ")}
      style={glowStyle}
      aria-hidden="true"
    />
  );
}
