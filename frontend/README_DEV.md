# HERETIC Frontend — Developer Guide

**Last updated:** 2026-05-07
**Scope:** L4 Vebond / Eldahus — React frontend for the Summoning Circle
**Stack:** Vite 5 + React 18 + TypeScript 5.4 + Tailwind CSS 3.4 + Zustand 4.5

---

## Prerequisites

- Node.js v22 LTS (`node --version` should print `v22.x.x`)
- npm 10+ (ships with Node 22)
- Python backend running (`heretic serve`) or not — the frontend can start in
  scaffold mode without a live backend (components show placeholder state)

---

## Install

From the `frontend/` directory:

```
npm install
```

This installs all dependencies declared in `package.json`. No global installs required.

---

## Run in development mode

```
npm run dev
```

Opens the Vite dev server at `http://localhost:5173`. The proxy in `vite.config.ts`
forwards `/ws` requests to `ws://localhost:8642/ws` (the Python backend). If the
backend is not running, the frontend loads but the WebSocket connection shows "disconnected."

To run the Python backend first:

```
pip install heretic[serve]
heretic serve
```

Then open the browser at `http://localhost:5173`.

---

## Run tests

```
npm test
```

Runs all Vitest tests in `tests/`. Most tests are skip-marked during the scaffold phase.
The active tests confirm:
- The testing setup works (scaffold smoke test)
- `parseProtocolEvent()` handles valid and invalid JSON correctly
- The Zustand store imports without error

Once Forge implements the component bodies and WsClient, tests are activated by
removing `describe.skip` / `it.skip` decorators.

---

## Type checking

```
npm run typecheck
```

Runs `tsc --noEmit` against all TypeScript in `src/` and `tests/`. Strict mode is
enforced (`strict: true` in `tsconfig.json`). Fix all type errors before committing.

---

## Build for production

```
npm run build
```

Produces a `dist/` directory with the compiled and bundled frontend. This is what
the Tauri shell (v0.4.1) will serve via WebView. The output is static HTML + JS + CSS.

---

## Directory structure

```
frontend/
  index.html            — HTML entry point (Google Fonts + root div)
  package.json          — npm manifest
  vite.config.ts        — Vite + Vitest config (port 5173, /ws proxy)
  tsconfig.json         — TypeScript strict config
  tailwind.config.js    — Norse color tokens + animation keyframes
  postcss.config.js     — Tailwind + autoprefixer
  README_DEV.md         — this file
  src/
    main.tsx            — React entry point
    App.tsx             — root component tree
    types/
      ipc.ts            — TypeScript types mirroring Python protocol.py
    api/
      ws-client.ts      — WebSocket client (skeleton)
    store/
      ceremony.ts       — Zustand ceremony state store
    components/
      SummoningCircle.tsx, LifecyclePulse.tsx, CenterCrest.tsx
      LayerStatusPanel.tsx, LayerStatusItem.tsx, SenseTogglePanel.tsx
      ChatPanel.tsx, ChatHistory.tsx, ChatInput.tsx
      LightButton.tsx, ExtinguishButton.tsx, ConnectionIndicator.tsx
      ToastSystem.tsx
    styles/
      theme.css         — CSS custom properties (Norse color tokens)
      index.css         — Tailwind directives + theme.css import
  tests/
    components.test.tsx — component tests (mostly skipped in scaffold)
    ws-client.test.ts   — WsClient tests (partially active)
    ceremony-store.test.ts — store tests (partially active)
```

---

## Color tokens

All tokens come from `docs/vision/AESTHETIC.md` and are defined in both
`tailwind.config.js` (as Tailwind utilities) and `src/styles/theme.css` (as CSS vars).

| Token         | Tailwind class        | Hex       | Role                          |
|---------------|-----------------------|-----------|-------------------------------|
| void          | `bg-void`             | `#0a0c10` | Deepest background            |
| structure     | `bg-structure`        | `#111418` | Panels, sidebars              |
| surface       | `bg-surface`          | `#1a1e25` | Cards, inputs                 |
| raised        | `bg-raised`           | `#232830` | Tooltips, modals              |
| text-primary  | `text-text-primary`   | `#e8dfc8` | Main text (warm off-white)    |
| text-secondary| `text-text-secondary` | `#8a8070` | Labels, captions              |
| text-ghost    | `text-text-ghost`     | `#4a4540` | Inactive, disabled            |
| eld           | `bg-eld` / `text-eld` | `#c8860a` | Primary accent (amber-gold)   |
| eld-glow      | `bg-eld-glow`         | `#e8a020` | Eld hover / glow variant      |
| sjon          | `bg-sjon`             | `#4080b0` | Vision accent (blue-silver)   |
| sjon-glow     | `bg-sjon-glow`        | `#60a8e0` | Sjon glow variant             |
| mal           | `bg-mal`              | `#1a6050` | Voice accent (teal-green)     |
| mal-glow      | `bg-mal-glow`         | `#30a880` | Mal glow / active voice       |
| varud         | `bg-varud`            | `#c04020` | Warning / attention           |
| hvila         | `bg-hvila`            | `#404850` | Dormant / resting state       |

---

## IPC protocol

The WebSocket protocol is documented in `docs/architecture/IPC_PROTOCOL.md`.
TypeScript types are in `src/types/ipc.ts`. Python types are in `src/heretic/vebond/protocol.py`.
The three files must remain in sync — any change to the schema requires updating all three.

---

## Contributing

Follow the Mythic Engineering protocol documented in `MYTHIC_ENGINEERING.md`.
Norse aesthetic rules: `docs/vision/AESTHETIC.md`.
No emoji in code or docs.
No absolute paths.
Type hints everywhere.
