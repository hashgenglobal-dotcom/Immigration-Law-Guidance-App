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
import { LEGAL_DISCLAIMER_SHORT } from '@/lib/legalCopy'
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
      <ScreenScroll contentStyle={styles.scroll}>
        <Text style={styles.intro}>
          Guides for common situations. Confirm with official sources and an attorney for your case.
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
              <View style={styles.modalHeaderText}>
                <Text style={styles.modalTitle}>{selected.title}</Text>
                <RiskBadge level={selected.riskLevel} small />
              </View>
              <Pressable
                onPress={() => setSelected(null)}
                hitSlop={12}
                style={({ pressed }) => [styles.closeBtn, pressed && styles.closeBtnPressed]}
              >
                <Text style={styles.close}>Close</Text>
              </Pressable>
            </View>
            <ScrollView contentContainerStyle={styles.modalContent} showsVerticalScrollIndicator={false}>
              <Text style={styles.sectionLabel}>Overview</Text>
              <Text style={styles.body}>{selected.overview}</Text>
              <Text style={styles.sectionLabel}>Key points</Text>
              {selected.keyPoints.map((point, i) => (
                <Text key={i} style={styles.bullet}>
                  · {point}
                </Text>
              ))}
              <Text style={styles.sectionLabel}>Official sources</Text>
              {selected.sources.map((source, i) => (
                <CitationCard key={i} source={source} compact />
              ))}
              <DisclaimerCard compact title="Legal disclaimer">
                {LEGAL_DISCLAIMER_SHORT}
              </DisclaimerCard>
            </ScrollView>
          </View>
        ) : null}
      </Modal>
    </>
  )
}

const styles = StyleSheet.create({
  scroll: {
    paddingTop: spacing.sm,
  },
  intro: {
    fontSize: typography.small,
    lineHeight: 18,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  search: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: typography.small,
    color: colors.text,
    marginBottom: spacing.sm,
  },
  empty: {
    alignItems: 'center',
    paddingVertical: spacing.lg,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: colors.border,
    borderRadius: radii.md,
    backgroundColor: colors.surface,
  },
  emptyTitle: {
    fontSize: typography.small,
    fontWeight: '700',
    color: colors.text,
  },
  emptyBody: {
    fontSize: typography.caption,
    color: colors.textMuted,
    marginTop: spacing.xs,
  },
  emptyAction: {
    marginTop: spacing.sm,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.bronzeDark,
  },
  modal: {
    flex: 1,
    backgroundColor: colors.background,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 4,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    backgroundColor: colors.surface,
  },
  modalHeaderText: {
    flex: 1,
    gap: spacing.xs,
  },
  modalTitle: {
    fontSize: typography.subheading,
    fontWeight: '700',
    color: colors.text,
    lineHeight: 20,
  },
  closeBtn: {
    borderRadius: radii.sm,
    paddingHorizontal: spacing.xs,
    paddingVertical: spacing.xs,
  },
  closeBtnPressed: {
    opacity: 0.7,
  },
  close: {
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.bronzeDark,
  },
  modalContent: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  sectionLabel: {
    fontSize: typography.caption,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    color: colors.textMuted,
    marginTop: spacing.md,
    marginBottom: spacing.xs,
  },
  body: {
    fontSize: typography.small,
    lineHeight: 19,
    color: colors.textSecondary,
  },
  bullet: {
    fontSize: typography.small,
    lineHeight: 19,
    color: colors.textSecondary,
    marginBottom: 4,
  },
})
