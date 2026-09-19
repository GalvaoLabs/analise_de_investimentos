import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          app: "#0B0E14",
          panel: "#111622",
          panel2: "#0D1119",
          input: "#1E293B",
        },
        border: {
          DEFAULT: "#1E293B",
          strong: "#334155",
        },
        text: {
          primary: "#F8FAFC",
          secondary: "#94A3B8",
          muted: "#64748B",
        },
        accent: {
          DEFAULT: "#38BDF8",
          strong: "#0284C7",
          hover: "#0369A1",
        },
        success: "#4ADE80",
        danger: "#F87171",
        warning: "#FACC15",
      },
      borderRadius: {
        card: "12px",
      },
    },
  },
  plugins: [],
};

export default config;
