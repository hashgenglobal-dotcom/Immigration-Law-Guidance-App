import { Pressable, StyleSheet, Text, View } from 'react-native'
import type { ClarificationOption } from '@/types/chat'
import { colors, fontFamily, radii, spacing, typography } from '@/theme'

type Props = {
  intro: string
  question: string
  options: ClarificationOption[]
  disclaimer: string
  onSelect: (option: ClarificationOption) => void
  disabled?: boolean
}

export function ClarificationOptions({
  intro,
  question,
  options,
  disclaimer,
  onSelect,
  disabled = false,
}: Props) {
  return (
    <View style={styles.wrap}>
      {intro ? <Text style={styles.intro}>{intro}</Text> : null}
      <Text style={styles.question}>{question}</Text>
      <View style={styles.chips}>
        {options.map((option) => (
          <Pressable
            key={option.value}
            style={({ pressed }) => [
              styles.chip,
              pressed && styles.chipPressed,
              disabled && styles.chipDisabled,
            ]}
            onPress={() => onSelect(option)}
            disabled={disabled}
            accessibilityRole="button"
            accessibilityLabel={option.label}
          >
            <Text style={styles.chipText}>{option.label}</Text>
          </Pressable>
        ))}
      </View>
      {disclaimer ? <Text style={styles.disclaimer}>{disclaimer}</Text> : null}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    gap: spacing.sm,
  },
  intro: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.brandNavy,
    opacity: 0.88,
  },
  question: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    fontWeight: '600',
    lineHeight: 20,
    color: colors.brandNavy,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  chip: {
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: spacing.xs + 2,
    borderRadius: radii.full,
    backgroundColor: colors.bronzeTint,
    borderWidth: 1,
    borderColor: 'rgba(184, 134, 11, 0.35)',
  },
  chipPressed: {
    opacity: 0.85,
    backgroundColor: colors.surfaceWhite,
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
  disclaimer: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    lineHeight: 17,
    color: colors.brandNavy,
    opacity: 0.75,
    fontStyle: 'italic',
    marginTop: spacing.xs,
  },
})
