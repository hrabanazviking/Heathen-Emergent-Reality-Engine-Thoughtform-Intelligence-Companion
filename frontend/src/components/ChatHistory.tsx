/**
 * ChatHistory — scrollable list of conversation messages.
 *
 * Displays ChatMessage entries from the ceremony store's chatHistory array.
 * Streaming assistant messages show a cursor while streaming=true.
 * Auto-scrolls to the bottom when new tokens arrive.
 *
 * Message styling:
 *   - User messages: right-aligned, Surface background
 *   - Assistant messages: left-aligned, Structure background, Eld cursor during streaming
 *   - System messages: centered, ghost text
 *
 * Forge implements the full component. This scaffold renders a placeholder.
 */

import React from "react";
import { useCeremonyStore } from "../store/ceremony";

export function ChatHistory(): React.ReactElement {
  const chatHistory = useCeremonyStore((s) => s.chatHistory);

  return (
    <div
      className="h-full overflow-y-auto p-4 flex flex-col gap-3"
      role="log"
      aria-label="Conversation history"
      aria-live="polite"
    >
      {chatHistory.length === 0 ? (
        <p className="text-text-ghost text-small text-center mt-8">
          The ceremony awaits. Light the candle to begin.
        </p>
      ) : (
        chatHistory.map((msg) => (
          <div
            key={msg.id}
            className={[
              "rounded-xl2 px-3 py-2 max-w-xs text-body",
              msg.role === "user"
                ? "self-end bg-surface text-text-primary"
                : msg.role === "assistant"
                  ? "self-start bg-structure text-text-primary"
                  : "self-center text-text-ghost text-small",
            ].join(" ")}
          >
            {/* TODO Forge: implement streaming cursor, markdown rendering, timestamps */}
            {msg.content}
            {msg.streaming && (
              <span className="inline-block w-1 h-3 bg-eld ml-1 animate-pulse" aria-hidden="true" />
            )}
          </div>
        ))
      )}
    </div>
  );
}
