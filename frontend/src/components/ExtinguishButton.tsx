/**
 * ExtinguishButton — the "Extinguish" shutdown action.
 *
 * Sends ExtinguishCommand to the backend via the ceremony store's sendCommand action.
 * Only enabled when lifecycle is active (tengsl, samraedur, recovering).
 *
 * Visual:
 *   - Idle (enabled): Varud (burnt sienna) fill, subdued
 *   - Hover: slightly brighter
 *   - Disabled: Hvila-grey, muted
 *
 * Per AESTHETIC.md: "the sound that recedes rather than arrives" — the visual
 * should mirror that quality. Not alarming; intentional closure.
 *
 * Note: ceremony_button_confirm (VebondConfig) is a v0.4.x feature.
 * In v0.4.0 the command is sent directly without a confirmation dialog.
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";

export function ExtinguishButton(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);
  const sendCommand = useCeremonyStore((s) => s.sendCommand);

  const isEnabled =
    lifecycleState === "tengsl" ||
    lifecycleState === "samraedur" ||
    lifecycleState === "recovering";

  const handleClick = (): void => {
    if (!isEnabled) return;
    sendCommand({ type: "extinguish" });
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
          ? "bg-varud text-text-primary hover:opacity-80 active:scale-95 cursor-pointer"
          : "bg-hvila text-text-ghost cursor-not-allowed opacity-50",
      ].join(" ")}
      aria-label="Extinguish the ceremony"
    >
      Extinguish
    </button>
  );
}
