/** @type {import('tailwindcss').Config} */
import tailwindcssAnimate from "tailwindcss-animate";

export default {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        background: "hsl(240 30% 4%)",
        foreground: "hsl(0 0% 98%)",
        card: "hsl(240 30% 6%)",
        "card-foreground": "hsl(0 0% 98%)",
        primary: "hsl(199 89% 48%)",
        "primary-foreground": "hsl(0 0% 100%)",
        secondary: "hsl(240 20% 14%)",
        "secondary-foreground": "hsl(0 0% 98%)",
        muted: "hsl(240 15% 14%)",
        "muted-foreground": "hsl(240 10% 65%)",
        accent: "hsl(199 89% 48%)",
        "accent-foreground": "hsl(0 0% 100%)",
        destructive: "hsl(0 72% 51%)",
        "destructive-foreground": "hsl(0 0% 98%)",
        border: "hsl(240 20% 16%)",
        input: "hsl(240 20% 16%)",
        ring: "hsl(199 89% 48%)",
      },
      borderRadius: {
        lg: "0.75rem",
        md: "0.5rem",
        sm: "0.375rem",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px -2px hsl(199 89% 48% / 0.5)",
        "glow-lg": "0 0 40px -4px hsl(199 89% 48% / 0.6)",
        "glow-soft": "0 0 30px -8px hsl(199 89% 48% / 0.35)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.6", filter: "blur(8px)" },
          "50%": { opacity: "1", filter: "blur(12px)" },
        },
        spinSlow: {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(2000%)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out",
        pulseGlow: "pulseGlow 2.4s ease-in-out infinite",
        "spin-slow": "spinSlow 8s linear infinite",
        scan: "scan 4s linear infinite",
      },
    },
  },
  plugins: [tailwindcssAnimate],
};
