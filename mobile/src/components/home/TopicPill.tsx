import { Pressable, StyleSheet, Text } from 'react-native'
import { colors, fontFamily, layout, radii, spacing, typography } from '@/theme'

const BRONZE_BORDER_30 = 'rgba(156, 123, 92, 0.3)'

export function TopicPill({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [styles.pill, pressed && styles.pillPressed]}
    >
      <Text style={styles.label}>{label}</Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  pill: {
    minHeight: layout.minTouchTarget,
    justifyContent: 'center',
    backgroundColor: colors.surfaceWhite,
    borderRadius: radii.full,
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderColor: BRONZE_BORDER_30,
  },
  pillPressed: {
    opacity: 0.78,
    backgroundColor: 'rgba(255, 255, 255, 0.92)',
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    fontWeight: '400',
    color: colors.brandNavy,
    letterSpacing: 0.1,
  },
})
