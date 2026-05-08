/**
 * ToastSystem — error and warning toast notification overlay.
 *
 * Renders all active toasts from the ceremony store. Positioned fixed,
 * top-right, z-index above all other content.
 *
 * Per AESTHETIC.md motion language (error states):
 *   "A single, slow, dull-orange pulse — once, not repeating — and then a
 *   return to resting state with the error message present. Errors should
 *   not perform urgency. They should be present and readable."
 *
 * Toast behavior:
 *   - Appears with animate-error-once (single pulse per AESTHETIC.md)
 *   - Auto-dismissed after 6 seconds for "warn" level
 *   - Remains until manually dismissed for "error" level
 *   - Dismiss button visible on hover
 *
 * Forge implements auto-dismiss timer and full visual. This scaffold renders
 * the list structure with basic toast cards.
 */

import React from "react";
import clsx from "clsx";
import { useCeremonyStore, type Toast } from "../store/ceremony";

function ToastCard({ toast }: { toast: Toast }): React.ReactElement {
  const dismissToast = useCeremonyStore((s) => s.dismissToast);

  return (
    <div
      role="alert"
      aria-live={toast.level === "error" ? "assertive" : "polite"}
      className={clsx(
        "flex items-start gap-3 p-3 rounded-xl2 shadow-lg",
        "text-body font-inter max-w-xs animate-error-once",
        toast.level === "error"
          ? "bg-varud text-text-primary"
          : "bg-raised border border-varud text-text-secondary"
      )}
    >
      <div className="flex-1">
        <div className="text-small font-semibold capitalize">{toast.level}</div>
        <div className="text-small text-text-ghost">{toast.source}</div>
        <div className="mt-1">{toast.message}</div>
      </div>
      <button
        type="button"
        onClick={() => dismissToast(toast.id)}
        className="shrink-0 text-text-ghost hover:text-text-primary transition-colors"
        aria-label="Dismiss notification"
      >
        x
      </button>
    </div>
  );
}

export function ToastSystem(): React.ReactElement {
  const toasts = useCeremonyStore((s) => s.toasts);

  if (toasts.length === 0) return <></>;

  return (
    <div
      className="fixed top-4 right-4 z-50 flex flex-col gap-2"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} />
      ))}
      {/* TODO Forge: implement auto-dismiss timer (6s for warn, persistent for error) */}
    </div>
  );
}
