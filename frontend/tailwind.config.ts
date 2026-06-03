import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // MonitorMBG brand palette
        brand: {
          50: "#eef7ff",
          100: "#d9edff",
          200: "#bce0ff",
          300: "#8eccff",
          400: "#59afff",
          500: "#338dff",
          600: "#1a6df5",
          700: "#1357e1",
          800: "#1647b6",
          900: "#183f8f",
          950: "#142857",
        },
        // Severity colors
        severity: {
          low: "#22c55e",
          medium: "#f59e0b",
          high: "#f97316",
          critical: "#ef4444",
        },
        // Dashboard surface colors (dark mode first)
        surface: {
          DEFAULT: "#0f1117",
          raised: "#1a1d27",
          overlay: "#252833",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        lg: "0.75rem",
        md: "0.5rem",
        sm: "0.375rem",
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 5px rgba(51, 141, 255, 0.3)" },
          "50%": { boxShadow: "0 0 20px rgba(51, 141, 255, 0.6)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
