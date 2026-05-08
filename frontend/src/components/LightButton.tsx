/**
 * LightButton — the "Light the Candle" primary action.
 *
 * Sends LightCommand to the backend via the ceremony store's sendCommand action.
 * Only enabled when lifecycleState is "hvild" or "kynding".
 *
 * Visual:
 *   - Idle (enabled): Eld-amber fill, Cinzel font
 *   - Hover: Eld-glow brighten, subtle scale
 *   - Pressed: Scale down slightly (organic, not mechanical)
 *   - Disabled: Hvila-grey, muted
 *
 * Per AESTHETIC.md: the transition "should feel like fire catching" (1.8s bloom).
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";

export function LightButton(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);
  const sendCommand = useCeremonyStore((s) => s.sendCommand);

  const isEnabled = lifecycleState === "kynding" || lifecycleState === "hvild";

  const handleClick = (): void => {
    if (!isEnabled) return;
    sendCommand({ type: "light" });
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={!isEnabled}
      className={[
        "px-6 py-2 rounded-xl2 font-cinzel tracking-wider",
        "transition-all duration-200",
        isEnabled
          ? "bg-eld text-void hover:bg-eld-glow active:scale-95 cursor-pointer"
          : "bg-hvila text-text-ghost cursor-not-allowed opacity-50",
      ].join(" ")}
      aria-label="Light the candle — begin the ceremony"
    >
      Light
    </button>
  );
}
