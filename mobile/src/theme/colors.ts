/**
 * Palette "01. Subdued & Professional"
 * - Off-white #F5F5EF
 * - Muted gold #B69D74
 * - Navy #1F2839
 */
export const colors = {
  cream: '#F5F5EF',
  creamMuted: '#FAFAF7',
  gold: '#B69D74',
  goldLight: '#D9C9B0',
  goldDark: '#9A8460',
  navy: '#1F2839',
  navyMuted: '#2A3544',
  /** Legacy aliases used across components */
  sage: '#B69D74',
  sageLight: '#D9C9B0',
  forest: '#1F2839',
  forestMuted: '#2A3544',
  primary: '#B69D74',
  primaryDark: '#1F2839',
  primaryLight: '#C9B08A',
  background: '#F5F5EF',
  surface: '#FFFFFF',
  border: '#E0DFD6',
  text: '#1F2839',
  textSecondary: '#4A5769',
  textMuted: '#6F7B92',
  disclaimerBg: '#F7F3ED',
  disclaimerBorder: '#D9C9B0',
  disclaimerText: '#1F2839',
  riskLowBg: '#16A34A',
  riskLowText: '#FFFFFF',
  riskLowBorder: '#15803D',
  riskMediumBg: '#FACC15',
  riskMediumText: '#422006',
  riskMediumBorder: '#CA8A04',
  riskHighBg: '#DC2626',
  riskHighText: '#FFFFFF',
  riskHighBorder: '#B91C1C',
  dangerBg: '#F7F3ED',
  white: '#FFFFFF',
  onPrimary: '#F5F5EF',
  onNavy: '#F5F5EF',
} as const

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const

export const typography = {
  title: 28,
  heading: 22,
  subheading: 18,
  body: 16,
  small: 14,
  caption: 12,
} as const

export const radii = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  full: 999,
} as const
