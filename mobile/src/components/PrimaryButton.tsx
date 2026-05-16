import { Pressable, StyleSheet, Text } from 'react-native'
import { colors, radii, spacing, typography } from '@/theme'

export function PrimaryButton({
  label,
  onPress,
  variant = 'primary',
  disabled,
  compact,
}: {
  label: string
  onPress: () => void
  variant?: 'primary' | 'secondary' | 'ghost'
  disabled?: boolean
  compact?: boolean
}) {
  const isPrimary = variant === 'primary'
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
    borderRadius: radii.md,
    paddingVertical: spacing.sm + 4,
    paddingHorizontal: spacing.md,
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  baseCompact: {
    paddingVertical: spacing.sm,
    marginBottom: 0,
  },
  primary: {
    backgroundColor: colors.navy,
  },
  secondary: {
    backgroundColor: colors.surface,
    borderWidth: 1.5,
    borderColor: colors.bronze,
  },
  ghost: {
    backgroundColor: 'transparent',
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.sm,
  },
  disabled: {
    opacity: 0.45,
  },
  pressed: {
    opacity: 0.88,
  },
  label: {
    fontSize: typography.body,
    fontWeight: '600',
  },
  labelCompact: {
    fontSize: typography.small,
  },
  labelPrimary: {
    color: colors.onNavy,
  },
  labelSecondary: {
    color: colors.navy,
  },
  labelGhost: {
    color: colors.bronzeDark,
    fontWeight: '600',
  },
})
