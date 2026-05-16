import { useMemo, useState } from 'react'
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'
import {
  Chip,
  ChipRow,
  CitationCard,
  DisclaimerCard,
  RiskBadge,
  ScenarioCard,
  ScreenScroll,
} from '@/components'
import { mockScenarios, type Scenario } from '@/lib/mockData'
import { colors, radii, spacing, typography } from '@/theme'

type RiskFilter = 'all' | Scenario['riskLevel']

export default function ScenariosScreen() {
  const [selected, setSelected] = useState<Scenario | null>(null)
  const [query, setQuery] = useState('')
  const [riskFilter, setRiskFilter] = useState<RiskFilter>('all')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return mockScenarios.filter((s) => {
      const matchesRisk = riskFilter === 'all' || s.riskLevel === riskFilter
      const matchesQuery =
        !q ||
        s.title.toLowerCase().includes(q) ||
        s.shortDescription.toLowerCase().includes(q) ||
        s.overview.toLowerCase().includes(q)
      return matchesRisk && matchesQuery
    })
  }, [query, riskFilter])

  return (
    <>
      <ScreenScroll>
        <Text style={styles.intro}>
          General guides for common situations. Always confirm with official sources and consult an attorney for your
          specific case.
        </Text>

        <TextInput
          style={styles.search}
          value={query}
          onChangeText={setQuery}
          placeholder="Search scenarios…"
          placeholderTextColor={colors.textMuted}
          clearButtonMode="while-editing"
        />

        <ChipRow>
          {(['all', 'low', 'medium', 'high'] as const).map((level) => (
            <Chip
              key={level}
              label={level === 'all' ? 'All' : level}
              selected={riskFilter === level}
              onPress={() => setRiskFilter(level)}
            />
          ))}
        </ChipRow>

        {filtered.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>No scenarios match</Text>
            <Text style={styles.emptyBody}>Try another search or clear filters.</Text>
            <Pressable
              onPress={() => {
                setQuery('')
                setRiskFilter('all')
              }}
            >
              <Text style={styles.emptyAction}>Clear filters</Text>
            </Pressable>
          </View>
        ) : (
          filtered.map((scenario) => (
            <ScenarioCard key={scenario.id} scenario={scenario} onPress={() => setSelected(scenario)} />
          ))
        )}
      </ScreenScroll>

      <Modal
        visible={selected !== null}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setSelected(null)}
      >
        {selected ? (
          <View style={styles.modal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{selected.title}</Text>
              <Pressable
                onPress={() => setSelected(null)}
                hitSlop={12}
                style={({ pressed }) => [styles.closeBtn, pressed && styles.closeBtnPressed]}
              >
                <Text style={styles.close}>Close</Text>
              </Pressable>
            </View>
            <ScrollView contentContainerStyle={styles.modalContent} showsVerticalScrollIndicator={false}>
              <RiskBadge level={selected.riskLevel} />
              <Text style={styles.sectionLabel}>Overview</Text>
              <Text style={styles.body}>{selected.overview}</Text>
              <Text style={styles.sectionLabel}>Key points</Text>
              {selected.keyPoints.map((point, i) => (
                <Text key={i} style={styles.body}>
                  • {point}
                </Text>
              ))}
              <Text style={styles.sectionLabel}>Official sources</Text>
              {selected.sources.map((source, i) => (
                <CitationCard key={i} source={source} />
              ))}
              <DisclaimerCard title="Legal disclaimer">
                This is general legal information, not legal advice. Consult with a qualified immigration attorney for
                your specific situation.
              </DisclaimerCard>
            </ScrollView>
          </View>
        ) : null}
      </Modal>
    </>
  )
}

const styles = StyleSheet.create({
  intro: {
    fontSize: typography.body,
    lineHeight: 24,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  search: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
    fontSize: typography.body,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  empty: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: colors.border,
    borderRadius: radii.lg,
    backgroundColor: colors.surface,
  },
  emptyTitle: {
    fontSize: typography.subheading,
    fontWeight: '700',
    color: colors.text,
  },
  emptyBody: {
    fontSize: typography.small,
    color: colors.textMuted,
    marginTop: spacing.sm,
  },
  emptyAction: {
    marginTop: spacing.md,
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.gold,
  },
  modal: {
    flex: 1,
    backgroundColor: colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: spacing.md,
    padding: spacing.md,
    paddingTop: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
  },
  modalTitle: {
    flex: 1,
    fontSize: typography.heading,
    fontWeight: '700',
    color: colors.text,
  },
  closeBtn: {
    borderRadius: radii.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  closeBtnPressed: {
    opacity: 0.7,
  },
  close: {
    fontSize: typography.body,
    fontWeight: '600',
    color: colors.gold,
  },
  modalContent: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  sectionLabel: {
    fontSize: typography.small,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    color: colors.textMuted,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  body: {
    fontSize: typography.body,
    lineHeight: 24,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
})
