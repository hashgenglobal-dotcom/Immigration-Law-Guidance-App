import { Pressable, StyleSheet, Text } from 'react-native'
import { colors, fontFamily, layout, radii, spacing, typography } from '@/theme'

export function PrimaryButton({
  label,
  onPress,
  variant = 'primary',
  disabled,
  compact,
}: {
  label: string
  onPress: () => void
  variant?: 'primary' | 'secondary' | 'ghost' | 'onDark'
  disabled?: boolean
  compact?: boolean
}) {
  const isPrimary = variant === 'primary'
  const isOnDark = variant === 'onDark'
  const isGhost = variant === 'ghost'

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.base,
        compact && styles.baseCompact,
        isPrimary && styles.primary,
        variant === 'secondary' && styles.secondary,
        isOnDark && styles.onDark,
        isGhost && styles.ghost,
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
      ]}
      accessibilityRole="button"
    >
      <Text
        style={[
          styles.label,
          compact && styles.labelCompact,
          isPrimary && styles.labelPrimary,
          variant === 'secondary' && styles.labelSecondary,
          isOnDark && styles.labelOnDark,
          isGhost && styles.labelGhost,
        ]}
      >
        {label}
      </Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  base: {
    minHeight: layout.minTouchTarget,
    borderRadius: radii.button,
    paddingHorizontal: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  baseCompact: {
    minHeight: layout.minTouchTarget,
    marginBottom: 0,
  },
  primary: {
    backgroundColor: colors.brandNavy,
  },
  secondary: {
    backgroundColor: colors.surfaceWhite,
    borderWidth: 1.5,
    borderColor: colors.brandBronze,
  },
  onDark: {
    backgroundColor: colors.surfaceWhite,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  ghost: {
    backgroundColor: 'transparent',
    minHeight: layout.minTouchTarget,
    paddingHorizontal: spacing.sm,
  },
  disabled: {
    opacity: 0.45,
  },
  pressed: {
    opacity: 0.88,
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: typography.body,
    fontWeight: '400',
  },
  labelCompact: {
    fontSize: typography.small,
  },
  labelPrimary: {
    color: colors.onNavy,
  },
  labelSecondary: {
    color: colors.brandNavy,
  },
  labelOnDark: {
    color: colors.brandNavy,
    fontWeight: '600',
  },
  labelGhost: {
    color: colors.brandBronzeLight,
    fontWeight: '600',
  },
})
