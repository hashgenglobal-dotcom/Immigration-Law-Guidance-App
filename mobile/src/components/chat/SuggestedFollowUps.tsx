import { Pressable, StyleSheet, Text, View } from 'react-native'
import { colors, fontFamily, radii, spacing, typography } from '@/theme'

export function SuggestedFollowUps({
  suggestions,
  onSelect,
  disabled,
}: {
  suggestions: string[]
  onSelect: (text: string) => void
  disabled?: boolean
}) {
  if (!suggestions.length) return null

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>Continue the conversation</Text>
      <View style={styles.chips}>
        {suggestions.map((text) => (
          <Pressable
            key={text}
            onPress={() => onSelect(text)}
            disabled={disabled}
            style={({ pressed }) => [
              styles.chip,
              pressed && !disabled && styles.chipPressed,
              disabled && styles.chipDisabled,
            ]}
            accessibilityRole="button"
            accessibilityLabel={text}
          >
            <Text style={styles.chipText}>{text}</Text>
          </Pressable>
        ))}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    marginTop: spacing.sm,
    gap: spacing.xs,
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandBronze,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  chips: {
    gap: spacing.xs,
  },
  chip: {
    alignSelf: 'flex-start',
    maxWidth: '100%',
    backgroundColor: colors.surfaceWhite,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.35)',
    borderRadius: radii.full,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  chipPressed: {
    opacity: 0.88,
    backgroundColor: colors.bronzeTint,
  },
  chipDisabled: {
    opacity: 0.5,
  },
  chipText: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    lineHeight: 18,
    color: colors.brandNavy,
    fontWeight: '500',
  },
})
