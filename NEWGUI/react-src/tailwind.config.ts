import type { Config } from "tailwindcss";

/**
 * Premium dark mode token seti. Renkler PyQt6 temasından türetilmiştir;
 * YouTube kırmızısı = accent. İstersen sınıflarda doğrudan
 * `bg-[rgba(255,255,255,0.022)]` gibi arbitrary değerler de kullanabilirsin.
 */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#0a0a0c",  // ana içerik
          850: "#0a0a0d",  // pencere gövdesi
          800: "#0c0c10",  // başlık çubuğu
          750: "#141418",  // popover
        },
        accent: {
          DEFAULT: "#ff2233",
          light: "#ff5a68",
          dark: "#e0001a",
        },
        info: { DEFAULT: "#2d7bff", light: "#3d8bff", dark: "#1456d6" },
        ok: { DEFAULT: "#22c55e", light: "#4ade80" },
        line: "rgba(255,255,255,0.06)",
        "line-strong": "rgba(255,255,255,0.12)",
        glass: "rgba(255,255,255,0.022)",
        "glass-2": "rgba(255,255,255,0.04)",
      },
      fontFamily: {
        sora: ['"Sora"', "system-ui", "sans-serif"],
        sans: ['"Manrope"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        "accent-glow": "0 12px 36px -8px rgba(255,40,60,0.55), inset 0 1px 0 rgba(255,255,255,0.2)",
        "accent-glow-hover": "0 18px 48px -8px rgba(255,40,60,0.72), inset 0 1px 0 rgba(255,255,255,0.24)",
        card: "0 20px 44px -18px rgba(0,0,0,0.75)",
        pop: "0 20px 44px -14px rgba(0,0,0,0.75)",
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
      },
    },
  },
  plugins: [],
} satisfies Config;
