/**
 * SenseTogglePanel — left-panel sense enable/disable display.
 *
 * In v0.4.0: READ-ONLY display of which senses are enabled. Toggles are not
 * functional — the backend emits ErrorEvent (level='warn') if ToggleSenseCommand
 * is sent. See IPC_PROTOCOL.md §Commands §toggle_sense for the v0.4.0 limitation.
 *
 * In v0.4.x: Toggles will be interactive and will send ToggleSenseCommand.
 *
 * Per CEREMONY.md, sense health is pushed via LayerStatusPanel (Bifrost/Tunga/Hlust).
 * This panel displays the configured sense availability from heretic.yaml
 * (reflected via capability flags or a future /status REST endpoint).
 *
 * Forge implements the full panel. This scaffold renders a labeled placeholder.
 */

import React from "react";

export function SenseTogglePanel(): React.ReactElement {
  return (
    <section className="flex flex-col gap-2 p-4 mt-auto">
      <h2 className="text-small font-cinzel text-text-secondary uppercase tracking-wider">
        Senses
      </h2>
      {/* TODO Forge: render a list of senses from config/capability data */}
      {/* TODO Forge: in v0.4.0 show status indicators only (not interactive toggles) */}
      {/* TODO Forge: in v0.4.x wire ToggleSenseCommand */}
      <p className="text-small text-text-ghost">
        Sense toggles — read-only in v0.4.0
      </p>
    </section>
  );
}
