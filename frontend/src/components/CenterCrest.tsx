/**
 * CenterCrest — the sigil at the center of the Summoning Circle.
 *
 * Displays the Eld-flame icon or a ceremonial mark appropriate to the current
 * lifecycle state. Per AESTHETIC.md iconography: "a simple, single-stroke
 * stylized flame, not a clipart candle."
 *
 * States:
 *   - Hvild: dim, barely visible mark
 *   - Kynding: kindling glow emerging
 *   - Tengsl / Samraedur: full Eld amber flame, glowing
 *   - Recovering: flickering variant
 *   - Slokna / Extinguished: dimming out
 *
 * Forge implements the SVG flame icon and state-dependent styling.
 * This scaffold returns a placeholder text glyph.
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";

export function CenterCrest(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);

  return (
    <div
      className="absolute flex items-center justify-center text-text-ghost font-cinzel"
      aria-label={`Ceremony state: ${lifecycleState}`}
    >
      {/* TODO Forge: replace with SVG flame icon per AESTHETIC.md iconography */}
      <span className="text-2xl select-none">*</span>
    </div>
  );
}
