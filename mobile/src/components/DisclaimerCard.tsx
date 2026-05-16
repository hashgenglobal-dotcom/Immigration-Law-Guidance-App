import { StyleSheet, Text, View } from 'react-native'
import { colors, spacing, typography } from '@/theme'

export function DisclaimerCard({
  title,
  children,
  compact,
}: {
  title?: string
  children: string
  compact?: boolean
}) {
  return (
    <View style={[styles.card, compact && styles.cardCompact]}>
      {title ? <Text style={[styles.title, compact && styles.titleCompact]}>{title}</Text> : null}
      <Text style={[styles.body, compact && styles.bodyCompact]}>{children}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.disclaimerBg,
    borderColor: colors.disclaimerBorder,
    borderWidth: 1,
    borderRadius: 10,
    padding: spacing.md,
  },
  cardCompact: {
    padding: spacing.sm + 2,
    borderRadius: 8,
  },
  title: {
    fontSize: typography.caption,
    fontWeight: '700',
    color: colors.disclaimerText,
    marginBottom: spacing.xs,
    textTransform: 'uppercase',
    letterSpacing: 0.35,
  },
  titleCompact: {
    marginBottom: 2,
  },
  body: {
    fontSize: typography.small,
    lineHeight: 20,
    color: colors.disclaimerText,
  },
  bodyCompact: {
    fontSize: typography.caption,
    lineHeight: 16,
  },
})
