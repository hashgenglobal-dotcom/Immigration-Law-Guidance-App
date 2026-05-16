import { StyleSheet, Text, View } from 'react-native'
import { colors, spacing, typography } from '@/theme'

export function DisclaimerCard({
  title,
  children,
}: {
  title?: string
  children: string
}) {
  return (
    <View style={styles.card}>
      {title ? <Text style={styles.title}>{title}</Text> : null}
      <Text style={styles.body}>{children}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.disclaimerBg,
    borderColor: colors.disclaimerBorder,
    borderWidth: 1,
    borderRadius: 12,
    padding: spacing.md,
  },
  title: {
    fontSize: typography.small,
    fontWeight: '700',
    color: colors.disclaimerText,
    marginBottom: spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.4,
  },
  body: {
    fontSize: typography.small,
    lineHeight: 22,
    color: colors.disclaimerText,
  },
})
