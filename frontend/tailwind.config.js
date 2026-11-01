/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ocean: {
          950: '#030d1a',
          900: '#071b33',
          850: '#0a2540',
          800: '#0e3153',
          700: '#144673',
          600: '#1d5e96',
          500: '#2779bd',
          400: '#38a0e8',
        }
      }
    },
  },
  plugins: [],
}
