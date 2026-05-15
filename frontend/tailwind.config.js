/** @type {import('tailwindcss').Config} */
/**
 * Palette "16. Dark & Earthy" (exact swatches):
 * - Cream #F3EEED
 * - Sage #567470
 * - Forest #0C2924
 */
const cream = {
  50: '#FBFAF9',
  100: '#F7F4F2',
  200: '#F3EEED',
  DEFAULT: '#F3EEED',
  300: '#E8E3E0',
  400: '#DCD6D3',
}

const sage = {
  50: '#EEF3F2',
  100: '#D9E3E1',
  200: '#B5C9C5',
  300: '#89A39E',
  400: '#6D8782',
  500: '#567470',
  DEFAULT: '#567470',
  600: '#4A635F',
  700: '#3F5350',
  800: '#354441',
  900: '#2C3836',
}

const forest = {
  50: '#E9F1EF',
  100: '#C5D9D4',
  200: '#9CBAB2',
  300: '#729A90',
  400: '#4A7A6F',
  500: '#2F5A52',
  600: '#1A453E',
  700: '#123731',
  800: '#0E2F2A',
  900: '#0C2924',
  DEFAULT: '#0C2924',
  950: '#061614',
}

module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        cream,
        sage,
        forest,
        /** Alias for components that still expect `primary` */
        primary: sage,
      },
    },
  },
  plugins: [],
}
