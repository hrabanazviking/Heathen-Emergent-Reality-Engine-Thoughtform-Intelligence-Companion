/**
 * LightButton — the "Light the Candle" primary action.
 *
 * Sends LightCommand to the backend. Only enabled when lifecycleState is
 * "kynding" (READY sub-state — Bifrost not yet open).
 *
 * Visual:
 *   - Idle (enabled): Eld-amber fill, Cinzel font
 *   - Hover: Eld-glow brighten, subtle scale
 *   - Pressed: Scale down slightly (organic, not mechanical)
 *   - Disabled: Hvila-grey, muted
 *
 * Per AESTHETIC.md: the transition "should feel like fire catching" (1.8s bloom).
 *
 * Forge implements full behavior. This scaffold renders a functional placeholder.
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";

export function LightButton(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);

  const isEnabled = lifecycleState === "kynding" || lifecycleState === "hvild";

  const handleClick = (): void => {
    if (!isEnabled) return;
    // TODO Forge: call wsClient.send({ type: "light" }) via store or context
    throw new Error(
      "Forge will implement: send LightCommand via WsClient: { type: 'light' }"
    );
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
