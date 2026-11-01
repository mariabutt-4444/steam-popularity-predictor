/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        steam: {
          dark: '#171a21',
          navy: '#1b2838',
          blue: '#2a475e',
          accent: '#66c0f4',
          light: '#c7d5e0'
        }
      }
    },
  },
  plugins: [],
}
