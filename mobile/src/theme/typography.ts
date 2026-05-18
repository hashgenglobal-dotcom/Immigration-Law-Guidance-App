import { palette } from './tokens'

/** Inter 600 — headers; Public Sans 400 — body (loaded in root layout) */
export const fontFamily = {
  heading: 'Inter_600SemiBold',
  body: 'PublicSans_400Regular',
} as const

export const fontSize = {
  h1: 24,
  h2: 20,
  h3: 16,
  subheading: 16,
  body: 15,
  small: 13,
  caption: 11,
  title: 24,
  heading: 20,
} as const

/** @deprecated Use fontSize + textStyles */
export const typography = fontSize

export const textStyles = {
  h1: {
    fontFamily: fontFamily.heading,
    fontSize: fontSize.h1,
    fontWeight: '600' as const,
    color: palette.textPrimary,
    letterSpacing: -0.3,
  },
  h2: {
    fontFamily: fontFamily.heading,
    fontSize: fontSize.h2,
    fontWeight: '600' as const,
    color: palette.textPrimary,
    letterSpacing: -0.2,
  },
  h3: {
    fontFamily: fontFamily.heading,
    fontSize: fontSize.h3,
    fontWeight: '600' as const,
    color: palette.textPrimary,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.body,
    fontWeight: '400' as const,
    color: palette.textPrimary,
    lineHeight: 22,
  },
  bodyMuted: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.body,
    fontWeight: '400' as const,
    color: palette.textMuted,
    lineHeight: 22,
  },
  small: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.small,
    fontWeight: '400' as const,
    color: palette.textSecondary,
    lineHeight: 19,
  },
  caption: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.caption,
    fontWeight: '400' as const,
    color: palette.textMuted,
    lineHeight: 16,
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.small,
    fontWeight: '400' as const,
    color: palette.textPrimary,
  },
  button: {
    fontFamily: fontFamily.body,
    fontSize: fontSize.body,
    fontWeight: '400' as const,
  },
} as const
