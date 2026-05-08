/**
 * ChatPanel — right-panel conversation display and input.
 *
 * Composes ChatHistory (scrollable message list) and ChatInput (text entry).
 * When Hlust is active, ChatInput also shows a voice cue indicator.
 *
 * Forge implements the full panel. This scaffold renders the structural shell.
 */

import React from "react";
import { ChatHistory } from "./ChatHistory";
import { ChatInput } from "./ChatInput";

export function ChatPanel(): React.ReactElement {
  return (
    <div className="flex flex-col h-full">
      <header className="px-4 py-3 border-b border-raised">
        <h2 className="text-small font-cinzel text-text-secondary uppercase tracking-wider">
          Communion
        </h2>
      </header>

      {/* Message history — grows to fill available space */}
      <div className="flex-1 overflow-hidden">
        <ChatHistory />
      </div>

      {/* Input — anchored to bottom */}
      <div className="border-t border-raised">
        <ChatInput />
      </div>
    </div>
  );
}
