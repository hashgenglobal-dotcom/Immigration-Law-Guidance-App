import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native'
import type { UpdateTopic } from '@/types/updates'
import { colors, fontFamily, layout, radii, shadows, spacing, typography } from '@/theme'

export function TopicFilterPills({
  topics,
  selectedIds,
  onToggle,
  onClearAll,
}: {
  topics: UpdateTopic[]
  selectedIds: string[]
  onToggle: (topicId: string) => void
  onClearAll: () => void
}) {
  const showAll = selectedIds.length === 0

  return (
    <View style={styles.section}>
      <Text style={styles.sectionLabel}>Filter by topic</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.row}
      >
        <Pressable
          onPress={onClearAll}
          style={({ pressed }) => [
            styles.pill,
            showAll ? styles.pillActive : styles.pillInactive,
            pressed && styles.pillPressed,
          ]}
          accessibilityRole="tab"
          accessibilityState={{ selected: showAll }}
        >
          <Text style={[styles.label, showAll && styles.labelActive]}>All</Text>
        </Pressable>
        {topics
          .filter((t) => t.id !== 'general')
          .map((topic) => {
            const selected = selectedIds.includes(topic.id)
            return (
              <Pressable
                key={topic.id}
                onPress={() => onToggle(topic.id)}
                style={({ pressed }) => [
                  styles.pill,
                  selected ? styles.pillActive : styles.pillInactive,
                  pressed && styles.pillPressed,
                ]}
                accessibilityRole="tab"
                accessibilityState={{ selected }}
              >
                <Text style={[styles.label, selected && styles.labelActive]}>{topic.label}</Text>
              </Pressable>
            )
          })}
      </ScrollView>
    </View>
  )
}

const styles = StyleSheet.create({
  section: {
    marginBottom: spacing.md,
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
    gap: spacing.sm,
    paddingRight: spacing.md,
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
  },
  labelActive: {
    color: colors.surfaceWhite,
  },
})
