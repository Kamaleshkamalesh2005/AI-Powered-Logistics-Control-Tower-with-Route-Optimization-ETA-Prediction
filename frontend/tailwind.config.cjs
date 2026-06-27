/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      boxShadow: {
        glow: "0 0 0 1px rgba(45, 212, 191, 0.18), 0 24px 80px rgba(8, 17, 31, 0.45)",
      },
      colors: {
        ink: {
          950: "#04111d",
          900: "#071425",
          800: "#0c1d33",
        },
        signal: {
          50: "#ecfdf5",
          400: "#34d399",
          500: "#10b981",
          600: "#059669",
        },
        amber: {
          400: "#fbbf24",
        },
      },
    },
  },
  plugins: [],
};