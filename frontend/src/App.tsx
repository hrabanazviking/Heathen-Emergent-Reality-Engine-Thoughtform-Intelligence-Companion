/**
 * HERETIC App — root component tree for the Summoning Circle UI
 *
 * Component tree (per TASK_HERETIC_v0.4_SUMMONING_CIRCLE.md §4):
 *
 *   <App>
 *     <ToastSystem />
 *     <div class="ceremony-layout">
 *       <SidePanel orientation="left">
 *         <LayerStatusPanel />
 *         <SenseTogglePanel />
 *       </SidePanel>
 *       <main>
 *         <SummoningCircle>
 *           <LifecyclePulse />
 *           <CenterCrest />
 *         </SummoningCircle>
 *         <BottomBar>
 *           <LightButton />
 *           <ExtinguishButton />
 *           <ConnectionIndicator />
 *         </BottomBar>
 *       </main>
 *       <SidePanel orientation="right">
 *         <ChatPanel>
 *           <ChatHistory />
 *           <ChatInput />
 *         </ChatPanel>
 *       </SidePanel>
 *     </div>
 *   </App>
 */

import React, { useEffect } from "react";
import { ToastSystem } from "./components/ToastSystem";
import { SummoningCircle } from "./components/SummoningCircle";
import { LayerStatusPanel } from "./components/LayerStatusPanel";
import { SenseTogglePanel } from "./components/SenseTogglePanel";
import { ChatPanel } from "./components/ChatPanel";
import { LightButton } from "./components/LightButton";
import { ExtinguishButton } from "./components/ExtinguishButton";
import { ConnectionIndicator } from "./components/ConnectionIndicator";
import { useCeremonyStore } from "./store/ceremony";

function App(): React.ReactElement {
  const connectWs = useCeremonyStore((s) => s.connectWs);
  const disconnectWs = useCeremonyStore((s) => s.disconnectWs);

  useEffect(() => {
    // Connect to the backend WebSocket on mount.
    // WsClient handles reconnect backoff automatically — no polling needed here.
    connectWs().catch((err: unknown) => {
      console.warn("[HERETIC] WS connect error on mount:", err);
    });

    return () => {
      disconnectWs().catch(() => {
        // Silence disconnect errors on unmount — we are shutting down
      });
    };
  }, [connectWs, disconnectWs]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-void text-text-primary">
      {/* Toast notifications — rendered above all other content */}
      <ToastSystem />

      {/* Left panel: layer status + sense toggles */}
      <aside className="flex flex-col w-80 shrink-0 bg-structure border-r border-raised">
        <LayerStatusPanel />
        <SenseTogglePanel />
      </aside>

      {/* Center: summoning circle + bottom bar */}
      <main className="flex flex-col flex-1 items-center justify-between py-6 bg-void">
        <div className="flex-1 flex items-center justify-center">
          <SummoningCircle />
        </div>

        {/* Bottom bar: light / extinguish / connection indicator */}
        <footer className="flex items-center gap-4 h-16">
          <LightButton />
          <ExtinguishButton />
          <ConnectionIndicator />
        </footer>
      </main>

      {/* Right panel: chat */}
      <aside className="flex flex-col w-80 shrink-0 bg-structure border-l border-raised">
        <ChatPanel />
      </aside>
    </div>
  );
}

export default App;
