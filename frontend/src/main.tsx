/**
 * HERETIC frontend — React entry point
 *
 * Mounts the App component tree into the #root div defined in index.html.
 * React 18 concurrent mode is used (createRoot).
 *
 * Global styles (Tailwind base + Norse theme CSS variables) are imported here.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error(
    "[HERETIC] Could not find #root element. Check index.html — " +
    "the root div is required for the React app to mount."
  );
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
