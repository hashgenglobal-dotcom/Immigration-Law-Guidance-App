import { Pressable, StyleSheet, Text, View } from 'react-native'
import type { Scenario } from '@/lib/mockData'
import { RiskBadge } from './RiskBadge'
import { colors, radii, spacing, typography } from '@/theme'

export function ScenarioCard({
  scenario,
  onPress,
}: {
  scenario: Scenario
  onPress: () => void
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.card, pressed && styles.cardPressed]}
      accessibilityRole="button"
    >
      <View style={styles.row}>
        <Text style={styles.title} numberOfLines={2}>
          {scenario.title}
        </Text>
        <RiskBadge level={scenario.riskLevel} small />
      </View>
      <Text style={styles.description} numberOfLines={2}>
        {scenario.shortDescription}
      </Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 4,
    marginBottom: spacing.sm,
  },
  cardPressed: {
    backgroundColor: colors.creamMuted,
    borderColor: colors.bronze,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: spacing.sm,
    marginBottom: 4,
  },
  title: {
    flex: 1,
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.text,
    lineHeight: 18,
  },
  description: {
    fontSize: typography.caption,
    lineHeight: 16,
    color: colors.textMuted,
  },
})
