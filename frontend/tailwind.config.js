// Design tokens: a restrained dark palette; gold is reserved for primary actions.
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0B0D0F", sidebar: "#101316", surface: "#15191D", surface2: "#1B2025", line: "#293038",
        ink: "#F0F2F4", ink2: "#929BA5", muted: "#68727D",
        accent: "#D6A84F", ok: "#42B883", warn: "#E6A23C", bad: "#E45D5D", info: "#6599D8",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: { DEFAULT: "4px", md: "6px" },
    },
  },
  plugins: [],
};
