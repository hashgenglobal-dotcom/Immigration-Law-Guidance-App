import { Pressable, StyleSheet, Text, View } from 'react-native'
import { useRouter } from 'expo-router'
import { DisclaimerCard, PrimaryButton, ScreenScroll } from '@/components'
import { brand } from '@/lib/brand'
import { LEGAL_DISCLAIMER_FULL } from '@/lib/legalCopy'
import { colors, radii, spacing, typography } from '@/theme'

const QUICK_TOPICS = [
  'Asylum work authorization',
  'Notice to Appear',
  'Adjustment of status',
] as const

export default function HomeScreen() {
  const router = useRouter()

  return (
    <ScreenScroll contentStyle={styles.scroll}>
      <View style={styles.hero}>
        <Text style={styles.eyebrow}>{brand.motto}</Text>
        <Text style={styles.title}>{brand.name}</Text>
        <Text style={styles.tagline}>{brand.tagline}</Text>
        <Text style={styles.subtitle}>
          Plain-language guidance grounded in official sources—not unchecked AI memory.
        </Text>
      </View>

      <DisclaimerCard compact>{LEGAL_DISCLAIMER_FULL}</DisclaimerCard>

      <View style={styles.actions}>
        <PrimaryButton label="Ask a Question" onPress={() => router.push('/ask')} />
        <PrimaryButton
          label="Browse Scenarios"
          variant="secondary"
          onPress={() => router.push('/scenarios')}
        />
        <PrimaryButton label="About" variant="ghost" onPress={() => router.push('/about')} />
      </View>

      <Text style={styles.quickLabel}>Popular topics</Text>
      <View style={styles.pillRow}>
        {QUICK_TOPICS.map((topic) => (
          <Pressable
            key={topic}
            onPress={() => router.push('/ask')}
            style={({ pressed }) => [styles.pill, pressed && styles.pillPressed]}
          >
            <Text style={styles.pillText}>{topic}</Text>
          </Pressable>
        ))}
      </View>
    </ScreenScroll>
  )
}

const styles = StyleSheet.create({
  scroll: {
    paddingTop: spacing.sm,
  },
  hero: {
    backgroundColor: colors.navy,
    borderRadius: radii.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.bronze,
  },
  eyebrow: {
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.bronzeLight,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  title: {
    fontSize: typography.heading,
    fontWeight: '800',
    color: colors.onNavy,
    marginBottom: 2,
  },
  tagline: {
    fontSize: typography.small,
    fontWeight: '600',
    color: colors.cream,
    marginBottom: spacing.xs,
    opacity: 0.95,
  },
  subtitle: {
    fontSize: typography.caption,
    lineHeight: 16,
    color: colors.cream,
    opacity: 0.88,
  },
  actions: {
    marginTop: spacing.md,
    marginBottom: spacing.md,
  },
  quickLabel: {
    fontSize: typography.caption,
    fontWeight: '700',
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
    marginBottom: spacing.sm,
  },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs + 2,
  },
  pill: {
    backgroundColor: colors.surface,
    borderRadius: radii.full,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 6,
    paddingHorizontal: spacing.sm + 2,
  },
  pillPressed: {
    opacity: 0.85,
    borderColor: colors.bronze,
  },
  pillText: {
    fontSize: typography.caption,
    fontWeight: '500',
    color: colors.textSecondary,
  },
})
