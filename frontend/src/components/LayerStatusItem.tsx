/**
 * LayerStatusItem — a single row in the LayerStatusPanel.
 *
 * Displays: colored dot (health) + layer name label + optional note.
 *
 * Dot colors (per AESTHETIC.md accent palette):
 *   "healthy"     -> Mal-green (#30a880)
 *   "degraded"    -> Varud (#c04020)
 *   "unavailable" -> Hvila-grey (#404850)
 *
 * Forge implements the full visual. This scaffold renders a text row.
 */

import React from "react";
import clsx from "clsx";

export type LayerHealth = "healthy" | "degraded" | "unavailable";

interface LayerStatusItemProps {
  label: string;
  status: LayerHealth;
  /** Optional short note displayed after the label (e.g. "v0.5" for deferred layers). */
  note?: string;
}

export function LayerStatusItem({
  label,
  status,
  note,
}: LayerStatusItemProps): React.ReactElement {
  const dotColor = clsx({
    "bg-mal-glow":  status === "healthy",
    "bg-varud":     status === "degraded",
    "bg-hvila":     status === "unavailable",
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
      {/* TODO Forge: add hover tooltip with detailed status info */}
    </div>
  );
}
