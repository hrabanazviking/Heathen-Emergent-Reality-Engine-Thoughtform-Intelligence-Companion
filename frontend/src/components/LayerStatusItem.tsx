/**
 * LayerStatusItem — a single row in the LayerStatusPanel.
 *
 * Displays: colored dot (health) + layer name label + optional note.
 *
 * Dot colors (per AESTHETIC.md accent palette):
 *   "healthy"     -> Mal-green (#30a880)
 *   "active"      -> accent-dependent pulsing dot (used for Sjon capturing/encoding)
 *   "degraded"    -> Varud sienna (#c04020)
 *   "unavailable" -> Hvila-grey (#404850)
 *
 * Accent colors (for "active" and "healthy" states):
 *   undefined / "default" -> Mal-green (voice layers, Bifrost)
 *   "sjon"                -> Sjon-glow blue (#4080b0 / #60a8e0 glow) — L3 Vision
 *   "eld"                 -> Eld-amber (#c8860a / #e8a020 glow) — L5 Smidja / forge
 *
 * The "active" health value is a superset of "healthy" — it adds a pulse animation
 * so that the operator can see when the capture pipeline is in-flight.
 */

import React from "react";
import clsx from "clsx";

export type LayerHealth = "healthy" | "active" | "degraded" | "unavailable";
export type LayerAccent = "sjon" | "eld" | "default" | undefined;

interface LayerStatusItemProps {
  label: string;
  status: LayerHealth;
  /** Optional short note displayed after the label (e.g. "capturing" for Sjon pipeline). */
  note?: string;
  /**
   * Accent theme for the status dot.
   * "sjon"    — Sjon-glow blue (#4080b0 / #60a8e0 glow per AESTHETIC.md L3 token).
   * "eld"     — Eld-amber (#c8860a / #e8a020 glow per AESTHETIC.md forge/Smidja token).
   * "default" — Mal-green (standard for voice/connection layers).
   * undefined — falls back to "default".
   */
  accent?: LayerAccent;
}

export function LayerStatusItem({
  label,
  status,
  note,
  accent,
}: LayerStatusItemProps): React.ReactElement {
  // Determine base dot color class.
  // "active" uses the same base color as "healthy" but adds a pulse.
  const isSjon = accent === "sjon";
  const isEld = accent === "eld";

  const dotColor = clsx({
    // Healthy / active — color depends on accent
    "bg-mal-glow":  (status === "healthy" || status === "active") && !isSjon && !isEld,
    "bg-sjon-glow": (status === "healthy" || status === "active") && isSjon,
    "bg-eld-glow":  (status === "healthy" || status === "active") && isEld,
    // Degraded — always Varud sienna regardless of accent
    "bg-varud":     status === "degraded",
    // Unavailable — always Hvila-grey
    "bg-hvila":     status === "unavailable",
    // Pulse animation for the "active" state (tool call / capture in flight)
    "animate-pulse": status === "active",
  });

  return (
    <div className="flex items-center gap-2 text-body">
      {/* Status dot */}
      <span
        className={clsx("inline-block w-2 h-2 rounded-full shrink-0", dotColor)}
        aria-label={`${label}: ${status}`}
      />
      {/* Layer name */}
      <span className="text-text-secondary font-inter">{label}</span>
      {/* Optional note */}
      {note && (
        <span className="text-text-ghost text-small ml-auto">{note}</span>
      )}
    </div>
  );
}
