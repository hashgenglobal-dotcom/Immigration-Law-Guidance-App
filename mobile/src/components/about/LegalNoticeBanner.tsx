import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { LEGAL_DISCLAIMER_FULL } from '@/lib/legalCopy'
import { colors, fontFamily, radii, shadows, spacing, warningNotice } from '@/theme'

export function LegalNoticeBanner() {
  return (
    <View style={styles.outer}>
      <View style={styles.banner}>
        <View style={styles.bronzeRail} />
        <View style={styles.mesh} pointerEvents="none">
          {Array.from({ length: 6 }).map((_, i) => (
            <View key={i} style={[styles.meshDot, { left: `${12 + i * 16}%` as `${number}%` }]} />
          ))}
        </View>
        <View style={styles.content}>
          <View style={styles.headerRow}>
            <View style={styles.iconSeal}>
              <Ionicons name="warning" size={22} color={colors.surfaceWhite} />
            </View>
            <View style={styles.headerCopy}>
              <Text style={styles.eyebrow}>Legal notice</Text>
              <Text style={styles.heading}>NOT A LAWYER</Text>
            </View>
          </View>
          <View style={styles.divider} />
          <Text style={styles.body}>{LEGAL_DISCLAIMER_FULL}</Text>
        </View>
      </View>
    </View>
  )
}

const styles = StyleSheet.create({
  outer: {
    marginBottom: spacing.lg,
    ...shadows.soft,
  },
  banner: {
    width: '100%',
    flexDirection: 'row',
    backgroundColor: warningNotice.background,
    borderRadius: radii.card,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(156, 123, 92, 0.3)',
  },
  bronzeRail: {
    width: 5,
    backgroundColor: colors.brandBronze,
  },
  mesh: {
    ...StyleSheet.absoluteFillObject,
    left: 5,
  },
  meshDot: {
    position: 'absolute',
    top: 12,
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: colors.brandNavy,
    opacity: 0.08,
  },
  content: {
    flex: 1,
    padding: spacing.md,
    zIndex: 1,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  iconSeal: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.brandBronze,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    ...shadows.soft,
  },
  headerCopy: {
    flex: 1,
    gap: 2,
  },
  eyebrow: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    fontWeight: '600',
    color: colors.brandNavy,
    opacity: 0.55,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
  },
  heading: {
    fontFamily: fontFamily.heading,
    fontSize: 15,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: 0.5,
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(31, 40, 57, 0.12)',
    marginBottom: spacing.sm,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    lineHeight: 19,
    fontWeight: '400',
    color: colors.brandNavy,
    opacity: 0.88,
  },
})
