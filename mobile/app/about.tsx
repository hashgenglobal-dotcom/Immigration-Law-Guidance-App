import { StyleSheet, Text, View } from 'react-native'
import { DisclaimerCard, ScreenScroll } from '@/components'
import { colors, spacing, typography } from '@/theme'

function Section({ title, children }: { title: string; children: string }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <Text style={styles.sectionBody}>{children}</Text>
    </View>
  )
}

export default function AboutScreen() {
  return (
    <ScreenScroll>
      <Section
        title="What this app does"
        children="Provides general immigration law information in plain language. Explains common procedures and rights, links to official government sources, and offers scenario-based overviews. Designed for a privacy-first, citation-first experience once fully connected to verified legal text."
      />

      <Section
        title="What this app does not do"
        children="It does not provide legal advice, legal representation, or an attorney-client relationship. It does not replace consultation with a qualified immigration attorney. It does not handle emergencies. It does not store your questions in this mock mobile build."
      />

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Privacy-first design</Text>
        <Text style={styles.sectionBody}>
          The product goal is minimal data collection: process questions with strong privacy controls and ground
          answers in retrieved official materials rather than model memory alone.
        </Text>
      </View>

      <DisclaimerCard title="Not a lawyer">
        This application is an information tool only. It is not a law firm and does not act as your attorney. Never
        rely solely on this app for urgent or high-risk immigration matters.
      </DisclaimerCard>

      <DisclaimerCard title="Official sources first">
        Answers are intended to cite regulations, statutes, and agency guidance you can verify. Always read the
        linked official source and confirm it applies to your facts.
      </DisclaimerCard>

      <Text style={styles.footer}>Built by HashGen Global LLC · Mobile MVP (mock data only)</Text>
    </ScreenScroll>
  )
}

const styles = StyleSheet.create({
  section: {
    backgroundColor: colors.surface,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
    shadowColor: colors.navy,
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 1,
  },
  sectionTitle: {
    fontSize: typography.subheading,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.sm,
  },
  sectionBody: {
    fontSize: typography.body,
    lineHeight: 24,
    color: colors.textSecondary,
  },
  footer: {
    fontSize: typography.caption,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.md,
  },
})
