import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { SourcePathLogoMark } from '@/components/brand/SourcePathLogoMark'
import { FadeIn } from '@/components/digital'
import { brand } from '@/lib/brand'
import { colors, fontFamily, radii, spacing } from '@/theme'

const PILLARS = [
  { icon: 'library-outline' as const, label: 'Official sources', sub: 'USCIS · eCFR · INA' },
  { icon: 'document-text-outline' as const, label: 'Citation-first', sub: 'Verify every answer' },
  { icon: 'shield-checkmark-outline' as const, label: 'Privacy-first', sub: 'Your questions stay yours' },
] as const

export function WelcomeShowcase() {
  return (
    <View style={styles.root}>
      <FadeIn>
        <View style={styles.logoRow}>
          <SourcePathLogoMark size={112} showExplainer />
        </View>
      </FadeIn>

      <FadeIn delay={120}>
        <Text style={styles.eyebrow}>Digital immigration law · Your rights, explained</Text>
        <Text style={styles.title}>{brand.name}</Text>
        <Text style={styles.tagline}>{brand.tagline}</Text>
        <Text style={styles.description}>{brand.description}</Text>
      </FadeIn>

      <FadeIn delay={280}>
        <View style={styles.mottoRow}>
          <Ionicons name="scale-outline" size={14} color={colors.brandBronzeLight} />
          <Text style={styles.motto}>{brand.motto}</Text>
        </View>
      </FadeIn>

      <FadeIn delay={380}>
        <View style={styles.pillars}>
          {PILLARS.map((p) => (
            <View key={p.label} style={styles.pillar}>
              <View style={styles.pillarIcon}>
                <Ionicons name={p.icon} size={18} color={colors.brandBronzeLight} />
              </View>
              <Text style={styles.pillarLabel}>{p.label}</Text>
              <Text style={styles.pillarSub}>{p.sub}</Text>
            </View>
          ))}
        </View>
      </FadeIn>
    </View>
  )
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    paddingTop: spacing.md,
  },
  logoRow: {
    alignItems: 'center',
    marginBottom: spacing.xl,
  },
  eyebrow: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: spacing.xs,
    textAlign: 'center',
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 42,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: -1,
    lineHeight: 46,
    marginBottom: spacing.xs,
    textAlign: 'center',
  },
  tagline: {
    fontFamily: fontFamily.body,
    fontSize: 18,
    lineHeight: 26,
    color: colors.surfaceWhite,
    opacity: 0.95,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  description: {
    fontFamily: fontFamily.body,
    fontSize: 14,
    lineHeight: 22,
    color: colors.surfaceWhite,
    opacity: 0.78,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  mottoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'center',
    gap: 8,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.full,
    backgroundColor: 'rgba(156, 123, 92, 0.22)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    marginBottom: spacing.lg,
  },
  motto: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: 0.3,
  },
  pillars: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  pillar: {
    flex: 1,
    padding: spacing.sm,
    borderRadius: radii.card,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  pillarIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(156, 123, 92, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.xs,
  },
  pillarLabel: {
    fontFamily: fontFamily.heading,
    fontSize: 11,
    fontWeight: '600',
    color: colors.surfaceWhite,
    marginBottom: 2,
  },
  pillarSub: {
    fontFamily: fontFamily.body,
    fontSize: 9,
    color: colors.surfaceWhite,
    opacity: 0.6,
    lineHeight: 12,
  },
})
