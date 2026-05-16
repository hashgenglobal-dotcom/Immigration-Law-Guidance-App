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
      <View style={styles.accent} />
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
    borderRadius: radii.lg,
    padding: spacing.md,
    marginBottom: spacing.md,
    overflow: 'hidden',
    shadowColor: colors.navy,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    elevation: 3,
  },
  cardPressed: {
    transform: [{ scale: 0.98 }, { translateY: 1 }],
    borderColor: colors.gold,
    shadowOpacity: 0.14,
  },
  accent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: colors.gold,
    opacity: 0.85,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: spacing.sm,
    marginBottom: spacing.sm,
    marginTop: spacing.xs,
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
    color: colors.goldDark,
  },
})
