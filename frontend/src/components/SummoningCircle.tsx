/**
 * SummoningCircle — the visual heart of the Eldahus UI.
 *
 * The primary ceremony indicator: a ring that breathes with lifecycle state.
 * Contains LifecyclePulse (the animated ring) and CenterCrest (the sigil).
 *
 * Visual behavior (per AESTHETIC.md motion language):
 *   - Hvild / Kynding:  Hvila-grey ring, still or barely perceptible breath
 *   - Tengsl / Samraedur: Eld-amber ring, slow 4s sinusoidal breathing pulse
 *   - Recovering:       Eld-amber ring with a "flickering" modifier
 *   - Slokna:           Ring dims from Eld back to Hvila-grey over 1.8s
 *
 * Forge implements all visual behavior. This scaffold returns a placeholder.
 */

import React from "react";
import { LifecyclePulse } from "./LifecyclePulse";
import { CenterCrest } from "./CenterCrest";
import { useCeremonyStore } from "../store/ceremony";

export function SummoningCircle(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);

  return (
    <div
      className="relative flex items-center justify-center"
      role="img"
      aria-label={`Summoning Circle — ceremony state: ${lifecycleState}`}
    >
      {/* TODO Forge: implement ring animation, Eld glow, Hvila dormant state */}
      <div className="ring-ceremony flex items-center justify-center">
        <LifecyclePulse />
        <CenterCrest />
      </div>
    </div>
  );
}
