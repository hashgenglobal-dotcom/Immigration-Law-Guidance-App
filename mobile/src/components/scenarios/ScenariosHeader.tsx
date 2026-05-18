import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { colors, fontFamily, radii, shadows, spacing } from '@/theme'

export function ScenariosHeader({ guideCount }: { guideCount: number }) {
  return (
    <View style={styles.wrap}>
      <View style={styles.hero}>
        <View style={styles.iconRing}>
          <Ionicons name="library-outline" size={22} color={colors.surfaceWhite} />
        </View>
        <View style={styles.copy}>
          <Text style={styles.eyebrow}>Browse</Text>
          <Text style={styles.title}>Scenario guides</Text>
          <Text style={styles.subtitle}>
            Step-by-step paths for common situations—always verify with official sources.
          </Text>
        </View>
        <View style={styles.countBadge}>
          <Text style={styles.countValue}>{guideCount}</Text>
          <Text style={styles.countLabel}>guides</Text>
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
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    backgroundColor: colors.brandNavy,
    borderRadius: radii.card,
    padding: spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.35)',
    ...shadows.soft,
  },
  iconRing: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(156, 123, 92, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  copy: {
    flex: 1,
    paddingRight: spacing.xs,
  },
  eyebrow: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 2,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: 18,
    fontWeight: '600',
    color: colors.surfaceWhite,
    letterSpacing: -0.2,
    marginBottom: spacing.xs,
  },
  subtitle: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 17,
    color: colors.surfaceWhite,
    opacity: 0.82,
  },
  countBadge: {
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 44,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: radii.button,
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  countValue: {
    fontFamily: fontFamily.heading,
    fontSize: 18,
    fontWeight: '600',
    color: colors.surfaceWhite,
    lineHeight: 22,
  },
  countLabel: {
    fontFamily: fontFamily.body,
    fontSize: 9,
    fontWeight: '600',
    color: colors.brandBronzeLight,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
})
