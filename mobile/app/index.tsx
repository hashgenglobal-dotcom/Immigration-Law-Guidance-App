import { Text, StyleSheet, View } from 'react-native'
import { useRouter } from 'expo-router'
import { DisclaimerCard, PrimaryButton, ScreenScroll } from '@/components'
import { colors, radii, spacing, typography } from '@/theme'

const QUICK_TOPICS = [
  'Asylum work authorization',
  'Notice to Appear',
  'Adjustment of status',
] as const

export default function HomeScreen() {
  const router = useRouter()

  return (
    <ScreenScroll>
      <View style={styles.hero}>
        <View style={styles.heroAccent} />
        <Text style={styles.eyebrow}>HashGen Global LLC · MVP</Text>
        <Text style={styles.title}>Immigration Law Guidance</Text>
        <Text style={styles.subtitle}>
          Privacy-first legal information grounded in official sources—not unchecked AI memory.
        </Text>
      </View>

      <DisclaimerCard title="Important">
        {`GENERAL LEGAL INFORMATION, NOT LEGAL ADVICE.\nHIGH-RISK SITUATIONS - TAKE A LEGAL ADVICE FROM ATTORNEY`}
      </DisclaimerCard>

      <Text style={styles.quickLabel}>Popular topics</Text>
      <View style={styles.pillRow}>
        {QUICK_TOPICS.map((topic) => (
          <View key={topic} style={styles.pill}>
            <Text style={styles.pillText}>{topic}</Text>
          </View>
        ))}
      </View>

      <View style={styles.actions}>
        <PrimaryButton label="Ask a Question" onPress={() => router.push('/ask')} />
        <PrimaryButton
          label="Browse Scenarios"
          variant="secondary"
          onPress={() => router.push('/scenarios')}
        />
        <PrimaryButton label="About" variant="secondary" onPress={() => router.push('/about')} />
      </View>

      <Text style={styles.footer}>
        This app does not provide legal advice and does not replace an immigration attorney.
      </Text>
    </ScreenScroll>
  )
}

const styles = StyleSheet.create({
  hero: {
    backgroundColor: colors.navy,
    borderRadius: radii.lg,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.navyMuted,
    overflow: 'hidden',
  },
  heroAccent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    backgroundColor: colors.gold,
  },
  eyebrow: {
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.goldLight,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: spacing.sm,
  },
  title: {
    fontSize: typography.title,
    fontWeight: '800',
    color: colors.onNavy,
    marginBottom: spacing.sm,
  },
  subtitle: {
    fontSize: typography.body,
    lineHeight: 24,
    color: colors.cream,
    opacity: 0.92,
  },
  quickLabel: {
    fontSize: typography.small,
    fontWeight: '700',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: spacing.sm,
  },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  pill: {
    backgroundColor: colors.surface,
    borderRadius: radii.full,
    borderWidth: 1,
    borderColor: colors.goldLight,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  pillText: {
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  actions: {
    marginBottom: spacing.md,
  },
  footer: {
    fontSize: typography.small,
    lineHeight: 22,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: spacing.md,
  },
})
