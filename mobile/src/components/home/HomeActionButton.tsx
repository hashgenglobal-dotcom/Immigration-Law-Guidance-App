import { Pressable, StyleSheet, Text, View } from 'react-native'
import type { ComponentProps } from 'react'
import { Ionicons } from '@expo/vector-icons'
import { colors, fontFamily, layout, radii, shadows, spacing, typography } from '@/theme'

type IoniconName = ComponentProps<typeof Ionicons>['name']

export function HomeActionButton({
  label,
  icon,
  variant,
  onPress,
}: {
  label: string
  icon: IoniconName
  variant: 'primary' | 'outline'
  onPress: () => void
}) {
  const isPrimary = variant === 'primary'

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.base,
        isPrimary ? styles.primary : styles.secondary,
        pressed && (isPrimary ? styles.primaryPressed : styles.secondaryPressed),
      ]}
    >
      <View style={[styles.iconWrap, isPrimary ? styles.iconPrimary : styles.iconSecondary]}>
        <Ionicons
          name={icon}
          size={20}
          color={isPrimary ? colors.surfaceWhite : colors.brandBronze}
        />
      </View>
      <Text style={[styles.label, isPrimary ? styles.labelPrimary : styles.labelSecondary]}>
        {label}
      </Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    minHeight: layout.minTouchTarget,
    borderRadius: radii.button,
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
  },
  primary: {
    backgroundColor: colors.brandNavy,
    shadowColor: colors.brandNavy,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 5,
  },
  primaryPressed: {
    opacity: 0.92,
    transform: [{ scale: 0.99 }],
  },
  secondary: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: colors.brandBronze,
  },
  secondaryPressed: {
    opacity: 0.85,
    backgroundColor: 'rgba(156, 123, 92, 0.06)',
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: radii.button,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconPrimary: {
    backgroundColor: 'rgba(255, 255, 255, 0.14)',
  },
  iconSecondary: {
    backgroundColor: 'rgba(156, 123, 92, 0.1)',
  },
  label: {
    flex: 1,
    fontFamily: fontFamily.body,
    fontSize: typography.body,
    fontWeight: '400',
    letterSpacing: 0.1,
  },
  labelPrimary: {
    color: colors.surfaceWhite,
    fontWeight: '600',
  },
  labelSecondary: {
    color: colors.brandNavy,
    fontWeight: '600',
  },
})
