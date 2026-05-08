import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vite configuration for the HERETIC Eldahus frontend.
//
// Dev server: http://localhost:5173
// Backend WebSocket: ws://localhost:8642/ws  (Python heretic serve)
//
// The proxy rewrites /ws -> ws://localhost:8642/ws so that the React app
// can connect to the backend without CORS issues during development.
// In Tauri (v0.4.1), the WebView connects directly to localhost:8642
// and this proxy is not used.

// TAURI v0.4.1 NOTE:
// When running under `cargo tauri dev`, Tauri injects TAURI_DEV_HOST into the
// environment and expects the Vite dev server on port 1420 with strictPort.
// When running standalone (`npm run dev`), the original 5173 port is used and
// TAURI_DEV_HOST is undefined, so the proxy remains active for WebSocket.
const isTauriDev = !!process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [react()],

  // Tauri requires clearScreen:false so its own output is not suppressed.
  clearScreen: false,

  server: {
    // Tauri 2.x convention: port 1420 for the dev WebView.
    // Standalone npm dev: falls back to 5173 if 1420 is taken and strictPort is false.
    port: isTauriDev ? 1420 : 5173,
    strictPort: isTauriDev,
    // Tauri injects the dev host; use it when present, otherwise localhost only.
    host: process.env.TAURI_DEV_HOST || false,
    proxy: isTauriDev
      ? undefined // In Tauri dev mode, WebView connects directly to localhost:8642.
      : {
          // Proxy WebSocket upgrade requests to the Python backend (standalone dev)
          "/ws": {
            target: "ws://localhost:8642",
            ws: true,
            changeOrigin: false,
            rewrite: (path) => path,
          },
        },
  },

  test: {
    // Vitest configuration — co-located with vite config per Vitest convention
    environment: "jsdom",
    globals: true,
    setupFiles: [],
    include: ["tests/**/*.{test,spec}.{ts,tsx}"],
    coverage: {
      reporter: ["text", "json", "html"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx"],
    },
  },
});
