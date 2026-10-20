import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        void: "#080808",
        absolute: "#000000",
        charcoal: "#171617",
        smoke: "#262525",
        graphite: "#393939",
        bone: "#fcfcfc",
        linen: "#f3efef",
        ash: "#d4d2d2",
        pebble: "#b5b2b2",
        iron: "#525252",
        arterial: "#fe1e34",
        crimson: "#ff0000",
        space: {
          canvas: "#000000",
          fg: "#f0f0fa",
          secondary: "#545457",
          separator: "#404040",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-playfair)", "Georgia", "serif"],
        "d-din": ["var(--font-d-din)", "sans-serif"],
        "d-din-bold": ["var(--font-d-din-bold)", "sans-serif"],
      },
      borderRadius: {
        nav: "3px",
        card: "8px",
        panel: "14.4px",
      },
      boxShadow: {
        glass: "rgba(255, 255, 255, 0.15) 0px 1px 3px 0px inset",
      },
    },
  },
  plugins: [],
};

export default config;
