import { useMemo, useState } from 'react'
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import {
  CitationCard,
  DisclaimerCard,
  RiskBadge,
  ScenarioCard,
  ScreenScroll,
} from '@/components'
import { DigitalBackdrop } from '@/components/digital'
import {
  ScenarioFilterPills,
  ScenarioListMeta,
  ScenarioSearchBar,
  ScenariosHeader,
} from '@/components/scenarios'
import { LEGAL_DISCLAIMER_SHORT } from '@/lib/legalCopy'
import { mockScenarios, type Scenario } from '@/lib/mockData'
import { cardStandard, colors, fontFamily, radii, spacing, typography } from '@/theme'

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
    <View style={styles.screen}>
      <DigitalBackdrop variant="scenarios" />
      <ScreenScroll contentStyle={styles.scroll}>
        <ScenariosHeader guideCount={mockScenarios.length} />

        <ScenarioSearchBar value={query} onChangeText={setQuery} />
        <ScenarioFilterPills value={riskFilter} onChange={setRiskFilter} />

        {filtered.length === 0 ? (
          <View style={styles.empty}>
            <View style={styles.emptyIcon}>
              <Ionicons name="search-outline" size={28} color={colors.brandBronze} />
            </View>
            <Text style={styles.emptyTitle}>No scenarios match</Text>
            <Text style={styles.emptyBody}>Try another search or clear filters.</Text>
            <Pressable
              onPress={() => {
                setQuery('')
                setRiskFilter('all')
              }}
              style={({ pressed }) => [styles.emptyActionBtn, pressed && styles.emptyActionPressed]}
            >
              <Text style={styles.emptyAction}>Clear filters</Text>
            </Pressable>
          </View>
        ) : (
          <>
            <ScenarioListMeta visible={filtered.length} total={mockScenarios.length} />
            <View style={styles.list}>
              {filtered.map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  onPress={() => setSelected(scenario)}
                />
              ))}
            </View>
          </>
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
              <View style={styles.modalHeaderMain}>
                <View style={styles.modalHeaderText}>
                  <Text style={styles.modalEyebrow}>Scenario guide</Text>
                  <Text style={styles.modalTitle}>{selected.title}</Text>
                  <RiskBadge level={selected.riskLevel} small />
                </View>
                <Pressable
                  onPress={() => setSelected(null)}
                  hitSlop={12}
                  style={({ pressed }) => [styles.closeBtn, pressed && styles.closeBtnPressed]}
                >
                  <Ionicons name="close" size={22} color={colors.surfaceWhite} />
                </Pressable>
              </View>
            </View>
            <ScrollView contentContainerStyle={styles.modalContent} showsVerticalScrollIndicator={false}>
              <Text style={styles.sectionLabel}>Overview</Text>
              <Text style={styles.body}>{selected.overview}</Text>
              <Text style={styles.sectionLabel}>Steps and key points</Text>
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
    </View>
  )
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.parchment,
  },
  scroll: {
    paddingTop: spacing.sm,
    paddingBottom: spacing.xl,
    backgroundColor: 'transparent',
    zIndex: 1,
  },
  list: {
    marginTop: spacing.xs,
  },
  empty: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
    paddingHorizontal: spacing.md,
    ...cardStandard,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.08)',
  },
  emptyIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.bronzeTint,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.md,
  },
  emptyTitle: {
    fontFamily: fontFamily.heading,
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.brandNavy,
  },
  emptyBody: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    color: colors.brandNavy,
    opacity: 0.7,
    marginTop: spacing.xs,
    textAlign: 'center',
  },
  emptyActionBtn: {
    marginTop: spacing.md,
    minHeight: 48,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    borderRadius: radii.full,
    backgroundColor: colors.brandNavy,
  },
  emptyActionPressed: {
    opacity: 0.9,
  },
  emptyAction: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.surfaceWhite,
  },
  modal: {
    flex: 1,
    backgroundColor: colors.parchment,
  },
  modalHeader: {
    backgroundColor: colors.brandNavy,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
    borderBottomWidth: 3,
    borderBottomColor: colors.brandBronze,
  },
  modalHeaderMain: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  modalHeaderText: {
    flex: 1,
    minWidth: 0,
    gap: spacing.xs,
  },
  modalEyebrow: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  modalTitle: {
    fontFamily: fontFamily.heading,
    fontSize: typography.subheading,
    fontWeight: '600',
    color: colors.surfaceWhite,
    lineHeight: 22,
    flexShrink: 1,
  },
  closeBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
  },
  closeBtnPressed: {
    opacity: 0.75,
  },
  modalContent: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  sectionLabel: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    color: colors.brandBronze,
    marginTop: spacing.md,
    marginBottom: spacing.xs,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 19,
    color: colors.brandNavy,
    opacity: 0.88,
  },
  bullet: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 19,
    color: colors.brandNavy,
    opacity: 0.88,
    marginBottom: 4,
  },
})
