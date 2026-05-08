/**
 * ChatInput — text entry field for user messages.
 *
 * Sends SendMessageCommand via the ceremony store's sendCommand action.
 * Disabled when lifecycle is not "samraedur" or "tengsl", or when an agent turn
 * is in progress (activeTurnId is not null).
 *
 * When Hlust is active (hlustState === "listening" or "transcribing"), shows a
 * visual cue indicating the agent is listening via voice.
 *
 * Keyboard: Enter sends (Shift+Enter inserts newline).
 */

import React, { useState } from "react";
import { useCeremonyStore } from "../store/ceremony";

export function ChatInput(): React.ReactElement {
  const [text, setText] = useState("");

  const lifecycleState = useCeremonyStore((s) => s.lifecycleState);
  const activeTurnId = useCeremonyStore((s) => s.activeTurnId);
  const hlustState = useCeremonyStore((s) => s.hlustState);
  const addUserMessage = useCeremonyStore((s) => s.addUserMessage);
  const sendCommand = useCeremonyStore((s) => s.sendCommand);

  const isListening = hlustState === "listening" || hlustState === "transcribing";
  const canSend =
    (lifecycleState === "samraedur" || lifecycleState === "tengsl") &&
    activeTurnId === null &&
    text.trim().length > 0;

  const handleSubmit = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!canSend) return;
    const trimmed = text.trim();
    addUserMessage(trimmed);
    setText("");
    sendCommand({ type: "send_message", text: trimmed });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as React.FormEvent);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 p-3">
      {/* Voice listening indicator */}
      {isListening && (
        <div
          className="shrink-0 w-3 h-3 rounded-full bg-mal-glow animate-listen"
          aria-label="Listening via voice"
        />
      )}

      <textarea
        className={[
          "flex-1 resize-none bg-surface border border-raised rounded-xl",
          "text-text-primary text-body placeholder:text-text-ghost",
          "px-3 py-2 focus:outline-none focus:border-eld",
          "disabled:opacity-50 disabled:cursor-not-allowed",
        ].join(" ")}
        placeholder={
          isListening
            ? "Listening..."
            : lifecycleState === "hvild" || lifecycleState === "kynding"
              ? "Light the candle to begin"
              : "Enter your message..."
        }
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={2}
        disabled={lifecycleState !== "samraedur" && lifecycleState !== "tengsl"}
        aria-label="Message input"
      />

      <button
        type="submit"
        disabled={!canSend}
        className={[
          "shrink-0 px-4 py-2 rounded-xl font-inter text-small",
          "bg-eld text-void font-semibold",
          "disabled:opacity-40 disabled:cursor-not-allowed",
          "hover:bg-eld-glow transition-colors",
        ].join(" ")}
      >
        Send
      </button>
    </form>
  );
}
