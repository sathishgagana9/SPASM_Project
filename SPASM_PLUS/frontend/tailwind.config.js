/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        lab: {
          bg: "#0a0e14",
          panel: "#111721",
          border: "#1f2937",
          accent: "#22d3ee",
          warn: "#f59e0b",
          danger: "#f43f5e",
          ok: "#34d399",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
};
