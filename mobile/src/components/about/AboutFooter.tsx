import { StyleSheet, Text, View } from 'react-native'
import { Ionicons } from '@expo/vector-icons'
import { brand } from '@/lib/brand'
import { cardStandard, colors, fontFamily, radii, spacing } from '@/theme'

export function AboutFooter() {
  return (
    <View style={styles.card}>
      <View style={styles.topRule} />
      <View style={styles.brandRow}>
        <View style={styles.shieldSeal}>
          <Ionicons name="shield-checkmark" size={20} color={colors.surfaceWhite} />
        </View>
        <View style={styles.brandCopy}>
          <Text style={styles.brandName}>{brand.name}</Text>
          <Text style={styles.brandTagline}>{brand.tagline}</Text>
        </View>
      </View>
      <View style={styles.metaRow}>
        <Text style={styles.meta}>{brand.motto}</Text>
        <View style={styles.metaDot} />
        <Text style={styles.meta}>{brand.company}</Text>
      </View>
      <Text style={styles.previewNote}>Mobile preview · Mock data only</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    alignItems: 'center',
    padding: spacing.lg,
    paddingTop: spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(31, 40, 57, 0.08)',
    ...cardStandard,
  },
  topRule: {
    alignSelf: 'stretch',
    height: 3,
    borderRadius: 2,
    backgroundColor: colors.brandBronze,
    marginBottom: spacing.md,
    opacity: 0.85,
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
    marginBottom: spacing.sm,
    alignSelf: 'stretch',
  },
  shieldSeal: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.brandNavy,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(156, 123, 92, 0.35)',
  },
  brandCopy: {
    alignItems: 'flex-start',
    maxWidth: '70%',
  },
  brandName: {
    fontFamily: fontFamily.heading,
    fontSize: 17,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: -0.2,
  },
  brandTagline: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    color: colors.brandNavy,
    opacity: 0.7,
    marginTop: 2,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    marginTop: spacing.xs,
  },
  meta: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    fontWeight: '500',
    color: colors.brandBronze,
    letterSpacing: 0.2,
  },
  metaDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.brandBronze,
    opacity: 0.5,
  },
  previewNote: {
    fontFamily: fontFamily.body,
    fontSize: 10,
    color: colors.brandNavy,
    opacity: 0.4,
    marginTop: spacing.md,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
})
