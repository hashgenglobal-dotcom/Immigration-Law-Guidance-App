import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { DigitalHeroArt } from '@/components/digital'
import { AboutTrustStrip } from './AboutTrustStrip'
import { brand } from '@/lib/brand'
import { colors, fontFamily, radii, shadows, spacing } from '@/theme'

export function AboutHero() {
  return (
    <View style={styles.wrap}>
      <View style={styles.hero}>
        <DigitalHeroArt />
        <View style={styles.content}>
          <View style={styles.badgeRow}>
            <View style={styles.trustBadge}>
              <Ionicons name="ribbon-outline" size={14} color={colors.brandBronzeLight} />
              <Text style={styles.trustBadgeText}>Trust center</Text>
            </View>
          </View>
          <Text style={styles.title}>{brand.name}</Text>
          <Text style={styles.tagline}>{brand.tagline}</Text>
          <Text style={styles.body}>{brand.description}</Text>
          <View style={styles.mottoPill}>
            <Ionicons name="scale-outline" size={13} color={colors.surfaceWhite} />
            <Text style={styles.motto}>{brand.motto}</Text>
          </View>
          <AboutTrustStrip />
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: spacing.md,
  },
  hero: {
    position: 'relative',
    borderRadius: radii.card,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.45)',
    backgroundColor: colors.brandNavy,
    ...shadows.soft,
  },
  content: {
    padding: spacing.lg,
    zIndex: 1,
  },
  badgeRow: {
    flexDirection: 'row',
    marginBottom: spacing.sm,
  },
  trustBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 6,
    borderRadius: radii.full,
    backgroundColor: 'rgba(156, 123, 92, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  trustBadgeText: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 28,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: -0.5,
    marginBottom: spacing.xs,
  },
  tagline: {
    fontFamily: fontFamily.body,
    fontSize: 16,
    lineHeight: 24,
    color: colors.surfaceWhite,
    opacity: 0.94,
    marginBottom: spacing.sm,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    lineHeight: 20,
    color: colors.surfaceWhite,
    opacity: 0.8,
    marginBottom: spacing.md,
  },
  mottoPill: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 8,
    backgroundColor: colors.brandBronze,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.full,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  motto: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: 0.3,
  },
})
