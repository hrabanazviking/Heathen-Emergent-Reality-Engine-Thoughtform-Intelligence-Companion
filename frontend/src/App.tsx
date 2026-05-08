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
 *
 * All leaf components are stubs in this scaffold. Forge implements the bodies.
 * The structural layout is declared here so Forge has clear boundaries.
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
    // Forge implements connectWs/disconnectWs — these will throw NotImplementedError
    // in the scaffold. Once implemented, the app connects on mount and cleans up on unmount.
    //
    // connectWs().catch((err) => console.warn("[HERETIC] WS connect:", err));
    // return () => { disconnectWs().catch(() => {}); };
    //
    // TODO Forge: uncomment the above once connectWs is implemented.
    void connectWs;
    void disconnectWs;
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
