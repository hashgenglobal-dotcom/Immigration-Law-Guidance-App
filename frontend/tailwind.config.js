/** @type {import('tailwindcss').Config} */
/**
 * Palette "01. Subdued & Professional"
 * - Off-white #F5F5EF
 * - Muted gold #B69D74
 * - Navy #1F2839
 *
 * Token names (cream / sage / forest) kept for stable class names across the app.
 */
const cream = {
  50: '#FDFDFB',
  100: '#FAFAF7',
  200: '#F5F5EF',
  DEFAULT: '#F5F5EF',
  300: '#ECEBE4',
  400: '#E0DFD6',
}

const sage = {
  50: '#F7F3ED',
  100: '#EDE4D6',
  200: '#D9C9B0',
  300: '#C9B08A',
  400: '#B69D74',
  500: '#B69D74',
  DEFAULT: '#B69D74',
  600: '#9A8460',
  700: '#7E6B4E',
  800: '#63543D',
  900: '#4A3F2E',
}

const forest = {
  50: '#E8EAEE',
  100: '#C5CAD4',
  200: '#9AA3B3',
  300: '#6F7B92',
  400: '#4A5769',
  500: '#354252',
  600: '#2A3544',
  700: '#232D3A',
  800: '#1F2839',
  900: '#1F2839',
  DEFAULT: '#1F2839',
  950: '#151B27',
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
        primary: sage,
        navy: forest,
        gold: sage,
      },
      boxShadow: {
        card: '0 1px 3px rgb(31 40 57 / 0.06), 0 8px 24px rgb(31 40 57 / 0.05)',
        elevated: '0 4px 20px rgb(31 40 57 / 0.1), 0 1px 3px rgb(31 40 57 / 0.06)',
        'glow-gold': '0 4px 14px rgb(182 157 116 / 0.35), 0 1px 3px rgb(31 40 57 / 0.08)',
        'glow-gold-lg': '0 8px 28px rgb(182 157 116 / 0.45), 0 2px 8px rgb(31 40 57 / 0.1)',
      },
      transitionDuration: {
        400: '400ms',
      },
    },
  },
  plugins: [],
}
