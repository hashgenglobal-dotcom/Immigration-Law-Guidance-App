import { Pressable, StyleSheet, Text, View } from 'react-native'
import type { RiskLevel } from '@/lib/mockData'
import { colors, fontFamily, layout, radii, shadows, spacing, typography } from '@/theme'

type Filter = 'all' | RiskLevel

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
]

export function ScenarioFilterPills({
  value,
  onChange,
}: {
  value: Filter
  onChange: (filter: Filter) => void
}) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionLabel}>Filter by risk</Text>
      <View style={styles.row} accessibilityRole="tablist">
        {FILTERS.map((f) => {
          const selected = value === f.value
          return (
            <Pressable
              key={f.value}
              onPress={() => onChange(f.value)}
              style={({ pressed }) => [
                styles.pill,
                selected ? styles.pillActive : styles.pillInactive,
                pressed && styles.pillPressed,
              ]}
              accessibilityRole="tab"
              accessibilityState={{ selected }}
            >
              <Text style={[styles.label, selected && styles.labelActive]}>{f.label}</Text>
            </Pressable>
          )
        })}
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  section: {
    marginBottom: spacing.md,
    padding: spacing.sm,
    borderRadius: radii.card,
    backgroundColor: 'rgba(31, 40, 57, 0.04)',
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.08)',
  },
  sectionLabel: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandNavy,
    opacity: 0.55,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: spacing.sm,
    marginLeft: spacing.xs,
  },
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  pill: {
    minHeight: layout.minTouchTarget,
    justifyContent: 'center',
    borderRadius: radii.full,
    paddingHorizontal: spacing.md,
  },
  pillActive: {
    backgroundColor: colors.brandNavy,
    ...shadows.soft,
  },
  pillInactive: {
    backgroundColor: colors.surfaceWhite,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.14)',
  },
  pillPressed: {
    opacity: 0.88,
  },
  label: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandNavy,
    textTransform: 'capitalize',
  },
  labelActive: {
    color: colors.surfaceWhite,
  },
})
