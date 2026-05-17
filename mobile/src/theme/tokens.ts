/**
 * Authoritative Legal — design tokens
 */
export const palette = {
  parchment: '#F4F1EA',
  parchmentTint: '#E8E4DB',
  backgroundBase: '#F4F1EA',
  brandNavy: '#1F2839',
  brandBronze: '#9C7B5C',
  brandBronzeLight: '#B89A7D',
  brandBronzeDark: '#7A6048',
  /** Light bronze wash — motto pills, subtle highlights on navy */
  bronzeTint: '#F0EBE3',
  surfaceWhite: '#FFFFFF',
  textPrimary: '#111620',
  textMuted: '#5C667A',
  textSecondary: '#434D5C',
  border: '#D4C4B0',
  onNavy: '#F4F0E6',
} as const

export const radii = {
  card: 12,
  modal: 12,
  button: 8,
  sm: 8,
  md: 12,
  lg: 16,
  full: 999,
} as const

export const layout = {
  minTouchTarget: 48,
} as const

/** 0 4px 6px -1px rgba(31, 40, 57, 0.08) */
export const shadows = {
  soft: {
    shadowColor: '#1F2839',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
} as const

/** Matches web `.card-standard` — white surface, 12px radius, navy-tinted shadow */
export const cardStandard = {
  backgroundColor: palette.surfaceWhite,
  borderRadius: radii.card,
  ...shadows.soft,
} as const

/** Trust Center legal notice — pale amber warning surface */
export const warningNotice = {
  background: '#FEF3C7',
  borderBronze: palette.brandBronze,
} as const

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 20,
  xl: 28,
} as const
