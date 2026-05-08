/**
 * ExtinguishButton — the "Extinguish" shutdown action.
 *
 * Sends ExtinguishCommand to the backend. Only enabled when lifecycle is active
 * (tengsl, samraedur, recovering).
 *
 * If VebondConfig.ceremony_button_confirm is true (default), the button shows
 * a confirmation step before sending — the backend does not confirm again.
 *
 * Visual:
 *   - Idle (enabled): Varud (burnt sienna) fill, subdued
 *   - Hover: slightly brighter
 *   - Disabled: Hvila-grey, muted
 *
 * Per AESTHETIC.md: "the sound that recedes rather than arrives" — the visual
 * should mirror that quality. Not alarming; intentional closure.
 *
 * Forge implements full behavior including confirmation dialog. This scaffold
 * renders a functional placeholder without confirmation.
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";

export function ExtinguishButton(): React.ReactElement {
  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);

  const isEnabled =
    lifecycleState === "tengsl" ||
    lifecycleState === "samraedur" ||
    lifecycleState === "recovering";

  const handleClick = (): void => {
    if (!isEnabled) return;
    // TODO Forge: show confirmation dialog if ceremony_button_confirm is true
    // TODO Forge: call wsClient.send({ type: "extinguish" }) via store or context
    throw new Error(
      "Forge will implement: show confirmation if needed, then send ExtinguishCommand: { type: 'extinguish' }"
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
          ? "bg-varud text-text-primary hover:opacity-80 active:scale-95 cursor-pointer"
          : "bg-hvila text-text-ghost cursor-not-allowed opacity-50",
      ].join(" ")}
      aria-label="Extinguish the ceremony"
    >
      Extinguish
    </button>
  );
}
