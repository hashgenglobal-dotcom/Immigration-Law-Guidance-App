import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { brand } from '@/lib/brand'
import { colors, fontFamily, radii, shadows, spacing } from '@/theme'

export function AboutHero() {
  return (
    <View style={styles.wrap}>
      <View style={styles.hero}>
        <View style={styles.topRow}>
          <View style={styles.iconSeal}>
            <Ionicons name="shield-checkmark" size={28} color={colors.surfaceWhite} />
          </View>
          <View style={styles.mottoPill}>
            <Ionicons name="scale-outline" size={12} color={colors.brandBronzeLight} />
            <Text style={styles.motto}>{brand.motto}</Text>
          </View>
        </View>
        <Text style={styles.eyebrow}>Trust center</Text>
        <Text style={styles.title}>{brand.name}</Text>
        <Text style={styles.tagline}>{brand.tagline}</Text>
        <Text style={styles.body}>
          {brand.description}
        </Text>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: spacing.lg,
  },
  hero: {
    backgroundColor: colors.brandNavy,
    borderRadius: radii.card,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.4)',
    ...shadows.soft,
  },
  topRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  iconSeal: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(156, 123, 92, 0.3)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mottoPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: colors.bronzeTint,
    paddingHorizontal: spacing.sm + 2,
    paddingVertical: 6,
    borderRadius: radii.full,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.35)',
  },
  motto: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: 0.4,
  },
  eyebrow: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    textTransform: 'uppercase',
    letterSpacing: 1.2,
    marginBottom: spacing.xs,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 26,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: -0.4,
    marginBottom: spacing.xs,
  },
  tagline: {
    fontFamily: fontFamily.body,
    fontSize: 15,
    lineHeight: 22,
    color: colors.surfaceWhite,
    opacity: 0.92,
    marginBottom: spacing.sm,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    lineHeight: 20,
    color: colors.surfaceWhite,
    opacity: 0.78,
  },
})
