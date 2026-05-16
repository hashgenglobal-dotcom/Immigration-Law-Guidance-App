import { useState } from 'react'
import {
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native'
import {
  CitationCard,
  DisclaimerCard,
  RiskBadge,
  ScenarioCard,
  ScreenScroll,
} from '@/components'
import { mockScenarios, type Scenario } from '@/lib/mockData'
import { colors, spacing, typography } from '@/theme'

export default function ScenariosScreen() {
  const [selected, setSelected] = useState<Scenario | null>(null)

  return (
    <>
      <ScreenScroll>
        <Text style={styles.intro}>
          General guides for common situations. Always confirm with official sources and consult an attorney for
          your specific case.
        </Text>

        {mockScenarios.map((scenario) => (
          <ScenarioCard
            key={scenario.id}
            scenario={scenario}
            onPress={() => setSelected(scenario)}
          />
        ))}
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
              <Pressable onPress={() => setSelected(null)} hitSlop={12}>
                <Text style={styles.close}>Close</Text>
              </Pressable>
            </View>
            <ScrollView contentContainerStyle={styles.modalContent}>
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
                This is general legal information, not legal advice. Consult with a qualified immigration attorney
                for your specific situation.
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
    marginBottom: spacing.lg,
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
  close: {
    fontSize: typography.body,
    fontWeight: '600',
    color: colors.primary,
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
