/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],

  // Dark mode is the identity of HERETIC — not a preference. It is always on.
  // Per AESTHETIC.md: "Dark mode is not a preference setting; it is the identity."
  darkMode: "class",

  theme: {
    extend: {
      // ------------------------------------------------------------------
      // Norse color tokens — exact hex values from AESTHETIC.md
      // All token names use Norse True Names (transliterated, lowercase).
      // ------------------------------------------------------------------
      colors: {
        // Background layers (deepest to surface)
        void:      "#0a0c10",  // Void — near-black with cool blue-grey undertone
        structure: "#111418",  // Structure — panels, sidebars, container backgrounds
        surface:   "#1a1e25",  // Surface — card backgrounds, input fields
        raised:    "#232830",  // Raised — tooltips, dropdowns, modals

        // Text
        "text-primary":   "#e8dfc8",  // Primary text — off-white with warm gold tinge
        "text-secondary": "#8a8070",  // Secondary text — muted warm grey
        "text-ghost":     "#4a4540",  // Ghost / inactive — barely perceptible

        // Accent colors — the bioluminescence
        // Eld (fire / primary accent)
        eld: {
          DEFAULT: "#c8860a",  // Deep amber-gold — candlelight
          glow:    "#e8a020",  // Brighter glow variant for active/hover states
        },
        // Sjon-glow (vision / perception accent)
        sjon: {
          DEFAULT: "#4080b0",  // Cool blue-silver — moonlight on water
          glow:    "#60a8e0",  // Brighter glow variant
        },
        // Mal-green (voice accent — aurora thread)
        mal: {
          DEFAULT: "#1a6050",  // Deep teal-green
          glow:    "#30a880",  // Brighter glow variant
        },
        // Varud (warning / attention — dying embers)
        varud: "#c04020",
        // Hvila-grey (dormant / resting state)
        hvila: "#404850",
      },

      // ------------------------------------------------------------------
      // Typography — AESTHETIC.md font stack
      // Google Fonts are loaded in index.html; these families just reference them.
      // ------------------------------------------------------------------
      fontFamily: {
        // Display / headings — ceremonial, serious
        cinzel:    ["Cinzel", "Georgia", "serif"],
        // Body / reading — disappears behind the aesthetic
        inter:     ["Inter", "system-ui", "sans-serif"],
        // Code / monospace — precise, purposeful
        jetbrains: ["JetBrains Mono", "Fira Code", "monospace"],
      },

      // ------------------------------------------------------------------
      // Animation — breathing, not blinking (per AESTHETIC.md motion language)
      // ------------------------------------------------------------------
      keyframes: {
        // The summoning ring breathing pulse — slow, sinusoidal, ~4s cycle
        breathe: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%":      { opacity: "0.85", transform: "scale(0.985)" },
        },
        // Connection bloom — fire catching, 1.5-2s
        "connection-bloom": {
          "0%":   { opacity: "0.3" },
          "100%": { opacity: "1" },
        },
        // Single slow error pulse — once, not repeating
        "error-pulse": {
          "0%":   { opacity: "1" },
          "50%":  { opacity: "0.6" },
          "100%": { opacity: "1" },
        },
        // Listening inward pull — receptive, contracting
        "listen-pull": {
          "0%, 100%": { transform: "scale(1)" },
          "50%":      { transform: "scale(0.94)" },
        },
      },
      animation: {
        // Summoning ring — 4s sinusoidal, infinite, ease-in-out
        "ring-breathe": "breathe 4s ease-in-out infinite",
        // Connection state transition — 1.8s, once
        "bloom": "connection-bloom 1.8s ease-out forwards",
        // Error notification — once, slow
        "error-once": "error-pulse 1.2s ease-in-out",
        // Listening indicator — 2s, infinite while Hlust is listening
        "listen": "listen-pull 2s ease-in-out infinite",
      },

      // ------------------------------------------------------------------
      // Spacing / sizing extensions for the ritual layout
      // ------------------------------------------------------------------
      spacing: {
        "128": "32rem",  // Large summoning ring diameter
        "96":  "24rem",
        "72":  "18rem",
      },

      // ------------------------------------------------------------------
      // Border radius — rounded containers per AESTHETIC.md reference aesthetics
      // ------------------------------------------------------------------
      borderRadius: {
        "xl2": "1rem",
        "xl3": "1.5rem",
      },
    },
  },

  plugins: [],
};
