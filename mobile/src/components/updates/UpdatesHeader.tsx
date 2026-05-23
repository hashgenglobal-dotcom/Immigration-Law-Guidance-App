import { StyleSheet, Text, View } from 'react-native'
import { colors, fontFamily, spacing, typography } from '@/theme'

export function UpdatesHeader({ total }: { total: number }) {
  return (
    <View style={styles.wrap}>
      <Text style={styles.eyebrow}>Official updates</Text>
      <Text style={styles.title}>Government announcements</Text>
      <Text style={styles.body}>
        Plain-language summaries of USCIS, DHS, and Federal Register releases. Always verify
        details on the official link—not legal advice.
      </Text>
      {total > 0 ? (
        <Text style={styles.meta}>{total} published item{total === 1 ? '' : 's'}</Text>
      ) : null}
    </View>
  )
}

const styles = StyleSheet.create({
  wrap: {
    marginBottom: spacing.md,
  },
  eyebrow: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    fontWeight: '600',
    color: colors.brandBronze,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  title: {
    fontFamily: fontFamily.heading,
    fontSize: typography.h2,
    fontWeight: '600',
    color: colors.brandNavy,
    letterSpacing: -0.3,
    marginBottom: spacing.xs,
  },
  body: {
    fontFamily: fontFamily.body,
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.brandNavy,
    opacity: 0.78,
  },
  meta: {
    fontFamily: fontFamily.body,
    fontSize: typography.caption,
    color: colors.brandBronze,
    marginTop: spacing.sm,
    fontWeight: '600',
  },
})
