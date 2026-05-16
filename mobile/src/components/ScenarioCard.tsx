import { Pressable, StyleSheet, Text, View } from 'react-native'
import type { Scenario } from '@/lib/mockData'
import { RiskBadge } from './RiskBadge'
import { colors, spacing, typography } from '@/theme'

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
      <View style={styles.header}>
        <Text style={styles.title}>{scenario.title}</Text>
        <RiskBadge level={scenario.riskLevel} />
      </View>
      <Text style={styles.description}>{scenario.shortDescription}</Text>
      <Text style={styles.cta}>View overview →</Text>
    </Pressable>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: 14,
    padding: spacing.md,
    marginBottom: spacing.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  cardPressed: {
    opacity: 0.92,
    borderColor: colors.primaryLight,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  title: {
    flex: 1,
    fontSize: typography.subheading,
    fontWeight: '700',
    color: colors.text,
  },
  description: {
    fontSize: typography.body,
    lineHeight: 24,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  cta: {
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.primary,
  },
})
