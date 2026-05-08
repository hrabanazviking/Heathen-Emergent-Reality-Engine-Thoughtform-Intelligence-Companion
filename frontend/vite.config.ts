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

export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    strictPort: false,
    proxy: {
      // Proxy WebSocket upgrade requests to the Python backend
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
