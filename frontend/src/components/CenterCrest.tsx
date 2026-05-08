/**
 * CenterCrest — the sigil at the center of the Summoning Circle.
 *
 * Displays a stylized single-stroke flame icon (per AESTHETIC.md iconography:
 * "a simple, single-stroke stylized flame, not a clipart candle.")
 *
 * States:
 *   - Hvild: dim, barely visible mark (text-text-ghost)
 *   - Kynding: kindling glow emerging (text-hvila)
 *   - Tengsl / Samraedur: full Eld amber flame, glowing (text-eld)
 *   - Recovering: flickering (text-eld with animate-listen as flutter)
 *   - Slokna: dimming out (text-hvila transitioning)
 *   - config_error: Varud orange-red
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";
import type { LifecycleState } from "../types/ipc";

function getFlameClass(state: LifecycleState): string {
  switch (state) {
    case "samraedur":
    case "tengsl":
      return "text-eld-glow";
    case "recovering":
      return "text-eld animate-pulse";
    case "kynding":
      return "text-hvila";
    case "config_error":
      return "text-varud";
    case "slokna":
    case "hvild":
    default:
      return "text-text-ghost";
  }
}

/** Inline SVG: single-stroke stylized flame (per AESTHETIC.md). */
function FlameIcon({ className }: { className?: string }): React.ReactElement {
  return (
    <svg
      viewBox="0 0 24 32"
      width="48"
      height="64"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {/*
        A simple flame path: starts at base, rises, curves inward at the top.
        Single continuous stroke per AESTHETIC.md aesthetic intent.
      */}
      <path d="M12 30 C6 30 3 24 3 18 C3 12 7 8 10 5 C10 9 12 11 12 11 C12 11 14 8 14 4 C18 8 21 13 21 18 C21 24 18 30 12 30 Z" />
      {/* Inner tendril — gives life to the flame */}
      <path d="M12 24 C10 22 10 18 12 15 C14 18 14 22 12 24 Z" />
    </svg>
  );
}

export function CenterCrest(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);
  const flameClass = getFlameClass(lifecycleState);

  return (
    <div
      className={[
        "absolute flex items-center justify-center",
        "transition-colors duration-700",
        flameClass,
      ].join(" ")}
      aria-label={`Ceremony state: ${lifecycleState}`}
    >
      <FlameIcon />
    </div>
  );
}
