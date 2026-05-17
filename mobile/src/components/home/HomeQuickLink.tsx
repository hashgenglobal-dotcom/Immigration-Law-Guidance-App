import { Pressable, StyleSheet, Text } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, fontFamily, layout, radii, spacing, typography } from '@/theme'

/** Compact pill nav — mirrors web `pill-link` row under the hero. */
export function HomeQuickLink({
  label,
  onPress,
}: {
  label: string
  onPress: () => void
}) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [styles.pill, pressed && styles.pillPressed]}
    >
      <Text style={styles.label}>{label}</Text>
      <Ionicons name="arrow-forward" size={14} color={colors.brandBronze} />
    </Pressable>
  )
}

const styles = StyleSheet.create({
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    minHeight: layout.minTouchTarget,
    paddingHorizontal: spacing.md,
    borderRadius: radii.full,
    backgroundColor: colors.surfaceWhite,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.3)',
  },
  pillPressed: {
    opacity: 0.85,
    backgroundColor: colors.parchment,
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandNavy,
  },
})
