import { StyleSheet, Text, View } from 'react-native'
import { DisclaimerCard, ScreenScroll } from '@/components'
import { brand } from '@/lib/brand'
import { LEGAL_DISCLAIMER_FULL } from '@/lib/legalCopy'
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
    <ScreenScroll contentStyle={styles.scroll}>
      <Section title="What this app does">
        Plain-language immigration information, common procedures, and links to official government sources. Built for a
        privacy-first, citation-first experience when connected to verified legal text.
      </Section>

      <Section title="What this app does not do">
        No legal advice, representation, or attorney–client relationship. Does not replace an immigration attorney or
        handle emergencies. This preview does not store your questions.
      </Section>

      <Section title="Privacy-first design">
        Minimal data collection: process questions with strong privacy controls and ground answers in retrieved official
        materials—not model memory alone.
      </Section>

      <Section title="Official sources first">
        Answers cite regulations, statutes, and agency guidance you can verify. Read the linked source and confirm it
        applies to your facts.
      </Section>

      <DisclaimerCard compact title="Not a lawyer">
        {LEGAL_DISCLAIMER_FULL}
      </DisclaimerCard>

      <Text style={styles.footer}>
        {brand.name} · {brand.tagline}
        {'\n'}
        {brand.motto} · {brand.company} · Mobile preview (mock data)
      </Text>
    </ScreenScroll>
  )
}

const styles = StyleSheet.create({
  scroll: {
    paddingTop: spacing.sm,
  },
  section: {
    marginBottom: spacing.md,
    paddingBottom: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  sectionTitle: {
    fontSize: typography.small,
    fontWeight: '700',
    color: colors.text,
    marginBottom: spacing.xs,
  },
  sectionBody: {
    fontSize: typography.small,
    lineHeight: 19,
    color: colors.textSecondary,
  },
  footer: {
    fontSize: typography.caption,
    lineHeight: 16,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
})
