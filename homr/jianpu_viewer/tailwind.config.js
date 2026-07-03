/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
        },
        dark: {
          900: '#1e1e1e',
          800: '#252526',
        },
      },
      fontFamily: {
        sans: ['Noto Sans', 'sans-serif'],
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
