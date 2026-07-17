/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        vortex: {
          primary: '#2563eb', // Blue 600
          secondary: '#1e40af', // Blue 800
          accent: '#3b82f6', // Blue 500
          dark: '#0f172a', // Slate 900
        }
      }
    },
  },
  plugins: [],
}
